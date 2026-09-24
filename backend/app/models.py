from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class YouTubeVideo(Base):
    __tablename__ = "youtube_videos"

    video_id = Column(String(32), primary_key=True)
    url = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    channel_id = Column(String(128), nullable=True)
    channel_name = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    publish_date = Column(Date, nullable=True)
    upload_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    description_has_transcript_hint = Column(Boolean, nullable=False, default=False)
    scraped_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    transcript_source = Column(String(128), nullable=True)
    transcript_language = Column(String(64), nullable=True)
    transcript_language_code = Column(String(32), nullable=True)
    transcript_is_generated = Column(Boolean, nullable=True)
    transcript_is_translatable = Column(Boolean, nullable=True)
    transcript_text = Column(Text, nullable=True)
    transcript_segments = Column(JSONB, nullable=True)
    transcript_error = Column(Text, nullable=True)
    raw_payload = Column(JSONB, nullable=True)


class TranscriptJob(Base):
    __tablename__ = "transcript_jobs"
    __table_args__ = (UniqueConstraint("video_id", name="uq_transcript_jobs_video_id"),)

    id = Column(Integer, primary_key=True)
    video_id = Column(String(32), ForeignKey("youtube_videos.video_id", ondelete="CASCADE"), nullable=False)
    status = Column(String(24), nullable=False, default="queued", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    available_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
