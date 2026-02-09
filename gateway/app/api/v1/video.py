"""
Video API Endpoints

Handles video generation, metadata retrieval, and streaming.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncpg
import os
import logging
from pathlib import Path
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[4]
VIDEO_DIR = REPO_ROOT / "storage" / "video"


def _resolve_video_path(path_or_filename: str) -> Path:
    """Resolve DB-stored or URL-provided video path to an absolute repo-safe path."""
    value = (path_or_filename or "").strip()
    if not value:
        return VIDEO_DIR / "__missing__"

    candidate = Path(value)
    if not candidate.is_absolute():
        if "/" in value or "\\" in value:
            candidate = REPO_ROOT / candidate
        else:
            candidate = VIDEO_DIR / candidate.name
    resolved = candidate.resolve()
    if VIDEO_DIR.resolve() not in resolved.parents and resolved != VIDEO_DIR.resolve():
        return VIDEO_DIR / "__invalid__"
    return resolved


class VideoGenerateRequest(BaseModel):
    user_id: str
    total_duration: int = 120


def _derive_error_code(error_message: Optional[str]) -> Optional[str]:
    if not error_message:
        return None
    lower = error_message.lower()
    if "429" in lower or "resource_exhausted" in lower or "quota" in lower:
        return "quota_exceeded"
    return None


@router.get("/metadata/{artifact_id}")
async def get_video_metadata(artifact_id: str):
    """Get video metadata for an artifact"""
    dsn = os.getenv("SUPABASE_URL")
    logger.info("Fetching video metadata", extra={"artifact_id": artifact_id})
    conn = await asyncpg.connect(dsn)
    
    try:
        row = await conn.fetchrow(
            """
            SELECT id, video_path, duration_seconds, file_size_bytes,
                   resolution, aspect_ratio, status, error_message, generated_at
            FROM video_artifacts
            WHERE artifact_id = $1
            """,
            artifact_id
        )
        
        if not row:
            logger.info("Video metadata not found", extra={"artifact_id": artifact_id})
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Calculate progress if generating
        progress = 0
        current_segment = 0
        total_segments = 0
        
        if row['status'] == 'ready':
            progress = 100
        elif row['status'] == 'generating':
            # Get segment counts
            segments = await conn.fetch(
                "SELECT status FROM video_segments WHERE video_artifact_id = $1",
                row['id']  # row['id'] is the video_artifact_id
            )
            total_segments = len(segments)
            completed_segments = sum(1 for s in segments if s['status'] == 'ready')
            
            if total_segments > 0:
                # 90% for generation, 10% for stitching
                progress = int((completed_segments / total_segments) * 90)
                current_segment = completed_segments + 1
        
        filename = os.path.basename(row['video_path'])
        
        payload = {
            "status": row['status'],
            "video_url": f"/api/v1/video/{filename}" if row['status'] == 'ready' else None,
            "duration_seconds": row['duration_seconds'],
            "file_size_bytes": row['file_size_bytes'],
            "resolution": row['resolution'],
            "aspect_ratio": row['aspect_ratio'],
            "generated_at": str(row['generated_at']),
            "error_message": row["error_message"],
            "error_code": _derive_error_code(row["error_message"]),
            "progress": progress,
            "current_segment": current_segment,
            "total_segments": total_segments
        }
        logger.info(
            "Video metadata loaded",
            extra={
                "artifact_id": artifact_id,
                "status": payload["status"],
                "error_code": payload["error_code"],
                "progress": payload["progress"],
                "video_url": payload["video_url"],
            },
        )
        return payload
    finally:
        await conn.close()


@router.post("/generate/{artifact_id}")
async def generate_video(
    artifact_id: str,
    request: VideoGenerateRequest,
    retry: bool = Query(False),
    force: bool = Query(False),
):
    """
    Trigger video generation for an existing artifact.
    """
    from app.a2a.client import get_a2a_client

    if retry:
        dsn = os.getenv("SUPABASE_URL")
        conn = await asyncpg.connect(dsn)
        try:
            existing = await conn.fetchrow(
                "SELECT id, status FROM video_artifacts WHERE artifact_id = $1",
                artifact_id,
            )
            if existing:
                if existing["status"] == "generating" and not force:
                    raise HTTPException(
                        status_code=409,
                        detail="Video is still generating. Use force=true to reset and retry anyway.",
                    )
                await conn.execute("DELETE FROM video_artifacts WHERE artifact_id = $1", artifact_id)
                logger.info(
                    "Cleared existing video state for retry",
                    extra={"artifact_id": artifact_id, "prior_status": existing["status"], "force": force},
                )
        finally:
            await conn.close()

    a2a_client = await get_a2a_client()
    message = f"""Generate video for artifact {artifact_id}.

Use the generate_video tool with these parameters:
- artifact_id: {artifact_id}
- user_id: {request.user_id}
- total_duration: {request.total_duration}

Return the video job metadata."""

    response = await a2a_client.run_agent(
        agent_name="synthesis",
        message=message,
        user_id=request.user_id
    )
    logger.info(
        "Video generation trigger sent",
        extra={
            "artifact_id": artifact_id,
            "user_id": request.user_id,
            "duration": request.total_duration,
            "retry": retry,
            "force": force,
        },
    )

    if response.error:
        logger.error(
            "Video generation trigger failed",
            extra={"artifact_id": artifact_id, "user_id": request.user_id, "error": response.error},
        )
        raise HTTPException(
            status_code=500,
            detail=f"Video generation failed: {response.error.get('message', 'Unknown error')}",
        )

    logger.info(
        "Video generation trigger accepted",
        extra={"artifact_id": artifact_id, "user_id": request.user_id},
    )
    return response.result


@router.get("/{filename}")
async def stream_video(filename: str):
    """Stream video file"""
    video_path = _resolve_video_path(filename)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        str(video_path),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Disposition": f"inline; filename={filename}"
        }
    )
