from datetime import date, datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class TranscriptSegment(BaseModel):
    text: str
    start: float
    duration: float


class VideoSummary(BaseModel):
    video_id: str
    url: str
    title: str
    channel_name: Optional[str] = None
    publish_date: Optional[date] = None
    scraped_at: datetime
    has_transcript: bool
    transcript_error: Optional[str] = None


class VideoDetail(VideoSummary):
    channel_id: Optional[str] = None
    duration_seconds: Optional[int] = None
    upload_date: Optional[date] = None
    description: Optional[str] = None
    description_has_transcript_hint: bool
    transcript_source: Optional[str] = None
    transcript_language: Optional[str] = None
    transcript_language_code: Optional[str] = None
    transcript_is_generated: Optional[bool] = None
    transcript_is_translatable: Optional[bool] = None
    transcript_text: Optional[str] = None
    transcript_segments: List[TranscriptSegment] = Field(default_factory=list)
    raw_payload: Optional[dict[str, Any]] = None


class TranscriptLibraryResponse(BaseModel):
    recent: List[VideoSummary]
    items: List[VideoSummary]


class CreateTranscriptRequest(BaseModel):
    url: HttpUrl


class ChannelScrapeRequest(BaseModel):
    url: HttpUrl
    title_query: str = Field(min_length=1)
    max_videos: int = Field(default=20, ge=1, le=100)


class ChannelScrapeVideoResult(BaseModel):
    video_id: str
    url: str
    title: str
    channel_name: Optional[str] = None
    publish_date: Optional[date] = None
    source_tab: Literal["videos", "streams"]
    has_transcript: bool
    transcript_error: Optional[str] = None


class ChannelScrapeResponse(BaseModel):
    url: str
    title_query: str
    max_videos: int
    processed_count: int
    saved_count: int
    failed_count: int
    videos_with_transcript: int
    videos_without_transcript: int
    first_valid_video_id: Optional[str] = None
    videos: List[ChannelScrapeVideoResult]


class ChatMessageIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    video_id: str
    message: str = Field(min_length=1)
    history: List[ChatMessageIn] = Field(default_factory=list)


class ChatResponse(BaseModel):
    video_id: str
    answer: str
    used_tools: bool
    model: str

