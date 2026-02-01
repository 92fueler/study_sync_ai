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


@pytest.mark.asyncio
async def test_get_note():
    from app.api.v1.notes import get_note

    row = {
        "id": "n5",
        "user_id": "user-1",
        "note_type": "text",
        "title": "Single Note",
        "description": "Details",
        "tags": [{"type": "topic", "label": "AI"}],
        "author": "AI",
        "topic": None,
        "thumbnail_url": None,
        "source_id": None,
        "created_at": None,
    }

    with patch('app.api.v1.notes.fetchrow', AsyncMock(return_value=row)):
        result = await get_note(note_id="n5", user_id="user-1")

    assert result["id"] == "n5"


@pytest.mark.asyncio
async def test_create_note_with_tag_objects():
    from app.api.v1.notes import create_note, NoteCreate

    payload = NoteCreate(
        user_id="user-1",
        note_type="text",
        title="Dashboard note",
        description="Example",
        tags=[{"type": "format", "label": "Notes"}],
        author="AI",
    )

    row = {
        "id": "n3",
        "user_id": "user-1",
        "note_type": "text",
        "title": "Dashboard note",
        "description": "Example",
        "tags": [{"type": "format", "label": "Notes"}],
        "author": "AI",
        "topic": None,
        "thumbnail_url": None,
        "source_id": None,
        "created_at": None,
    }

    with patch('app.api.v1.notes.fetchrow', AsyncMock(return_value=row)):
        result = await create_note(payload)

    assert result["tags"][0]["label"] == "Notes"


@pytest.mark.asyncio
async def test_create_note_with_string_tags():
    from app.api.v1.notes import create_note, NoteCreate

    payload = NoteCreate(
        user_id="user-1",
        note_type="text",
        title="Tag note",
        tags=["history", "biology"],
    )

    row = {
        "id": "n4",
        "user_id": "user-1",
        "note_type": "text",
        "title": "Tag note",
        "description": None,
        "tags": [{"type": "topic", "label": "history"}, {"type": "topic", "label": "biology"}],
        "author": None,
        "topic": None,
        "thumbnail_url": None,
        "source_id": None,
        "created_at": None,
    }

    with patch('app.api.v1.notes.fetchrow', AsyncMock(return_value=row)):
        result = await create_note(payload)

    assert result["tags"][0]["type"] == "topic"


@pytest.mark.asyncio
async def test_list_recent_notes():
    from app.api.v1.notes import list_recent_notes

    rows = [
        {"id": "n1", "user_id": "user-1", "note_type": "text", "title": "Recent", "created_at": None},
    ]

    with patch('app.api.v1.notes.fetch', AsyncMock(return_value=rows)):
        result = await list_recent_notes(user_id="user-1", limit=1)

    assert result["count"] == 1
