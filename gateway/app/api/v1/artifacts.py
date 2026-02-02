"""
Artifacts API Endpoints

Reads artifacts directly from the database.
"""

import json
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query

from app.db import fetch, fetchrow

router = APIRouter()


@router.get("")
async def list_artifacts(
    user_id: str = Query(...),
    artifact_type: Optional[str] = Query(None, alias="type")
):
    """List artifacts for a user."""
    params = [user_id]
    filters = ["user_id = $1"]
    if artifact_type:
        filters.append("artifact_type = $2")
        params.append(artifact_type)

    query = f"""
        SELECT id, artifact_type, estimated_minutes, created_at, content_ids, content
        FROM artifacts
        WHERE {' AND '.join(filters)}
        ORDER BY created_at DESC
        LIMIT 50
    """
    try:
        rows = await fetch(query, *params)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    items: list[Dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["id"] = str(item["id"])
        if item.get("content_ids") is not None:
            item["content_ids"] = [str(cid) for cid in item["content_ids"]]
        if item.get("content"):
            snippet = item["content"].strip().splitlines()[0][:140]
            item["title"] = snippet or f"Material ({item.get('artifact_type')})"
        items.append(item)

    return {"user_id": user_id, "count": len(items), "items": items}


@router.get("/{artifact_id}")
async def get_artifact(artifact_id: str):
    """Get a specific artifact by ID."""
    query = "SELECT * FROM artifacts WHERE id = $1"
    try:
        row = await fetchrow(query, artifact_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Artifact not found")

    result = dict(row)
    result["id"] = str(result["id"])
    if result.get("content_ids") is not None:
        result["content_ids"] = [str(cid) for cid in result["content_ids"]]
    if isinstance(result.get("metadata"), str):
        try:
            result["metadata"] = json.loads(result["metadata"])
        except Exception:
            pass
    return result
