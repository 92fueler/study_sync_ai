"""
Pytest fixtures and configuration for ADK agent tests.
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any


@pytest.fixture
def mock_db_connection():
    """Mock asyncpg database connection."""
    conn = AsyncMock()
    conn.fetchrow = AsyncMock()
    conn.fetch = AsyncMock()
    conn.execute = AsyncMock()
    conn.close = AsyncMock()
    return conn


@pytest.fixture
def mock_genai():
    """Mock Google Generative AI."""
    with patch('google.generativeai.GenerativeModel') as mock_model:
        instance = MagicMock()
        instance.generate_content = MagicMock()
        mock_model.return_value = instance
        yield mock_model, instance


@pytest.fixture
def sample_user_id():
    return "user-123-abc"


@pytest.fixture
def sample_content_id():
    return "content-456-def"


@pytest.fixture
def sample_style_dna():
    return {
        "tone": "eli5",
        "format_pref": "cornell",
        "uses_emoji": True,
        "prefers_diagrams": True
    }


@pytest.fixture
def sample_goals():
    return ["Learn React", "Master TypeScript", "Build full-stack apps"]


@pytest.fixture
def sample_profile(sample_user_id, sample_style_dna, sample_goals):
    return {
        "user_id": sample_user_id,
        "display_name": "Test User",
        "style_dna": sample_style_dna,
        "goals": sample_goals,
        "profile_version": 1
    }


@pytest.fixture
def sample_content():
    return {
        "id": "content-456-def",
        "content_hash": "abc123hash",
        "title": "Introduction to React",
        "raw_text": "React is a JavaScript library for building user interfaces...",
        "media_type": "TXT",
        "topics": ["React", "JavaScript", "UI"],
        "word_count": 500
    }


@pytest.fixture
def sample_artifact():
    return {
        "id": "artifact-789-ghi",
        "user_id": "user-123-abc",
        "content_ids": ["content-456-def"],
        "profile_version": 1,
        "artifact_type": "full",
        "content": "# React Study Notes\n\nReact is a powerful library...",
        "estimated_minutes": 5,
        "created_at": "2026-01-25T10:00:00Z"
    }


@pytest.fixture
def sample_job():
    return {
        "id": "job-101-xyz",
        "user_id": "user-123-abc",
        "job_type": "generate_5min_new",
        "status": "QUEUED",
        "priority": "NORMAL",
        "attempts": 0,
        "created_at": "2026-01-25T10:00:00Z"
    }


@pytest.fixture
def sample_notification():
    return {
        "id": "notif-202-abc",
        "user_id": "user-123-abc",
        "channel": "in_app",
        "title": "New summary ready",
        "body": "Your React notes are ready to review",
        "data": '{"artifact_id": "artifact-789-ghi"}',
        "read": False,
        "created_at": "2026-01-25T10:05:00Z"
    }
