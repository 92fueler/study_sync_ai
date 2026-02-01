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
async def test_create_learning_plan_with_details_metadata():
    from app.api.v1.learning_plans import create_learning_plan, PlanCreate

    plan_row = {
        "id": "p3",
        "user_id": "user-1",
        "title": "Plan B",
        "goal": "Goal",
        "status": "proposed",
        "details": "{\"source\":\"ui\"}",
        "metadata": "{\"seeded\":true}",
        "created_at": None,
        "updated_at": None,
    }

    with patch('app.api.v1.learning_plans.fetchrow', AsyncMock(return_value=plan_row)):
        result = await create_learning_plan(
            PlanCreate(
                user_id="user-1",
                title="Plan B",
                details={"source": "ui"},
                metadata={"seeded": True},
            )
        )

    assert result["plan"]["details"]["source"] == "ui"
    assert result["plan"]["metadata"]["seeded"] is True


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
async def test_get_learning_plan():
    from app.api.v1.learning_plans import get_learning_plan

    plan_row = {
        "id": "p10",
        "user_id": "user-1",
        "status": "active",
        "details": "{\"current_module\":\"Intro\"}",
        "metadata": None,
        "created_at": None,
        "updated_at": None,
    }

    with patch('app.api.v1.learning_plans.fetchrow', AsyncMock(return_value=plan_row)):
        result = await get_learning_plan(plan_id="p10", user_id="user-1", include_items=False)

    assert result["plan"]["id"] == "p10"
    assert result["plan"]["details"]["current_module"] == "Intro"


@pytest.mark.asyncio
async def test_list_proposed_learning_plans():
    from app.api.v1.learning_plans import list_proposed_learning_plans

    rows = [
        {"id": "p11", "user_id": "user-1", "status": "proposed", "created_at": None, "updated_at": None},
    ]

    with patch('app.api.v1.learning_plans.fetch', AsyncMock(return_value=rows)):
        result = await list_proposed_learning_plans(user_id="user-1")

    assert result["count"] == 1


@pytest.mark.asyncio
async def test_pause_and_resume_plan():
    from app.api.v1.learning_plans import pause_learning_plan, resume_learning_plan

    pause_row = {
        "id": "p12",
        "user_id": "user-1",
        "status": "paused",
        "paused_at": None,
        "created_at": None,
        "updated_at": None,
    }
    resume_row = {
        "id": "p12",
        "user_id": "user-1",
        "status": "active",
        "paused_at": None,
        "created_at": None,
        "updated_at": None,
    }

    with patch('app.api.v1.learning_plans.fetchrow', AsyncMock(side_effect=[pause_row, resume_row])):
        paused = await pause_learning_plan(plan_id="p12", user_id="user-1")
        resumed = await resume_learning_plan(plan_id="p12", user_id="user-1")

    assert paused["plan"]["status"] == "paused"
    assert resumed["plan"]["status"] == "active"


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
