"""
Notifications API Endpoints

Reads notifications from the database.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

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


def _sse_event(event: str, data: Dict[str, Any]) -> str:
    payload = json.dumps(data, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


def _serialize_notification(row: Dict[str, Any]) -> Dict[str, Any]:
    serialized = dict(row)
    for key in ("created_at", "sent_at"):
        value = serialized.get(key)
        if isinstance(value, datetime):
            serialized[key] = value.isoformat()
    return serialized


@router.get("/stream")
async def stream_notifications(user_id: str = Query(...)):
    """Stream notifications via SSE."""
    async def event_stream() -> AsyncGenerator[str, None]:
        last_seen: Optional[datetime] = None
        while True:
            try:
                if last_seen is None:
                    rows = await fetch(
                        """
                        SELECT id, user_id, title, body, data, sent, read, sent_at, created_at
                        FROM notifications
                        WHERE user_id = $1
                        ORDER BY created_at DESC
                        LIMIT 50
                        """,
                        user_id,
                    )
                    badge_row = await fetchrow(
                        """
                        SELECT COUNT(*) AS unread_count
                        FROM notifications
                        WHERE user_id = $1 AND read = FALSE
                        """,
                        user_id,
                    )
                    notifications: List[Dict[str, Any]] = [_serialize_notification(dict(row)) for row in rows]
                    if rows:
                        last_seen = rows[0]["created_at"]
                    yield _sse_event(
                        "notifications",
                        {
                            "notifications": notifications,
                            "unread_count": int(badge_row["unread_count"] if badge_row else 0),
                        },
                    )
                else:
                    rows = await fetch(
                        """
                        SELECT id, user_id, title, body, data, sent, read, sent_at, created_at
                        FROM notifications
                        WHERE user_id = $1 AND created_at > $2
                        ORDER BY created_at DESC
                        """,
                        user_id,
                        last_seen,
                    )
                    if rows:
                        notifications = [_serialize_notification(dict(row)) for row in rows]
                        last_seen = rows[0]["created_at"]
                        badge_row = await fetchrow(
                            """
                            SELECT COUNT(*) AS unread_count
                            FROM notifications
                            WHERE user_id = $1 AND read = FALSE
                            """,
                            user_id,
                        )
                        yield _sse_event(
                            "notifications",
                            {
                                "notifications": notifications,
                                "unread_count": int(badge_row["unread_count"] if badge_row else 0),
                            },
                        )
                    else:
                        yield _sse_event("keepalive", {"ts": datetime.now(timezone.utc).isoformat()})
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                yield _sse_event("error", {"message": "stream_error", "detail": str(exc)})
                await asyncio.sleep(5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
