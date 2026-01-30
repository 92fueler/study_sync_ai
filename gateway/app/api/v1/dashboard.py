"""
Dashboard API Endpoints

Aggregated data for the dashboard UI.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

from app.db import fetch

router = APIRouter()


def _plan_row_to_dict(row) -> Dict[str, Any]:
    plan = dict(row)
    plan["id"] = str(plan["id"])
    plan["created_at"] = plan.get("created_at")
    plan["updated_at"] = plan.get("updated_at")
    return plan


def _note_row_to_dict(row) -> Dict[str, Any]:
    note = dict(row)
    note["id"] = str(note["id"])
    note["created_at"] = note.get("created_at")
    return note


@router.get("")
async def get_dashboard(user_id: str = Query(...)):
    """Return dashboard summary data (active plans + recent notes)."""
    plans_query = """
        SELECT * FROM learning_plans
        WHERE user_id = $1 AND status = 'active'
        ORDER BY updated_at DESC NULLS LAST, created_at DESC
        LIMIT 3
    """
    notes_query = """
        SELECT * FROM learning_notes
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 6
    """
    try:
        plans_rows = await fetch(plans_query, user_id)
        notes_rows = await fetch(notes_query, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    return {
        "user_id": user_id,
        "active_plans": [_plan_row_to_dict(row) for row in plans_rows],
        "recent_notes": [_note_row_to_dict(row) for row in notes_rows],
    }
