"""
Minimal ADK runtime client for workers.

Uses ADK api_server session creation + /run_sse.
"""

import ast
import json
import logging
import uuid
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


def _extract_structured(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort extraction of a JSON-like object from model text."""
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    snippet = text[start:end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        try:
            value = ast.literal_eval(snippet)
            if isinstance(value, dict):
                return value
        except Exception:
            return None
    return None


def run_adk_agent(
    base_url: str,
    app_name: str,
    user_id: str,
    message: str,
    session_id: Optional[str] = None,
    timeout: float = 120.0,
) -> Dict[str, Any]:
    """
    Run an ADK agent via /run_sse and return parsed content.
    """
    if session_id is None:
        # Deterministic per user so sessions are stable across processes.
        session_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"studysync:{user_id}"))
    result: Dict[str, Any] = {"session_id": session_id}

    with httpx.Client(timeout=timeout) as client:
        # Create session (id may be overridden by server)
        try:
            create = client.post(
                f"{base_url}/apps/{app_name}/users/{user_id}/sessions",
                json={"id": session_id},
                headers={"Content-Type": "application/json"},
            )
            if create.status_code == 200:
                data = create.json()
                result["session_id"] = data.get("id", session_id)
                session_id = result["session_id"]
        except Exception as exc:
            logger.warning("Session creation failed for %s: %s", app_name, exc)

        # Run agent
        response = client.post(
            f"{base_url}/run_sse",
            json={
                "app_name": app_name,
                "user_id": user_id,
                "session_id": session_id,
                "new_message": {"role": "user", "parts": [{"text": message}]},
            },
            headers={"Content-Type": "application/json"},
        )

        response.raise_for_status()

        # Parse SSE response - get last event with content
        for line in response.text.split("\n"):
            if line.startswith("data: "):
                try:
                    event = json.loads(line[6:])
                except json.JSONDecodeError:
                    continue
                if event.get("content"):
                    result["content"] = event["content"]
                    parts = event["content"].get("parts", [])
                    for part in parts:
                        if "text" in part:
                            result["text"] = part["text"]

    # Best-effort parse to structured result
    parsed = _extract_structured(result.get("text", ""))
    if parsed is not None:
        result["parsed"] = parsed
    return result
