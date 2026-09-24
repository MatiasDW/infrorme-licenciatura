from __future__ import annotations

import json
import re
from urllib.request import Request, urlopen
from typing import Any, Iterable, Optional

from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi

from app.config import settings
from app.utils import (
    build_channel_tab_url,
    build_video_url,
    extract_video_id,
    has_transcript_hint,
    normalize_text,
    parse_iso_date,
    parse_publish_date,
    parse_upload_date,
    prune_video_payload,
)


PREFERRED_TRANSCRIPT_LANGUAGES = ["es", "es-419", "en", "en-US"]
INITIAL_DATA_RE = re.compile(r"var ytInitialData = (\{.*?\});")
PLAYER_RESPONSE_RE = re.compile(r"var ytInitialPlayerResponse = (\{.*?\});")
INNERTUBE_API_KEY_RE = re.compile(r'INNERTUBE_API_KEY":"([^"]+)')
INNERTUBE_CLIENT_VERSION_RE = re.compile(r'INNERTUBE_CLIENT_VERSION":"([^"]+)')


def _youtube_dl(options: Optional[dict[str, Any]] = None) -> YoutubeDL:
    base_options = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": False,
        "nocheckcertificate": True,
    }
    if options:
        base_options.update(options)
    if settings.youtube_cookies_file:
        base_options["cookiefile"] = settings.youtube_cookies_file
    if settings.youtube_proxy_url and "proxy" not in base_options:
        base_options["proxy"] = settings.youtube_proxy_url
    return YoutubeDL(base_options)


def _extract_text(value: Any) -> Optional[str]:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if "simpleText" in value:
            return value["simpleText"]
        if "runs" in value:
            return "".join(run.get("text", "") for run in value["runs"])
    return None


def _channel_video_entries(node: Any, tab: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("contentType") == "LOCKUP_CONTENT_TYPE_VIDEO" and value.get("contentId"):
                video_id = value["contentId"]
                entries.append(
                    {
                        "video_id": video_id,
                        "title": (
                            ((value.get("rendererContext") or {}).get("accessibilityContext") or {}).get("label")
                            or video_id
                        ),
                        "url": build_video_url(video_id),
                        "source_tab": tab,
                        "timestamp": None,
                    }
                )
            elif value.get("videoId"):
                video_id = value["videoId"]
                title = _extract_text(value.get("title")) or _extract_text(value.get("headline"))
                if not title:
                    title = ((value.get("accessibility") or {}).get("accessibilityData") or {}).get("label")
                entries.append(
                    {
                        "video_id": video_id,
                        "title": title or video_id,
                        "url": build_video_url(video_id),
                        "source_tab": tab,
                        "timestamp": None,
                    }
                )
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(node)
    return entries


def _channel_continuation_tokens(node: Any) -> list[str]:
    tokens: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            command = value.get("continuationCommand")
            if isinstance(command, dict) and command.get("token"):
                tokens.append(command["token"])
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(node)
    return list(dict.fromkeys(tokens))


def _dedupe_channel_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in entries:
        video_id = item.get("video_id")
        if not video_id or video_id in seen:
            continue
        seen.add(video_id)
        deduped.append(item)
    return deduped


def _fetch_channel_continuation(api_key: str, client_version: str, token: str) -> dict[str, Any]:
    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": client_version,
            }
        },
        "continuation": token,
    }
    request = Request(
        f"https://www.youtube.com/youtubei/v1/browse?key={api_key}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36"
            ),
        },
    )
    return json.loads(urlopen(request, timeout=30).read().decode("utf-8", errors="ignore"))


def _discover_channel_tab_via_html(
    tab_url: str,
    tab: str,
    max_items: int = 1000,
) -> list[dict[str, Any]]:
    request = Request(
        tab_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36"
            )
        },
    )
    html = urlopen(request, timeout=30).read().decode("utf-8", errors="ignore")
    match = INITIAL_DATA_RE.search(html)
    if not match:
        return []

    data = json.loads(match.group(1))
    discovered = _dedupe_channel_entries(_channel_video_entries(data, tab))
    api_key_match = INNERTUBE_API_KEY_RE.search(html)
    client_version_match = INNERTUBE_CLIENT_VERSION_RE.search(html)
    tokens = _channel_continuation_tokens(data)

    if not api_key_match or not client_version_match:
        return discovered[:max_items]

    api_key = api_key_match.group(1)
    client_version = client_version_match.group(1)
    visited_tokens: set[str] = set()
    pages = 0

    while tokens and len(discovered) < max_items and pages < 200:
        token = tokens.pop(0)
        if token in visited_tokens:
            continue
        visited_tokens.add(token)
        try:
            continuation = _fetch_channel_continuation(api_key, client_version, token)
        except Exception:
            break

        discovered = _dedupe_channel_entries(discovered + _channel_video_entries(continuation, tab))
        for continuation_token in _channel_continuation_tokens(continuation):
            if continuation_token not in visited_tokens:
                tokens.append(continuation_token)
        pages += 1

    return discovered[:max_items]


