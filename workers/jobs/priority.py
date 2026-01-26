"""
Priority calculation jobs for RQ workers.

Handles recalculating content priority and clustering.
"""

import os
import logging
import httpx

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
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{PLANNER_AGENT_URL}/a2a/tasks/send",
                json={
                    "jsonrpc": "2.0",
                    "method": "tasks/send",
                    "params": {
                        "id": f"recalc-{user_id}",
                        "message": {
                            "role": "user",
                            "parts": [{"text": f'{{"action": "recalculate_priority", "user_id": "{user_id}"}}'}]
                        }
                    }
                }
            )
            result = response.json()
            
            if "result" in result:
                queue_length = len(result["result"].get("queue", []))
                logger.info(f"Priority recalculated for user={user_id}, queue_length={queue_length}")
                return {"status": "success", "queue_length": queue_length}
            else:
                raise Exception(f"Priority recalc failed: {result.get('error')}")
                
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
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{PLANNER_AGENT_URL}/a2a/tasks/send",
                json={
                    "jsonrpc": "2.0",
                    "method": "tasks/send",
                    "params": {
                        "id": f"cluster-{user_id}",
                        "message": {
                            "role": "user",
                            "parts": [{"text": f'{{"action": "cluster_topics", "user_id": "{user_id}"}}'}]
                        }
                    }
                }
            )
            result = response.json()
            
            if "result" in result:
                clusters = result["result"].get("clusters", [])
                logger.info(f"Found {len(clusters)} topic clusters for user={user_id}")
                return {"status": "success", "cluster_count": len(clusters), "clusters": clusters}
            else:
                raise Exception(f"Clustering failed: {result.get('error')}")
                
    except Exception as e:
        logger.error(f"Failed to cluster topics for user={user_id}: {e}")
        raise
