"""
Tests for calendar API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_availability_no_events():
    from app.api.v1.calendar import get_availability

    with patch('app.api.v1.calendar.fetch', AsyncMock(return_value=[])):
        result = await get_availability(
            user_id="user-1",
            time_min="2026-01-01T10:00:00Z",
            time_max="2026-01-01T12:00:00Z",
            duration_min=30,
            step_min=60,
        )

    assert len(result["slots"]) == 2


@pytest.mark.asyncio
async def test_create_event():
    from app.api.v1.calendar import create_event, CalendarEventCreate

    row = {
        "id": "e1",
        "user_id": "user-1",
        "provider": "local",
        "calendar_id": None,
        "external_id": None,
        "title": "Study",
        "description": None,
        "start_time": None,
        "end_time": None,
        "metadata": None,
    }

    with patch('app.api.v1.calendar.fetchrow', AsyncMock(return_value=row)):
        result = await create_event(
            CalendarEventCreate(
                user_id="user-1",
                title="Study",
                start_time="2026-01-01T10:00:00Z",
                end_time="2026-01-01T10:30:00Z",
            )
        )

    assert result["id"] == "e1"
