"""
Tests for Gateway-Worker integration.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestUploadWorkerIntegration:
    """Test upload endpoint worker integration."""
    
    @patch('app.api.v1.upload._enqueue_proactive_generation')
    @patch('app.api.v1.upload.get_a2a_client')
    @pytest.mark.asyncio
    async def test_upload_enqueues_generation_on_success(self, mock_client, mock_enqueue):
        """Test that successful upload triggers proactive generation."""
        from app.api.v1.upload import upload_files
        from fastapi import UploadFile
        from io import BytesIO
        
        # Mock ADK runtime client
        mock_a2a = AsyncMock()
        mock_response = MagicMock()
        mock_response.error = None
        mock_response.result = {"content_id": "test-content-123", "status": "success"}
        mock_a2a.run_agent = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_a2a
        
        # Create mock file
        file_content = b"Test content for upload"
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.read = AsyncMock(return_value=file_content)
        
        # Execute
        result = await upload_files(user_id="user-1", files=[mock_file])
        
        # Verify proactive generation was enqueued
        mock_enqueue.assert_called_once_with("user-1", "test-content-123")
        assert result["results"][0]["content_id"] == "test-content-123"
    
    @patch('app.api.v1.upload._enqueue_proactive_generation')
    @patch('app.api.v1.upload.get_a2a_client')
    @pytest.mark.asyncio
    async def test_upload_no_enqueue_on_error(self, mock_client, mock_enqueue):
        """Test that failed upload does not trigger generation."""
        from app.api.v1.upload import upload_files
        from fastapi import UploadFile
        
        # Mock ADK runtime client with error
        mock_a2a = AsyncMock()
        mock_response = MagicMock()
        mock_response.error = {"message": "Ingestion failed"}
        mock_response.result = None
        mock_a2a.run_agent = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_a2a
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.read = AsyncMock(return_value=b"content")
        
        result = await upload_files(user_id="user-1", files=[mock_file])
        
        # Verify no generation enqueued
        mock_enqueue.assert_not_called()
        assert result["results"][0]["status"] == "error"


class TestGenerateWorkerIntegration:
    """Test generate endpoint worker integration."""
    
    @patch('app.api.v1.generate._enqueue_user_generation')
    @pytest.mark.asyncio
    async def test_async_generate_enqueues_high_priority(self, mock_enqueue):
        """Test async generation uses high priority queue."""
        from app.api.v1.generate import generate_artifact_async, AsyncGenerateRequest
        
        # Mock job return
        mock_job = MagicMock()
        mock_job.id = "job-123"
        mock_enqueue.return_value = mock_job
        
        request = AsyncGenerateRequest(
            user_id="user-1",
            content_id="content-1",
            artifact_type="full"
        )
        
        result = await generate_artifact_async(request)
        
        mock_enqueue.assert_called_once_with("user-1", "content-1", "full")
        assert result["job_id"] == "job-123"
        assert result["queue"] == "high"
    
    @patch('app.api.v1.generate._enqueue_user_generation')
    @pytest.mark.asyncio
    async def test_async_generate_returns_503_on_queue_failure(self, mock_enqueue):
        """Test returns 503 when queue unavailable."""
        from app.api.v1.generate import generate_artifact_async, AsyncGenerateRequest
        from fastapi import HTTPException
        
        mock_enqueue.return_value = None  # Queue failure
        
        request = AsyncGenerateRequest(
            user_id="user-1",
            content_id="content-1"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await generate_artifact_async(request)
        
        assert exc_info.value.status_code == 503


class TestEnqueueHelpers:
    """Test the enqueue helper functions."""
    
    def test_enqueue_proactive_generation_catches_errors(self):
        """Test that enqueue helper doesn't raise on queue errors."""
        from app.api.v1.upload import _enqueue_proactive_generation
        
        with patch('workers.queue.enqueue_generation', side_effect=Exception("Redis down")):
            # Should not raise
            _enqueue_proactive_generation("user-1", "content-1")
    
    def test_enqueue_user_generation_returns_none_on_error(self):
        """Test that enqueue helper returns None on errors."""
        from app.api.v1.generate import _enqueue_user_generation
        
        with patch('workers.queue.enqueue_generation', side_effect=Exception("Redis down")):
            result = _enqueue_user_generation("user-1", "content-1")
            assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
