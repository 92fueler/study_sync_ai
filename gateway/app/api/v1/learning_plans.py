"""
Learning Plans API Endpoints

CRUD for learning plans and plan items (non-agent, direct DB).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import json
import logging
import re
import ast

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db import fetch, fetchrow, execute
from app.a2a.client import get_a2a_client

logger = logging.getLogger(__name__)


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

router = APIRouter()


class PlanItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    content_ids: Optional[List[str]] = None
    status: Optional[str] = "pending"
    order_index: Optional[int] = 0
    estimated_minutes: Optional[int] = None
    scheduled_at: Optional[datetime] = None


class PlanCreate(BaseModel):
    user_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[str] = "proposed"
    difficulty: Optional[str] = None
    category: Optional[str] = None
    category_color: Optional[str] = None
    estimated_time: Optional[str] = None
    module_count: Optional[int] = None
    progress_percent: Optional[int] = None
    total_modules: Optional[int] = None
    completed_modules: Optional[int] = None
    next_session_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    weeks: Optional[int] = None
    sessions_per_week: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    items: Optional[List[PlanItemCreate]] = None


class PlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[str] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None
    category_color: Optional[str] = None
    estimated_time: Optional[str] = None
    module_count: Optional[int] = None
    progress_percent: Optional[int] = None
    total_modules: Optional[int] = None
    completed_modules: Optional[int] = None
    next_session_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    weeks: Optional[int] = None
    sessions_per_week: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class PlanItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content_ids: Optional[List[str]] = None
    status: Optional[str] = None
    order_index: Optional[int] = None
    estimated_minutes: Optional[int] = None
    scheduled_at: Optional[datetime] = None


def _plan_row_to_dict(row) -> Dict[str, Any]:
    plan = dict(row)
    plan["id"] = str(plan["id"])
    plan["created_at"] = plan.get("created_at")
    plan["updated_at"] = plan.get("updated_at")
    for field in ("details", "metadata"):
        if isinstance(plan.get(field), str):
            try:
                plan[field] = json.loads(plan[field])
            except Exception:
                pass
    return plan


def _item_row_to_dict(row) -> Dict[str, Any]:
    item = dict(row)
    item["id"] = str(item["id"])
    item["plan_id"] = str(item["plan_id"])
    if item.get("content_ids") is not None:
        item["content_ids"] = [str(cid) for cid in item["content_ids"]]
    item["created_at"] = item.get("created_at")
    item["updated_at"] = item.get("updated_at")
    return item


@router.post("")
async def create_learning_plan(request: PlanCreate):
    """Create a learning plan (draft by default)."""
    query = """
        INSERT INTO learning_plans (
            user_id, title, description, goal, status, difficulty, category, category_color,
            estimated_time, module_count, progress_percent, total_modules, completed_modules,
            next_session_at, paused_at, weeks, sessions_per_week, details, metadata
        )
        VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8,
            $9, $10, $11, $12, $13,
            $14, $15, $16, $17, $18, $19
        )
        RETURNING *
    """
    try:
        details_payload = json.dumps(request.details) if request.details is not None else None
        metadata_payload = json.dumps(request.metadata) if request.metadata is not None else None
        row = await fetchrow(
            query,
            request.user_id,
            request.title,
            request.description,
            request.goal,
            request.status,
            request.difficulty,
            request.category,
            request.category_color,
            request.estimated_time,
            request.module_count,
            request.progress_percent,
            request.total_modules,
            request.completed_modules,
            request.next_session_at,
            request.paused_at,
            request.weeks,
            request.sessions_per_week,
            details_payload,
            metadata_payload,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")

    plan = _plan_row_to_dict(row)
    items: List[Dict[str, Any]] = []

    if request.items:
        item_query = """
            INSERT INTO learning_plan_items
                (plan_id, user_id, title, description, content_ids, status, order_index, estimated_minutes, scheduled_at)
            VALUES ($1, $2, $3, $4, $5::uuid[], $6, $7, $8, $9)
            RETURNING *
        """
        for item in request.items:
            try:
                item_row = await fetchrow(
                    item_query,
                    plan["id"],
                    request.user_id,
                    item.title,
                    item.description,
                    item.content_ids,
                    item.status,
                    item.order_index,
                    item.estimated_minutes,
                    item.scheduled_at,
                )
                items.append(_item_row_to_dict(item_row))
            except RuntimeError as exc:
                raise HTTPException(status_code=503, detail=str(exc))
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Database error: {exc}")

    return {"plan": plan, "items": items}


@router.get("")
async def list_learning_plans(
    user_id: str = Query(...),
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List learning plans for a user."""
    status_filter = ""
    params: List[Any] = [user_id]
    if status:
        status_filter = "AND status = $2"
        params.append(status)

    query = f"""
        SELECT * FROM learning_plans
        WHERE user_id = $1 {status_filter}
        ORDER BY created_at DESC
        LIMIT ${{limit_param}} OFFSET ${{offset_param}}
    """

    try:
        limit_param = len(params) + 1
        offset_param = len(params) + 2
        rows = await fetch(query.format(limit_param=limit_param, offset_param=offset_param), *params, limit, offset)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    plans = [_plan_row_to_dict(row) for row in rows]
    return {"user_id": user_id, "count": len(plans), "items": plans}


