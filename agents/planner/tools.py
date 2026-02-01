"""
Planner Agent Tools

ADK tools for content prioritization using multi-signal algorithm.
Enhanced with context-aware dynamic weights and semantic clustering.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional

import asyncpg
from google import genai

logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    logging.basicConfig(level=os.getenv("AGENT_LOG_LEVEL", "INFO"))

# Lazy-initialized clients
_client = None
_db_pool: Optional[asyncpg.Pool] = None


def _get_genai_client():
    """Get or create the Gemini client lazily."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            _client = genai.Client(api_key=api_key)
    return _client


async def _get_db_pool():
    """Get or create database connection pool (singleton pattern)."""
    global _db_pool
    if _db_pool is None:
        dsn = os.getenv("SUPABASE_URL", "")
        if not dsn:
            raise ValueError("SUPABASE_URL is not set")
        _db_pool = await asyncpg.create_pool(
            dsn,
            min_size=1,
            max_size=10
        )
    return _db_pool


async def _get_db_connection():
    """Legacy: Get single connection (for backward compatibility)."""
    dsn = os.getenv("SUPABASE_URL", "")
    logger.debug("Connecting to DB for planner tools")
    return await asyncpg.connect(dsn)


# Priority weights from design doc (default/static weights)
WEIGHT_GOAL_MATCH = 0.40
WEIGHT_TRENDING = 0.25
WEIGHT_PREREQUISITE = 0.20
WEIGHT_BEHAVIOR = 0.15


def _get_dynamic_weights(context_mode: str = "growth") -> Dict[str, float]:
    """
    Get dynamic weights based on learning context mode.
    
    Args:
        context_mode: "cram" | "growth" | "exploration"
    
    Returns:
        Dict with weights for goal_match, trending, prerequisite, difficulty
    
    Note: Weights are relative, not probabilities. They don't sum to 1.0 because:
    - Missing "behavior" signal (15% in original) is not included
    - Difficulty signal can be negative (penalty) in cram mode
    """
    # Validate context mode, default to growth if invalid
    if context_mode not in ["cram", "growth", "exploration"]:
        logger.warning(f"Invalid context_mode: {context_mode}, defaulting to 'growth'")
        context_mode = "growth"
    
    if context_mode == "cram":
        # Cram mode: Focus on high-value matches, ignore trending, boost prerequisites
        return {
            "goal_match": 0.6,
            "trending": 0.0,
            "prerequisite": 0.4,
            "difficulty": -0.2  # Penalize advanced content
        }
    elif context_mode == "exploration":
        # Exploration mode: Boost trending/new content
        return {
            "goal_match": 0.2,
            "trending": 0.5,
            "prerequisite": 0.1,
            "difficulty": 0.0
        }
    else:  # growth (default)
        # Growth mode: Balanced approach
        return {
            "goal_match": 0.4,
            "trending": 0.25,
            "prerequisite": 0.2,
            "difficulty": 0.0
        }


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
    logger.info("get_priority_queue called", extra={"user_id": user_id, "limit": limit})
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
            logger.info("get_priority_queue completed", extra={"user_id": user_id, "count": 0})
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
        result = {"status": "success", "queue": queue[:limit], "total_items": len(queue)}
        logger.info("get_priority_queue completed", extra={"user_id": user_id, "count": len(result["queue"])})
        return result
    except Exception as e:
        logger.exception("get_priority_queue failed", extra={"user_id": user_id})
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


