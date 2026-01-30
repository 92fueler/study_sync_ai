"""
Tests for settings API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_get_settings_defaults():
    from app.api.v1.settings import get_settings

    with patch('app.api.v1.settings.fetchrow', AsyncMock(return_value=None)):
        result = await get_settings("user-1")

    assert result["user_id"] == "user-1"
    assert result["theme"] == "light"


@pytest.mark.asyncio
async def test_update_settings_insert():
    from app.api.v1.settings import update_settings, SettingsUpdate

    row = {
        "user_id": "user-1",
        "theme": "dark",
        "notifications": {"in_app": True},
        "timezone": "UTC",
        "study_preferences": None,
        "created_at": None,
        "updated_at": None,
    }

    with patch('app.api.v1.settings.fetchrow', AsyncMock(side_effect=[None, row])):
        result = await update_settings("user-1", SettingsUpdate(theme="dark", timezone="UTC"))

    assert result["theme"] == "dark"
