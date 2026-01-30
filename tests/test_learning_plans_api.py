"""
Tests for learning plans API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_create_learning_plan():
    from app.api.v1.learning_plans import create_learning_plan, PlanCreate

    plan_row = {
        "id": "11111111-1111-1111-1111-111111111111",
        "user_id": "user-1",
        "title": "Plan A",
        "goal": "Goal",
        "status": "draft",
        "weeks": 4,
        "sessions_per_week": 3,
        "metadata": None,
        "created_at": None,
        "updated_at": None,
    }

    with patch('app.api.v1.learning_plans.fetchrow', AsyncMock(return_value=plan_row)):
        result = await create_learning_plan(PlanCreate(user_id="user-1", title="Plan A"))

    assert result["plan"]["id"] == plan_row["id"]
    assert result["items"] == []


@pytest.mark.asyncio
async def test_list_learning_plans():
    from app.api.v1.learning_plans import list_learning_plans

    rows = [
        {"id": "p1", "user_id": "user-1", "status": "draft", "created_at": None, "updated_at": None},
        {"id": "p2", "user_id": "user-1", "status": "active", "created_at": None, "updated_at": None},
    ]

    with patch('app.api.v1.learning_plans.fetch', AsyncMock(return_value=rows)):
        result = await list_learning_plans(user_id="user-1")

    assert result["count"] == 2


@pytest.mark.asyncio
async def test_plan_progress():
    from app.api.v1.learning_plans import get_learning_plan_progress

    rows = [
        {"status": "done", "count": 2},
        {"status": "pending", "count": 3},
    ]

    with patch('app.api.v1.learning_plans.fetch', AsyncMock(return_value=rows)):
        result = await get_learning_plan_progress(plan_id="p1", user_id="user-1")

    assert result["total"] == 5
    assert result["completed"] == 2
