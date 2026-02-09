"""
Audio API Endpoints

Handles audio generation and streaming.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
from pathlib import Path

router = APIRouter()
REPO_ROOT = Path(__file__).resolve().parents[4]
AUDIO_DIR = REPO_ROOT / "storage" / "audio"


def _resolve_audio_path(path_or_filename: str) -> Path:
    """Resolve DB-stored or URL-provided audio path to a safe absolute path."""
    value = (path_or_filename or "").strip()
    if not value:
        return AUDIO_DIR / "__missing__"

    candidate = Path(value)
    if not candidate.is_absolute():
        # Legacy rows may store "storage/audio/..." and URL input may be only filename.
        if "/" in value or "\\" in value:
            candidate = REPO_ROOT / candidate
        else:
            candidate = AUDIO_DIR / candidate.name
    resolved = candidate.resolve()

    # Prevent path traversal outside configured audio directory.
    if AUDIO_DIR.resolve() not in resolved.parents and resolved != AUDIO_DIR.resolve():
        return AUDIO_DIR / "__invalid__"
    return resolved


class AudioGenerateRequest(BaseModel):
    voice_name: Optional[str] = "Kore"
    cognitive_tone: Optional[str] = None


@router.post("/generate/{artifact_id}")
async def generate_audio(
    artifact_id: str,
    request: AudioGenerateRequest = AudioGenerateRequest()
):
    """
    Generate audio for an existing artifact.
    
    Args:
        artifact_id: UUID of the artifact
        request: Audio generation parameters
    
    Returns:
        Audio metadata including URL
    """
    from app.a2a.client import get_a2a_client
    
    a2a_client = await get_a2a_client()
    
    # Call Synthesis Agent to generate audio
    message = f"""Generate audio for artifact {artifact_id}.
    
Use the generate_audio tool with these parameters:
- artifact_id: {artifact_id}
- voice_name: {request.voice_name}
- cognitive_tone: {request.cognitive_tone}

Return the audio metadata."""
    
    response = await a2a_client.run_agent(
        agent_name="synthesis",
        message=message,
        user_id="system"
    )
    
    if response.error:
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {response.error.get('message', 'Unknown error')}")
    
    return response.result


@router.get("/{filename}")
async def stream_audio(filename: str):
    """
    Stream audio file.
    
    Args:
        filename: Audio filename (e.g., artifact-id_Kore.wav)
    
    Returns:
        Audio file as streaming response
    """
    audio_path = _resolve_audio_path(filename)
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        str(audio_path),
        media_type="audio/wav",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Disposition": f"inline; filename={filename}"
        }
    )


@router.get("/metadata/{artifact_id}")
async def get_audio_metadata(artifact_id: str):
    """
    Get audio metadata for an artifact.
    
    Args:
        artifact_id: UUID of the artifact
    
    Returns:
        Audio metadata if exists
    """
    import asyncpg
    import os
    
    dsn = os.getenv("SUPABASE_URL", "")
    conn = await asyncpg.connect(dsn)
    
    try:
        row = await conn.fetchrow(
            """
            SELECT audio_path, voice_name, duration_seconds, file_size_bytes, generated_at
            FROM audio_artifacts
            WHERE artifact_id = $1
            """,
            artifact_id
        )
        
        if not row:
            raise HTTPException(status_code=404, detail="Audio not found for this artifact")
        
        # Extract filename from path
        filename = os.path.basename(row['audio_path'])
        
        return {
            "audio_url": f"/api/v1/audio/{filename}",
            "voice_name": row['voice_name'],
            "duration_seconds": row['duration_seconds'],
            "file_size_bytes": row['file_size_bytes'],
            "generated_at": str(row['generated_at'])
        }
    finally:
        await conn.close()


@router.delete("/{artifact_id}")
async def delete_audio(artifact_id: str):
    """
    Delete audio for an artifact.
    
    Args:
        artifact_id: UUID of the artifact
    
    Returns:
        Success message
    """
    import asyncpg
    import os
    
    dsn = os.getenv("SUPABASE_URL", "")
    conn = await asyncpg.connect(dsn)
    
    try:
        # Get audio path before deleting
        row = await conn.fetchrow(
            "SELECT audio_path FROM audio_artifacts WHERE artifact_id = $1",
            artifact_id
        )
        
        if not row:
            raise HTTPException(status_code=404, detail="Audio not found")
        
        audio_path = _resolve_audio_path(str(row["audio_path"]))
        
        # Delete from database
        await conn.execute(
            "DELETE FROM audio_artifacts WHERE artifact_id = $1",
            artifact_id
        )
        
        # Update artifacts table
        await conn.execute(
            "UPDATE artifacts SET audio_url = NULL WHERE id = $1",
            artifact_id
        )
        
        # Delete file if exists
        if audio_path.exists():
            audio_path.unlink()
        
        return {"status": "success", "message": "Audio deleted"}
        
    finally:
        await conn.close()
