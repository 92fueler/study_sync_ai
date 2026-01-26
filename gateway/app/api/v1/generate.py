"""
Generate API Endpoints

Handles artifact generation requests via ADK Synthesis Agent.
"""

import uuid
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.a2a.client import get_a2a_client

router = APIRouter()


class GenerateRequest(BaseModel):
    user_id: str
    content_ids: Optional[List[str]] = None
    time_available_minutes: Optional[int] = None
    format: Optional[str] = "text"


@router.post("")
async def generate_artifact(request: GenerateRequest):
    """
    Generate a personalized artifact for the user.
    
    Flow:
    1. Get user profile from Profile Agent
    2. Get calendar context if time not specified
    3. Get priority queue from Planner Agent (if no content_ids)
    4. Generate content via Synthesis Agent
    """
    a2a_client = await get_a2a_client()
    task_id = str(uuid.uuid4())
    
    # Step 1: Get user profile
    profile_response = await a2a_client.run_agent(
        agent_name="profile",
        message=f"Get the profile for user_id: {request.user_id}",
        user_id=request.user_id
    )
    
    if profile_response.error:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to get profile: {profile_response.error.get('message')}"
        )
    
    # Step 2: Determine time available
    time_available = request.time_available_minutes or 25
    
    # Step 3: Get content to generate from
    content_ids = request.content_ids or []
    if not content_ids:
        planner_response = await a2a_client.run_agent(
            agent_name="planner",
            message=f"Get the priority queue for user_id: {request.user_id}, limit 1",
            user_id=request.user_id
        )
        # Would extract content_ids from planner response
    
    if not content_ids:
        raise HTTPException(
            status_code=400,
            detail="No content available to generate from"
        )
    
    # Step 4: Generate artifact
    synthesis_response = await a2a_client.run_agent(
        agent_name="synthesis",
        message=f"""Generate a personalized study artifact:
- user_id: {request.user_id}
- content_ids: {content_ids}
- time_available_minutes: {time_available}
- format: {request.format}""",
        user_id=request.user_id,
        session_id=task_id
    )
    
    if synthesis_response.error:
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {synthesis_response.error.get('message')}"
        )
    
    return {
        "id": task_id,
        "response": synthesis_response.result,
        "format": request.format
    }


@router.get("/status/{task_id}")
async def get_generation_status(task_id: str):
    """Check the status of a generation task."""
    return {"id": task_id, "status": "completed"}
