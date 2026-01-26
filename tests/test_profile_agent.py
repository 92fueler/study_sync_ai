"""
Unit tests for Profile Agent tools.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json


class TestCreateProfile:
    """Tests for create_profile tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.profile.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_create_new_profile_returns_success(self, mock_db, sample_user_id, sample_style_dna, sample_goals):
        """Creating a new profile should succeed."""
        mock_db.fetchrow = AsyncMock(side_effect=[
            None,  # No existing profile
            {"id": "new-profile-id"}  # INSERT returns id
        ])
        
        from agents.profile.tools import create_profile
        
        result = create_profile(
            user_id=sample_user_id,
            display_name="Test User",
            goals=sample_goals,
            style_dna=sample_style_dna
        )
        
        assert result["status"] == "success"
        assert result["profile_id"] == "new-profile-id"
        assert result["user_id"] == sample_user_id
    
    def test_create_duplicate_profile_returns_error(self, mock_db, sample_user_id):
        """Creating duplicate profile should return error."""
        mock_db.fetchrow = AsyncMock(return_value={"id": "existing-id"})
        
        from agents.profile.tools import create_profile
        
        result = create_profile(user_id=sample_user_id)
        
        assert result["status"] == "error"
        assert "already exists" in result["error"]


class TestGetProfile:
    """Tests for get_profile tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.profile.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_get_existing_profile(self, mock_db, sample_user_id, sample_style_dna):
        """Should return existing profile data."""
        mock_db.fetchrow = AsyncMock(return_value={
            "user_id": sample_user_id,
            "display_name": "Test User",
            "style_dna": json.dumps(sample_style_dna),
            "goals": json.dumps(["Learn React"]),
            "calendar_context": None,
            "profile_version": 2
        })
        
        from agents.profile.tools import get_profile
        
        result = get_profile(sample_user_id)
        
        assert result["status"] == "success"
        assert result["user_id"] == sample_user_id
        assert result["profile_version"] == 2
        assert result["style_dna"]["tone"] == "eli5"
    
    def test_get_nonexistent_profile_returns_defaults(self, mock_db, sample_user_id):
        """Non-existent profile should return defaults."""
        mock_db.fetchrow = AsyncMock(return_value=None)
        
        from agents.profile.tools import get_profile
        
        result = get_profile(sample_user_id)
        
        assert result["status"] == "success"
        assert result["is_default"] is True
        assert result["style_dna"]["tone"] == "eli5"
        assert result["profile_version"] == 1


class TestUpdateProfile:
    """Tests for update_profile tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.profile.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_update_profile_returns_new_version(self, mock_db, sample_user_id, sample_style_dna):
        """Updating profile should return new version."""
        mock_db.fetchrow = AsyncMock(return_value={"profile_version": 3})
        
        from agents.profile.tools import update_profile
        
        result = update_profile(
            user_id=sample_user_id,
            style_dna=sample_style_dna
        )
        
        assert result["status"] == "success"
        assert result["profile_version"] == 3
    
    def test_update_with_no_fields_returns_error(self, mock_db, sample_user_id):
        """Updating with no fields should return error."""
        from agents.profile.tools import update_profile
        
        result = update_profile(user_id=sample_user_id)
        
        assert result["status"] == "error"
        assert "No fields" in result["error"]


class TestGetCalendarContext:
    """Tests for get_calendar_context tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.profile.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_no_calendar_returns_default(self, mock_db, sample_user_id):
        """No calendar should return default context."""
        mock_db.fetchrow = AsyncMock(return_value=None)
        
        from agents.profile.tools import get_calendar_context
        
        result = get_calendar_context(sample_user_id)
        
        assert result["status"] == "success"
        assert result["has_calendar"] is False
        assert result["context"] == "default"
    
    def test_with_calendar_returns_context(self, mock_db, sample_user_id):
        """With calendar should return time-aware context."""
        mock_db.fetchrow = AsyncMock(return_value={
            "calendar_context": json.dumps({
                "work_hours": "09:00-17:00",
                "timezone": "UTC"
            })
        })
        
        from agents.profile.tools import get_calendar_context
        
        result = get_calendar_context(sample_user_id)
        
        assert result["status"] == "success"
        assert result["has_calendar"] is True


class TestRecordFeedback:
    """Tests for record_feedback tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.profile.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_record_feedback_returns_id(self, mock_db, sample_user_id, sample_content_id):
        """Recording feedback should return feedback ID."""
        mock_db.fetchrow = AsyncMock(return_value={"id": "feedback-123"})
        
        from agents.profile.tools import record_feedback
        
        result = record_feedback(
            user_id=sample_user_id,
            artifact_id=sample_content_id,
            explicit_rating=5,
            completed=True
        )
        
        assert result["status"] == "success"
        assert result["feedback_id"] == "feedback-123"