async def _calc_goal_match(topics: List[str], goals: List[str], title: str) -> float:
    """Calculate semantic relevance between content and user goals using improved prompt."""
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
        prompt = f"""You are evaluating how well content matches a user's learning goals.

TASK: Rate the semantic relevance between the user's goals and the content on a scale of 0.0 to 1.0.

USER'S LEARNING GOALS:
{', '.join(goals)}

CONTENT INFORMATION:
- Title: {title}
- Topics: {', '.join(topics)}

SCORING GUIDELINES:
- 0.9-1.0: Content directly addresses one or more goals (e.g., goal is "Learn React" and content is "React Tutorial")
- 0.7-0.9: Content is highly relevant but may be a subset or prerequisite (e.g., goal is "Build web apps" and content is "JavaScript Basics")
- 0.5-0.7: Content is somewhat related but not directly aligned (e.g., goal is "Learn Python" and content is "General Programming Concepts")
- 0.3-0.5: Content has minimal relevance (e.g., goal is "Learn Python" and content is "History of Computing")
- 0.0-0.3: Content is not relevant to the goals

EXAMPLES:
- Goals: ["Learn React", "Build web apps"]
  Content: "React Hooks Tutorial" → Score: 0.95 (direct match)
- Goals: ["Learn React"]
  Content: "JavaScript Fundamentals" → Score: 0.75 (prerequisite, highly relevant)
- Goals: ["Learn Python"]
  Content: "Machine Learning Overview" → Score: 0.4 (minimal relevance)

Return ONLY a number between 0.0 and 1.0 (e.g., 0.75):"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return max(0.0, min(1.0, float(response.text.strip())))
    except Exception as e:
        logger.warning(f"Goal match calculation failed, using fallback: {e}")
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
    logger.info("recalculate_priority called", extra={"user_id": user_id})
    return get_priority_queue(user_id)


def cluster_topics(user_id: str) -> Dict[str, Any]:
    """
    Group related content by topic clusters.
    
    Args:
        user_id: User identifier
    
    Returns:
        Dict with status and topic clusters with their content
    """
    logger.info("cluster_topics called", extra={"user_id": user_id})
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
        result = {"status": "success", "clusters": clusters}
        logger.info("cluster_topics completed", extra={"user_id": user_id, "clusters": len(clusters)})
        return result
    except Exception as e:
        logger.exception("cluster_topics failed", extra={"user_id": user_id})
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
    logger.info("calculate_effort called", extra={"content_id": content_id})
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
        
        result = {
            "status": "success",
            "content_id": content_id,
            "word_count": word_count,
            "reading_minutes": reading_minutes,
            "study_minutes": study_minutes,
            "complexity": "high" if complexity_factor >= 1.5 else "medium" if complexity_factor >= 1.2 else "low"
        }
        logger.info("calculate_effort completed", extra={"content_id": content_id, "study_minutes": study_minutes})
        return result
    except Exception as e:
        logger.exception("calculate_effort failed", extra={"content_id": content_id})
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


# ============================================================================
# Enhanced Functions (Context-Aware & Semantic)
# ============================================================================

def get_adaptive_priority(
    user_id: str,
    context_mode: str = "growth",
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get prioritized content queue with dynamic weights based on learning context.
    
    Args:
        user_id: User identifier
        context_mode: "cram" | "growth" | "exploration"
        limit: Maximum items to return
    
    Returns:
        Dict with status, mode, and ranked queue with context-aware scores
    """
    logger.info("get_adaptive_priority called", extra={"user_id": user_id, "context_mode": context_mode, "limit": limit})
    return _run_async(_get_adaptive_priority_async(user_id, context_mode, limit))


async def _get_adaptive_priority_async(user_id: str, context_mode: str, limit: int) -> Dict[str, Any]:
    """Internal async implementation of adaptive priority."""
    pool = await _get_db_pool()
    async with pool.acquire() as conn:
        try:
            # Get user profile
            profile = await conn.fetchrow("SELECT goals FROM user_profiles WHERE user_id = $1", user_id)
            goals = json.loads(profile["goals"]) if profile and profile.get("goals") else []
            
            # Get dynamic weights based on context mode
            weights = _get_dynamic_weights(context_mode)
            
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
                return {"status": "success", "mode": context_mode, "queue": [], "message": "No content to prioritize"}
            
            queue = []
            for m in materials:
                topics = json.loads(m["topics"]) if m.get("topics") else []
                
                # Calculate signals
                goal_score = await _calc_goal_match(topics, goals, m.get("title", ""))
                trending_score = _calc_trending(m.get("created_at"))
                prereq_score = _calc_prerequisite(topics, m.get("title", ""))
                
                # Infer difficulty for difficulty signal
                difficulty = await _infer_difficulty(m.get("title", ""), topics)
                difficulty_score = 0.5 if difficulty == "Intermediate" else 0.3 if difficulty == "Beginner" else 0.7
                
                # Calculate weighted score with dynamic weights
                final_score = (
                    weights["goal_match"] * goal_score +
                    weights["trending"] * trending_score +
                    weights["prerequisite"] * prereq_score +
                    weights["difficulty"] * difficulty_score
                )
                
                reasoning = _generate_adaptive_reasoning(
                    goal_score, trending_score, prereq_score, difficulty_score,
                    weights, goals, m.get("title", ""), context_mode
                )
                
                queue.append({
                    "content_id": str(m["content_id"]),
                    "title": m.get("title", "Untitled"),
                    "topics": topics,
                    "priority_score": round(final_score, 3),
                    "priority_reasoning": reasoning,
                    "difficulty": difficulty,
                    "signals": {
                        "goal_match": round(goal_score, 2),
                        "trending": round(trending_score, 2),
                        "prerequisites": round(prereq_score, 2),
                        "difficulty": difficulty
                    },
                    "word_count": m.get("word_count", 0)
                })
            
            queue.sort(key=lambda x: x["priority_score"], reverse=True)
            result = {
                "status": "success",
                "mode": context_mode,
                "queue": queue[:limit],
                "total_items": len(queue),
                "weights_used": weights
            }
            logger.info("get_adaptive_priority completed", extra={"user_id": user_id, "count": len(result["queue"])})
            return result
        except Exception as e:
            logger.exception("get_adaptive_priority failed", extra={"user_id": user_id})
            return {"status": "error", "error": str(e)}


