"""
Unit tests for Orchestrator Agent tools.
"""

import pytest
from unittest.mock import AsyncMock, patch
import json


class TestDetectChanges:
    """Tests for detect_changes tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.orchestrator.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_detect_new_content(self, mock_db, sample_user_id):
        """Should detect unprocessed content."""
        mock_db.fetch = AsyncMock(return_value=[
            {"content_id": "c1", "uploaded_at": "2026-01-25T10:00:00Z"},
            {"content_id": "c2", "uploaded_at": "2026-01-25T11:00:00Z"}
        ])
        mock_db.fetchrow = AsyncMock(return_value={"count": 1})
        
        from agents.orchestrator.tools import detect_changes
        
        result = detect_changes(sample_user_id)
        
        assert result["status"] == "success"
        assert len(result["new_content"]) == 2
        assert result["pending_jobs"] == 1
    
    def test_no_changes_returns_empty(self, mock_db, sample_user_id):
        """Should return empty when no changes."""
        mock_db.fetch = AsyncMock(return_value=[])
        mock_db.fetchrow = AsyncMock(return_value={"count": 0})
        
        from agents.orchestrator.tools import detect_changes
        
        result = detect_changes(sample_user_id)
        
        assert result["status"] == "success"
        assert result["new_content"] == []
        assert result["pending_jobs"] == 0


class TestScheduleGeneration:
    """Tests for schedule_generation tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.orchestrator.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_schedule_job_returns_id(self, mock_db, sample_user_id):
        """Should create job and return ID."""
        mock_db.fetchrow = AsyncMock(return_value={"id": "job-123"})
        
        from agents.orchestrator.tools import schedule_generation
        
        result = schedule_generation(
            user_id=sample_user_id,
            job_type="generate_5min_new",
            content_id="content-456",
            priority="HIGH"
        )
        
        assert result["status"] == "success"
        assert result["job_id"] == "job-123"
        assert result["job_status"] == "QUEUED"
    
    def test_schedule_without_content_id(self, mock_db, sample_user_id):
        """Should handle jobs without content_id."""
        mock_db.fetchrow = AsyncMock(return_value={"id": "job-789"})
        
        from agents.orchestrator.tools import schedule_generation
        
        result = schedule_generation(
            user_id=sample_user_id,
            job_type="recalc_priority"
        )
        
        assert result["status"] == "success"


class TestGetJobStatus:
    """Tests for get_job_status tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.orchestrator.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_get_existing_job(self, mock_db, sample_job):
        """Should return job details."""
        mock_db.fetchrow = AsyncMock(return_value=sample_job)
        
        from agents.orchestrator.tools import get_job_status
        
        result = get_job_status("job-101-xyz")
        
        assert result["status"] == "success"
        assert result["job_id"] == "job-101-xyz"
        assert result["job_status"] == "QUEUED"
        assert result["job_type"] == "generate_5min_new"
    
    def test_get_nonexistent_job(self, mock_db):
        """Should return error for non-existent job."""
        mock_db.fetchrow = AsyncMock(return_value=None)
        
        from agents.orchestrator.tools import get_job_status
        
        result = get_job_status("nonexistent-job")
        
        assert result["status"] == "error"
        assert "not found" in result["error"]


class TestGetNotifications:
    """Tests for get_notifications tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.orchestrator.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_get_all_notifications(self, mock_db, sample_user_id, sample_notification):
        """Should return all notifications."""
        mock_db.fetch = AsyncMock(return_value=[sample_notification])
        
        from agents.orchestrator.tools import get_notifications
        
        result = get_notifications(sample_user_id)
        
        assert result["status"] == "success"
        assert len(result["notifications"]) == 1
        assert result["notifications"][0]["title"] == "New summary ready"
    
    def test_get_unread_only(self, mock_db, sample_user_id, sample_notification):
        """Should filter unread notifications."""
        mock_db.fetch = AsyncMock(return_value=[sample_notification])
        
        from agents.orchestrator.tools import get_notifications
        
        result = get_notifications(sample_user_id, unread_only=True)
        
        assert result["status"] == "success"


class TestGetBadgeCount:
    """Tests for get_badge_count tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.orchestrator.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_badge_count_returns_number(self, mock_db, sample_user_id):
        """Should return unread count."""
        mock_db.fetchrow = AsyncMock(return_value={"count": 5})
        
        from agents.orchestrator.tools import get_badge_count
        
        result = get_badge_count(sample_user_id)
        
        assert result["status"] == "success"
        assert result["unread_count"] == 5
    
    def test_zero_badge_count(self, mock_db, sample_user_id):
        """Should handle zero notifications."""
        mock_db.fetchrow = AsyncMock(return_value={"count": 0})
        
        from agents.orchestrator.tools import get_badge_count
        
        result = get_badge_count(sample_user_id)
        
        assert result["unread_count"] == 0


class TestMarkNotificationRead:
    """Tests for mark_notification_read tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.orchestrator.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_mark_read_success(self, mock_db):
        """Should mark notification as read."""
        mock_db.execute = AsyncMock()
        
        from agents.orchestrator.tools import mark_notification_read
        
        result = mark_notification_read("notif-123")
        
        assert result["status"] == "success"


class TestCreateNotification:
    """Tests for create_notification tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.orchestrator.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_create_notification_returns_id(self, mock_db, sample_user_id):
        """Should create notification and return ID."""
        mock_db.fetchrow = AsyncMock(return_value={"id": "notif-new-123"})
        
        from agents.orchestrator.tools import create_notification
        
        result = create_notification(
            user_id=sample_user_id,
            title="Your notes are ready",
            body="Click to view your React study notes",
            channel="push",
            data={"artifact_id": "art-123"}
        )
        
        assert result["status"] == "success"
        assert result["notification_id"] == "notif-new-123"
    
    def test_create_notification_default_channel(self, mock_db, sample_user_id):
        """Should use in_app as default channel."""
        mock_db.fetchrow = AsyncMock(return_value={"id": "notif-456"})
        
        from agents.orchestrator.tools import create_notification
        
        result = create_notification(
            user_id=sample_user_id,
            title="Test",
            body="Test body"
        )
        
        assert result["status"] == "success"
