"""
Tests for developer helper endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_dev_generate_learning_plan():
    from app.api.v1.dev import dev_generate_learning_plan, DevPlanGenerateRequest

    plan_row = {
        "id": "p1",
        "user_id": "user-1",
        "title": "Generated Plan 123",
        "description": "Auto-generated dev plan.",
        "goal": "Focus on core concepts and practice.",
        "status": "proposed",
        "difficulty": "Intermediate",
        "category": "TECH",
        "category_color": "blue",
        "estimated_time": "4 weeks",
        "module_count": 6,
        "details": "{\"source\":\"dev\",\"seeded\":true}",
        "metadata": "{\"seeded_at\":\"now\"}",
        "created_at": None,
        "updated_at": None,
    }

    item_row = {
        "id": "i1",
        "plan_id": "p1",
        "user_id": "user-1",
        "title": "Module 1",
        "description": "Auto-generated session",
        "status": "scheduled",
        "order_index": 0,
        "estimated_minutes": 45,
        "scheduled_at": None,
        "created_at": None,
        "updated_at": None,
    }

    with patch('app.api.v1.dev.fetchrow', AsyncMock(side_effect=[plan_row, item_row])):
        result = await dev_generate_learning_plan(
            DevPlanGenerateRequest(user_id="user-1", item_count=1)
        )

    assert result["plan"]["id"] == "p1"
    assert result["items"][0]["title"] == "Module 1"
