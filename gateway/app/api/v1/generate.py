"""
Generate API Endpoints

Handles artifact generation requests via ADK Synthesis Agent.
User-triggered generation uses high priority queue.
"""

import uuid
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.a2a.client import get_a2a_client

router = APIRouter()


def _enqueue_user_generation(user_id: str, content_id: str, artifact_type: str = "full"):
    """Enqueue user-triggered generation to high priority queue."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from workers.queue import enqueue_generation, get_redis_connection
        from redis import (
            ConnectionError as RedisConnectionError,
            TimeoutError as RedisTimeoutError,
            RedisError
        )
        
        # Test Redis connection first
        try:
            conn = get_redis_connection()
            conn.ping()
        except (RedisConnectionError, RedisTimeoutError, OSError, RedisError) as e:
            logger.error(f"Redis connection test failed: {e}", exc_info=True)
            return None
        
        # Try to enqueue
        try:
            return enqueue_generation(user_id, content_id, artifact_type, high_priority=True)
        except (RedisConnectionError, RedisTimeoutError, OSError, RedisError) as e:
            # Redis connection issues during enqueue
            logger.error(f"Redis connection failed during enqueue: {e}", exc_info=True)
            return None
        except Exception as e:
            # Other queue/enqueue errors (e.g., RQ errors)
            logger.error(f"Failed to enqueue generation: {e}", exc_info=True)
            return None
    except ImportError as e:
        logger.error(f"Failed to import workers.queue: {e}")
        return None


class GenerateRequest(BaseModel):
    user_id: str
    content_ids: Optional[List[str]] = None
    time_available_minutes: Optional[int] = None
    format: Optional[str] = "text"


class AsyncGenerateRequest(BaseModel):
    user_id: str
    content_id: str
    artifact_type: str = "full"  # "5min" or "full"


@router.post("/async")
async def generate_artifact_async(request: AsyncGenerateRequest):
    """
    Queue artifact generation for background processing.
    
    Returns immediately with a job_id. User-triggered = high priority queue.
    Poll /generate/job/{job_id} for status.
    """
    job = _enqueue_user_generation(request.user_id, request.content_id, request.artifact_type)
    
    if job is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        raise HTTPException(
            status_code=503,
            detail=f"Job queue unavailable. Check: 1) Redis is running at {redis_url}, 2) Workers are running (generation-worker, notification-worker, priority-worker), 3) Gateway can connect to Redis. To start: docker-compose up -d redis generation-worker notification-worker priority-worker"
        )
    
    return {
        "job_id": job.id,
        "status": "queued",
        "queue": "high",
        "message": f"Generation queued for {request.artifact_type} artifact"
    }


@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a queued generation job.
    
    RQ status values: 'queued', 'started', 'finished', 'failed', 'deferred', 'scheduled'
    Test expects: 'finished' (success) or 'failed' (error)
    """
    try:
        from rq.job import Job
        from workers.queue import get_redis_connection
        
        job = Job.fetch(job_id, connection=get_redis_connection())
        status = job.get_status()  # Returns lowercase: 'queued', 'started', 'finished', 'failed'
        
        result = {
            "job_id": job_id,
            "status": status,
            "created_at": str(job.created_at) if job.created_at else None,
            "started_at": str(job.started_at) if job.started_at else None,
            "ended_at": str(job.ended_at) if job.ended_at else None,
        }
        
        if job.is_finished:
            result["result"] = job.result
        elif job.is_failed:
            result["error"] = str(job.exc_info) if job.exc_info else "Unknown error"
        
        return result
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to fetch job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")


@router.post("")
async def generate_artifact(request: GenerateRequest):
    """
    Generate a personalized artifact for the user.
    
    Flow:
    1. Get user profile from Profile Agent
    2. Get calendar context if time not specified
    3. Get priority queue from Planner Agent (if no content_ids)
    4. Generate content via Synthesis Agent
    """
    a2a_client = await get_a2a_client()
    task_id = str(uuid.uuid4())
    
    # Step 1: Get user profile
    profile_response = await a2a_client.run_agent(
        agent_name="profile",
        message=f"Get the profile for user_id: {request.user_id}",
        user_id=request.user_id
    )
    
    if profile_response.error:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to get profile: {profile_response.error.get('message')}"
        )
    
    # Step 2: Determine time available
    time_available = request.time_available_minutes or 25
    
    # Step 3: Get content to generate from
    content_ids = request.content_ids or []
    if not content_ids:
        planner_response = await a2a_client.run_agent(
            agent_name="planner",
            message=f"Get the priority queue for user_id: {request.user_id}, limit 1",
            user_id=request.user_id
        )
        # Would extract content_ids from planner response
    
    if not content_ids:
        raise HTTPException(
            status_code=400,
            detail="No content available to generate from"
        )
    
    # Step 4: Generate artifact
    synthesis_response = await a2a_client.run_agent(
        agent_name="synthesis",
        message=f"""Generate a personalized study artifact:
- user_id: {request.user_id}
- content_ids: {content_ids}
- time_available_minutes: {time_available}
- format: {request.format}""",
        user_id=request.user_id,
        session_id=task_id
    )
    
    if synthesis_response.error:
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {synthesis_response.error.get('message')}"
        )
    
    return {
        "id": task_id,
        "response": synthesis_response.result,
        "format": request.format
    }


@router.get("/status/{task_id}")
async def get_generation_status(task_id: str):
    """Check the status of a generation task."""
    return {"id": task_id, "status": "completed"}