def cluster_semantically(user_id: str, similarity_threshold: float = 0.75) -> Dict[str, Any]:
    """
    Group content using vector similarity (pgvector) instead of exact string matching.
    This creates coherent learning modules (e.g., "Neural Networks" and "Deep Learning" grouped together).
    
    Args:
        user_id: User identifier
        similarity_threshold: Minimum cosine similarity for clustering (0.0-1.0, default 0.75)
    
    Returns:
        Dict with status and semantic clusters
    """
    logger.info("cluster_semantically called", extra={"user_id": user_id, "threshold": similarity_threshold})
    return _run_async(_cluster_semantically_async(user_id, similarity_threshold))


async def _cluster_semantically_async(user_id: str, threshold: float) -> Dict[str, Any]:
    """Internal async implementation of semantic clustering using pgvector."""
    pool = await _get_db_pool()
    async with pool.acquire() as conn:
        try:
            # Get user's content with embeddings
            items = await conn.fetch(
                """
                SELECT ci.id, ci.title, ci.topics, ci.embedding
                FROM user_materials um
                JOIN content_items ci ON um.content_id = ci.id
                WHERE um.user_id = $1 
                  AND um.status = 'PROCESSED'
                  AND ci.embedding IS NOT NULL
                """,
                user_id
            )
            
            if not items:
                return {"status": "success", "clusters": []}
            
            # Use DB-side vector similarity for clustering
            # For each item, find similar items using pgvector's <=> operator
            clusters = []
            processed_ids = set()
            
            for item in items:
                item_id = str(item["id"])
                if item_id in processed_ids:
                    continue
                
                # Find similar items using vector similarity (DB-side, fast!)
                # Note: pgvector <=> returns distance (lower = more similar)
                # We convert to similarity: similarity = 1 - distance
                similar_items = await conn.fetch(
                    """
                    SELECT ci2.id, ci2.title, ci2.topics,
                           (ci1.embedding::halfvec(3072) <=> ci2.embedding::halfvec(3072)) as distance
                    FROM content_items ci1, content_items ci2
                    WHERE ci1.id = $1
                      AND ci2.id != ci1.id
                      AND ci2.embedding IS NOT NULL
                      AND EXISTS (
                          SELECT 1 FROM user_materials um
                          WHERE um.content_id = ci2.id AND um.user_id = $2
                      )
                    ORDER BY distance
                    LIMIT 20
                    """,
                    item["id"], user_id
                )
                
                # Build cluster with items above threshold
                cluster_items = [{
                    "content_id": item_id,
                    "title": item.get("title", "Untitled"),
                    "topics": json.loads(item["topics"]) if item.get("topics") else []
                }]
                processed_ids.add(item_id)
                
                for similar in similar_items:
                    # Convert distance to similarity: similarity = 1 - distance
                    distance = float(similar["distance"])
                    similarity = 1.0 - distance
                    similar_id = str(similar["id"])
                    
                    if similarity >= threshold and similar_id not in processed_ids:
                        cluster_items.append({
                            "content_id": similar_id,
                            "title": similar.get("title", "Untitled"),
                            "topics": json.loads(similar["topics"]) if similar.get("topics") else [],
                            "similarity": round(similarity, 3)
                        })
                        processed_ids.add(similar_id)
                
                # Only create cluster if it has items (should always be at least 1, but safety check)
                if len(cluster_items) > 0:
                    # Use first item's title as cluster theme (could be improved with LLM)
                    clusters.append({
                        "theme": cluster_items[0]["title"],
                        "item_count": len(cluster_items),
                        "items": cluster_items
                    })
            
            result = {
                "status": "success",
                "clusters": clusters,
                "total_clusters": len(clusters),
                "similarity_threshold": threshold
            }
            logger.info("cluster_semantically completed", extra={"user_id": user_id, "clusters": len(clusters)})
            return result
        except Exception as e:
            logger.exception("cluster_semantically failed", extra={"user_id": user_id})
            return {"status": "error", "error": str(e)}


