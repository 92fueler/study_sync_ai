"""
Orchestrator Agent Tools

ADK tools for background job management and notifications.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional

import asyncpg

logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    logging.basicConfig(level=os.getenv("AGENT_LOG_LEVEL", "INFO"))


async def _get_db_connection():
    dsn = os.getenv("SUPABASE_URL", "")
    logger.debug("Connecting to DB for orchestrator tools")
    return await asyncpg.connect(dsn)


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
    logger.info("detect_changes called", extra={"user_id": user_id})
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
        
        result = {
            "status": "success",
            "new_content": [{"content_id": str(m["content_id"]), "uploaded_at": str(m["uploaded_at"])} for m in materials],
            "profile_updated": False,
            "pending_jobs": job_count["count"] if job_count else 0
        }
        logger.info("detect_changes completed", extra={"user_id": user_id, "new_content": len(materials)})
        return result
    except Exception as e:
        logger.exception("detect_changes failed", extra={"user_id": user_id})
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
    logger.info("schedule_generation called", extra={"user_id": user_id, "job_type": job_type, "priority": priority})
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
        result = {"status": "success", "job_id": str(row["id"]), "job_status": "QUEUED"}
        logger.info("schedule_generation queued", extra={"user_id": user_id, "job_id": result["job_id"]})
        return result
    except Exception as e:
        logger.exception("schedule_generation failed", extra={"user_id": user_id, "job_type": job_type})
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
    logger.info("get_job_status called", extra={"job_id": job_id})
    return _run_async(_get_job_status_async(job_id))


async def _get_job_status_async(job_id: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM background_jobs WHERE id = $1", job_id)
        if not row:
            return {"status": "error", "error": "Job not found"}
        result = {
            "status": "success",
            "job_id": str(row["id"]),
            "job_status": row["status"],
            "job_type": row["job_type"],
            "priority": row["priority"],
            "attempts": row["attempts"],
            "created_at": str(row["created_at"]),
            "started_at": str(row["started_at"]) if "started_at" in row and row["started_at"] else "",
            "completed_at": str(row["completed_at"]) if "completed_at" in row and row["completed_at"] else "",
            "error_message": row["error_message"] if "error_message" in row else None
        }
        logger.info("get_job_status completed", extra={"job_id": job_id, "status": result["job_status"]})
        return result
    except Exception as e:
        logger.exception("get_job_status failed", extra={"job_id": job_id})
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
    logger.info("get_notifications called", extra={"user_id": user_id, "unread_only": unread_only})
    return _run_async(_get_notifications_async(user_id, unread_only))


async def _get_notifications_async(user_id: str, unread_only: bool) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        if unread_only:
            rows = await conn.fetch(
                """
                SELECT id, user_id, title, body, data, read, created_at
                FROM notifications
                WHERE user_id = $1 AND read = FALSE
                ORDER BY created_at DESC
                """,
                user_id
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, user_id, title, body, data, read, created_at
                FROM notifications
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                user_id
            )
        result = {
            "status": "success",
            "notifications": [
                {
                    "id": str(r["id"]),
                    "title": r["title"],
                    "body": r["body"],
                    "data": json.loads(r["data"]) if isinstance(r.get("data"), str) else r.get("data"),
                    "read": r["read"],
                    "created_at": str(r["created_at"])
                }
                for r in rows
            ]
        }
        logger.info("get_notifications completed", extra={"user_id": user_id, "count": len(rows)})
        return result
    except Exception as e:
        logger.exception("get_notifications failed", extra={"user_id": user_id})
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
    logger.info("get_badge_count called", extra={"user_id": user_id})
    return _run_async(_get_badge_count_async(user_id))


async def _get_badge_count_async(user_id: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT COUNT(*) as count FROM notifications WHERE user_id = $1 AND read = FALSE",
            user_id
        )
        result = {"status": "success", "unread_count": row["count"] if row else 0}
        logger.info("get_badge_count completed", extra={"user_id": user_id, "unread_count": result["unread_count"]})
        return result
    except Exception as e:
        logger.exception("get_badge_count failed", extra={"user_id": user_id})
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
    logger.info("mark_notification_read called", extra={"notification_id": notification_id})
    return _run_async(_mark_read_async(notification_id))


async def _mark_read_async(notification_id: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        await conn.execute("UPDATE notifications SET read = TRUE WHERE id = $1", notification_id)
        logger.info("mark_notification_read completed", extra={"notification_id": notification_id})
        return {"status": "success"}
    except Exception as e:
        logger.exception("mark_notification_read failed", extra={"notification_id": notification_id})
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
    logger.info("create_notification called", extra={"user_id": user_id, "title": title})
    return _run_async(
        _create_notification_async(user_id, title, body, channel, data)
    )


async def _create_notification_async(
    user_id: str, title: str, body: str, channel: str, data: Dict[str, Any]
) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        payload = dict(data or {})
        payload.setdefault("channel", channel)
        row = await conn.fetchrow(
            """
            INSERT INTO notifications (user_id, title, body, data)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            user_id, title, body, json.dumps(payload) if payload else None
        )
        result = {"status": "success", "notification_id": str(row["id"])}
        logger.info("create_notification completed", extra={"user_id": user_id, "notification_id": result["notification_id"]})
        return result
    except Exception as e:
        logger.exception("create_notification failed", extra={"user_id": user_id})
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()
