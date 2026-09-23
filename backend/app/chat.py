from __future__ import annotations

import json
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import YouTubeVideo
from app.warehouse import read_warehouse_segments, search_warehouse_segments, serialize_llm_context
from app.youtube import search_transcript_segments


SYSTEM_PROMPT = (
    "You answer questions about a YouTube video transcript. "
    "Use only the transcript and metadata provided by the system or tools. "
    "Tool results use the compact TOON format; read their tabular rows directly. "
    "If the answer is not supported by the transcript, say so plainly."
)


def _serialize_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "\n".join(part for part in parts if part)
    return json.dumps(content, ensure_ascii=False)


def _tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "search_transcript",
                "description": "Search transcript segments by a natural-language query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Words or short phrase to find in the transcript.",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of matching segments to return.",
                            "default": 6,
                        },
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_transcript_chunk",
                "description": "Read a sequential slice of transcript segments by index.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_index": {
                            "type": "integer",
                            "description": "Zero-based transcript segment index.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of segments to read.",
                            "default": 8,
                        },
                    },
                    "required": ["start_index"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_video_metadata",
                "description": "Get the stored metadata summary for the current video.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    ]


def _execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    video: YouTubeVideo,
    db: Session,
) -> dict[str, Any]:
    segments = video.transcript_segments or []

    if tool_name == "search_transcript":
        query = str(arguments.get("query", ""))
        max_results = max(1, min(int(arguments.get("max_results", 6)), 12))
        matches = search_warehouse_segments(db, video.video_id, query, max_results)
        if not matches:
            matches = search_transcript_segments(segments, query=query, max_results=max_results)
        return {
            "matches": matches,
        }

    if tool_name == "read_transcript_chunk":
        start_index = max(0, int(arguments.get("start_index", 0)))
        limit = max(1, min(int(arguments.get("limit", 8)), 20))
        chunk = read_warehouse_segments(db, video.video_id, start_index, limit)
        if not chunk:
            chunk = []
            for index, segment in enumerate(segments[start_index : start_index + limit], start=start_index):
                chunk.append(
                    {
                        "index": index,
                        "start": segment.get("start"),
                        "duration": segment.get("duration"),
                        "text": segment.get("text"),
                    }
                )
        return {"segments": chunk}

    if tool_name == "get_video_metadata":
        return {
            "video_id": video.video_id,
            "title": video.title,
            "channel_name": video.channel_name,
            "publish_date": video.publish_date.isoformat() if video.publish_date else None,
            "transcript_language": video.transcript_language,
            "transcript_is_generated": video.transcript_is_generated,
            "segment_count": len(segments),
        }

    return {"error": f"Unknown tool: {tool_name}"}


async def answer_chat(
    video: YouTubeVideo,
    history: list[dict[str, str]],
    message: str,
    db: Session,
) -> tuple[str, bool]:
    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")
    if not video.transcript_text:
        raise RuntimeError("This video does not have a saved transcript to chat against")

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": serialize_llm_context(
                {
                    "video_id": video.video_id,
                    "title": video.title,
                    "channel_name": video.channel_name,
                    "publish_date": video.publish_date.isoformat() if video.publish_date else None,
                    "transcript_language": video.transcript_language,
                    "segment_count": len(video.transcript_segments or []),
                }
            ),
        },
    ]

    for item in history:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.openrouter_site_url,
        "X-Title": settings.openrouter_site_name,
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": messages,
        "tools": _tool_definitions(),
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        assistant_message = choice["message"]
        tool_calls = assistant_message.get("tool_calls") or []

        if not tool_calls:
            return _serialize_content(assistant_message.get("content", "")), False

        messages.append(
            {
                "role": "assistant",
                "content": assistant_message.get("content") or "",
                "tool_calls": tool_calls,
            }
        )

        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"].get("arguments") or "{}")
            result = _execute_tool(function_name, arguments, video, db)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": function_name,
                    "content": serialize_llm_context(result),
                }
            )

        second_response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": settings.openrouter_model,
                "messages": messages,
                "tools": _tool_definitions(),
            },
        )
        second_response.raise_for_status()
        second_data = second_response.json()
        final_message = second_data["choices"][0]["message"]
        return _serialize_content(final_message.get("content", "")), True
