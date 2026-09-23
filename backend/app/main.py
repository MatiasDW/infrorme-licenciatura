from __future__ import annotations

from datetime import datetime, timezone

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.chat import answer_chat
from app.config import settings
from app.database import Base, SessionLocal, engine, get_db
from app.models import YouTubeVideo
from app.schemas import (
    ChannelScrapeRequest,
    ChannelScrapeAllRequest,
    ChannelScrapeResponse,
    ChannelScrapeVideoResult,
    ChatRequest,
    ChatResponse,
    CreateTranscriptRequest,
    TranscriptLibraryResponse,
    TranscriptSegment,
    VideoDetail,
    VideoSummary,
)
from app.youtube import build_channel_video_payload, build_video_payload, discover_channel_matches
from app.warehouse import backfill_warehouse, ensure_warehouse_schema, sync_video_to_warehouse


app = FastAPI(title="YouTube Transcript Console", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def persist_video(db: Session, payload: dict) -> YouTubeVideo:
    video = db.get(YouTubeVideo, payload["video_id"])
    if video is None:
        video = YouTubeVideo(video_id=payload["video_id"])
        db.add(video)

    for key, value in payload.items():
        setattr(video, key, value)

    video.scraped_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(video)
    sync_video_to_warehouse(db, video)
    db.commit()
    return video


def to_summary(video: YouTubeVideo) -> VideoSummary:
    has_transcript = bool(video.transcript_text and video.transcript_segments)
    return VideoSummary(
        video_id=video.video_id,
        url=video.url,
        title=video.title,
        channel_name=video.channel_name,
        publish_date=video.publish_date,
        scraped_at=video.scraped_at,
        has_transcript=has_transcript,
        transcript_error=video.transcript_error,
    )


def to_detail(video: YouTubeVideo) -> VideoDetail:
    summary = to_summary(video)
    return VideoDetail(
        **summary.model_dump(),
        channel_id=video.channel_id,
        duration_seconds=video.duration_seconds,
        upload_date=video.upload_date,
        description=video.description,
        description_has_transcript_hint=video.description_has_transcript_hint,
        transcript_source=video.transcript_source,
        transcript_language=video.transcript_language,
        transcript_language_code=video.transcript_language_code,
        transcript_is_generated=video.transcript_is_generated,
        transcript_is_translatable=video.transcript_is_translatable,
        transcript_text=video.transcript_text,
        transcript_segments=[TranscriptSegment(**segment) for segment in (video.transcript_segments or [])],
        raw_payload=video.raw_payload,
    )


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_warehouse_schema(engine)
    with SessionLocal() as db:
        backfill_warehouse(db)


@app.get("/api/health")
def health(db: Session = Depends(get_db)) -> dict:
    db.execute(select(1))
    return {
        "status": "ok",
        "database": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/transcripts", response_model=TranscriptLibraryResponse)
def list_transcripts(db: Session = Depends(get_db)) -> TranscriptLibraryResponse:
    valid_filter = func.length(func.coalesce(YouTubeVideo.transcript_text, "")) > 0

    recent = db.scalars(
        select(YouTubeVideo)
        .where(valid_filter)
        .order_by(desc(YouTubeVideo.scraped_at))
        .limit(5)
    ).all()

    items = db.scalars(
        select(YouTubeVideo)
        .where(valid_filter)
        .order_by(desc(YouTubeVideo.scraped_at))
        .limit(100)
    ).all()

    return TranscriptLibraryResponse(
        recent=[to_summary(video) for video in recent],
        items=[to_summary(video) for video in items],
    )


@app.get("/api/transcripts/{video_id}", response_model=VideoDetail)
def get_transcript(video_id: str, db: Session = Depends(get_db)) -> VideoDetail:
    video = db.get(YouTubeVideo, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return to_detail(video)


@app.post("/api/transcripts", response_model=VideoDetail)
def create_transcript(payload: CreateTranscriptRequest, db: Session = Depends(get_db)) -> VideoDetail:
    try:
        video_payload = build_video_payload(str(payload.url))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    video = persist_video(db, video_payload)
    return to_detail(video)


def process_channel_scrape(
    payload: ChannelScrapeRequest | ChannelScrapeAllRequest,
    db: Session,
) -> ChannelScrapeResponse:
    try:
        matches = discover_channel_matches(
            str(payload.url),
            payload.title_query,
            payload.max_videos,
            all_content=payload.all_content,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    results: list[ChannelScrapeVideoResult] = []
    first_valid_video_id = None
    saved_count = 0
    failed_count = 0
    videos_with_transcript = 0
    videos_without_transcript = 0

    for item in matches:
        try:
            existing = db.get(YouTubeVideo, item["video_id"])
            if existing and existing.transcript_text and not payload.refresh_existing:
                video = existing
            else:
                video = persist_video(db, build_channel_video_payload(item))
            saved_count += 1
        except Exception as exc:
            failed_count += 1
            results.append(
                ChannelScrapeVideoResult(
                    video_id=item["video_id"],
                    url=item["url"],
                    title=item["title"],
                    channel_name=None,
                    publish_date=None,
                    source_tab=item["source_tab"],
                    has_transcript=False,
                    transcript_error=str(exc),
                )
            )
            continue

        has_transcript = bool(video.transcript_text and video.transcript_segments)
        if has_transcript:
            videos_with_transcript += 1
            if first_valid_video_id is None:
                first_valid_video_id = video.video_id
        else:
            videos_without_transcript += 1

        results.append(
            ChannelScrapeVideoResult(
                video_id=video.video_id,
                url=video.url,
                title=video.title,
                channel_name=video.channel_name,
                publish_date=video.publish_date,
                source_tab=item["source_tab"],
                has_transcript=has_transcript,
                transcript_error=video.transcript_error,
            )
        )

    return ChannelScrapeResponse(
        url=str(payload.url),
        title_query=payload.title_query,
        max_videos=payload.max_videos,
        processed_count=len(matches),
        saved_count=saved_count,
        failed_count=failed_count,
        videos_with_transcript=videos_with_transcript,
        videos_without_transcript=videos_without_transcript,
        first_valid_video_id=first_valid_video_id,
        videos=results,
    )


@app.post("/api/channels/scrape", response_model=ChannelScrapeResponse)
def scrape_channel(payload: ChannelScrapeRequest, db: Session = Depends(get_db)) -> ChannelScrapeResponse:
    return process_channel_scrape(payload, db)


@app.post("/api/channels/scrape-all", response_model=ChannelScrapeResponse)
def scrape_all_channel(
    payload: ChannelScrapeAllRequest,
    db: Session = Depends(get_db),
) -> ChannelScrapeResponse:
    return process_channel_scrape(payload, db)


@app.post("/api/v1/chat/message", response_model=ChatResponse)
async def chat_message(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    video = db.get(YouTubeVideo, payload.video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    try:
        answer, used_tools = await answer_chat(
            video=video,
            history=[item.model_dump() for item in payload.history],
            message=payload.message,
            db=db,
        )
    except httpx.HTTPStatusError as exc:  # type: ignore[name-defined]
        detail = exc.response.text if exc.response is not None else str(exc)
        raise HTTPException(status_code=502, detail=detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ChatResponse(
        video_id=payload.video_id,
        answer=answer,
        used_tools=used_tools,
        model=settings.openrouter_model,
    )