@router.get("/proposed")
async def list_proposed_learning_plans(
    user_id: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    """List proposed learning plans (carousel)."""
    query = """
        SELECT * FROM learning_plans
        WHERE user_id = $1 AND status = 'proposed'
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
    """
    try:
        rows = await fetch(query, user_id, limit, offset)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    plans = [_plan_row_to_dict(row) for row in rows]
    return {"user_id": user_id, "count": len(plans), "items": plans}


@router.get("/{plan_id}")
async def get_learning_plan(
    plan_id: str,
    user_id: str = Query(...),
    include_items: bool = Query(True),
):
    """Get a learning plan and optionally its items."""
    query = "SELECT * FROM learning_plans WHERE id = $1 AND user_id = $2"
    try:
        row = await fetchrow(query, plan_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan = _plan_row_to_dict(row)

    items: List[Dict[str, Any]] = []
    if include_items:
        item_query = """
            SELECT * FROM learning_plan_items
            WHERE plan_id = $1 AND user_id = $2
            ORDER BY order_index ASC, created_at ASC
        """
        try:
            item_rows = await fetch(item_query, plan_id, user_id)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        except Exception:
            raise HTTPException(status_code=500, detail="Database error")
        items = [_item_row_to_dict(row) for row in item_rows]

    return {"plan": plan, "items": items}


@router.patch("/{plan_id}")
async def update_learning_plan(plan_id: str, user_id: str = Query(...), update: PlanUpdate = ...):
    """Update a learning plan."""
    update = update or PlanUpdate()
    updates: List[str] = []
    params: List[Any] = []
    idx = 1

    for field, value in update.model_dump(exclude_unset=True).items():
        if field in {"details", "metadata"} and value is not None:
            value = json.dumps(value)
        updates.append(f"{field} = ${idx}")
        params.append(value)
        idx += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = NOW()")
    query = f"""
        UPDATE learning_plans
        SET {', '.join(updates)}
        WHERE id = ${idx} AND user_id = ${idx + 1}
        RETURNING *
    """

    try:
        row = await fetchrow(query, *params, plan_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")

    return {"plan": _plan_row_to_dict(row)}


@router.post("/{plan_id}/approve")
async def approve_learning_plan(plan_id: str, user_id: str = Query(...)):
    """Approve (activate) a learning plan."""
    query = """
        UPDATE learning_plans
        SET status = 'active', paused_at = NULL, updated_at = NOW()
        WHERE id = $1 AND user_id = $2
        RETURNING *
    """
    try:
        row = await fetchrow(query, plan_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")

    return {"plan": _plan_row_to_dict(row)}


@router.post("/{plan_id}/pause")
async def pause_learning_plan(plan_id: str, user_id: str = Query(...)):
    """Pause an active learning plan."""
    query = """
        UPDATE learning_plans
        SET status = 'paused', paused_at = NOW(), updated_at = NOW()
        WHERE id = $1 AND user_id = $2
        RETURNING *
    """
    try:
        row = await fetchrow(query, plan_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")

    return {"plan": _plan_row_to_dict(row)}


@router.post("/{plan_id}/resume")
async def resume_learning_plan(plan_id: str, user_id: str = Query(...)):
    """Resume a paused learning plan."""
    query = """
        UPDATE learning_plans
        SET status = 'active', paused_at = NULL, updated_at = NOW()
        WHERE id = $1 AND user_id = $2
        RETURNING *
    """
    try:
        row = await fetchrow(query, plan_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")

    return {"plan": _plan_row_to_dict(row)}


@router.delete("/{plan_id}")
async def delete_learning_plan(plan_id: str, user_id: str = Query(...)):
    """Delete a learning plan and all its items."""
    # First delete all plan items
    delete_items_query = """
        DELETE FROM learning_plan_items
        WHERE plan_id = $1 AND user_id = $2
    """
    try:
        await execute(delete_items_query, plan_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    # Then delete the plan
    delete_plan_query = """
        DELETE FROM learning_plans
        WHERE id = $1 AND user_id = $2
        RETURNING *
    """
    try:
        row = await fetchrow(delete_plan_query, plan_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")

    return {"message": "Plan deleted successfully", "plan": _plan_row_to_dict(row)}


@router.post("/{plan_id}/items")
async def add_learning_plan_item(
    plan_id: str,
    request: PlanItemCreate,
    user_id: str = Query(...),
):
    """Add an item to a learning plan."""
    query = """
        INSERT INTO learning_plan_items
            (plan_id, user_id, title, description, content_ids, status, order_index, estimated_minutes, scheduled_at)
        VALUES ($1, $2, $3, $4, $5::uuid[], $6, $7, $8, $9)
        RETURNING *
    """
    try:
        row = await fetchrow(
            query,
            plan_id,
            user_id,
            request.title,
            request.description,
            request.content_ids,
            request.status,
            request.order_index,
            request.estimated_minutes,
            request.scheduled_at,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    return {"item": _item_row_to_dict(row)}


@router.patch("/{plan_id}/items/{item_id}")
async def update_learning_plan_item(
    plan_id: str,
    item_id: str,
    user_id: str = Query(...),
    update: PlanItemUpdate = ...,
):
    """Update a plan item."""
    update = update or PlanItemUpdate()
    updates: List[str] = []
    params: List[Any] = []
    idx = 1

    for field, value in update.model_dump(exclude_unset=True).items():
        updates.append(f"{field} = ${idx}")
        params.append(value)
        idx += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = NOW()")
    query = f"""
        UPDATE learning_plan_items
        SET {', '.join(updates)}
        WHERE id = ${idx} AND plan_id = ${idx + 1} AND user_id = ${idx + 2}
        RETURNING *
    """

    try:
        row = await fetchrow(query, *params, item_id, plan_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"item": _item_row_to_dict(row)}


@router.delete("/{plan_id}/items/{item_id}")
async def delete_learning_plan_item(
    plan_id: str,
    item_id: str,
    user_id: str = Query(...),
):
    """Delete a plan item."""
    query = """
        DELETE FROM learning_plan_items
        WHERE id = $1 AND plan_id = $2 AND user_id = $3
        RETURNING id
    """
    try:
        row = await fetchrow(query, item_id, plan_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"success": True}


@router.get("/{plan_id}/progress")
async def get_learning_plan_progress(plan_id: str, user_id: str = Query(...)):
    """Return counts by status for a plan."""
    query = """
        SELECT status, COUNT(*) AS count
        FROM learning_plan_items
        WHERE plan_id = $1 AND user_id = $2
        GROUP BY status
    """
    try:
        rows = await fetch(query, plan_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    totals = {row["status"]: row["count"] for row in rows}
    total = sum(totals.values())
    completed = totals.get("done", 0)
    return {
        "plan_id": plan_id,
        "total": total,
        "completed": completed,
        "by_status": totals,
        "percent": round((completed / total) * 100, 2) if total else 0.0,
    }


@router.post("/generate-suggested")
async def generate_suggested_plans(
    user_id: str = Query(...),
    context_mode: str = Query("growth"),
    max_plans: int = Query(3, ge=1, le=5)
):
    """
    Generate suggested learning plans using Planner Agent.
    
    Uses semantic clustering and prioritization to create structured learning plans
    with modules, sequencing, and time estimates. Plans are created with status='proposed'.
    """
    try:
        a2a_client = await get_a2a_client()
        
        # Call Planner Agent to generate plans
        # Use explicit tool call format that ADK agents understand
        try:
            response = await a2a_client.run_agent(
                agent_name="planner",
                message=f"Call the generate_learning_plan tool with user_id={user_id}, context_mode={context_mode}, and max_plans={max_plans}. Return the plans result.",
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Failed to call planner agent: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to communicate with planner agent: {str(e)}"
            )
        
        if response.error:
            error_msg = "Unknown error"
            if isinstance(response.error, dict):
                error_msg = response.error.get('message', str(response.error))
            else:
                error_msg = str(response.error)
            logger.error(f"Planner agent returned error: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Planner agent error: {error_msg}"
            )
        
        # Extract plans from agent response
        result = response.result or {}
        text = result.get("text", "")
        
        # Check if the tool returned an error status
        # The planner tool can return {"status": "error", "error": "..."}
        if isinstance(result, dict) and result.get("status") == "error":
            error_msg = result.get("error", "Unknown error from planner agent")
            logger.error(f"Planner agent tool returned error: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Planner agent error: {error_msg}"
            )
        
        # Look for JSON in function_response or text
        content = result.get("content", {})
        parts = content.get("parts", [])
        plans_data = None
        
        # First, try to get from function_response (ADK tool result)
        # Check function_responses array (if ADK client extracted them)
        function_responses = result.get("function_responses", [])
        for func_response in function_responses:
            if isinstance(func_response, dict):
                # Check for error status first
                if func_response.get("status") == "error":
                    error_msg = func_response.get("error", "Unknown error from planner agent")
                    logger.error(f"Planner agent tool returned error in function_response: {error_msg}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Planner agent error: {error_msg}"
                    )
                if "plans" in func_response:
                    plans_data = func_response
                    break
                if "response" in func_response and isinstance(func_response["response"], dict):
                    # Check nested response for error
                    nested_response = func_response["response"]
                    if nested_response.get("status") == "error":
                        error_msg = nested_response.get("error", "Unknown error from planner agent")
                        logger.error(f"Planner agent tool returned error in nested response: {error_msg}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Planner agent error: {error_msg}"
                        )
                    if "plans" in nested_response:
                        plans_data = nested_response
                        break
        
        # Also check parts array directly (fallback)
        if not plans_data:
            for part in parts:
                if "function_response" in part:
                    func_response = part["function_response"]
                    if isinstance(func_response, dict):
                        # Check for error status first
                        if func_response.get("status") == "error":
                            error_msg = func_response.get("error", "Unknown error from planner agent")
                            logger.error(f"Planner agent tool returned error in parts function_response: {error_msg}")
                            raise HTTPException(
                                status_code=500,
                                detail=f"Planner agent error: {error_msg}"
                            )
                        # Tool returns {"status": "success", "plans": [...]}
                        if "plans" in func_response:
                            plans_data = func_response
                            break
                        # Or might be nested in a response field
                        if "response" in func_response and isinstance(func_response["response"], dict):
                            nested_response = func_response["response"]
                            # Check nested response for error
                            if nested_response.get("status") == "error":
                                error_msg = nested_response.get("error", "Unknown error from planner agent")
                                logger.error(f"Planner agent tool returned error in nested parts response: {error_msg}")
                                raise HTTPException(
                                    status_code=500,
                                    detail=f"Planner agent error: {error_msg}"
                                )
                            if "plans" in nested_response:
                                plans_data = nested_response
                                break
        
        # If not found, try parsing text (agent might return JSON as text)
        if not plans_data and text:
            # First try: Use the same extraction method as queue.py
            parsed = _extract_structured(text)
            if isinstance(parsed, dict) and "plans" in parsed:
                plans_data = parsed
            
            # Second try: Extract from markdown code blocks
            if not plans_data:
                if "```json" in text:
                    start = text.find("```json") + 7
                    end = text.find("```", start)
                    if end > start:
                        try:
                            extracted = json.loads(text[start:end].strip())
                            if isinstance(extracted, dict) and "plans" in extracted:
                                plans_data = extracted
                        except json.JSONDecodeError:
                            pass
                elif "```" in text:
                    start = text.find("```") + 3
                    end = text.find("```", start)
                    if end > start:
                        try:
                            extracted = json.loads(text[start:end].strip())
                            if isinstance(extracted, dict) and "plans" in extracted:
                                plans_data = extracted
                        except json.JSONDecodeError:
                            pass
            
            # Third try: Parse entire text as JSON (might be pure JSON)
            if not plans_data:
                try:
                    parsed = json.loads(text.strip())
                    if isinstance(parsed, dict):
                        if "plans" in parsed:
                            plans_data = parsed
                        # Check if nested in a response field
                        elif "response" in parsed and isinstance(parsed["response"], dict):
                            if "plans" in parsed["response"]:
                                plans_data = parsed["response"]
                except json.JSONDecodeError:
                    pass
            
            # Fourth try: Look for JSON object with "plans" key using regex (more flexible)
            if not plans_data:
                # Try to find a JSON object containing "plans" array
                json_match = re.search(r'\{[^{}]*"plans"\s*:\s*\[.*?\][^{}]*\}', text, re.DOTALL)
                if json_match:
                    try:
                        extracted = json.loads(json_match.group())
                        if isinstance(extracted, dict) and "plans" in extracted:
                            plans_data = extracted
                    except json.JSONDecodeError:
                        pass
        
        if not plans_data or "plans" not in plans_data:
            # Log detailed debug info for troubleshooting
            debug_info = {
                "result_keys": list(result.keys()),
                "has_content": "content" in result,
                "parts_count": len(parts),
                "function_responses_count": len(result.get("function_responses", [])),
                "text_length": len(text),
                "text_preview": text[:500] if text else "No text"
            }
            
            # Log parts structure
            parts_info = []
            for i, part in enumerate(parts):
                part_info = {"index": i, "keys": list(part.keys())}
                if "function_response" in part:
                    part_info["function_response_keys"] = list(part["function_response"].keys()) if isinstance(part["function_response"], dict) else "not_dict"
                if "function_call" in part:
                    part_info["has_function_call"] = True
                parts_info.append(part_info)
            debug_info["parts"] = parts_info
            
            logger.error(f"Could not parse plans from planner agent response. Debug: {json.dumps(debug_info, indent=2)}")
            
            # Return more helpful error with debug info in development
            error_detail = "Could not parse plans from planner agent response."
            if text:
                error_detail += f" Text preview: {text[:300]}"
            
            raise HTTPException(
                status_code=500,
                detail=error_detail
            )
        
        plans = plans_data.get("plans", [])
        
        if not plans or len(plans) == 0:
            raise HTTPException(
                status_code=400,
                detail="No plans were generated. Make sure you have content uploaded."
            )
        
        created_plans = []
        
        # Create each plan in the database
        for plan_data in plans:
            try:
                # Prepare plan items
                items = []
                modules = plan_data.get("modules", [])
                if not modules:
                    logger.warning(f"Plan '{plan_data.get('title')}' has no modules, skipping")
                    continue
                    
                for module in modules:
                    # Validate content_ids are strings (UUIDs)
                    content_ids = module.get("content_ids", [])
                    if content_ids:
                        # Ensure all content_ids are strings and filter out empty values
                        content_ids = [str(cid).strip() for cid in content_ids if cid and str(cid).strip()]
                    
                    items.append(PlanItemCreate(
                        title=module.get("title", "Untitled Module"),
                        description=module.get("description"),
                        content_ids=content_ids if content_ids else None,
                        order_index=module.get("order_index", len(items)),
                        estimated_minutes=module.get("estimated_minutes", 45)
                    ))
                
                # Create the plan
                plan_request = PlanCreate(
                    user_id=user_id,
                    title=plan_data.get("title", "Untitled Plan"),
                    description=plan_data.get("description", ""),
                    goal=plan_data.get("goal"),
                    status="proposed",  # Always proposed for AI-generated plans
                    difficulty=plan_data.get("difficulty", "Intermediate"),
                    category=plan_data.get("category"),
                    category_color=plan_data.get("category_color", "blue"),
                    estimated_time=plan_data.get("estimated_time", "4 weeks"),
                    weeks=plan_data.get("weeks", 4),
                    sessions_per_week=plan_data.get("sessions_per_week", 3),
                    total_modules=plan_data.get("total_modules", len(items)),
                    module_count=len(items),  # Use actual count of items created
                    details=plan_data.get("details", {}),
                    metadata={"source": "planner_agent", "context_mode": context_mode},
                    items=items
                )
                
                created_plan = await create_learning_plan(plan_request)
                created_plans.append(created_plan.get("plan"))
                
            except Exception as e:
                logger.error(f"Failed to create plan: {e}", exc_info=True)
                # Continue with other plans even if one fails
        
        if len(created_plans) == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to create any plans. Check logs for details."
            )
        
        return {
            "status": "success",
            "plans_generated": len(created_plans),
            "plans": created_plans
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any other unexpected exceptions
        logger.error(f"Unexpected error in generate_suggested_plans: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
