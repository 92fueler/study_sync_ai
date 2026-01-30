"""
Learning Plans API Endpoints

CRUD for learning plans and plan items (non-agent, direct DB).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db import fetch, fetchrow

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
    goal: Optional[str] = None
    status: Optional[str] = "draft"
    weeks: Optional[int] = None
    sessions_per_week: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    items: Optional[List[PlanItemCreate]] = None


class PlanUpdate(BaseModel):
    title: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[str] = None
    weeks: Optional[int] = None
    sessions_per_week: Optional[int] = None
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
        INSERT INTO learning_plans (user_id, title, goal, status, weeks, sessions_per_week, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
    """
    try:
        row = await fetchrow(
            query,
            request.user_id,
            request.title,
            request.goal,
            request.status,
            request.weeks,
            request.sessions_per_week,
            request.metadata,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

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
            except Exception:
                raise HTTPException(status_code=500, detail="Database error")

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
        SET status = 'active', updated_at = NOW()
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
