"""
Learning Notes API Endpoints

Supports dashboard + knowledge bank cards.
"""

from typing import Any, Dict, List, Optional, Union

import json
import asyncio
import hashlib
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from app.db import fetch, fetchrow
from app.a2a.client import get_a2a_client

router = APIRouter()


class NoteCreate(BaseModel):
    user_id: str
    note_type: str
    title: str
    description: Optional[str] = None
    tags: Optional[List[Union[Dict[str, str], str]]] = None
    author: Optional[str] = None
    topic: Optional[str] = None
    thumbnail_url: Optional[str] = None
    source_id: Optional[str] = None


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[Union[Dict[str, str], str]]] = None
    author: Optional[str] = None
    topic: Optional[str] = None
    thumbnail_url: Optional[str] = None
    source_id: Optional[str] = None


def _note_row_to_dict(row) -> Dict[str, Any]:
    note = dict(row)
    note["id"] = str(note["id"])
    note["created_at"] = note.get("created_at")
    if isinstance(note.get("tags"), str):
        try:
            note["tags"] = json.loads(note["tags"])
        except Exception:
            pass
    note["has_audio"] = note.get("has_audio", False)
    note["has_video"] = note.get("has_video", False)
    return note


async def _trigger_note_pipeline(user_id: str, note_id: str, event: str) -> None:
    """Best-effort trigger for the agent pipeline when notes change."""
    try:
        a2a_client = await get_a2a_client()
        message = (
            "A note was updated. Trigger the background pipeline for this note. "
            f"Event: {event}. user_id: {user_id}. content_id: {note_id}. "
            "Use schedule_generation with job_type generate_5min_new and include content_id."
        )
        await a2a_client.run_agent(
            agent_name="orchestrator",
            message=message,
            user_id=user_id,
        )
    except Exception:
        # Do not block note operations if the agent is unavailable.
        return


async def _create_notification(user_id: str, note: Dict[str, Any], event: str, status: str, title: str, body: str) -> None:
    """Best-effort notification for note processing."""
    try:
        data = json.dumps({"note_id": note.get("id"), "event": event, "status": status})
        query = """
            INSERT INTO notifications (user_id, channel, title, body, data)
            VALUES ($1, 'in_app', $2, $3, $4)
            RETURNING id
        """
        await fetchrow(query, user_id, title, body, data)
    except Exception:
        return


async def _ensure_content_item(user_id: str, note: Dict[str, Any]) -> Optional[str]:
    """Create a content_item for note text and link via user_materials."""
    raw_text = (note.get("description") or note.get("title") or "").strip()
    if not raw_text:
        return None
    content_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    existing = await fetchrow(
        "SELECT id FROM content_items WHERE content_hash = $1",
        content_hash,
    )
    if existing:
        content_id = str(existing["id"])
    else:
        row = await fetchrow(
            """
            INSERT INTO content_items (content_hash, title, raw_text, media_type, word_count)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            content_hash,
            note.get("title") or "Note",
            raw_text,
            "TXT",
            len(raw_text.split()),
        )
        content_id = str(row["id"])

    # Link user to content (no dedupe for hackathon simplicity)
    await fetchrow(
        """
        INSERT INTO user_materials (user_id, content_id, status)
        VALUES ($1, $2, 'PROCESSED')
        RETURNING id
        """,
        user_id,
        content_id,
    )
    return content_id


def _parse_dt(value: Union[str, datetime]) -> datetime:
    """Parse datetime from string or return datetime object as-is."""
    if isinstance(value, datetime):
        return value
    if not value:
        raise ValueError("Cannot parse empty datetime value")
    # Handle ISO format strings with or without Z suffix
    if isinstance(value, str):
        # Replace Z with +00:00 for ISO format compatibility
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    raise TypeError(f"Expected str or datetime, got {type(value)}")


async def _queue_ready_notification(user_id: str, note: Dict[str, Any], event: str) -> None:
    """Follow-up notification when background job completes."""
    created_at = note.get("created_at")
    if not created_at:
        return
    since = _parse_dt(created_at)
    # Poll for completion (up to ~90s)
    for _ in range(30):
        row = await fetchrow(
            """
            SELECT id FROM background_jobs
            WHERE user_id = $1
              AND job_type = 'generate_5min_new'
              AND status = 'COMPLETED'
              AND created_at >= $2
            ORDER BY created_at DESC
            LIMIT 1
            """,
            user_id,
            since,
        )
        if row:
            break
        await asyncio.sleep(3)
    else:
        return
    await _create_notification(
        user_id,
        note,
        event,
        "ready",
        "Materials ready",
        f"Your study materials for '{note.get('title') or 'your note'}' are ready.",
    )


@router.get("")
async def list_notes(
    user_id: str = Query(...),
    topic: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List notes, optionally filtered by topic."""
    filters = ["user_id = $1"]
    params: List[Any] = [user_id]
    if topic:
        filters.append(f"topic = ${len(params) + 1}")
        params.append(topic)

    query = f"""
        SELECT n.*,
               EXISTS(SELECT 1 FROM audio_artifacts a WHERE a.artifact_id = n.id) as has_audio,
               EXISTS(SELECT 1 FROM video_artifacts v WHERE v.artifact_id = n.id) as has_video
        FROM learning_notes n
        WHERE {' AND '.join(filters)}
        ORDER BY created_at DESC
        LIMIT ${{limit_param}} OFFSET ${{offset_param}}
    """

    try:
        limit_param = len(params) + 1
        offset_param = len(params) + 2
        formatted_query = query.format(limit_param=limit_param, offset_param=offset_param)
        rows = await fetch(formatted_query, *params, limit, offset)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Database error in list_notes: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(exc)}")

    return {"user_id": user_id, "count": len(rows), "items": [_note_row_to_dict(row) for row in rows]}


