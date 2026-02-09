"""
Video API Endpoints

Handles video generation, metadata retrieval, and streaming.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncpg
import os
from pathlib import Path

router = APIRouter()
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


@router.get("/metadata/{artifact_id}")
async def get_video_metadata(artifact_id: str):
    """Get video metadata for an artifact"""
    dsn = os.getenv("SUPABASE_URL")
    conn = await asyncpg.connect(dsn)
    
    try:
        row = await conn.fetchrow(
            """
            SELECT id, video_path, duration_seconds, file_size_bytes,
                   resolution, aspect_ratio, status, generated_at
            FROM video_artifacts
            WHERE artifact_id = $1
            """,
            artifact_id
        )
        
        if not row:
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
        
        return {
            "status": row['status'],
            "video_url": f"/api/v1/video/{filename}" if row['status'] == 'ready' else None,
            "duration_seconds": row['duration_seconds'],
            "file_size_bytes": row['file_size_bytes'],
            "resolution": row['resolution'],
            "aspect_ratio": row['aspect_ratio'],
            "generated_at": str(row['generated_at']),
            "progress": progress,
            "current_segment": current_segment,
            "total_segments": total_segments
        }
    finally:
        await conn.close()


@router.post("/generate/{artifact_id}")
async def generate_video(artifact_id: str, request: VideoGenerateRequest):
    """
    Trigger video generation for an existing artifact.
    """
    from app.a2a.client import get_a2a_client

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

    if response.error:
        raise HTTPException(
            status_code=500,
            detail=f"Video generation failed: {response.error.get('message', 'Unknown error')}",
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
