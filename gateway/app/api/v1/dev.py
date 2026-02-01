"""
Developer helper endpoints.

Use for seeding data during local development.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone
import json
import random

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import fetchrow

router = APIRouter()


class DevPlanGenerateRequest(BaseModel):
    user_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[str] = "proposed"
    difficulty: Optional[str] = "Intermediate"
    category: Optional[str] = "TECH"
    category_color: Optional[str] = "blue"
    estimated_time: Optional[str] = "4 weeks"
    module_count: Optional[int] = 6
    include_items: Optional[bool] = True
    item_count: Optional[int] = 5
    start_days_from_now: Optional[int] = 1


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


@router.post("/learning-plans/generate")
async def dev_generate_learning_plan(payload: DevPlanGenerateRequest):
    """
    Create a learning plan + optional items for dev/testing.
    """
    query = """
        INSERT INTO learning_plans (
            user_id, title, description, goal, status, difficulty, category, category_color,
            estimated_time, module_count, details, metadata
        )
        VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8,
            $9, $10, $11, $12
        )
        RETURNING *
    """
    title = payload.title or f"Generated Plan {random.randint(100, 999)}"
    description = payload.description or "Auto-generated dev plan."
    goal = payload.goal or "Focus on core concepts and practice."
    details_payload = json.dumps({"source": "dev", "seeded": True})
    metadata_payload = json.dumps({"seeded_at": datetime.now(timezone.utc).isoformat()})

    try:
        plan_row = await fetchrow(
            query,
            payload.user_id,
            title,
            description,
            goal,
            payload.status,
            payload.difficulty,
            payload.category,
            payload.category_color,
            payload.estimated_time,
            payload.module_count,
            details_payload,
            metadata_payload,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")

    items: List[Dict[str, Any]] = []
    if payload.include_items:
        item_query = """
            INSERT INTO learning_plan_items (
                plan_id, user_id, title, description, status, order_index, estimated_minutes, scheduled_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
        """
        base_date = datetime.now(timezone.utc) + timedelta(days=payload.start_days_from_now or 0)
        for i in range(payload.item_count or 0):
            try:
                row = await fetchrow(
                    item_query,
                    plan_row["id"],
                    payload.user_id,
                    f"Module {i + 1}",
                    "Auto-generated session",
                    "scheduled" if i == 0 else "pending",
                    i,
                    45,
                    base_date + timedelta(days=i),
                )
            except RuntimeError as exc:
                raise HTTPException(status_code=503, detail=str(exc))
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Database error: {exc}")
            if row:
                items.append(_item_row_to_dict(row))

    return {"plan": _plan_row_to_dict(plan_row), "items": items}
