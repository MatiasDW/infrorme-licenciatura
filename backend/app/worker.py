from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.main import persist_video
from app.models import TranscriptJob, YouTubeVideo
from app.warehouse import ensure_warehouse_schema
from app.youtube import build_video_payload


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("transcript-worker")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_rate_limited(error: Exception) -> bool:
    message = str(error).lower()
    return any(
        marker in message
        for marker in ("429", "too many requests", "ipblocked", "requestblocked", "blocking requests")
    )


def _recover_stale_jobs() -> None:
    now = _now()
    with SessionLocal() as db:
        db.execute(
            update(TranscriptJob)
            .where(
                TranscriptJob.status == "running",
                TranscriptJob.locked_at < now - timedelta(hours=1),
            )
            .values(status="queued", locked_at=None, available_at=now, updated_at=now)
        )
        db.commit()


def _claim_job() -> tuple[int, str, str] | None:
    now = _now()
    with SessionLocal() as db:
        job = db.scalar(
            select(TranscriptJob)
            .where(
                TranscriptJob.status == "queued",
                TranscriptJob.available_at <= now,
            )
            .order_by(TranscriptJob.available_at, TranscriptJob.id)
            .with_for_update(skip_locked=True)
        )
        if job is None:
            return None
        video = db.get(YouTubeVideo, job.video_id)
        if video is None:
            job.status = "failed"
            job.last_error = "Video no longer exists"
            job.updated_at = now
            db.commit()
            return None
        job.status = "running"
        job.locked_at = now
        job.updated_at = now
        db.commit()
        return job.id, video.video_id, video.url


def _mark_success(job_id: int) -> None:
    with SessionLocal() as db:
        job = db.get(TranscriptJob, job_id)
        if job:
            job.status = "completed"
            job.locked_at = None
            job.last_error = None
            job.updated_at = _now()
            db.commit()


def _mark_failure(job_id: int, error: Exception) -> bool:
    """Return true when the worker should stop because a rate limit was hit."""
    now = _now()
    rate_limited = _is_rate_limited(error)
    with SessionLocal() as db:
        job = db.get(TranscriptJob, job_id)
        if job is None:
            return rate_limited
        job.attempts += 1
        job.locked_at = None
        job.last_error = str(error)
        if rate_limited:
            job.status = "blocked"
            job.available_at = now + timedelta(seconds=settings.youtube_block_cooldown_seconds)
            db.execute(
                update(TranscriptJob)
                .where(TranscriptJob.status == "queued")
                .values(
                    available_at=now + timedelta(seconds=settings.youtube_block_cooldown_seconds),
                    updated_at=now,
                )
            )
        elif job.attempts >= settings.youtube_max_attempts:
            job.status = "failed"
            job.available_at = now
        else:
            job.status = "queued"
            delay = settings.youtube_retry_backoff_seconds * (2 ** (job.attempts - 1))
            job.available_at = now + timedelta(seconds=delay)
        job.updated_at = now
        db.commit()
    return rate_limited


def run() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_warehouse_schema(engine)
    _recover_stale_jobs()
    last_started = 0.0
    logger.info(
        "worker started: interval=%.1fs max_attempts=%d",
        settings.youtube_min_request_interval_seconds,
        settings.youtube_max_attempts,
    )

    while True:
        job = _claim_job()
        if job is None:
            time.sleep(settings.youtube_worker_poll_seconds)
            continue

        elapsed = time.monotonic() - last_started
        if elapsed < settings.youtube_min_request_interval_seconds:
            time.sleep(settings.youtube_min_request_interval_seconds - elapsed)
        job_id, video_id, url = job
        last_started = time.monotonic()
        logger.info("processing video_id=%s job_id=%s", video_id, job_id)
        try:
            payload = build_video_payload(url)
            if not payload.get("transcript_text"):
                raise RuntimeError(payload.get("transcript_error") or "Transcript was not returned")
            with SessionLocal() as db:
                persist_video(db, payload)
            _mark_success(job_id)
            logger.info("completed video_id=%s", video_id)
        except Exception as error:
            logger.warning("failed video_id=%s: %s", video_id, error)
            if _mark_failure(job_id, error):
                logger.error("rate limit detected; queue paused for %.1f seconds", settings.youtube_block_cooldown_seconds)
                return


if __name__ == "__main__":
    run()
