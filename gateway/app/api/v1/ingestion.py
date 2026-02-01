"""
Ingestion API Endpoints

Tracks ingestion jobs for UI processing states (non-agent).
"""

from typing import Any, Dict, List, Optional

import json

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db import fetch, fetchrow

router = APIRouter()


class IngestionCreate(BaseModel):
    user_id: str
    name: str
    job_type: str
    status: str = "ingesting"
    progress: Optional[int] = 0
    metadata: Optional[Dict[str, Any]] = None


class IngestionUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


def _job_row_to_dict(row) -> Dict[str, Any]:
    job = dict(row)
    job["id"] = str(job["id"])
    job["created_at"] = job.get("created_at")
    job["updated_at"] = job.get("updated_at")
    if isinstance(job.get("metadata"), str):
        try:
            job["metadata"] = json.loads(job["metadata"])
        except Exception:
            pass
    return job


@router.get("/processing")
async def list_processing_jobs(
    user_id: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List ingestion jobs for the processing UI."""
    query = """
        SELECT * FROM ingestion_jobs
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
    """
    try:
        rows = await fetch(query, user_id, limit, offset)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    return {"user_id": user_id, "count": len(rows), "items": [_job_row_to_dict(row) for row in rows]}


@router.post("")
async def create_ingestion_job(request: IngestionCreate):
    """Create an ingestion job record."""
    query = """
        INSERT INTO ingestion_jobs (user_id, name, job_type, status, progress, metadata)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
    """
    try:
        metadata_payload = json.dumps(request.metadata) if request.metadata is not None else None
        row = await fetchrow(
            query,
            request.user_id,
            request.name,
            request.job_type,
            request.status,
            request.progress,
            metadata_payload,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    return _job_row_to_dict(row)


@router.patch("/{job_id}")
async def update_ingestion_job(job_id: str, user_id: str = Query(...), update: IngestionUpdate = ...):
    """Update status/progress for an ingestion job."""
    update = update or IngestionUpdate()
    updates: List[str] = []
    params: List[Any] = []
    idx = 1

    for field, value in update.model_dump(exclude_unset=True).items():
        if field == "metadata" and value is not None:
            value = json.dumps(value)
        updates.append(f"{field} = ${idx}")
        params.append(value)
        idx += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = NOW()")
    query = f"""
        UPDATE ingestion_jobs
        SET {', '.join(updates)}
        WHERE id = ${idx} AND user_id = ${idx + 1}
        RETURNING *
    """
    try:
        row = await fetchrow(query, *params, job_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    return _job_row_to_dict(row)
