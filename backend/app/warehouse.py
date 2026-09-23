from __future__ import annotations

import json
from math import ceil
from typing import Any

from sqlalchemy import Engine, select, text
from sqlalchemy.orm import Session

from app.models import YouTubeVideo


PARTITION_COUNT = 16
CHUNK_MAX_CHARS = 3200


def ensure_warehouse_schema(engine: Engine) -> None:
    """Create the warehouse tables and their hash partitions idempotently."""
    with engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS warehouse"))
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS warehouse.fact_transcript_segments (
                    video_id TEXT NOT NULL REFERENCES public.youtube_videos(video_id) ON DELETE CASCADE,
                    segment_index INTEGER NOT NULL,
                    start_seconds DOUBLE PRECISION NOT NULL,
                    duration_seconds DOUBLE PRECISION NOT NULL,
                    segment_text TEXT NOT NULL,
                    search_vector TSVECTOR NOT NULL,
                    PRIMARY KEY (video_id, segment_index)
                ) PARTITION BY HASH (video_id)
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS warehouse.fact_transcript_chunks (
                    video_id TEXT NOT NULL REFERENCES public.youtube_videos(video_id) ON DELETE CASCADE,
                    chunk_index INTEGER NOT NULL,
                    start_seconds DOUBLE PRECISION NOT NULL,
                    end_seconds DOUBLE PRECISION NOT NULL,
                    segment_start INTEGER NOT NULL,
                    segment_end INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    char_count INTEGER NOT NULL,
                    token_estimate INTEGER NOT NULL,
                    search_vector TSVECTOR NOT NULL,
                    PRIMARY KEY (video_id, chunk_index)
                ) PARTITION BY HASH (video_id)
                """
            )
        )

        for remainder in range(PARTITION_COUNT):
            suffix = f"p{remainder:02d}"
            segments_partition = f"warehouse.fact_transcript_segments_{suffix}"
            chunks_partition = f"warehouse.fact_transcript_chunks_{suffix}"
            connection.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {segments_partition}
                    PARTITION OF warehouse.fact_transcript_segments
                    FOR VALUES WITH (MODULUS {PARTITION_COUNT}, REMAINDER {remainder})
                    """
                )
            )
            connection.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {chunks_partition}
                    PARTITION OF warehouse.fact_transcript_chunks
                    FOR VALUES WITH (MODULUS {PARTITION_COUNT}, REMAINDER {remainder})
                    """
                )
            )
            connection.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS {suffix}_segments_video_idx "
                    f"ON {segments_partition} (video_id, segment_index)"
                )
            )
            connection.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS {suffix}_segments_search_idx "
                    f"ON {segments_partition} USING GIN (search_vector)"
                )
            )
            connection.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS {suffix}_chunks_video_idx "
                    f"ON {chunks_partition} (video_id, chunk_index)"
                )
            )
            connection.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS {suffix}_chunks_search_idx "
                    f"ON {chunks_partition} USING GIN (search_vector)"
                )
            )


def _clean_segments(video: YouTubeVideo) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for raw_segment in video.transcript_segments or []:
        segment_text = str(raw_segment.get("text") or "").strip()
        if not segment_text:
            continue
        cleaned.append(
            {
                "segment_index": len(cleaned),
                "start_seconds": float(raw_segment.get("start", 0.0)),
                "duration_seconds": float(raw_segment.get("duration", 0.0)),
                "segment_text": segment_text,
            }
        )

    if not cleaned and video.transcript_text:
        cleaned.append(
            {
                "segment_index": 0,
                "start_seconds": 0.0,
                "duration_seconds": 0.0,
                "segment_text": video.transcript_text.strip(),
            }
        )
    return cleaned


def _build_chunks(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    current_chars = 0

    def flush() -> None:
        nonlocal current, current_chars
        if not current:
            return
        chunk_text = " ".join(segment["segment_text"] for segment in current)
        chunks.append(
            {
                "chunk_index": len(chunks),
                "start_seconds": current[0]["start_seconds"],
                "end_seconds": max(
                    segment["start_seconds"] + segment["duration_seconds"] for segment in current
                ),
                "segment_start": current[0]["segment_index"],
                "segment_end": current[-1]["segment_index"],
                "chunk_text": chunk_text,
                "char_count": len(chunk_text),
                "token_estimate": ceil(len(chunk_text) / 4),
            }
        )
        current = []
        current_chars = 0

    for segment in segments:
        segment_chars = len(segment["segment_text"])
        if current and current_chars + segment_chars + 1 > CHUNK_MAX_CHARS:
            flush()
        current.append(segment)
        current_chars += segment_chars + (1 if current_chars else 0)
    flush()
    return chunks


def sync_video_to_warehouse(db: Session, video: YouTubeVideo) -> None:
    """Replace one video's derived warehouse rows after raw ingestion."""
    db.execute(
        text("DELETE FROM warehouse.fact_transcript_chunks WHERE video_id = :video_id"),
        {"video_id": video.video_id},
    )
    db.execute(
        text("DELETE FROM warehouse.fact_transcript_segments WHERE video_id = :video_id"),
        {"video_id": video.video_id},
    )

    segments = _clean_segments(video)
    if not segments:
        return

    db.execute(
        text(
            """
            INSERT INTO warehouse.fact_transcript_segments
                (video_id, segment_index, start_seconds, duration_seconds, segment_text, search_vector)
            VALUES
                (:video_id, :segment_index, :start_seconds, :duration_seconds, :segment_text,
                 to_tsvector('simple', :segment_text))
            """
        ),
        [{"video_id": video.video_id, **segment} for segment in segments],
    )

    db.execute(
        text(
            """
            INSERT INTO warehouse.fact_transcript_chunks
                (video_id, chunk_index, start_seconds, end_seconds, segment_start, segment_end,
                 chunk_text, char_count, token_estimate, search_vector)
            VALUES
                (:video_id, :chunk_index, :start_seconds, :end_seconds, :segment_start, :segment_end,
                 :chunk_text, :char_count, :token_estimate, to_tsvector('simple', :chunk_text))
            """
        ),
        [{"video_id": video.video_id, **chunk} for chunk in _build_chunks(segments)],
    )


