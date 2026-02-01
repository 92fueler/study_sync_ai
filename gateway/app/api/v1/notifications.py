"""
Notifications API Endpoints

Reads notifications from the database.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

from app.db import fetch, fetchrow

router = APIRouter()

@router.get("")
async def get_notifications(
    user_id: str = Query(...),
    unread_only: bool = Query(False)
):
    """Get notifications for a user."""
    filter_clause = "AND read = FALSE" if unread_only else ""
    query = f"""
        SELECT id, user_id, title, body, data, sent, read, sent_at, created_at
        FROM notifications
        WHERE user_id = $1 {filter_clause}
        ORDER BY created_at DESC
        LIMIT 50
    """
    try:
        rows = await fetch(query, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    notifications: List[Dict[str, Any]] = [dict(row) for row in rows]
    return {"notifications": notifications}


@router.get("/badge")
async def get_badge_count(user_id: str = Query(...)):
    """Get unread notification count."""
    query = """
        SELECT COUNT(*) AS unread_count
        FROM notifications
        WHERE user_id = $1 AND read = FALSE
    """
    try:
        row = await fetchrow(query, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    return {"unread_count": int(row["unread_count"] if row else 0)}


@router.post("/{notification_id}/read")
async def mark_as_read(notification_id: str, user_id: str = Query("system")):
    """Mark a notification as read."""
    query = """
        UPDATE notifications
        SET read = TRUE
        WHERE id = $1 AND user_id = $2
        RETURNING id
    """
    try:
        row = await fetchrow(query, notification_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    return {"success": row is not None}
