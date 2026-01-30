"""
Learning Notes API Endpoints

Supports dashboard + knowledge bank cards.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db import fetch, fetchrow

router = APIRouter()


class NoteCreate(BaseModel):
    user_id: str
    note_type: str
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    topic: Optional[str] = None
    thumbnail_url: Optional[str] = None
    source_id: Optional[str] = None


def _note_row_to_dict(row) -> Dict[str, Any]:
    note = dict(row)
    note["id"] = str(note["id"])
    note["created_at"] = note.get("created_at")
    return note


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
    idx = 2
    if topic:
        filters.append(f"topic = ${idx}")
        params.append(topic)
        idx += 1

    query = f"""
        SELECT * FROM learning_notes
        WHERE {' AND '.join(filters)}
        ORDER BY created_at DESC
        LIMIT ${idx} OFFSET ${idx + 1}
    """
    try:
        rows = await fetch(query, *params, limit, offset)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

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


@router.post("")
async def create_note(request: NoteCreate):
    """Create a learning note (for manual curation or seed data)."""
    query = """
        INSERT INTO learning_notes
            (user_id, note_type, title, description, tags, author, topic, thumbnail_url, source_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
    """
    try:
        row = await fetchrow(
            query,
            request.user_id,
            request.note_type,
            request.title,
            request.description,
            request.tags,
            request.author,
            request.topic,
            request.thumbnail_url,
            request.source_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    return _note_row_to_dict(row)