def fetch_video_metadata(url_or_id: str) -> dict[str, Any]:
    video_id = extract_video_id(url_or_id)
    target_url = build_video_url(video_id) if video_id else url_or_id
    try:
        with _youtube_dl() as ydl:
            return ydl.extract_info(target_url, download=False)
    except Exception:
        return _fetch_video_metadata_via_html(target_url)


def _fetch_video_metadata_via_html(video_url: str) -> dict[str, Any]:
    request = Request(
        video_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36"
            )
        },
    )
    html = urlopen(request, timeout=30).read().decode("utf-8", errors="ignore")
    match = PLAYER_RESPONSE_RE.search(html)
    if not match:
        raise RuntimeError("Could not extract video metadata from the public watch page")

    data = json.loads(match.group(1))
    video_details = data.get("videoDetails") or {}
    microformat = (data.get("microformat") or {}).get("playerMicroformatRenderer") or {}
    video_id = video_details.get("videoId") or extract_video_id(video_url)
    if not video_id:
        raise RuntimeError("Could not determine video id from the watch page")

    return {
        "id": video_id,
        "webpage_url": build_video_url(video_id),
        "title": video_details.get("title") or video_id,
        "channel_id": video_details.get("channelId"),
        "channel": video_details.get("author"),
        "uploader": video_details.get("author"),
        "duration": int(video_details["lengthSeconds"]) if video_details.get("lengthSeconds") else None,
        "timestamp": None,
        "publish_date": microformat.get("publishDate"),
        "upload_date": microformat.get("uploadDate"),
        "description": video_details.get("shortDescription"),
        "raw_payload": {
            "videoDetails": video_details,
            "microformat": microformat,
        },
    }


def fetch_transcript_payload(video_id: str) -> dict[str, Any]:
    try:
        if settings.youtube_proxy_url:
            from youtube_transcript_api.proxies import GenericProxyConfig

            api = YouTubeTranscriptApi(
                proxy_config=GenericProxyConfig(
                    http_url=settings.youtube_proxy_url,
                    https_url=settings.youtube_proxy_url,
                )
            )
        else:
            api = YouTubeTranscriptApi()
        if hasattr(api, "list"):
            transcript_list = api.list(video_id)
        elif hasattr(api, "list_transcripts"):
            transcript_list = api.list_transcripts(video_id)
        elif hasattr(YouTubeTranscriptApi, "list_transcripts"):
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        else:
            raise RuntimeError("Installed youtube-transcript-api version does not support transcript listing")

        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(PREFERRED_TRANSCRIPT_LANGUAGES)
        except Exception:
            pass

        if transcript is None:
            try:
                transcript = transcript_list.find_transcript(PREFERRED_TRANSCRIPT_LANGUAGES)
            except Exception:
                pass

        if transcript is None:
            for candidate in transcript_list:
                transcript = candidate
                break

        if transcript is None:
            raise RuntimeError("No transcript candidates were found for this video")

        fetched = transcript.fetch()
        raw_segments = fetched.to_raw_data() if hasattr(fetched, "to_raw_data") else list(fetched)
        cleaned_segments = _clean_transcript_segments(raw_segments)

        return _transcript_payload(
            cleaned_segments,
            source="youtube-transcript-api",
            language=getattr(transcript, "language", None),
            language_code=getattr(transcript, "language_code", None),
            is_generated=getattr(transcript, "is_generated", None),
            is_translatable=getattr(transcript, "is_translatable", None),
        )
    except Exception as api_error:
        try:
            return _fetch_transcript_payload_via_ytdlp(video_id)
        except Exception as fallback_error:
            raise RuntimeError(f"{api_error}; yt-dlp fallback: {fallback_error}") from fallback_error


