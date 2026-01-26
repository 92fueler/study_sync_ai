"""
Orchestrator Agent Tools

ADK tools for background job management and notifications.
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional

import asyncpg


async def _get_db_connection():
    return await asyncpg.connect(os.getenv("SUPABASE_URL", ""))


def _run_async(coro):
    """Run async coroutine safely, handling existing event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


def detect_changes(user_id: str) -> Dict[str, Any]:
    """
    Detect new content or profile changes that need processing.
    
    Args:
        user_id: User identifier
    
    Returns:
        Dict with status, new_content list, profile_updated flag, pending_jobs count
    """
    return _run_async(_detect_changes_async(user_id))


async def _detect_changes_async(user_id: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        # Check unprocessed materials
        materials = await conn.fetch(
            "SELECT content_id, uploaded_at FROM user_materials WHERE user_id = $1 AND status = 'UNPROCESSED'",
            user_id
        )
        
        # Check pending jobs
        job_count = await conn.fetchrow(
            "SELECT COUNT(*) as count FROM background_jobs WHERE user_id = $1 AND status IN ('QUEUED', 'RUNNING')",
            user_id
        )
        
        return {
            "status": "success",
            "new_content": [{"content_id": str(m["content_id"]), "uploaded_at": str(m["uploaded_at"])} for m in materials],
            "profile_updated": False,
            "pending_jobs": job_count["count"] if job_count else 0
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def schedule_generation(
    user_id: str,
    job_type: str,
    content_id: Optional[str] = None,
    priority: str = "NORMAL"
) -> Dict[str, Any]:
    """
    Schedule content for background generation.
    
    Args:
        user_id: User identifier
        job_type: One of generate_5min_new, generate_full_new, regenerate_existing, recalc_priority, send_notification
        content_id: Content UUID (optional, depends on job_type)
        priority: HIGH, NORMAL, or LOW
    
    Returns:
        Dict with status, job_id, and initial job status
    """
    return _run_async(
        _schedule_generation_async(user_id, job_type, content_id, priority)
    )


async def _schedule_generation_async(user_id: str, job_type: str, content_id: str, priority: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO background_jobs (user_id, job_type, payload, priority)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            user_id, job_type, json.dumps({"content_id": content_id}) if content_id else None, priority
        )
        return {"status": "success", "job_id": str(row["id"]), "job_status": "QUEUED"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get status of a background job.
    
    Args:
        job_id: Job UUID
    
    Returns:
        Dict with status and job details including job_status, attempts, timestamps
    """
    return _run_async(_get_job_status_async(job_id))


async def _get_job_status_async(job_id: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM background_jobs WHERE id = $1", job_id)
        if not row:
            return {"status": "error", "error": "Job not found"}
        return {
            "status": "success",
            "job_id": str(row["id"]),
            "job_status": row["status"],
            "job_type": row["job_type"],
            "priority": row["priority"],
            "attempts": row["attempts"],
            "created_at": str(row["created_at"]),
            "started_at": str(row.get("started_at", "")),
            "completed_at": str(row.get("completed_at", "")),
            "error_message": row.get("error_message")
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def get_notifications(user_id: str, unread_only: bool = False) -> Dict[str, Any]:
    """
    Get notifications for a user.
    
    Args:
        user_id: User identifier
        unread_only: If True, return only unread notifications
    
    Returns:
        Dict with status and list of notifications
    """
    return _run_async(_get_notifications_async(user_id, unread_only))


async def _get_notifications_async(user_id: str, unread_only: bool) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        if unread_only:
            rows = await conn.fetch(
                "SELECT * FROM notifications WHERE user_id = $1 AND read = FALSE ORDER BY created_at DESC",
                user_id
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM notifications WHERE user_id = $1 ORDER BY created_at DESC",
                user_id
            )
        return {
            "status": "success",
            "notifications": [
                {
                    "id": str(r["id"]),
                    "channel": r["channel"],
                    "title": r["title"],
                    "body": r["body"],
                    "data": json.loads(r["data"]) if r.get("data") else None,
                    "read": r["read"],
                    "created_at": str(r["created_at"])
                }
                for r in rows
            ]
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def get_badge_count(user_id: str) -> Dict[str, Any]:
    """
    Get unread notification count for badge display.
    
    Args:
        user_id: User identifier
    
    Returns:
        Dict with status and unread_count
    """
    return _run_async(_get_badge_count_async(user_id))


async def _get_badge_count_async(user_id: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT COUNT(*) as count FROM notifications WHERE user_id = $1 AND read = FALSE",
            user_id
        )
        return {"status": "success", "unread_count": row["count"] if row else 0}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def mark_notification_read(notification_id: str) -> Dict[str, Any]:
    """
    Mark a notification as read.
    
    Args:
        notification_id: Notification UUID
    
    Returns:
        Dict with status
    """
    return _run_async(_mark_read_async(notification_id))


async def _mark_read_async(notification_id: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        await conn.execute("UPDATE notifications SET read = TRUE WHERE id = $1", notification_id)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def create_notification(
    user_id: str,
    title: str,
    body: str,
    channel: str = "in_app",
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a notification for a user.
    
    Args:
        user_id: User identifier
        title: Notification title
        body: Notification body text
        channel: One of push, in_app, email
        data: Optional metadata (e.g., artifact_id for deep linking)
    
    Returns:
        Dict with status and notification_id
    """
    return _run_async(
        _create_notification_async(user_id, title, body, channel, data)
    )


async def _create_notification_async(
    user_id: str, title: str, body: str, channel: str, data: Dict[str, Any]
) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO notifications (user_id, channel, title, body, data)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            user_id, channel, title, body, json.dumps(data) if data else None
        )
        return {"status": "success", "notification_id": str(row["id"])}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()
