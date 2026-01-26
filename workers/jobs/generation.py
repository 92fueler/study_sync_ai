"""
Generation jobs for RQ workers.

These jobs call the Synthesis Agent to generate personalized artifacts.
"""

import os
import logging
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYNTHESIS_AGENT_URL = os.getenv("SYNTHESIS_AGENT_URL", "http://localhost:8003")
PROFILE_AGENT_URL = os.getenv("PROFILE_AGENT_URL", "http://localhost:8002")


def _get_user_profile(user_id: str) -> dict:
    """Fetch user profile for personalization."""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{PROFILE_AGENT_URL}/a2a/tasks/send",
                json={
                    "jsonrpc": "2.0",
                    "method": "tasks/send",
                    "params": {
                        "id": f"get-profile-{user_id}",
                        "message": {
                            "role": "user",
                            "parts": [{"text": f'{{"action": "get_profile", "user_id": "{user_id}"}}'}]
                        }
                    }
                }
            )
            result = response.json()
            if "result" in result:
                return result["result"]
    except Exception as e:
        logger.warning(f"Failed to fetch profile for {user_id}: {e}")
    
    # Return defaults
    return {
        "style_dna": {
            "tone": "eli5",
            "format_pref": "outline",
            "uses_emoji": False,
            "prefers_diagrams": True
        },
        "profile_version": 1
    }


def generate_artifact(user_id: str, content_id: str, artifact_type: str = "5min") -> dict:
    """
    Generate a personalized artifact for content.
    
    Args:
        user_id: User identifier
        content_id: Content UUID to generate artifact for
        artifact_type: "5min" for quick summary, "full" for comprehensive
    
    Returns:
        Dict with artifact_id and status
    """
    logger.info(f"Generating {artifact_type} artifact for user={user_id}, content={content_id}")
    
    # Get user profile
    profile = _get_user_profile(user_id)
    style_dna = profile.get("style_dna", {})
    profile_version = profile.get("profile_version", 1)
    
    # Call Synthesis Agent
    try:
        with httpx.Client(timeout=120.0) as client:
            if artifact_type == "5min":
                action = "generate_5min_summary"
                payload = {
                    "action": action,
                    "user_id": user_id,
                    "content_id": content_id,
                    "profile_version": profile_version,
                    "style_dna": style_dna
                }
            else:
                action = "generate_artifact"
                payload = {
                    "action": action,
                    "user_id": user_id,
                    "content_ids": [content_id],
                    "profile_version": profile_version,
                    "style_dna": style_dna,
                    "time_available_minutes": 25
                }
            
            response = client.post(
                f"{SYNTHESIS_AGENT_URL}/a2a/tasks/send",
                json={
                    "jsonrpc": "2.0",
                    "method": "tasks/send",
                    "params": {
                        "id": f"gen-{artifact_type}-{content_id}",
                        "message": {
                            "role": "user",
                            "parts": [{"text": str(payload)}]
                        }
                    }
                }
            )
            result = response.json()
            
            if "result" in result:
                logger.info(f"Successfully generated {artifact_type} artifact for content={content_id}")
                
                # Enqueue notification
                from workers.queue import enqueue_notification
                enqueue_notification(
                    user_id=user_id,
                    title="New study material ready!",
                    body=f"Your {artifact_type} summary is ready to review.",
                    data={"artifact_id": result["result"].get("artifact_id"), "content_id": content_id}
                )
                
                return {"status": "success", "result": result["result"]}
            else:
                raise Exception(f"Synthesis agent error: {result.get('error')}")
                
    except Exception as e:
        logger.error(f"Generation failed for content={content_id}: {e}")
        raise


def regenerate_artifact(user_id: str, artifact_id: str) -> dict:
    """
    Regenerate an existing artifact (user-requested).
    
    Args:
        user_id: User identifier
        artifact_id: Existing artifact UUID to regenerate
    
    Returns:
        Dict with new artifact_id and status
    """
    logger.info(f"Regenerating artifact={artifact_id} for user={user_id}")
    
    # Get user profile (may have changed since original generation)
    profile = _get_user_profile(user_id)
    style_dna = profile.get("style_dna", {})
    profile_version = profile.get("profile_version", 1)
    
    try:
        with httpx.Client(timeout=120.0) as client:
            # First get the original artifact to find content_ids
            response = client.post(
                f"{SYNTHESIS_AGENT_URL}/a2a/tasks/send",
                json={
                    "jsonrpc": "2.0",
                    "method": "tasks/send",
                    "params": {
                        "id": f"get-artifact-{artifact_id}",
                        "message": {
                            "role": "user",
                            "parts": [{"text": f'{{"action": "get_artifact", "artifact_id": "{artifact_id}"}}'}]
                        }
                    }
                }
            )
            artifact_result = response.json()
            
            if "error" in artifact_result:
                raise Exception(f"Artifact not found: {artifact_id}")
            
            # Regenerate with current profile
            content_ids = artifact_result.get("result", {}).get("content_ids", [])
            
            response = client.post(
                f"{SYNTHESIS_AGENT_URL}/a2a/tasks/send",
                json={
                    "jsonrpc": "2.0",
                    "method": "tasks/send",
                    "params": {
                        "id": f"regen-{artifact_id}",
                        "message": {
                            "role": "user",
                            "parts": [{"text": str({
                                "action": "generate_artifact",
                                "user_id": user_id,
                                "content_ids": content_ids,
                                "profile_version": profile_version,
                                "style_dna": style_dna,
                                "time_available_minutes": 25
                            })}]
                        }
                    }
                }
            )
            result = response.json()
            
            if "result" in result:
                logger.info(f"Successfully regenerated artifact={artifact_id}")
                
                from workers.queue import enqueue_notification
                enqueue_notification(
                    user_id=user_id,
                    title="Material regenerated!",
                    body="Your updated study material is ready.",
                    data={"artifact_id": result["result"].get("artifact_id")}
                )
                
                return {"status": "success", "result": result["result"]}
            else:
                raise Exception(f"Regeneration failed: {result.get('error')}")
                
    except Exception as e:
        logger.error(f"Regeneration failed for artifact={artifact_id}: {e}")
        raise
