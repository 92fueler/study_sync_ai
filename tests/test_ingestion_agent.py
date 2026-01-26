"""
Unit tests for Ingestion Agent tools.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json


class TestIngestContent:
    """Tests for ingest_content tool."""
    
    @pytest.fixture
    def mock_deps(self, mock_db_connection):
        """Setup mocked dependencies."""
        with patch('agents.ingestion.tools._get_db_connection', return_value=mock_db_connection):
            with patch('agents.ingestion.tools.genai') as mock_genai:
                yield mock_db_connection, mock_genai
    
    def test_ingest_new_content_returns_success(self, mock_deps, sample_user_id):
        """New content should be processed and return success status."""
        conn, genai = mock_deps
        
        # Setup: no existing content
        conn.fetchrow = AsyncMock(side_effect=[
            None,  # No existing content
            {"id": "new-content-id"},  # INSERT content_items
            {"id": "new-material-id"}  # INSERT user_materials
        ])
        
        # Mock topic extraction
        mock_model = MagicMock()
        mock_model.generate_content.return_value = MagicMock(text='["React", "JavaScript"]')
        genai.GenerativeModel.return_value = mock_model
        genai.embed_content.return_value = {"embedding": [0.1] * 768}
        
        from agents.ingestion.tools import ingest_content
        
        result = ingest_content(
            user_id=sample_user_id,
            content_hash="hash123",
            filename="test.txt",
            media_type="TXT",
            content_text="React is a JavaScript library for building UIs."
        )
        
        assert result["status"] == "success"
        assert "content_id" in result
        assert "material_id" in result
    
    def test_ingest_duplicate_content_deduplicates(self, mock_deps, sample_user_id):
        """Duplicate content should be deduplicated."""
        conn, genai = mock_deps
        
        # Setup: existing content found
        conn.fetchrow = AsyncMock(side_effect=[
            {"id": "existing-content-id"},  # Existing content
            {"id": "new-material-id"}  # New material link
        ])
        
        from agents.ingestion.tools import ingest_content
        
        result = ingest_content(
            user_id=sample_user_id,
            content_hash="existing-hash",
            filename="duplicate.txt",
            media_type="TXT",
            content_text="Some content"
        )
        
        assert result["status"] == "success"
        assert result["deduplicated"] is True
        assert result["content_id"] == "existing-content-id"


class TestExtractTopics:
    """Tests for extract_topics tool."""
    
    def test_extract_topics_returns_list(self):
        """Should return a list of topics."""
        with patch('agents.ingestion.tools.genai') as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = MagicMock(text='["Python", "Machine Learning", "AI"]')
            mock_genai.GenerativeModel.return_value = mock_model
            
            from agents.ingestion.tools import extract_topics
            
            result = extract_topics("Python is great for machine learning and AI applications.")
            
            assert result["status"] == "success"
            assert "topics" in result
            assert isinstance(result["topics"], list)
    
    def test_extract_topics_handles_short_text(self):
        """Short text should return empty topics."""
        from agents.ingestion.tools import extract_topics
        
        result = extract_topics("Hi")
        
        assert result["status"] == "success"
        assert result["topics"] == []


class TestGenerateEmbedding:
    """Tests for generate_embedding tool."""
    
    def test_generate_embedding_returns_vector(self):
        """Should return embedding vector with dimensions."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1] * 768
        mock_result.embeddings = [mock_embedding]
        mock_client.models.embed_content.return_value = mock_result
        
        with patch('agents.ingestion.tools._get_genai_client', return_value=mock_client):
            from agents.ingestion.tools import generate_embedding
            
            result = generate_embedding("Some text to embed")
            
            assert result["status"] == "success"
            assert "embedding" in result
            assert result["dimensions"] == 768
    
    def test_generate_embedding_handles_empty_text(self):
        """Empty text should return null embedding."""
        from agents.ingestion.tools import generate_embedding
        
        result = generate_embedding("")
        
        assert result["status"] == "success"
        assert result["embedding"] is None
        assert result["dimensions"] == 0
