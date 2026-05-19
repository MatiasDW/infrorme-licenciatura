from __future__ import annotations

import json
import re
from urllib.request import Request, urlopen
from typing import Any, Iterable, Optional

from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi

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


def _youtube_dl(options: Optional[dict[str, Any]] = None) -> YoutubeDL:
    base_options = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": False,
        "nocheckcertificate": True,
    }
    if options:
        base_options.update(options)
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


def _discover_channel_tab_via_html(tab_url: str, tab: str) -> list[dict[str, Any]]:
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
    discovered: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("contentType") == "LOCKUP_CONTENT_TYPE_VIDEO" and node.get("contentId"):
                discovered.append(
                    {
                        "video_id": node["contentId"],
                        "title": (
                            ((node.get("rendererContext") or {}).get("accessibilityContext") or {}).get("label")
                            or node["contentId"]
                        ),
                        "url": build_video_url(node["contentId"]),
                        "source_tab": tab,
                        "timestamp": None,
                    }
                )
            elif node.get("videoId"):
                title = _extract_text(node.get("title")) or _extract_text(node.get("headline"))
                if not title:
                    title = ((node.get("accessibility") or {}).get("accessibilityData") or {}).get("label")
                discovered.append(
                    {
                        "video_id": node["videoId"],
                        "title": title or node["videoId"],
                        "url": build_video_url(node["videoId"]),
                        "source_tab": tab,
                        "timestamp": None,
                    }
                )
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in discovered:
        video_id = item["video_id"]
        if video_id in seen:
            continue
        seen.add(video_id)
        deduped.append(item)

    return deduped


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

    cleaned_segments = [
        {
            "text": (segment.get("text") or "").strip(),
            "start": float(segment.get("start", 0.0)),
            "duration": float(segment.get("duration", 0.0)),
        }
        for segment in raw_segments
        if (segment.get("text") or "").strip()
    ]

    transcript_text = " ".join(segment["text"] for segment in cleaned_segments)

    return {
        "transcript_source": "youtube-transcript-api",
        "transcript_language": getattr(transcript, "language", None),
        "transcript_language_code": getattr(transcript, "language_code", None),
        "transcript_is_generated": getattr(transcript, "is_generated", None),
        "transcript_is_translatable": getattr(transcript, "is_translatable", None),
        "transcript_segments": cleaned_segments,
        "transcript_text": transcript_text,
        "transcript_error": None,
    }


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


def discover_channel_matches(channel_url: str, title_query: str, max_videos: int) -> list[dict[str, Any]]:
    normalized_query = normalize_text(title_query)
    search_depth = min(max(max_videos * 6, 50), 200)
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
            tab_entries = _discover_channel_tab_via_html(tab_url, tab)

        if not tab_entries:
            continue

        successful_tabs += 1

        for entry in tab_entries:
            video_id = entry.get("video_id") or entry.get("id") or extract_video_id(entry.get("url") or "")
            title = entry.get("title") or ""
            if not video_id or video_id in discovered:
                continue
            if normalized_query and normalized_query not in normalize_text(title):
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

    ordered = sorted(
        discovered.values(),
        key=lambda item: item.get("timestamp") or 0,
        reverse=True,
    )
    return ordered[:max_videos]


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
