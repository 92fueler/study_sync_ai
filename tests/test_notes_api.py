"""
Tests for learning notes API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_list_notes():
    from app.api.v1.notes import list_notes

    rows = [
        {"id": "n1", "user_id": "user-1", "note_type": "pdf", "title": "A", "created_at": None},
        {"id": "n2", "user_id": "user-1", "note_type": "video", "title": "B", "created_at": None},
    ]

    with patch('app.api.v1.notes.fetch', AsyncMock(return_value=rows)):
        result = await list_notes(user_id="user-1")

    assert result["count"] == 2


@pytest.mark.asyncio
async def test_topics():
    from app.api.v1.notes import list_note_topics

    rows = [
        {"topic": "AI", "count": 3},
        {"topic": "History", "count": 2},
    ]

    with patch('app.api.v1.notes.fetch', AsyncMock(return_value=rows)):
        result = await list_note_topics(user_id="user-1")

    assert result["items"][0]["topic"] == "AI"