@router.get("/recent")
async def list_recent_notes(
    user_id: str = Query(...),
    limit: int = Query(6, ge=1, le=50),
):
    """List recent notes for dashboard/overview."""
    query = """
        SELECT * FROM learning_notes
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2
    """
    try:
        rows = await fetch(query, user_id, limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    return {"user_id": user_id, "count": len(rows), "items": [_note_row_to_dict(row) for row in rows]}


@router.get("/topics")
async def list_note_topics(user_id: str = Query(...)):
    """Return topic clusters with counts."""
    query = """
        SELECT topic, COUNT(*) AS count
        FROM learning_notes
        WHERE user_id = $1 AND topic IS NOT NULL
        GROUP BY topic
        ORDER BY count DESC
    """
    try:
        rows = await fetch(query, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    topics = [{"topic": row["topic"], "count": row["count"]} for row in rows]
    return {"user_id": user_id, "items": topics}


@router.get("/{note_id}")
async def get_note(note_id: str, user_id: str = Query(...)):
    """Get a single note by id."""
    query = """
        SELECT n.*,
               EXISTS(SELECT 1 FROM audio_artifacts a WHERE a.artifact_id = n.id) as has_audio,
               EXISTS(SELECT 1 FROM video_artifacts v WHERE v.artifact_id = n.id) as has_video
        FROM learning_notes n
        WHERE n.id = $1 AND n.user_id = $2
    """
    try:
        row = await fetchrow(query, note_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")

    if not row:
        raise HTTPException(status_code=404, detail="Note not found")

    return _note_row_to_dict(row)


@router.post("")
async def create_note(request: NoteCreate, background_tasks: BackgroundTasks = None):
    """Create a learning note (for manual curation or seed data)."""
    query = """
        INSERT INTO learning_notes
            (user_id, note_type, title, description, tags, author, topic, thumbnail_url, source_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
    """
    try:
        normalized_tags = None
        if request.tags is not None:
            normalized_tags = []
            for tag in request.tags:
                if isinstance(tag, dict):
                    normalized_tags.append(tag)
                else:
                    normalized_tags.append({"type": "topic", "label": str(tag)})
        tags_payload = json.dumps(normalized_tags) if normalized_tags is not None else None
        row = await fetchrow(
            query,
            request.user_id,
            request.note_type,
            request.title,
            request.description,
            tags_payload,
            request.author,
            request.topic,
            request.thumbnail_url,
            request.source_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")

    note = _note_row_to_dict(row)
    content_id = await _ensure_content_item(request.user_id, note)
    if content_id and note.get("source_id") is None:
        # Update note with source_id for traceability
        await fetchrow(
            "UPDATE learning_notes SET source_id = $1 WHERE id = $2",
            content_id,
            note["id"],
        )
        note["source_id"] = content_id
    await _trigger_note_pipeline(request.user_id, content_id or note["id"], "created")
    await _create_notification(
        request.user_id,
        note,
        "created",
        "processing",
        "Processing started",
        f"We are generating materials for '{note.get('title') or 'your note'}'.",
    )
    if background_tasks is not None:
        background_tasks.add_task(_queue_ready_notification, request.user_id, note, "created")
    return note


@router.patch("/{note_id}")
async def update_note(note_id: str, user_id: str = Query(...), update: NoteUpdate = ..., background_tasks: BackgroundTasks = None):
    """Update a learning note and trigger agent pipeline."""
    update = update or NoteUpdate()
    updates: List[str] = []
    params: List[Any] = []
    idx = 1

    for field, value in update.model_dump(exclude_unset=True).items():
        if field == "tags" and value is not None:
            normalized_tags = []
            for tag in value:
                if isinstance(tag, dict):
                    normalized_tags.append(tag)
                else:
                    normalized_tags.append({"type": "topic", "label": str(tag)})
            value = json.dumps(normalized_tags)
        updates.append(f"{field} = ${idx}")
        params.append(value)
        idx += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    query = f"""
        UPDATE learning_notes
        SET {', '.join(updates)}
        WHERE id = ${idx} AND user_id = ${idx + 1}
        RETURNING *
    """
    try:
        row = await fetchrow(query, *params, note_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")

    if not row:
        raise HTTPException(status_code=404, detail="Note not found")

    note = _note_row_to_dict(row)
    content_id = await _ensure_content_item(user_id, note)
    if content_id and note.get("source_id") is None:
        await fetchrow(
            "UPDATE learning_notes SET source_id = $1 WHERE id = $2",
            content_id,
            note["id"],
        )
        note["source_id"] = content_id
    await _trigger_note_pipeline(user_id, content_id or note["id"], "updated")
    await _create_notification(
        user_id,
        note,
        "updated",
        "processing",
        "Processing started",
        f"We are updating materials for '{note.get('title') or 'your note'}'.",
    )
    if background_tasks is not None:
        background_tasks.add_task(_queue_ready_notification, user_id, note, "updated")
    return note
