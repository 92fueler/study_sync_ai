"""
Generation jobs for RQ workers.

These jobs call the Synthesis Agent to generate personalized artifacts.
"""

import os
import json
import logging

from workers.adk_client import run_adk_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYNTHESIS_AGENT_URL = os.getenv("SYNTHESIS_AGENT_URL", "http://localhost:8003")
PROFILE_AGENT_URL = os.getenv("PROFILE_AGENT_URL", "http://localhost:8002")
GATEWAY_URL = os.getenv("GATEWAY_URL", "")


def _get_user_profile(user_id: str) -> dict:
    """Fetch user profile for personalization. Prefer gateway for-generation so style_dna.formats is present."""
    if GATEWAY_URL:
        try:
            import httpx
            r = httpx.get(f"{GATEWAY_URL.rstrip('/')}/api/v1/profile/for-generation", params={"user_id": user_id}, timeout=10.0)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, dict) and data.get("status") == "success":
                return data
        except Exception as e:
            logger.warning(f"Gateway profile-for-generation failed for {user_id}: {e}")
    try:
        message = json.dumps({"skill": "get_profile", "user_id": user_id})
        result = run_adk_agent(PROFILE_AGENT_URL, "profile", user_id, message, timeout=30.0)
        parsed = result.get("parsed")
        if isinstance(parsed, dict) and parsed.get("status") == "success":
            return parsed
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

    # #region agent log
    try:
        _dp = os.path.join(os.path.dirname(__file__), "..", "..", ".cursor", "debug.log")
        _e = {"timestamp": int(__import__("time").time() * 1000), "location": "generation.py:payload_before_call", "message": "worker payload style_dna", "data": {"style_dna_type": type(style_dna).__name__, "formats": style_dna.get("formats", "__missing__") if isinstance(style_dna, dict) else "not_dict", "artifact_type": artifact_type}, "hypothesisId": "A"}
        open(_dp, "a").write(json.dumps(_e) + "\n")
    except Exception:
        pass
    # #endregion

    # Call Synthesis Agent
    try:
        if artifact_type == "5min":
            payload = {
                "skill": "generate_5min_summary",
                "user_id": user_id,
                "content_id": content_id,
                "profile_version": profile_version,
                "style_dna": style_dna,
            }
        else:
            payload = {
                "skill": "generate_artifact",
                "user_id": user_id,
                "content_ids": [content_id],
                "profile_version": profile_version,
                "style_dna": style_dna,
                "time_available_minutes": 25,
            }

        # Synthesis can take 2+ min (LLM 5min summary + DB + SSE); use 5 min to avoid ReadTimeout
        result = run_adk_agent(
            SYNTHESIS_AGENT_URL,
            "synthesis",
            user_id,
            json.dumps(payload),
            timeout=300.0,
        )
        parsed = result.get("parsed", {})
        if isinstance(parsed, dict) and parsed.get("status") == "error":
            raise Exception(f"Synthesis agent error: {parsed.get('error')}")

        logger.info(f"Successfully generated {artifact_type} artifact for content={content_id}")

        from workers.queue import enqueue_notification
        enqueue_notification(
            user_id=user_id,
            title="New study material ready!",
            body=f"Your {artifact_type} summary is ready to review.",
            data={"artifact_id": parsed.get("artifact_id"), "content_id": content_id, "status": "ready"}
        )

        return {"status": "success", "result": parsed or result}

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
        artifact_result = run_adk_agent(
            SYNTHESIS_AGENT_URL,
            "synthesis",
            user_id,
            json.dumps({"skill": "get_artifact", "artifact_id": artifact_id}),
            timeout=120.0,
        )
        parsed_artifact = artifact_result.get("parsed", {})
        if not isinstance(parsed_artifact, dict) or parsed_artifact.get("status") == "error":
            raise Exception(f"Artifact not found: {artifact_id}")

        content_ids = parsed_artifact.get("content_ids", [])

        result = run_adk_agent(
            SYNTHESIS_AGENT_URL,
            "synthesis",
            user_id,
            json.dumps({
                "skill": "generate_artifact",
                "user_id": user_id,
                "content_ids": content_ids,
                "profile_version": profile_version,
                "style_dna": style_dna,
                "time_available_minutes": 25
            }),
            timeout=120.0,
        )
        parsed = result.get("parsed", {})
        if isinstance(parsed, dict) and parsed.get("status") == "error":
            raise Exception(f"Regeneration failed: {parsed.get('error')}")

        logger.info(f"Successfully regenerated artifact={artifact_id}")

        from workers.queue import enqueue_notification
        enqueue_notification(
            user_id=user_id,
            title="Material regenerated!",
            body="Your updated study material is ready.",
            data={"artifact_id": parsed.get("artifact_id"), "status": "ready"}
        )

        return {"status": "success", "result": parsed or result}

    except Exception as e:
        logger.error(f"Regeneration failed for artifact={artifact_id}: {e}")
        raise
