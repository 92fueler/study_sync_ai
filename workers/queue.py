"""
RQ queue configuration and helpers.

Queue priority:
- high: User-triggered jobs (immediate processing)
- default: Proactive background jobs
- low: Batch/maintenance jobs

Workers process high → default → low in order.
"""

import os
from redis import Redis
from rq import Queue


def get_redis_connection() -> Redis:
    """Get Redis connection from environment."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return Redis.from_url(redis_url)


def get_queue(name: str = "default") -> Queue:
    """Get an RQ queue by name."""
    return Queue(name, connection=get_redis_connection())


def get_high_queue() -> Queue:
    """Get high priority queue for user-triggered jobs."""
    return get_queue("high")


def get_default_queue() -> Queue:
    """Get default queue for proactive background jobs."""
    return get_queue("default")


def get_low_queue() -> Queue:
    """Get low priority queue for batch/maintenance."""
    return get_queue("low")


def enqueue_generation(user_id: str, content_id: str, job_type: str = "5min", high_priority: bool = False):
    """
    Enqueue a generation job.
    
    Args:
        user_id: User identifier
        content_id: Content to generate artifact for
        job_type: "5min" or "full"
        high_priority: True for user-triggered (high queue), False for proactive (default queue)
    """
    from workers.jobs.generation import generate_artifact
    
    queue = get_high_queue() if high_priority else get_default_queue()
    return queue.enqueue(
        generate_artifact,
        user_id=user_id,
        content_id=content_id,
        artifact_type=job_type,
        job_timeout="10m"
    )


def enqueue_regeneration(user_id: str, artifact_id: str):
    """Enqueue artifact regeneration (always high priority - user requested)."""
    from workers.jobs.generation import regenerate_artifact
    
    return get_high_queue().enqueue(
        regenerate_artifact,
        user_id=user_id,
        artifact_id=artifact_id,
        job_timeout="10m"
    )


def enqueue_priority_recalc(user_id: str):
    """Enqueue priority recalculation (low priority batch job)."""
    from workers.jobs.priority import recalculate_priority
    
    return get_low_queue().enqueue(
        recalculate_priority,
        user_id=user_id,
        job_timeout="5m"
    )


def enqueue_notification(user_id: str, title: str, body: str, data: dict = None):
    """Enqueue notification (low priority)."""
    from workers.jobs.notification import send_notification
    
    return get_low_queue().enqueue(
        send_notification,
        user_id=user_id,
        title=title,
        body=body,
        data=data,
        job_timeout="1m"
    )
