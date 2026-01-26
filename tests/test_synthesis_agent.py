"""
Unit tests for Synthesis Agent tools.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json


class TestGenerateArtifact:
    """Tests for generate_artifact tool."""
    
    @pytest.fixture
    def mock_deps(self, mock_db_connection):
        with patch('agents.synthesis.tools._get_db_connection', return_value=mock_db_connection):
            mock_client = MagicMock()
            with patch('agents.synthesis.tools._get_genai_client', return_value=mock_client):
                yield mock_db_connection, mock_client
    
    def test_generate_artifact_returns_content(self, mock_deps, sample_user_id, sample_style_dna):
        """Should generate and return artifact content."""
        conn, mock_client = mock_deps
        
        # No cache, get source content, insert artifacts
        conn.fetchrow = AsyncMock(side_effect=[
            None,  # No cached artifact
            {"raw_text": "React is a JavaScript library...", "title": "React Intro"},  # Source content
            {"id": "new-artifact-id"}  # INSERT artifact
        ])
        conn.execute = AsyncMock()
        
        mock_client.models.generate_content.return_value = MagicMock(text="# React Study Notes\n\nReact is powerful...")
        
        from agents.synthesis.tools import generate_artifact
        
        result = generate_artifact(
            user_id=sample_user_id,
            content_ids=["content-123"],
            profile_version=1,
            style_dna=sample_style_dna,
            time_available_minutes=20
        )
        
        assert result["status"] == "success"
        assert result["artifact_id"] == "new-artifact-id"
        assert result["cached"] is False
        assert "content" in result
    
    def test_generate_artifact_returns_cached(self, mock_deps, sample_user_id, sample_style_dna):
        """Should return cached artifact if available."""
        conn, mock_client = mock_deps
        
        conn.fetchrow = AsyncMock(return_value={
            "id": "cached-artifact-id",
            "content": "Cached content",
            "estimated_minutes": 10
        })
        
        from agents.synthesis.tools import generate_artifact
        
        result = generate_artifact(
            user_id=sample_user_id,
            content_ids=["content-123"],
            profile_version=1,
            style_dna=sample_style_dna
        )
        
        assert result["status"] == "success"
        assert result["cached"] is True
        assert result["artifact_id"] == "cached-artifact-id"
    
    def test_generate_artifact_no_source_returns_error(self, mock_deps, sample_user_id, sample_style_dna):
        """Should return error if no source content."""
        conn, mock_client = mock_deps
        
        conn.fetchrow = AsyncMock(side_effect=[
            None,  # No cache
            None   # No source content
        ])
        
        from agents.synthesis.tools import generate_artifact
        
        result = generate_artifact(
            user_id=sample_user_id,
            content_ids=["nonexistent-id"],
            profile_version=1,
            style_dna=sample_style_dna
        )
        
        assert result["status"] == "error"
        assert "No source content" in result["error"]


class TestGenerate5minSummary:
    """Tests for generate_5min_summary tool."""
    
    @pytest.fixture
    def mock_deps(self, mock_db_connection):
        with patch('agents.synthesis.tools._get_db_connection', return_value=mock_db_connection):
            mock_client = MagicMock()
            with patch('agents.synthesis.tools._get_genai_client', return_value=mock_client):
                yield mock_db_connection, mock_client
    
    def test_generate_5min_summary_success(self, mock_deps, sample_user_id, sample_style_dna):
        """Should generate 5-minute summary."""
        conn, mock_client = mock_deps
        
        conn.fetchrow = AsyncMock(side_effect=[
            {"raw_text": "Long content about React..."},  # Source
            {"id": "summary-artifact-id"}  # INSERT
        ])
        
        mock_client.models.generate_content.return_value = MagicMock(text="Quick summary of React...")
        
        from agents.synthesis.tools import generate_5min_summary
        
        result = generate_5min_summary(
            user_id=sample_user_id,
            content_id="content-123",
            profile_version=1,
            style_dna=sample_style_dna
        )
        
        assert result["status"] == "success"
        assert result["estimated_minutes"] == 5
        assert "content" in result


class TestGetArtifact:
    """Tests for get_artifact tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.synthesis.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_get_existing_artifact(self, mock_db, sample_artifact):
        """Should return artifact details."""
        mock_db.fetchrow = AsyncMock(return_value=sample_artifact)
        
        from agents.synthesis.tools import get_artifact
        
        result = get_artifact("artifact-789-ghi")
        
        assert result["status"] == "success"
        assert result["id"] == "artifact-789-ghi"
        assert "content" in result
    
    def test_get_nonexistent_artifact_returns_error(self, mock_db):
        """Should return error for non-existent artifact."""
        mock_db.fetchrow = AsyncMock(return_value=None)
        
        from agents.synthesis.tools import get_artifact
        
        result = get_artifact("nonexistent-id")
        
        assert result["status"] == "error"
        assert "not found" in result["error"]


class TestListArtifacts:
    """Tests for list_artifacts tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.synthesis.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_list_artifacts_returns_list(self, mock_db, sample_user_id):
        """Should return list of artifacts."""
        mock_db.fetch = AsyncMock(return_value=[
            {"id": "art-1", "artifact_type": "full", "estimated_minutes": 10, "created_at": "2026-01-25"},
            {"id": "art-2", "artifact_type": "5min", "estimated_minutes": 5, "created_at": "2026-01-24"}
        ])
        
        from agents.synthesis.tools import list_artifacts
        
        result = list_artifacts(sample_user_id)
        
        assert result["status"] == "success"
        assert len(result["artifacts"]) == 2
    
    def test_list_artifacts_with_filter(self, mock_db, sample_user_id):
        """Should filter by artifact type."""
        mock_db.fetch = AsyncMock(return_value=[
            {"id": "art-2", "artifact_type": "5min", "estimated_minutes": 5, "created_at": "2026-01-24"}
        ])
        
        from agents.synthesis.tools import list_artifacts
        
        result = list_artifacts(sample_user_id, artifact_type="5min")
        
        assert result["status"] == "success"
        assert all(a["artifact_type"] == "5min" for a in result["artifacts"])


class TestBuildSystemInstruction:
    """Tests for _build_system_instruction helper."""
    
    def test_eli5_tone(self):
        """ELI5 tone should include simple explanations."""
        from agents.synthesis.tools import _build_system_instruction
        
        result = _build_system_instruction({"tone": "eli5"})
        
        assert "simply" in result.lower() or "beginner" in result.lower()
    
    def test_academic_tone(self):
        """Academic tone should include formal language."""
        from agents.synthesis.tools import _build_system_instruction
        
        result = _build_system_instruction({"tone": "academic"})
        
        assert "formal" in result.lower() or "precise" in result.lower()
    
    def test_cornell_format(self):
        """Cornell format should be included."""
        from agents.synthesis.tools import _build_system_instruction
        
        result = _build_system_instruction({"format_pref": "cornell"})
        
        assert "cornell" in result.lower()
    
    def test_emoji_preference(self):
        """Emoji preference should be respected."""
        from agents.synthesis.tools import _build_system_instruction
        
        with_emoji = _build_system_instruction({"uses_emoji": True})
        without_emoji = _build_system_instruction({"uses_emoji": False})
        
        assert "use emojis" in with_emoji.lower()
        assert "do not use emojis" in without_emoji.lower()