def _clean_transcript_segments(raw_segments: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "text": (segment.get("text") or "").strip(),
            "start": float(segment.get("start", 0.0)),
            "duration": float(segment.get("duration", 0.0)),
        }
        for segment in raw_segments
        if (segment.get("text") or "").strip()
    ]


def _transcript_payload(
    segments: list[dict[str, Any]],
    *,
    source: str,
    language: str | None,
    language_code: str | None,
    is_generated: bool | None,
    is_translatable: bool | None,
) -> dict[str, Any]:
    return {
        "transcript_source": source,
        "transcript_language": language,
        "transcript_language_code": language_code,
        "transcript_is_generated": is_generated,
        "transcript_is_translatable": is_translatable,
        "transcript_segments": segments,
        "transcript_text": " ".join(segment["text"] for segment in segments),
        "transcript_error": None,
    }


def _fetch_transcript_payload_via_ytdlp(video_id: str) -> dict[str, Any]:
    """Use an alternate YouTube player client when transcript API requests are blocked."""
    options = {
        "extractor_args": {"youtube": {"player_client": ["android"]}},
    }
    with _youtube_dl(options) as ydl:
        info = ydl.extract_info(build_video_url(video_id), download=False)

        subtitle_map = info.get("subtitles") or {}
        automatic_map = info.get("automatic_captions") or {}
        selected_map = {}
        selected_key = None
        is_generated = False
        for candidate_map, candidate_generated in ((subtitle_map, False), (automatic_map, True)):
            for language in PREFERRED_TRANSCRIPT_LANGUAGES:
                selected_key = next(
                    (
                        key
                        for key in candidate_map
                        if key == language or key.startswith(f"{language}-")
                    ),
                    None,
                )
                if selected_key:
                    selected_map = candidate_map
                    is_generated = candidate_generated
                    break
            if selected_key:
                break

        if not selected_key:
            selected_map = subtitle_map or automatic_map
            selected_key = next(iter(selected_map), None)
            is_generated = not bool(subtitle_map)
        if not selected_key:
            raise RuntimeError("No subtitle candidates were found")

        formats = selected_map[selected_key]
        subtitle_format = next((item for item in formats if item.get("ext") == "json3"), formats[0])
        subtitle_data = json.loads(ydl.urlopen(subtitle_format["url"]).read().decode("utf-8"))
        raw_segments = []
        for event in subtitle_data.get("events", []):
            text = "".join(segment.get("utf8", "") for segment in event.get("segs") or []).strip()
            if text:
                raw_segments.append(
                    {
                        "text": text,
                        "start": float(event.get("tStartMs", 0)) / 1000,
                        "duration": float(event.get("dDurationMs", 0)) / 1000,
                    }
                )

    return _transcript_payload(
        _clean_transcript_segments(raw_segments),
        source="yt-dlp-subtitles",
        language=selected_key,
        language_code=selected_key,
        is_generated=is_generated,
        is_translatable=True,
    )


def build_video_payload(url_or_id: str) -> dict[str, Any]:
    info = fetch_video_metadata(url_or_id)
    video_id = info.get("id") or extract_video_id(url_or_id)
    if not video_id:
        raise ValueError("Could not determine the YouTube video id")

    description = info.get("description")
    publish_date = None
    if isinstance(info.get("publish_date"), str):
        publish_date = parse_iso_date(info.get("publish_date"))
    if publish_date is None:
        publish_date = parse_publish_date(info.get("timestamp"))

    upload_date = None
    if isinstance(info.get("upload_date"), str) and "-" in info.get("upload_date", ""):
        upload_date = parse_iso_date(info.get("upload_date"))
    if upload_date is None:
        upload_date = parse_upload_date(info.get("upload_date"))

    payload = {
        "video_id": video_id,
        "url": info.get("webpage_url") or build_video_url(video_id),
        "title": info.get("title") or f"YouTube video {video_id}",
        "channel_id": info.get("channel_id"),
        "channel_name": info.get("channel") or info.get("uploader"),
        "duration_seconds": info.get("duration"),
        "publish_date": publish_date,
        "upload_date": upload_date,
        "description": description,
        "description_has_transcript_hint": has_transcript_hint(description),
        "raw_payload": prune_video_payload(info.get("raw_payload") or info),
    }

    try:
        payload.update(fetch_transcript_payload(video_id))
    except Exception as exc:
        payload.update(
            {
                "transcript_source": "youtube-transcript-api",
                "transcript_language": None,
                "transcript_language_code": None,
                "transcript_is_generated": None,
                "transcript_is_translatable": None,
                "transcript_segments": [],
                "transcript_text": None,
                "transcript_error": str(exc),
            }
        )

    return payload


