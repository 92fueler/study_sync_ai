"""
Artifacts API Endpoints

Handles artifact retrieval via ADK Synthesis Agent.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.a2a.client import get_a2a_client

router = APIRouter()


@router.get("")
async def list_artifacts(
    user_id: str = Query(...),
    artifact_type: Optional[str] = Query(None, alias="type")
):
    """List artifacts for a user."""
    a2a_client = await get_a2a_client()
    
    message = f"List artifacts for user_id: {user_id}"
    if artifact_type:
        message += f" with type: {artifact_type}"
    
    response = await a2a_client.run_agent(
        agent_name="synthesis",
        message=message,
        user_id=user_id
    )
    
    if response.error:
        raise HTTPException(status_code=400, detail=response.error.get("message"))
    
    return {"artifacts": [], "response": response.result}


@router.get("/{artifact_id}")
async def get_artifact(artifact_id: str):
    """Get a specific artifact by ID."""
    a2a_client = await get_a2a_client()
    
    response = await a2a_client.run_agent(
        agent_name="synthesis",
        message=f"Get artifact with id: {artifact_id}",
        user_id="system"
    )
    
    if response.error:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    return response.result
