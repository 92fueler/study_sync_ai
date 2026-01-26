"""
Priority calculation jobs for RQ workers.

Handles recalculating content priority and clustering.
"""

import os
import json
import logging

from workers.adk_client import run_adk_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PLANNER_AGENT_URL = os.getenv("PLANNER_AGENT_URL", "http://localhost:8004")


def recalculate_priority(user_id: str) -> dict:
    """
    Recalculate priority queue for a user.
    
    Called after:
    - Profile update (goals changed)
    - New content added
    - Significant time passed
    
    Args:
        user_id: User identifier
    
    Returns:
        Dict with updated queue length
    """
    logger.info(f"Recalculating priority for user={user_id}")
    
    try:
        result = run_adk_agent(
            PLANNER_AGENT_URL,
            "planner",
            user_id,
            json.dumps({"skill": "recalculate_priority", "user_id": user_id}),
            timeout=60.0,
        )
        parsed = result.get("parsed", {})
        queue_length = len(parsed.get("queue", [])) if isinstance(parsed, dict) else 0
        logger.info(f"Priority recalculated for user={user_id}, queue_length={queue_length}")
        return {"status": "success", "queue_length": queue_length}
                
    except Exception as e:
        logger.error(f"Failed to recalculate priority for user={user_id}: {e}")
        raise


def cluster_topics(user_id: str) -> dict:
    """
    Cluster user's content by topic for study plan suggestions.
    
    Args:
        user_id: User identifier
    
    Returns:
        Dict with cluster count and details
    """
    logger.info(f"Clustering topics for user={user_id}")
    
    try:
        result = run_adk_agent(
            PLANNER_AGENT_URL,
            "planner",
            user_id,
            json.dumps({"skill": "cluster_topics", "user_id": user_id}),
            timeout=60.0,
        )
        parsed = result.get("parsed", {})
        clusters = parsed.get("clusters", []) if isinstance(parsed, dict) else []
        logger.info(f"Found {len(clusters)} topic clusters for user={user_id}")
        return {"status": "success", "cluster_count": len(clusters), "clusters": clusters}
                
    except Exception as e:
        logger.error(f"Failed to cluster topics for user={user_id}: {e}")
        raise
