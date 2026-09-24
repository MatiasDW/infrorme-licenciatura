from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timezone
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse


TRANSCRIPT_HINT_RE = re.compile(r"\b(transcrip|subtit|caption|cc)\b", re.IGNORECASE)


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return without_accents.casefold().strip()


def parse_upload_date(value: str | None) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except ValueError:
        return None


def parse_iso_date(value: str | None) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_publish_date(timestamp: int | float | None) -> Optional[date]:
    if timestamp is None:
        return None
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).date()
    except (OverflowError, OSError, ValueError):
        return None


def has_transcript_hint(description: str | None) -> bool:
    if not description:
        return False
    return bool(TRANSCRIPT_HINT_RE.search(description))


def extract_video_id(url_or_id: str) -> Optional[str]:
    raw_value = (url_or_id or "").strip()
    if not raw_value:
        return None
    if re.fullmatch(r"[\w-]{11}", raw_value):
        return raw_value

    parsed = urlparse(raw_value)
    host = parsed.netloc.lower()
    path_parts = [part for part in parsed.path.split("/") if part]

    if "youtu.be" in host and path_parts:
        return path_parts[0]

    if parsed.query:
        query_id = parse_qs(parsed.query).get("v")
        if query_id:
            return query_id[0]

    if path_parts and path_parts[0] in {"shorts", "embed", "live", "watch"} and len(path_parts) > 1:
        return path_parts[1]

    if path_parts:
        candidate = path_parts[-1]
        if re.fullmatch(r"[\w-]{11}", candidate):
            return candidate

    return None


def build_video_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def build_channel_tab_url(channel_url: str, tab: str) -> str:
    clean = channel_url.rstrip("/")
    for suffix in ("/videos", "/streams", "/featured", "/live"):
        if clean.endswith(suffix):
            clean = clean[: -len(suffix)]
            break
    return f"{clean}/{tab}"


def make_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): make_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [make_jsonable(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def prune_video_payload(payload: dict[str, Any]) -> dict[str, Any]:
    ignored_keys = {
        "formats",
        "automatic_captions",
        "subtitles",
        "thumbnails",
        "requested_formats",
        "requested_downloads",
        "heatmap",
        "http_headers",
    }
    return {
        key: make_jsonable(value)
        for key, value in payload.items()
        if key not in ignored_keys
    }