def backfill_warehouse(db: Session) -> int:
    """Populate derived rows for transcripts ingested before the warehouse existed."""
    videos = db.scalars(
        select(YouTubeVideo).where(YouTubeVideo.transcript_text.is_not(None))
    ).all()
    backfilled = 0
    for video in videos:
        has_rows = db.execute(
            text(
                """
                SELECT EXISTS(
                    SELECT 1 FROM warehouse.fact_transcript_segments WHERE video_id = :video_id
                )
                """
            ),
            {"video_id": video.video_id},
        ).scalar()
        if not has_rows:
            sync_video_to_warehouse(db, video)
            backfilled += 1
    db.commit()
    return backfilled


def search_warehouse_segments(
    db: Session,
    video_id: str,
    query: str,
    max_results: int,
) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT segment_index AS index, start_seconds AS start, duration_seconds AS duration,
                   segment_text AS text
            FROM warehouse.fact_transcript_segments
            WHERE video_id = :video_id
              AND search_vector @@ plainto_tsquery('simple', :query)
            ORDER BY ts_rank(search_vector, plainto_tsquery('simple', :query)) DESC, segment_index
            LIMIT :max_results
            """
        ),
        {"video_id": video_id, "query": query, "max_results": max_results},
    ).mappings().all()
    if rows:
        return [dict(row) for row in rows]

    fallback_rows = db.execute(
        text(
            """
            SELECT segment_index AS index, start_seconds AS start, duration_seconds AS duration,
                   segment_text AS text
            FROM warehouse.fact_transcript_segments
            WHERE video_id = :video_id AND segment_text ILIKE :pattern
            ORDER BY segment_index
            LIMIT :max_results
            """
        ),
        {"video_id": video_id, "pattern": f"%{query}%", "max_results": max_results},
    ).mappings().all()
    return [dict(row) for row in fallback_rows]


def read_warehouse_segments(
    db: Session,
    video_id: str,
    start_index: int,
    limit: int,
) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT segment_index AS index, start_seconds AS start, duration_seconds AS duration,
                   segment_text AS text
            FROM warehouse.fact_transcript_segments
            WHERE video_id = :video_id AND segment_index >= :start_index
            ORDER BY segment_index
            LIMIT :limit
            """
        ),
        {"video_id": video_id, "start_index": start_index, "limit": limit},
    ).mappings().all()
    return [dict(row) for row in rows]


def serialize_llm_context(value: Any) -> str:
    """Use TOON for compact tabular context, with JSON as a safe fallback."""
    try:
        from toon_format import encode

        return encode(value)
    except ImportError:
        return json.dumps(value, ensure_ascii=False)
