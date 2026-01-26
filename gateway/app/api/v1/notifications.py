"""
Notifications API Endpoints

Handles user notifications via ADK Orchestrator Agent.
"""

from fastapi import APIRouter, Query

from app.a2a.client import get_a2a_client

router = APIRouter()


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
    
    if response.error_data:
        return {"notifications": [], "error": response.error_data.get("message")}
    
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
    
    if response.error_data:
        return {"unread_count": 0}
    
    return {"unread_count": 0, "response": response.result}


@router.post("/{notification_id}/read")
async def mark_as_read(notification_id: str):
    """Mark a notification as read."""
    a2a_client = await get_a2a_client()
    
    response = await a2a_client.run_agent(
        agent_name="orchestrator",
        message=f"Mark notification {notification_id} as read",
        user_id="system"
    )
    
    return {"success": not response.error_data, "response": response.result}
