"""
Tests for dashboard API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_get_dashboard():
    from app.api.v1.dashboard import get_dashboard

    plan_rows = [
        {"id": "p1", "user_id": "user-1", "status": "active", "created_at": None, "updated_at": None},
    ]
    note_rows = [
        {"id": "n1", "user_id": "user-1", "note_type": "pdf", "title": "Note", "created_at": None},
    ]

    with patch('app.api.v1.dashboard.fetch', AsyncMock(side_effect=[plan_rows, note_rows])):
        result = await get_dashboard(user_id="user-1")

    assert len(result["active_plans"]) == 1
    assert len(result["recent_notes"]) == 1
