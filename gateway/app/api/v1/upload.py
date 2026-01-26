"""
Upload API Endpoints

Handles file upload and triggers ingestion agent.
"""

import hashlib
import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.a2a.client import get_a2a_client

router = APIRouter()


def _enqueue_proactive_generation(user_id: str, content_id: str):
    """Enqueue proactive 5min generation after upload (background, not blocking)."""
    try:
        from workers.queue import enqueue_generation
        enqueue_generation(user_id, content_id, "5min", high_priority=False)
    except Exception as e:
        # Don't fail upload if queue is unavailable
        print(f"Warning: Failed to enqueue generation: {e}")


@router.post("")
async def upload_files(
    user_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Upload files for processing.
    
    Triggers the Ingestion Agent to:
    1. Parse the file content
    2. Extract topics
    3. Generate embeddings
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    a2a_client = await get_a2a_client()
    
    for file in files:
        content = await file.read()
        content_hash = hashlib.sha256(content).hexdigest()
        
        # Determine media type
        media_type = "TXT"
        if file.filename:
            ext = file.filename.lower().split(".")[-1]
            media_type_map = {
                "pdf": "PDF", "txt": "TXT", "md": "MARKDOWN",
                "mp3": "AUDIO", "wav": "AUDIO", "mp4": "VIDEO",
            }
            media_type = media_type_map.get(ext, "TXT")
        
        # Decode content as text
        try:
            content_text = content.decode("utf-8", errors="ignore")
        except:
            content_text = ""
        
        task_id = str(uuid.uuid4())
        
        # Send to ADK Ingestion Agent with natural language message
        message = f"""Please ingest this content using the ingest_content tool:
- user_id: {user_id}
- content_hash: {content_hash}
- filename: {file.filename}
- media_type: {media_type}
- content_text: {content_text[:10000]}"""
        
        response = await a2a_client.run_agent(
            agent_name="ingestion",
            message=message,
            user_id=user_id,
            session_id=task_id
        )
        
        if response.error_data:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": response.error_data.get("message", "Unknown error")
            })
        else:
            # Extract content_id from response for proactive generation
            content_id = None
            if isinstance(response.result, dict):
                content_id = response.result.get("content_id")
            
            results.append({
                "filename": file.filename,
                "status": "processing",
                "task_id": task_id,
                "content_id": content_id,
                "response": response.result
            })
            
            # Proactive: queue 5-min summary generation (NEW content philosophy)
            if content_id:
                _enqueue_proactive_generation(user_id, content_id)
    
    return {
        "user_id": user_id,
        "uploaded": len(results),
        "results": results
    }


@router.get("/status/{task_id}")
async def get_upload_status(task_id: str):
    """Check the status of an upload/ingestion task."""
    a2a_client = await get_a2a_client()
    status = await a2a_client.get_task_status("ingestion", task_id)
    
    if status is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return status
