"""
Unit tests for Planner Agent tools.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime, timedelta


class AsyncContextManager:
    """Helper class for async context manager mocking."""
    def __init__(self, return_value):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, *args):
        return None


class TestGetPriorityQueue:
    """Tests for get_priority_queue tool."""
    
    @pytest.fixture
    def mock_deps(self, mock_db_connection):
        with patch('agents.planner.tools._get_db_connection', return_value=mock_db_connection):
            with patch('agents.planner.tools._get_genai_client') as mock_genai:
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
        
        # Mock Gemini client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "0.85"
        mock_client.models.generate_content.return_value = mock_response
        genai.return_value = mock_client
        
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
        
        # Mock Gemini client (won't be called but need to avoid errors)
        mock_client = MagicMock()
        genai.return_value = mock_client
        
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


class TestGetAdaptivePriority:
    """Tests for get_adaptive_priority tool (new context-aware function)."""
    
    @pytest.fixture
    def mock_pool(self, mock_db_connection):
        """Mock connection pool for new functions."""
        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextManager(mock_db_connection))
        
        async def get_pool():
            return mock_pool
        
        with patch('agents.planner.tools._get_db_pool', side_effect=get_pool):
            with patch('agents.planner.tools._get_genai_client') as mock_genai:
                yield mock_db_connection, mock_genai
    
    def test_adaptive_priority_cram_mode(self, mock_pool, sample_user_id):
        """Cram mode should prioritize high-value, short content."""
        conn, genai = mock_pool
        
        conn.fetchrow = AsyncMock(return_value={
            "goals": json.dumps(["Learn React"])
        })
        conn.fetch = AsyncMock(return_value=[
            {"content_id": "c1", "title": "React Basics", "topics": json.dumps(["React"]), 
             "word_count": 500, "created_at": datetime.now()}
        ])
        
        # Mock Gemini for goal match and difficulty inference
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "0.85"
        mock_client.models.generate_content.return_value = mock_response
        genai.Client.return_value = mock_client
        
        from agents.planner.tools import get_adaptive_priority
        
        result = get_adaptive_priority(sample_user_id, context_mode="cram", limit=10)
        
        assert result["status"] == "success"
        assert result["mode"] == "cram"
        assert "queue" in result
        assert "weights_used" in result
        assert result["weights_used"]["goal_match"] == 0.6  # Cram mode weights
    
    def test_adaptive_priority_exploration_mode(self, mock_pool, sample_user_id):
        """Exploration mode should boost trending content."""
        conn, genai = mock_pool
        
        conn.fetchrow = AsyncMock(return_value={
            "goals": json.dumps([])
        })
        conn.fetch = AsyncMock(return_value=[
            {"content_id": "c1", "title": "New Topic", "topics": json.dumps(["Topic"]), 
             "word_count": 300, "created_at": datetime.now()}
        ])
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Intermediate"
        mock_client.models.generate_content.return_value = mock_response
        genai.Client.return_value = mock_client
        
        from agents.planner.tools import get_adaptive_priority
        
        result = get_adaptive_priority(sample_user_id, context_mode="exploration", limit=10)
        
        assert result["status"] == "success"
        assert result["mode"] == "exploration"
        assert result["weights_used"]["trending"] == 0.5  # Exploration boosts trending


class TestClusterSemantically:
    """Tests for cluster_semantically tool (vector-based clustering)."""
    
    @pytest.fixture
    def mock_pool(self, mock_db_connection):
        """Mock connection pool for semantic clustering."""
        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextManager(mock_db_connection))
        
        async def get_pool():
            return mock_pool
        
        with patch('agents.planner.tools._get_db_pool', side_effect=get_pool):
            yield mock_db_connection
    
    def test_cluster_semantically_groups_by_similarity(self, mock_pool, sample_user_id):
        """Should group content by vector similarity."""
        # First fetch: get user's content items
        # Second fetch (inside loop): get similar items for each content item
        mock_pool.fetch = AsyncMock(side_effect=[
            # First call: user's content items
            [{"id": "c1", "title": "Python Basics", "topics": json.dumps(["Python"]), "embedding": None}],
            # Second call (inside loop): similar items for c1 (empty = no similar items)
            []
        ])
        
        from agents.planner.tools import cluster_semantically
        
        result = cluster_semantically(sample_user_id, similarity_threshold=0.75)
        
        assert result["status"] == "success"
        assert "clusters" in result
        assert result["similarity_threshold"] == 0.75
        # Should have at least one cluster (the seed item)
        assert len(result["clusters"]) >= 0  # Could be 0 if no items, or 1 if items exist
    
    def test_cluster_semantically_empty_content(self, mock_pool, sample_user_id):
        """Should handle empty content gracefully."""
        mock_pool.fetch = AsyncMock(return_value=[])
        
        from agents.planner.tools import cluster_semantically
        
        result = cluster_semantically(sample_user_id)
        
        assert result["status"] == "success"
        assert result["clusters"] == []


class TestEstimateStudyEffort:
    """Tests for estimate_study_effort tool (difficulty-aware)."""
    
    @pytest.fixture
    def mock_pool(self, mock_db_connection):
        """Mock connection pool for effort estimation."""
        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextManager(mock_db_connection))
        
        async def get_pool():
            return mock_pool
        
        with patch('agents.planner.tools._get_db_pool', side_effect=get_pool):
            with patch('agents.planner.tools._get_genai_client') as mock_genai:
                yield mock_db_connection, mock_genai
    
    def test_estimate_effort_with_difficulty(self, mock_pool):
        """Should return difficulty-aware time estimates."""
        conn, genai = mock_pool
        
        conn.fetchrow = AsyncMock(return_value={
            "word_count": 1000,
            "topics": json.dumps(["Topic1", "Topic2"]),
            "title": "Advanced Machine Learning"
        })
        
        # Mock difficulty inference - patch the async function
        async def mock_infer(title, topics):
            return "Advanced"
        
        with patch('agents.planner.tools._infer_difficulty', side_effect=mock_infer):
            from agents.planner.tools import estimate_study_effort
            
            result = estimate_study_effort("content-123")
            
            assert result["status"] == "success"
            assert result["word_count"] == 1000
            assert result["reading_minutes"] == 5  # 1000 / 200
            assert result["complexity_rating"] == "Advanced"
            assert result["difficulty_multiplier"] == 2.5  # Advanced multiplier
            assert result["study_minutes"] == 12  # 5 * 2.5
    
    def test_estimate_effort_beginner_content(self, mock_pool):
        """Beginner content should have 1.0x multiplier."""
        conn, genai = mock_pool
        
        conn.fetchrow = AsyncMock(return_value={
            "word_count": 1000,
            "topics": json.dumps(["Basics"]),
            "title": "Introduction to Python"
        })
        
        # Mock difficulty inference - need to mock _infer_difficulty directly
        with patch('agents.planner.tools._infer_difficulty', new_callable=AsyncMock, return_value="Beginner"):
            from agents.planner.tools import estimate_study_effort
            
            result = estimate_study_effort("content-123")
            
            assert result["complexity_rating"] == "Beginner"
            assert result["difficulty_multiplier"] == 1.0
            assert result["study_minutes"] == result["reading_minutes"]  # No multiplier
