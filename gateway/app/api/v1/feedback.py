"""
Feedback API Endpoints

Handles user feedback on artifacts via ADK Profile Agent.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.a2a.client import get_a2a_client

router = APIRouter()


class FeedbackCreate(BaseModel):
    user_id: str
    artifact_id: str
    explicit_rating: Optional[int] = Field(None, ge=1, le=5)
    time_spent_seconds: Optional[int] = None
    scroll_depth_percent: Optional[int] = Field(None, ge=0, le=100)
    completed: Optional[bool] = None


@router.post("")
async def submit_feedback(feedback: FeedbackCreate):
    """Submit feedback for an artifact."""
    a2a_client = await get_a2a_client()
    
    message = f"""Record user feedback:
- user_id: {feedback.user_id}
- artifact_id: {feedback.artifact_id}
- explicit_rating: {feedback.explicit_rating}
- time_spent_seconds: {feedback.time_spent_seconds}
- scroll_depth_percent: {feedback.scroll_depth_percent}
- completed: {feedback.completed}"""
    
    response = await a2a_client.run_agent(
        agent_name="profile",
        message=message,
        user_id=feedback.user_id
    )
    
    if response.error_data:
        raise HTTPException(status_code=400, detail=response.error_data.get("message"))
    
    return {"success": True, "response": response.result}
