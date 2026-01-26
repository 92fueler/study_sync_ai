"""
Planner Agent Tools

ADK tools for content prioritization using multi-signal algorithm.
"""

import asyncio
import json
import os
from typing import Dict, Any, List

import asyncpg
from google import genai


# Lazy-initialized Gemini client
_client = None


def _get_genai_client():
    """Get or create the Gemini client lazily."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            _client = genai.Client(api_key=api_key)
    return _client


# Priority weights from design doc
WEIGHT_GOAL_MATCH = 0.40
WEIGHT_TRENDING = 0.25
WEIGHT_PREREQUISITE = 0.20
WEIGHT_BEHAVIOR = 0.15


async def _get_db_connection():
    return await asyncpg.connect(os.getenv("SUPABASE_URL", ""))


def _run_async(coro):
    """Run async coroutine safely, handling existing event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


def get_priority_queue(user_id: str, limit: int = 10) -> Dict[str, Any]:
    """
    Get prioritized content queue for a user.
    
    Args:
        user_id: User identifier
        limit: Maximum items to return (default 10)
    
    Returns:
        Dict with status and ranked queue containing content_id, title, priority_score, and reasoning
    """
    return _run_async(_get_priority_queue_async(user_id, limit))


async def _get_priority_queue_async(user_id: str, limit: int) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        # Get user profile
        profile = await conn.fetchrow("SELECT goals FROM user_profiles WHERE user_id = $1", user_id)
        goals = json.loads(profile["goals"]) if profile and profile.get("goals") else []
        
        # Get user's materials
        materials = await conn.fetch(
            """
            SELECT um.content_id, ci.title, ci.topics, ci.word_count, ci.created_at
            FROM user_materials um
            JOIN content_items ci ON um.content_id = ci.id
            WHERE um.user_id = $1 AND um.status = 'PROCESSED'
            """,
            user_id
        )
        
        if not materials:
            return {"status": "success", "queue": [], "message": "No content to prioritize"}
        
        queue = []
        for m in materials:
            topics = json.loads(m["topics"]) if m.get("topics") else []
            
            # Calculate signals
            goal_score = await _calc_goal_match(topics, goals, m.get("title", ""))
            trending_score = _calc_trending(m.get("created_at"))
            prereq_score = _calc_prerequisite(topics, m.get("title", ""))
            behavior_score = 0.5  # Default
            
            # Weighted sum
            final_score = (
                WEIGHT_GOAL_MATCH * goal_score +
                WEIGHT_TRENDING * trending_score +
                WEIGHT_PREREQUISITE * prereq_score +
                WEIGHT_BEHAVIOR * behavior_score
            )
            
            reasoning = _generate_reasoning(goal_score, trending_score, prereq_score, goals, m.get("title", ""))
            
            queue.append({
                "content_id": str(m["content_id"]),
                "title": m.get("title", "Untitled"),
                "topics": topics,
                "priority_score": round(final_score, 3),
                "priority_reasoning": reasoning,
                "signals": {
                    "goal_match": round(goal_score, 2),
                    "trending": round(trending_score, 2),
                    "prerequisites": round(prereq_score, 2),
                    "behavior": round(behavior_score, 2)
                },
                "word_count": m.get("word_count", 0)
            })
        
        queue.sort(key=lambda x: x["priority_score"], reverse=True)
        return {"status": "success", "queue": queue[:limit], "total_items": len(queue)}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


