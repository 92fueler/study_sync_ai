"""
Unit tests for Planner Agent tools.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime, timedelta


class TestGetPriorityQueue:
    """Tests for get_priority_queue tool."""
    
    @pytest.fixture
    def mock_deps(self, mock_db_connection):
        with patch('agents.planner.tools._get_db_connection', return_value=mock_db_connection):
            with patch('agents.planner.tools.genai') as mock_genai:
                yield mock_db_connection, mock_genai
    
    def test_priority_queue_returns_ranked_items(self, mock_deps, sample_user_id):
        """Should return ranked content queue."""
        conn, genai = mock_deps
        
        conn.fetchrow = AsyncMock(return_value={
            "goals": json.dumps(["Learn React", "Master JavaScript"])
        })
        conn.fetch = AsyncMock(return_value=[
            {"content_id": "c1", "title": "React Basics", "topics": json.dumps(["React", "Components"]), "word_count": 500, "created_at": datetime.now()},
            {"content_id": "c2", "title": "Advanced Python", "topics": json.dumps(["Python", "OOP"]), "word_count": 800, "created_at": datetime.now() - timedelta(days=30)}
        ])
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = MagicMock(text="0.85")
        genai.GenerativeModel.return_value = mock_model
        
        from agents.planner.tools import get_priority_queue
        
        result = get_priority_queue(sample_user_id, limit=10)
        
        assert result["status"] == "success"
        assert "queue" in result
        assert len(result["queue"]) == 2
        # React should rank higher due to goal match
        assert all("priority_score" in item for item in result["queue"])
        assert all("priority_reasoning" in item for item in result["queue"])
    
    def test_empty_materials_returns_empty_queue(self, mock_deps, sample_user_id):
        """Should handle empty materials."""
        conn, genai = mock_deps
        
        conn.fetchrow = AsyncMock(return_value={"goals": json.dumps([])})
        conn.fetch = AsyncMock(return_value=[])
        
        from agents.planner.tools import get_priority_queue
        
        result = get_priority_queue(sample_user_id)
        
        assert result["status"] == "success"
        assert result["queue"] == []
        assert "No content" in result.get("message", "")


class TestCalcTrending:
    """Tests for _calc_trending helper."""
    
    def test_recent_content_scores_high(self):
        """Content from today should score 1.0."""
        from agents.planner.tools import _calc_trending
        
        score = _calc_trending(datetime.now())
        
        assert score >= 0.8
    
    def test_old_content_scores_low(self):
        """Content from 6 months ago should score low."""
        from agents.planner.tools import _calc_trending
        
        score = _calc_trending(datetime.now() - timedelta(days=180))
        
        assert score <= 0.3
    
    def test_none_returns_default(self):
        """None date should return 0.5."""
        from agents.planner.tools import _calc_trending
        
        score = _calc_trending(None)
        
        assert score == 0.5


class TestCalcPrerequisite:
    """Tests for _calc_prerequisite helper."""
    
    def test_foundational_content_scores_high(self):
        """Introductory content should score high."""
        from agents.planner.tools import _calc_prerequisite
        
        score = _calc_prerequisite(["JavaScript", "Basics"], "Introduction to JavaScript")
        
        assert score >= 0.7
    
    def test_advanced_content_scores_lower(self):
        """Advanced content should score lower."""
        from agents.planner.tools import _calc_prerequisite
        
        score = _calc_prerequisite(["Advanced Patterns", "Design"], "Expert Design Patterns")
        
        assert score < 0.7


class TestGenerateReasoning:
    """Tests for _generate_reasoning helper."""
    
    def test_high_goal_match_mentioned(self):
        """High goal match should be in reasoning."""
        from agents.planner.tools import _generate_reasoning
        
        result = _generate_reasoning(
            goal_score=0.9,
            trending_score=0.5,
            prereq_score=0.5,
            goals=["Learn React"],
            title="React Tutorial"
        )
        
        assert "goal" in result.lower()
        assert "React Tutorial" in result
    
    def test_foundational_mentioned(self):
        """Foundational content should be mentioned."""
        from agents.planner.tools import _generate_reasoning
        
        result = _generate_reasoning(
            goal_score=0.5,
            trending_score=0.5,
            prereq_score=0.9,
            goals=[],
            title="Getting Started"
        )
        
        assert "foundational" in result.lower()


class TestClusterTopics:
    """Tests for cluster_topics tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.planner.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_cluster_topics_groups_content(self, mock_db, sample_user_id):
        """Should group content by topic."""
        mock_db.fetch = AsyncMock(return_value=[
            {"content_id": "c1", "title": "React Hooks", "topics": json.dumps(["React", "Hooks"])},
            {"content_id": "c2", "title": "React Components", "topics": json.dumps(["React", "Components"])},
            {"content_id": "c3", "title": "Python Basics", "topics": json.dumps(["Python"])}
        ])
        
        from agents.planner.tools import cluster_topics
        
        result = cluster_topics(sample_user_id)
        
        assert result["status"] == "success"
        assert "clusters" in result
        # React should have 2 items
        react_cluster = next((c for c in result["clusters"] if c["topic"] == "React"), None)
        assert react_cluster is not None
        assert react_cluster["content_count"] == 2


class TestCalculateEffort:
    """Tests for calculate_effort tool."""
    
    @pytest.fixture
    def mock_db(self, mock_db_connection):
        with patch('agents.planner.tools._get_db_connection', return_value=mock_db_connection):
            yield mock_db_connection
    
    def test_calculate_effort_returns_estimates(self, mock_db):
        """Should return effort estimates."""
        mock_db.fetchrow = AsyncMock(return_value={
            "word_count": 1000,
            "topics": json.dumps(["Topic1", "Topic2", "Topic3"])
        })
        
        from agents.planner.tools import calculate_effort
        
        result = calculate_effort("content-123")
        
        assert result["status"] == "success"
        assert result["word_count"] == 1000
        assert result["reading_minutes"] == 5  # 1000 / 200
        assert result["complexity"] == "medium"  # 3 topics
    
    def test_high_complexity_content(self, mock_db):
        """Content with many topics should be high complexity."""
        mock_db.fetchrow = AsyncMock(return_value={
            "word_count": 2000,
            "topics": json.dumps(["T1", "T2", "T3", "T4", "T5", "T6"])
        })
        
        from agents.planner.tools import calculate_effort
        
        result = calculate_effort("content-123")
        
        assert result["complexity"] == "high"
    
    def test_nonexistent_content_returns_error(self, mock_db):
        """Non-existent content should return error."""
        mock_db.fetchrow = AsyncMock(return_value=None)
        
        from agents.planner.tools import calculate_effort
        
        result = calculate_effort("nonexistent-id")
        
        assert result["status"] == "error"
        assert "not found" in result["error"]