def estimate_study_effort(content_id: str) -> Dict[str, Any]:
    """
    Estimate study effort with difficulty-aware multipliers.
    
    Args:
        content_id: Content UUID
    
    Returns:
        Dict with status, word_count, reading_minutes, study_minutes, complexity_rating, difficulty
    """
    logger.info("estimate_study_effort called", extra={"content_id": content_id})
    return _run_async(_estimate_study_effort_async(content_id))


async def _estimate_study_effort_async(content_id: str) -> Dict[str, Any]:
    """Internal async implementation of difficulty-aware effort estimation."""
    pool = await _get_db_pool()
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                "SELECT word_count, topics, title FROM content_items WHERE id = $1",
                content_id
            )
            
            if not row:
                return {"status": "error", "error": "Content not found"}
            
            word_count = row.get("word_count", 0)
            topics = json.loads(row["topics"]) if row.get("topics") else []
            title = row.get("title", "")
            
            # Infer difficulty if not available
            difficulty = await _infer_difficulty(title, topics)
            
            # Base reading speed: 200 words/minute
            base_minutes = max(1, word_count // 200)
            
            # Difficulty multipliers
            multipliers = {
                "Beginner": 1.0,
                "Intermediate": 1.5,  # Re-reading required
                "Advanced": 2.5       # Deep study required
            }
            
            study_minutes = int(base_minutes * multipliers.get(difficulty, 1.5))
            
            result = {
                "status": "success",
                "content_id": content_id,
                "word_count": word_count,
                "reading_minutes": base_minutes,
                "study_minutes": study_minutes,
                "complexity_rating": difficulty,
                "difficulty_multiplier": multipliers.get(difficulty, 1.5)
            }
            logger.info("estimate_study_effort completed", extra={"content_id": content_id, "study_minutes": study_minutes})
            return result
        except Exception as e:
            logger.exception("estimate_study_effort failed", extra={"content_id": content_id})
            return {"status": "error", "error": str(e)}


async def _infer_difficulty(title: str, topics: List[str]) -> str:
    """
    Infer content difficulty using LLM when not available in metadata.
    
    Returns: "Beginner" | "Intermediate" | "Advanced"
    """
    client = _get_genai_client()
    if not client:
        # Fallback: infer from keywords
        beginner_keywords = ["introduction", "basics", "101", "beginner", "getting started", "overview"]
        advanced_keywords = ["advanced", "expert", "deep dive", "mastery", "optimization"]
        
        title_lower = title.lower()
        if any(kw in title_lower for kw in beginner_keywords):
            return "Beginner"
        if any(kw in title_lower for kw in advanced_keywords):
            return "Advanced"
        return "Intermediate"
    
    try:
        prompt = f"""Classify the difficulty level of this educational content.

Title: {title}
Topics: {', '.join(topics[:5]) if topics else "N/A"}

Difficulty Levels:
- Beginner: Introductory content, assumes no prior knowledge, uses simple language
- Intermediate: Assumes some background knowledge, covers standard concepts
- Advanced: Requires significant prior knowledge, covers complex/advanced topics

Return ONLY one word: Beginner, Intermediate, or Advanced"""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        result = response.text.strip().lower()
        if "beginner" in result:
            return "Beginner"
        elif "advanced" in result:
            return "Advanced"
        else:
            return "Intermediate"
    except Exception as e:
        logger.warning(f"Difficulty inference failed, using fallback: {e}")
        return "Intermediate"


def _generate_adaptive_reasoning(
    goal_score: float,
    trending_score: float,
    prereq_score: float,
    difficulty_score: float,
    weights: Dict[str, float],
    goals: List[str],
    title: str,
    context_mode: str
) -> str:
    """Generate context-aware reasoning for adaptive priority."""
    reasons = []
    
    if goal_score >= 0.7:
        reasons.append(f"highly aligns with your goals ({', '.join(goals[:2])})")
    elif goal_score >= 0.4:
        reasons.append("partially relevant to your goals")
    
    if context_mode == "cram":
        if prereq_score >= 0.7:
            reasons.append("contains foundational concepts (important for cramming)")
        if difficulty_score <= 0.3:
            reasons.append("suitable difficulty for quick study")
    elif context_mode == "exploration":
        if trending_score >= 0.7:
            reasons.append("recently added (great for exploration)")
    else:  # growth
        if prereq_score >= 0.7:
            reasons.append("contains foundational concepts")
        if trending_score >= 0.7:
            reasons.append("recently added")
    
    if not reasons:
        reasons.append("available for study")
    
    mode_context = {
        "cram": "In cram mode, prioritizing",
        "exploration": "In exploration mode, highlighting",
        "growth": "Prioritizing"
    }.get(context_mode, "Prioritizing")
    
    return f"{mode_context} {title} because it {', '.join(reasons)}."