def build_channel_video_payload(item: dict[str, Any]) -> dict[str, Any]:
    """Build a persistable record without a second YouTube metadata scrape.

    Channel discovery already provides the stable video id and title. Reusing those
    values is important for bulk imports because fetching every watch page triggers
    YouTube rate limits before transcript fetching can finish.
    """
    video_id = item["video_id"]
    payload = {
        "video_id": video_id,
        "url": item.get("url") or build_video_url(video_id),
        "title": item.get("title") or video_id,
        "channel_id": None,
        "channel_name": None,
        "duration_seconds": None,
        "publish_date": None,
        "upload_date": None,
        "description": None,
        "description_has_transcript_hint": False,
        "raw_payload": {
            "discovery_source": "youtube-channel",
            "source_tab": item.get("source_tab"),
        },
    }

    try:
        payload.update(fetch_transcript_payload(video_id))
    except Exception as exc:
        payload.update(
            {
                "transcript_source": "youtube-transcript-api",
                "transcript_language": None,
                "transcript_language_code": None,
                "transcript_is_generated": None,
                "transcript_is_translatable": None,
                "transcript_segments": [],
                "transcript_text": None,
                "transcript_error": str(exc),
            }
        )

    return payload


def discover_channel_matches(
    channel_url: str,
    title_query: str = "",
    max_videos: int = 1000,
    all_content: bool = False,
) -> list[dict[str, Any]]:
    normalized_queries = [
        normalize_text(term)
        for term in re.split(r"[|,]", title_query or "")
        if normalize_text(term)
    ]
    search_depth = min(max(max_videos * 2, 50), 5000)
    discovered: dict[str, dict[str, Any]] = {}
    successful_tabs = 0

    for tab in ("videos", "streams"):
        tab_url = build_channel_tab_url(channel_url, tab)
        tab_entries: list[dict[str, Any]] = []
        try:
            with _youtube_dl(
                {
                    "extract_flat": "in_playlist",
                    "playlistend": search_depth,
                }
            ) as ydl:
                info = ydl.extract_info(tab_url, download=False)
            tab_entries = info.get("entries") or []
        except Exception:
            tab_entries = []

        if not tab_entries:
            tab_entries = _discover_channel_tab_via_html(tab_url, tab, max_items=search_depth)

        if not tab_entries:
            continue

        successful_tabs += 1

        for entry in tab_entries:
            video_id = entry.get("video_id") or entry.get("id") or extract_video_id(entry.get("url") or "")
            title = entry.get("title") or ""
            if not video_id or video_id in discovered:
                continue
            normalized_title = normalize_text(title)
            if not all_content and normalized_queries and not any(
                query in normalized_title for query in normalized_queries
            ):
                continue
            discovered[video_id] = {
                "video_id": video_id,
                "title": title,
                "url": build_video_url(video_id),
                "source_tab": tab,
                "timestamp": entry.get("timestamp"),
            }

    if successful_tabs == 0:
        raise RuntimeError("Could not inspect channel videos or streams")

    ordered_by_tab = {
        tab: sorted(
            (item for item in discovered.values() if item.get("source_tab") == tab),
            key=lambda item: item.get("timestamp") or 0,
            reverse=True,
        )
        for tab in ("streams", "videos")
    }
    balanced: list[dict[str, Any]] = []
    index = 0
    while len(balanced) < max_videos:
        added = False
        for tab in ("streams", "videos"):
            entries = ordered_by_tab[tab]
            if index < len(entries):
                balanced.append(entries[index])
                added = True
                if len(balanced) >= max_videos:
                    break
        if not added:
            break
        index += 1

    return balanced


def search_transcript_segments(segments: Iterable[dict[str, Any]], query: str, max_results: int = 6) -> list[dict[str, Any]]:
    normalized_query = normalize_text(query)
    if not normalized_query:
        return []

    matches = []
    for index, segment in enumerate(segments):
        normalized_segment = normalize_text(segment.get("text", ""))
        if normalized_query in normalized_segment:
            matches.append(
                {
                    "index": index,
                    "start": segment.get("start"),
                    "duration": segment.get("duration"),
                    "text": segment.get("text"),
                }
            )
        if len(matches) >= max_results:
            break

    return matches
