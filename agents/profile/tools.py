"""
Profile Agent Tools

ADK tools for user profile management, style DNA, and calendar integration.
"""

import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

import asyncpg


async def _get_db_connection():
    """Get database connection."""
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


def create_profile(
    user_id: str,
    display_name: Optional[str] = None,
    goals: Optional[List[str]] = None,
    style_dna: Optional[Dict[str, Any]] = None,
    calendar_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new user profile.
    
    Args:
        user_id: Unique user identifier
        display_name: User's display name
        goals: List of learning goals (e.g., ["Learn React", "Master TypeScript"])
        style_dna: Style preferences dict with tone, format_pref, uses_emoji, prefers_diagrams
        calendar_context: Calendar settings with commute_times, work_hours, timezone
    
    Returns:
        Dict with status, profile_id, and user_id
    """
    return _run_async(
        _create_profile_async(user_id, display_name, goals, style_dna, calendar_context)
    )


async def _create_profile_async(
    user_id: str,
    display_name: str,
    goals: List[str],
    style_dna: Dict[str, Any],
    calendar_context: Dict[str, Any]
) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        # Check if exists
        existing = await conn.fetchrow(
            "SELECT id FROM user_profiles WHERE user_id = $1", user_id
        )
        if existing:
            return {"status": "error", "error": "Profile already exists", "profile_id": str(existing["id"])}
        
        row = await conn.fetchrow(
            """
            INSERT INTO user_profiles (user_id, display_name, style_dna, goals, calendar_context)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            user_id, display_name,
            json.dumps(style_dna) if style_dna else None,
            json.dumps(goals) if goals else None,
            json.dumps(calendar_context) if calendar_context else None
        )
        return {"status": "success", "profile_id": str(row["id"]), "user_id": user_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def get_profile(user_id: str) -> Dict[str, Any]:
    """
    Get a user's profile including Style DNA and goals.
    
    Args:
        user_id: The user identifier
    
    Returns:
        Dict with status, user_id, display_name, style_dna, goals, calendar_context, profile_version
    """
    return _run_async(_get_profile_async(user_id))


async def _get_profile_async(user_id: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT * FROM user_profiles WHERE user_id = $1", user_id
        )
        if not row:
            return {
                "status": "success",
                "user_id": user_id,
                "style_dna": {"format_pref": "outline", "tone": "eli5", "uses_emoji": False, "prefers_diagrams": True},
                "goals": [],
                "profile_version": 1,
                "is_default": True
            }
        return {
            "status": "success",
            "user_id": row["user_id"],
            "display_name": row.get("display_name"),
            "style_dna": json.loads(row["style_dna"]) if row.get("style_dna") else None,
            "goals": json.loads(row["goals"]) if row.get("goals") else [],
            "calendar_context": json.loads(row["calendar_context"]) if row.get("calendar_context") else None,
            "profile_version": row.get("profile_version", 1)
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def update_profile(
    user_id: str,
    display_name: Optional[str] = None,
    goals: Optional[List[str]] = None,
    style_dna: Optional[Dict[str, Any]] = None,
    calendar_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update a user's profile. Updates to style_dna or goals will increment profile_version.
    
    Args:
        user_id: The user identifier
        display_name: New display name (optional)
        goals: New learning goals (optional)
        style_dna: New style preferences (optional)
        calendar_context: New calendar settings (optional)
    
    Returns:
        Dict with status and new profile_version
    """
    return _run_async(
        _update_profile_async(user_id, display_name, goals, style_dna, calendar_context)
    )


async def _update_profile_async(
    user_id: str,
    display_name: str,
    goals: List[str],
    style_dna: Dict[str, Any],
    calendar_context: Dict[str, Any]
) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        updates = []
        values = []
        idx = 1
        
        if display_name is not None:
            updates.append(f"display_name = ${idx}")
            values.append(display_name)
            idx += 1
        if goals is not None:
            updates.append(f"goals = ${idx}")
            values.append(json.dumps(goals))
            idx += 1
        if style_dna is not None:
            updates.append(f"style_dna = ${idx}")
            values.append(json.dumps(style_dna))
            idx += 1
        if calendar_context is not None:
            updates.append(f"calendar_context = ${idx}")
            values.append(json.dumps(calendar_context))
            idx += 1
        
        if not updates:
            return {"status": "error", "error": "No fields to update"}
        
        values.append(user_id)
        query = f"UPDATE user_profiles SET {', '.join(updates)} WHERE user_id = ${idx}"
        await conn.execute(query, *values)
        
        # Get new version
        row = await conn.fetchrow(
            "SELECT profile_version FROM user_profiles WHERE user_id = $1", user_id
        )
        return {"status": "success", "profile_version": row["profile_version"] if row else 1}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def get_calendar_context(user_id: str) -> Dict[str, Any]:
    """
    Get calendar context for time-aware content generation.
    
    Args:
        user_id: The user identifier
    
    Returns:
        Dict with status, has_calendar, next_slot_minutes, and context type
    """
    return _run_async(_get_calendar_context_async(user_id))


async def _get_calendar_context_async(user_id: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT calendar_context FROM user_profiles WHERE user_id = $1", user_id
        )
        
        if not row or not row.get("calendar_context"):
            return {"status": "success", "has_calendar": False, "next_slot_minutes": 25, "context": "default"}
        
        cal = json.loads(row["calendar_context"])
        now = datetime.now()
        hour = now.hour
        
        # Check commute times
        for commute in cal.get("commute_times", []):
            if "-" in commute:
                start_h = int(commute.split("-")[0].split(":")[0])
                end_h = int(commute.split("-")[1].split(":")[0])
                if start_h <= hour < end_h:
                    return {"status": "success", "has_calendar": True, "next_slot_minutes": 30, "context": "commute", **cal}
        
        # Check work hours
        work_hours = cal.get("work_hours", "")
        if work_hours and "-" in work_hours:
            start_h = int(work_hours.split("-")[0].split(":")[0])
            end_h = int(work_hours.split("-")[1].split(":")[0])
            if start_h <= hour < end_h:
                return {"status": "success", "has_calendar": True, "next_slot_minutes": 5, "context": "work", **cal}
        
        return {"status": "success", "has_calendar": True, "next_slot_minutes": 45, "context": "free_time", **cal}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def record_feedback(
    user_id: str,
    artifact_id: str,
    explicit_rating: Optional[int] = None,
    time_spent_seconds: Optional[int] = None,
    scroll_depth_percent: Optional[int] = None,
    completed: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Record user feedback on an artifact.
    
    Args:
        user_id: The user identifier
        artifact_id: The artifact being rated
        explicit_rating: 1-5 star rating (optional)
        time_spent_seconds: Time spent reading (optional)
        scroll_depth_percent: How far scrolled 0-100 (optional)
        completed: Whether user completed reading (optional)
    
    Returns:
        Dict with status and feedback_id
    """
    return _run_async(
        _record_feedback_async(user_id, artifact_id, explicit_rating, time_spent_seconds, scroll_depth_percent, completed)
    )


async def _record_feedback_async(
    user_id: str,
    artifact_id: str,
    explicit_rating: int,
    time_spent_seconds: int,
    scroll_depth_percent: int,
    completed: bool
) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO feedback 
            (user_id, artifact_id, explicit_rating, time_spent_seconds, scroll_depth_percent, completed)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            user_id, artifact_id, explicit_rating, time_spent_seconds, scroll_depth_percent, completed
        )
        return {"status": "success", "feedback_id": str(row["id"])}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()
