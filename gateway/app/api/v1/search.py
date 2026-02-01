"""
Search API Endpoints

Simple keyword search across notes and learning plans.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.db import fetch

router = APIRouter()


@router.get("")
async def search(
    user_id: str = Query(...),
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
):
    """Search notes and plans for a user."""
    query = q.strip()
    if not query:
        return {"query": q, "count": 0, "items": []}

    like = f"%{query}%"

    notes_sql = """
        SELECT id, title, description, topic, created_at
        FROM learning_notes
        WHERE user_id = $1
          AND (title ILIKE $2 OR description ILIKE $2 OR topic ILIKE $2)
        ORDER BY created_at DESC
        LIMIT $3
    """

    plans_sql = """
        SELECT id, title, description, goal, status, created_at
        FROM learning_plans
        WHERE user_id = $1
          AND (title ILIKE $2 OR description ILIKE $2 OR goal ILIKE $2)
        ORDER BY created_at DESC
        LIMIT $3
    """

    try:
        notes_rows = await fetch(notes_sql, user_id, like, limit)
        plans_rows = await fetch(plans_sql, user_id, like, limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    items: List[Dict[str, Any]] = []
    for row in notes_rows:
        items.append(
            {
                "id": row["id"],
                "type": "note",
                "title": row["title"],
                "description": row["description"],
                "topic": row["topic"],
                "created_at": row["created_at"],
            }
        )
    for row in plans_rows:
        items.append(
            {
                "id": row["id"],
                "type": "plan",
                "title": row["title"],
                "description": row["description"] or row["goal"],
                "status": row["status"],
                "created_at": row["created_at"],
            }
        )

    items.sort(key=lambda item: item.get("created_at") or 0, reverse=True)
    items = items[:limit]

    return {"query": q, "count": len(items), "items": items}