async def _calc_goal_match(topics: List[str], goals: List[str], title: str) -> float:
    if not goals:
        return 0.5
    if not topics:
        return 0.3
    
    client = _get_genai_client()
    if not client:
        # Fallback: keyword overlap
        goal_words = set(' '.join(goals).lower().split())
        topic_words = set(' '.join(topics).lower().split())
        if not goal_words:
            return 0.5
        return min(1.0, len(goal_words & topic_words) / len(goal_words))
    
    try:
        prompt = f"""Rate relevance 0.0-1.0:
Goals: {', '.join(goals)}
Topics: {', '.join(topics)}
Title: {title}
Return ONLY a number like 0.75"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return max(0.0, min(1.0, float(response.text.strip())))
    except:
        # Fallback: keyword overlap
        goal_words = set(' '.join(goals).lower().split())
        topic_words = set(' '.join(topics).lower().split())
        if not goal_words:
            return 0.5
        return min(1.0, len(goal_words & topic_words) / len(goal_words))


def _calc_trending(created_at) -> float:
    from datetime import datetime
    if not created_at:
        return 0.5
    try:
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        days_old = (datetime.now(created_at.tzinfo) - created_at).days
        if days_old <= 1: return 1.0
        if days_old <= 7: return 0.8
        if days_old <= 30: return 0.6
        if days_old <= 90: return 0.4
        return 0.2
    except:
        return 0.5


def _calc_prerequisite(topics: List[str], title: str) -> float:
    foundational = ["basics", "introduction", "fundamentals", "getting started", "101", "beginner", "overview"]
    title_lower = title.lower()
    topics_lower = [t.lower() for t in topics]
    
    if any(kw in title_lower or any(kw in t for t in topics_lower) for kw in foundational):
        return 0.8
    return 0.4


def _generate_reasoning(goal_score: float, trending_score: float, prereq_score: float, goals: List[str], title: str) -> str:
    reasons = []
    if goal_score >= 0.7:
        reasons.append(f"aligns with your goals ({', '.join(goals[:2])})")
    elif goal_score >= 0.4:
        reasons.append("partially relevant to your goals")
    if trending_score >= 0.7:
        reasons.append("recently added")
    if prereq_score >= 0.7:
        reasons.append("contains foundational concepts")
    if not reasons:
        reasons.append("available for study")
    return f"{title} is prioritized because it {', '.join(reasons)}."


def recalculate_priority(user_id: str) -> Dict[str, Any]:
    """
    Force recalculation of priority queue.
    
    Args:
        user_id: User identifier
    
    Returns:
        Dict with status and fresh priority queue
    """
    return get_priority_queue(user_id)


def cluster_topics(user_id: str) -> Dict[str, Any]:
    """
    Group related content by topic clusters.
    
    Args:
        user_id: User identifier
    
    Returns:
        Dict with status and topic clusters with their content
    """
    return _run_async(_cluster_topics_async(user_id))


async def _cluster_topics_async(user_id: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        materials = await conn.fetch(
            """
            SELECT um.content_id, ci.title, ci.topics
            FROM user_materials um
            JOIN content_items ci ON um.content_id = ci.id
            WHERE um.user_id = $1 AND um.status = 'PROCESSED'
            """,
            user_id
        )
        
        topic_map = {}
        for m in materials:
            topics = json.loads(m["topics"]) if m.get("topics") else []
            for topic in topics:
                if topic not in topic_map:
                    topic_map[topic] = []
                topic_map[topic].append({"content_id": str(m["content_id"]), "title": m.get("title")})
        
        clusters = [{"topic": t, "content_count": len(items), "items": items} for t, items in topic_map.items()]
        clusters.sort(key=lambda x: x["content_count"], reverse=True)
        return {"status": "success", "clusters": clusters}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def calculate_effort(content_id: str) -> Dict[str, Any]:
    """
    Estimate study effort for content.
    
    Args:
        content_id: Content UUID
    
    Returns:
        Dict with status, word_count, reading_minutes, study_minutes, complexity
    """
    return _run_async(_calculate_effort_async(content_id))


async def _calculate_effort_async(content_id: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        row = await conn.fetchrow("SELECT word_count, topics FROM content_items WHERE id = $1", content_id)
        if not row:
            return {"status": "error", "error": "Content not found"}
        
        word_count = row.get("word_count", 0)
        topics = json.loads(row["topics"]) if row.get("topics") else []
        
        reading_minutes = max(1, word_count // 200)
        complexity_factor = 1.5 if len(topics) > 5 else 1.2 if len(topics) > 2 else 1.0
        study_minutes = int(reading_minutes * complexity_factor)
        
        return {
            "status": "success",
            "content_id": content_id,
            "word_count": word_count,
            "reading_minutes": reading_minutes,
            "study_minutes": study_minutes,
            "complexity": "high" if complexity_factor >= 1.5 else "medium" if complexity_factor >= 1.2 else "low"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()
