"""
Queue API Endpoints

Handles priority queue retrieval via ADK Planner Agent.
"""

from fastapi import APIRouter, Query

from app.a2a.client import get_a2a_client

router = APIRouter()


@router.get("")
async def get_priority_queue(
    user_id: str = Query(...),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get the prioritized content queue for a user.
    
    Multi-signal priority algorithm:
    - Goal alignment (40%)
    - Recency/trending (25%)
    - Prerequisites (20%)
    - User behavior (15%)
    """
    a2a_client = await get_a2a_client()
    
    response = await a2a_client.run_agent(
        agent_name="planner",
        message=f"Get the priority queue for user_id: {user_id} with limit: {limit}",
        user_id=user_id
    )
    
    if response.error_data:
        return {"queue": [], "error": response.error_data.get("message")}
    
    return {"queue": [], "response": response.result}


@router.post("/recalculate")
async def recalculate_priority(user_id: str = Query(...)):
    """Force recalculation of priority queue."""
    a2a_client = await get_a2a_client()
    
    response = await a2a_client.run_agent(
        agent_name="planner",
        message=f"Recalculate the priority queue for user_id: {user_id}",
        user_id=user_id
    )
    
    if response.error_data:
        return {"success": False, "error": response.error_data.get("message")}
    
    return {"success": True, "response": response.result}
