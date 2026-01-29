"""
Tests for Notifications API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_get_notifications_parses_structured_text():
    """Should surface notifications from structured agent text."""
    from app.api.v1.notifications import get_notifications

    mock_a2a = AsyncMock()
    mock_response = MagicMock()
    mock_response.error = None
    mock_response.result = {"text": "{'notifications': [{'id': 'n1'}]}"}
    mock_a2a.run_agent = AsyncMock(return_value=mock_response)

    with patch('app.api.v1.notifications.get_a2a_client', return_value=mock_a2a):
        result = await get_notifications(user_id="user-1", unread_only=False)

    assert result["notifications"] == [{"id": "n1"}]


@pytest.mark.asyncio
async def test_get_badge_count_parses_structured_text():
    """Should surface unread_count from structured agent text."""
    from app.api.v1.notifications import get_badge_count

    mock_a2a = AsyncMock()
    mock_response = MagicMock()
    mock_response.error = None
    mock_response.result = {"text": "{'unread_count': 3}"}
    mock_a2a.run_agent = AsyncMock(return_value=mock_response)

    with patch('app.api.v1.notifications.get_a2a_client', return_value=mock_a2a):
        result = await get_badge_count(user_id="user-1")

    assert result["unread_count"] == 3


@pytest.mark.asyncio
async def test_mark_as_read_uses_user_id():
    """Should pass user_id through to the agent call."""
    from app.api.v1.notifications import mark_as_read

    mock_a2a = AsyncMock()
    mock_response = MagicMock()
    mock_response.error = None
    mock_response.result = {"status": "success"}
    mock_a2a.run_agent = AsyncMock(return_value=mock_response)

    with patch('app.api.v1.notifications.get_a2a_client', return_value=mock_a2a):
        await mark_as_read(notification_id="notif-1", user_id="user-1")

    kwargs = mock_a2a.run_agent.call_args.kwargs
    assert kwargs["user_id"] == "user-1"
