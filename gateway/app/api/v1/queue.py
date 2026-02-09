"""
Queue API Endpoints

Handles priority queue retrieval via ADK Planner Agent.
"""

import json
import ast
from fastapi import APIRouter, Query, HTTPException

from app.a2a.client import get_a2a_client

router = APIRouter()


def _extract_structured(text: str) -> dict:
    """Extract JSON-like object from agent response text."""
    if not text:
        return {}
    # Try to find JSON object in text
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    snippet = text[start:end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        try:
            value = ast.literal_eval(snippet)
            if isinstance(value, dict):
                return value
        except Exception:
            pass
    return {}


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
    
    Returns prioritized list of content with scores and reasoning.
    """
    a2a_client = await get_a2a_client()
    
    # Use explicit tool call format that ADK agents understand
    response = await a2a_client.run_agent(
        agent_name="planner",
        message=f"Call the get_priority_queue tool with user_id={user_id} and limit={limit}. Return the queue result.",
        user_id=user_id
    )
    
    if response.error:
        raise HTTPException(
            status_code=500,
            detail=f"Planner agent error: {response.error.get('message', 'Unknown error')}"
        )
    
    # Extract structured data from agent response
    result = response.result or {}
    text = result.get("text", "")
    
    # ADK agents can return tool results in content.parts or directly in text
    # Check content.parts first (tool results)
    content = result.get("content", {})
    parts = content.get("parts", [])
    for part in parts:
        if "function_response" in part:
            # Tool result from ADK
            func_response = part["function_response"]
            if isinstance(func_response, dict) and "queue" in func_response:
                return {
                    "status": func_response.get("status", "success"),
                    "queue": func_response["queue"],
                    "total_items": func_response.get("total_items", len(func_response.get("queue", []))),
                    "message": func_response.get("message")
                }
    
    # Parse JSON from text response (agent might return JSON as text)
    parsed = _extract_structured(text)
    
    # Extract queue from parsed response (agent returns {"status": "success", "queue": [...]})
    if isinstance(parsed, dict) and "queue" in parsed:
        queue = parsed["queue"]
        return {
            "status": parsed.get("status", "success"),
            "queue": queue,
            "total_items": parsed.get("total_items", len(queue)),
            "message": parsed.get("message")
        }
    
    # Fallback: try to get queue from result directly
    if isinstance(result, dict) and "queue" in result:
        return {
            "status": "success",
            "queue": result["queue"],
            "total_items": result.get("total_items", len(result.get("queue", [])))
        }
    
    # If no queue found, return empty with helpful error message
    return {
        "status": "error",
        "queue": [],
        "error": "Could not parse priority queue from agent response. The agent may not have called the get_priority_queue tool.",
        "debug": {
            "text_preview": text[:200] if text else "No text in response",
            "result_keys": list(result.keys()) if isinstance(result, dict) else [],
            "has_content": "content" in result,
            "has_parts": "parts" in content if isinstance(content, dict) else False
        }
    }


@router.post("/recalculate")
async def recalculate_priority(user_id: str = Query(...)):
    """Force recalculation of priority queue."""
    a2a_client = await get_a2a_client()
    
    response = await a2a_client.run_agent(
        agent_name="planner",
        message=f"Recalculate the priority queue for user_id: {user_id}. Use the recalculate_priority tool.",
        user_id=user_id
    )
    
    if response.error:
        raise HTTPException(
            status_code=500,
            detail=f"Planner agent error: {response.error.get('message', 'Unknown error')}"
        )
    
    # Extract structured data from agent response
    result = response.result or {}
    text = result.get("text", "")
    parsed = _extract_structured(text)
    
    # Extract queue from parsed response
    if isinstance(parsed, dict) and "queue" in parsed:
        return {
            "success": True,
            "status": parsed.get("status", "success"),
            "queue": parsed["queue"],
            "total_items": parsed.get("total_items", len(parsed.get("queue", [])))
        }
    
    return {
        "success": True,
        "message": "Priority queue recalculated",
        "response": parsed if parsed else result
    }
