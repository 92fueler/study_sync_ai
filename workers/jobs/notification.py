"""
Notification jobs for RQ workers.

Handles sending notifications via various channels.
"""

import os
import logging
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ORCHESTRATOR_AGENT_URL = os.getenv("ORCHESTRATOR_AGENT_URL", "http://localhost:8005")


def send_notification(user_id: str, title: str, body: str, data: dict = None, channel: str = "in_app") -> dict:
    """
    Send a notification to a user.
    
    Args:
        user_id: User identifier
        title: Notification title
        body: Notification body text
        data: Optional metadata for deep linking
        channel: "in_app", "push", or "email"
    
    Returns:
        Dict with notification_id and status
    """
    logger.info(f"Sending {channel} notification to user={user_id}: {title}")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{ORCHESTRATOR_AGENT_URL}/a2a/tasks/send",
                json={
                    "jsonrpc": "2.0",
                    "method": "tasks/send",
                    "params": {
                        "id": f"notify-{user_id}",
                        "message": {
                            "role": "user",
                            "parts": [{"text": str({
                                "action": "create_notification",
                                "user_id": user_id,
                                "title": title,
                                "body": body,
                                "channel": channel,
                                "data": data
                            })}]
                        }
                    }
                }
            )
            result = response.json()
            
            if "result" in result:
                logger.info(f"Notification sent to user={user_id}")
                return {"status": "success", "notification_id": result["result"].get("notification_id")}
            else:
                raise Exception(f"Notification failed: {result.get('error')}")
                
    except Exception as e:
        logger.error(f"Failed to send notification to user={user_id}: {e}")
        raise


def send_push_notification(user_id: str, title: str, body: str, data: dict = None) -> dict:
    """Send a push notification (requires FCM token)."""
    return send_notification(user_id, title, body, data, channel="push")


def send_email_notification(user_id: str, title: str, body: str, data: dict = None) -> dict:
    """Send an email notification."""
    return send_notification(user_id, title, body, data, channel="email")
