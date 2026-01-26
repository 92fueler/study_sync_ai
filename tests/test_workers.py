"""
Unit tests for RQ worker queue functionality.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestQueueHelpers:
    """Test queue helper functions."""
    
    @patch('workers.queue.Redis')
    def test_get_redis_connection(self, mock_redis):
        """Test Redis connection creation."""
        from workers.queue import get_redis_connection
        
        mock_redis.from_url.return_value = MagicMock()
        
        conn = get_redis_connection()
        
        mock_redis.from_url.assert_called_once()
        assert conn is not None
    
    @patch('workers.queue.get_redis_connection')
    @patch('workers.queue.Queue')
    def test_get_queue(self, mock_queue_class, mock_conn):
        """Test queue creation."""
        from workers.queue import get_queue
        
        mock_conn.return_value = MagicMock()
        mock_queue_class.return_value = MagicMock()
        
        queue = get_queue("high")
        
        mock_queue_class.assert_called_once_with("high", connection=mock_conn.return_value)
    
    @patch('workers.queue.get_high_queue')
    @patch('workers.queue.get_default_queue')
    def test_enqueue_generation_default(self, mock_default, mock_high):
        """Test generation enqueue to default queue."""
        from workers.queue import enqueue_generation
        
        mock_queue = MagicMock()
        mock_default.return_value = mock_queue
        
        with patch('workers.jobs.generation.generate_artifact'):
            enqueue_generation("user-1", "content-1", "5min", high_priority=False)
        
        mock_default.assert_called_once()
        mock_queue.enqueue.assert_called_once()
    
    @patch('workers.queue.get_high_queue')
    @patch('workers.queue.get_default_queue')
    def test_enqueue_generation_high_priority(self, mock_default, mock_high):
        """Test generation enqueue to high priority queue."""
        from workers.queue import enqueue_generation
        
        mock_queue = MagicMock()
        mock_high.return_value = mock_queue
        
        with patch('workers.jobs.generation.generate_artifact'):
            enqueue_generation("user-1", "content-1", "5min", high_priority=True)
        
        mock_high.assert_called_once()
        mock_queue.enqueue.assert_called_once()


class TestGenerationJobs:
    """Test generation job functions."""
    
    @patch('workers.jobs.generation.httpx.Client')
    def test_get_user_profile_returns_defaults_on_error(self, mock_client):
        """Test profile fetch returns defaults on error."""
        from workers.jobs.generation import _get_user_profile
        
        mock_client.return_value.__enter__.return_value.post.side_effect = Exception("Network error")
        
        profile = _get_user_profile("user-1")
        
        assert "style_dna" in profile
        assert profile["style_dna"]["tone"] == "eli5"
    
    @patch('workers.jobs.generation._get_user_profile')
    @patch('workers.jobs.generation.httpx.Client')
    def test_generate_artifact_success(self, mock_client, mock_profile):
        """Test successful artifact generation."""
        from workers.jobs.generation import generate_artifact
        
        mock_profile.return_value = {
            "style_dna": {"tone": "eli5"},
            "profile_version": 1
        }
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {"artifact_id": "art-123", "content": "Generated content"}
        }
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        
        with patch('workers.queue.enqueue_notification'):
            result = generate_artifact("user-1", "content-1", "5min")
        
        assert result["status"] == "success"
        assert "result" in result


class TestNotificationJobs:
    """Test notification job functions."""
    
    @patch('workers.jobs.notification.httpx.Client')
    def test_send_notification_success(self, mock_client):
        """Test successful notification send."""
        from workers.jobs.notification import send_notification
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {"notification_id": "notif-123"}
        }
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        
        result = send_notification("user-1", "Test Title", "Test Body")
        
        assert result["status"] == "success"
        assert result["notification_id"] == "notif-123"


class TestPriorityJobs:
    """Test priority job functions."""
    
    @patch('workers.jobs.priority.httpx.Client')
    def test_recalculate_priority_success(self, mock_client):
        """Test successful priority recalculation."""
        from workers.jobs.priority import recalculate_priority
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {"queue": [{"id": "1"}, {"id": "2"}]}
        }
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        
        result = recalculate_priority("user-1")
        
        assert result["status"] == "success"
        assert result["queue_length"] == 2
    
    @patch('workers.jobs.priority.httpx.Client')
    def test_cluster_topics_success(self, mock_client):
        """Test successful topic clustering."""
        from workers.jobs.priority import cluster_topics
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {"clusters": [{"topic": "ML"}, {"topic": "Python"}]}
        }
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        
        result = cluster_topics("user-1")
        
        assert result["status"] == "success"
        assert result["cluster_count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
