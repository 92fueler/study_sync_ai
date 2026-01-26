"""
Integration tests for ADK agents with real Gemini API.

These tests require GEMINI_API_KEY to be set in the environment.
Run with: pytest tests/test_integration.py -v
"""

import os
import pytest

# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set"
)


class TestIngestionIntegration:
    """Integration tests for ingestion agent tools."""
    
    def test_extract_topics_real_api(self):
        """Test topic extraction with real Gemini API."""
        # Set API key from .env
        from dotenv import load_dotenv
        load_dotenv()
        
        from agents.ingestion.tools import extract_topics
        
        sample_text = """
        Machine learning is a subset of artificial intelligence that enables 
        systems to learn and improve from experience without being explicitly 
        programmed. Deep learning, a subset of machine learning, uses neural 
        networks with multiple layers to analyze various factors of data.
        Python is the most popular programming language for machine learning
        due to libraries like TensorFlow, PyTorch, and scikit-learn.
        """
        
        result = extract_topics(sample_text)
        
        assert result["status"] == "success"
        assert "topics" in result
        assert isinstance(result["topics"], list)
        assert len(result["topics"]) > 0
        print(f"Extracted topics: {result['topics']}")
    
    def test_generate_embedding_real_api(self):
        """Test embedding generation with real Gemini API."""
        from dotenv import load_dotenv
        load_dotenv()
        
        from agents.ingestion.tools import generate_embedding
        
        sample_text = "Machine learning is transforming how we build software."
        
        result = generate_embedding(sample_text)
        
        assert result["status"] == "success"
        assert "embedding" in result
        assert result["embedding"] is not None
        assert result["dimensions"] > 0
        print(f"Embedding dimensions: {result['dimensions']}")


class TestSynthesisIntegration:
    """Integration tests for synthesis agent tools."""
    
    def test_build_system_instruction(self):
        """Test system instruction building (no API call)."""
        from agents.synthesis.tools import _build_system_instruction
        
        style_dna = {
            "tone": "eli5",
            "format_pref": "cornell",
            "uses_emoji": True,
            "prefers_diagrams": True
        }
        
        instruction = _build_system_instruction(style_dna)
        
        assert "simply" in instruction.lower() or "beginner" in instruction.lower()
        assert "cornell" in instruction.lower()
        assert "emoji" in instruction.lower()
        print(f"System instruction length: {len(instruction)} chars")


class TestPlannerIntegration:
    """Integration tests for planner agent tools."""
    
    def test_calc_trending(self):
        """Test trending calculation (no API call)."""
        from agents.planner.tools import _calc_trending
        from datetime import datetime, timedelta
        
        # Recent content should score high
        recent = datetime.now()
        score = _calc_trending(recent)
        assert score >= 0.8
        
        # Old content should score low
        old = datetime.now() - timedelta(days=180)
        score = _calc_trending(old)
        assert score <= 0.3
        
        print("Trending calculation works correctly")
    
    def test_calc_prerequisite(self):
        """Test prerequisite calculation (no API call)."""
        from agents.planner.tools import _calc_prerequisite
        
        # Foundational content
        score = _calc_prerequisite(["basics", "getting started"], "Introduction to Python")
        assert score >= 0.7
        
        # Advanced content
        score = _calc_prerequisite(["advanced patterns"], "Expert Design Patterns")
        assert score < 0.7
        
        print("Prerequisite calculation works correctly")
    
    def test_generate_reasoning(self):
        """Test reasoning generation (no API call)."""
        from agents.planner.tools import _generate_reasoning
        
        reasoning = _generate_reasoning(
            goal_score=0.9,
            trending_score=0.8,
            prereq_score=0.5,
            goals=["Learn Python", "Master ML"],
            title="Python Basics"
        )
        
        assert "Python Basics" in reasoning
        assert "goal" in reasoning.lower()
        print(f"Generated reasoning: {reasoning}")


class TestEndToEndFlow:
    """End-to-end integration test simulating user workflow."""
    
    def test_content_processing_flow(self):
        """Test the flow: upload content -> extract topics -> generate embedding."""
        from dotenv import load_dotenv
        load_dotenv()
        
        from agents.ingestion.tools import extract_topics, generate_embedding
        
        # Simulate uploaded content
        content = """
        React is a JavaScript library for building user interfaces.
        It uses a virtual DOM to efficiently update the UI.
        Components are the building blocks of React applications.
        State and props allow data to flow through the component tree.
        Hooks like useState and useEffect enable state management in functional components.
        """
        
        # Step 1: Extract topics
        topics_result = extract_topics(content)
        assert topics_result["status"] == "success"
        topics = topics_result["topics"]
        print(f"Step 1 - Extracted topics: {topics}")
        
        # Step 2: Generate embedding
        embedding_result = generate_embedding(content)
        assert embedding_result["status"] == "success"
        print(f"Step 2 - Embedding dimensions: {embedding_result['dimensions']}")
        
        # Verify we got meaningful results
        assert len(topics) >= 1
        assert embedding_result["dimensions"] > 0
        
        print("\nEnd-to-end content processing flow completed successfully!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
