"""
Notifications API Endpoints

Handles user notifications via ADK Orchestrator Agent.
"""

import ast
import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

from app.a2a.client import get_a2a_client

router = APIRouter()


def _extract_structured(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort extraction of a JSON-like object from model text."""
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    snippet = text[start:end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        try:
            value = ast.literal_eval(snippet)
            if isinstance(value, dict):
                return value
        except Exception:
            return None
    return None


@router.get("")
async def get_notifications(
    user_id: str = Query(...),
    unread_only: bool = Query(False)
):
    """Get notifications for a user."""
    a2a_client = await get_a2a_client()
    
    message = f"Get notifications for user_id: {user_id}"
    if unread_only:
        message += " (unread only)"
    
    response = await a2a_client.run_agent(
        agent_name="orchestrator",
        message=message,
        user_id=user_id
    )
    
    if response.error:
        return {"notifications": [], "error": response.error.get("message")}

    structured = _extract_structured(response.result.get("text", "")) if response.result else None
    if structured and "notifications" in structured:
        return {"notifications": structured.get("notifications", []), "response": response.result}

    return {"notifications": [], "response": response.result}


@router.get("/badge")
async def get_badge_count(user_id: str = Query(...)):
    """Get unread notification count."""
    a2a_client = await get_a2a_client()
    
    response = await a2a_client.run_agent(
        agent_name="orchestrator",
        message=f"Get unread notification count for user_id: {user_id}",
        user_id=user_id
    )
    
    if response.error:
        return {"unread_count": 0}

    structured = _extract_structured(response.result.get("text", "")) if response.result else None
    if structured and "unread_count" in structured:
        return {"unread_count": structured.get("unread_count", 0), "response": response.result}

    return {"unread_count": 0, "response": response.result}


@router.post("/{notification_id}/read")
async def mark_as_read(notification_id: str, user_id: str = Query("system")):
    """Mark a notification as read."""
    a2a_client = await get_a2a_client()
    
    response = await a2a_client.run_agent(
        agent_name="orchestrator",
        message=f"Mark notification {notification_id} as read",
        user_id=user_id
    )
    
    return {"success": not response.error, "response": response.result}
