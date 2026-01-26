"""
Content API Endpoints

Lists ingested content for a user with a lightweight v1 ranker.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.db import fetch, fetchrow

router = APIRouter()


def _rank_v1(item: dict) -> float:
    """Lightweight heuristic ranker (v1)."""
    uploaded_at = item.get("uploaded_at")
    if uploaded_at is None:
        recency = 0.0
    else:
        now = datetime.now(timezone.utc)
        delta = now - uploaded_at
        days = max(delta.total_seconds() / 86400.0, 0.0)
        recency = 1.0 / (1.0 + days)

    status = (item.get("status") or "").upper()
    if status == "PROCESSED":
        status_score = 1.0
    elif status == "PROCESSING":
        status_score = 0.5
    elif status == "UNPROCESSED":
        status_score = 0.2
    else:
        status_score = 0.0

    has_artifact = 1.0 if item.get("has_artifact") else 0.0

    score = (0.7 * recency) + (0.2 * status_score) + (0.1 * has_artifact)
    return round(score, 4)


@router.get("")
async def list_content(
    user_id: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    sort: str = Query("rank", pattern="^(rank|uploaded_at)$"),
    ranker: str = Query("v1", pattern="^(v1|none)$"),
):
    """
    List content for a user.

    sort=rank uses a lightweight v1 ranker (recency + status + has_artifact).
    """
    status_filter = ""
    params = [user_id]
    if status:
        status_filter = "AND um.status = $2"
        params.append(status)

    base_query = f"""
        SELECT
            um.id AS user_material_id,
            um.user_id,
            um.content_id,
            um.status,
            um.storage_path,
            um.uploaded_at,
            ci.content_hash,
            ci.title,
            ci.media_type,
            ci.word_count,
            ci.topics,
            LEFT(ci.raw_text, 400) AS preview,
            ci.created_at AS content_created_at,
            EXISTS (
                SELECT 1
                FROM artifacts a
                WHERE a.user_id = um.user_id
                  AND um.content_id = ANY(a.content_ids)
            ) AS has_artifact
        FROM user_materials um
        JOIN content_items ci ON ci.id = um.content_id
        WHERE um.user_id = $1
        {status_filter}
        ORDER BY um.uploaded_at DESC
        LIMIT ${{limit_param}} OFFSET ${{offset_param}}
    """

    try:
        if sort == "rank":
            # Rank on a small window for speed; pagination is best-effort for v1.
            window_limit = min(max(limit * 5, limit), 200)
            limit_param = len(params) + 1
            offset_param = len(params) + 2
            query = base_query.format(limit_param=limit_param, offset_param=offset_param)
            rows = await fetch(query, *params, window_limit, offset)
        else:
            limit_param = len(params) + 1
            offset_param = len(params) + 2
            query = base_query.format(limit_param=limit_param, offset_param=offset_param)
            rows = await fetch(query, *params, limit, offset)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    items = []
    for row in rows:
        item = dict(row)
        item["content_id"] = str(item["content_id"])
        item["user_material_id"] = str(item["user_material_id"])
        item["uploaded_at"] = item["uploaded_at"]
        item["content_created_at"] = item["content_created_at"]
        if ranker == "v1":
            item["rank_score"] = _rank_v1(item)
        items.append(item)

    if sort == "rank" and ranker == "v1":
        items.sort(key=lambda x: x.get("rank_score", 0.0), reverse=True)

    return {
        "user_id": user_id,
        "ranker": ranker,
        "sort": sort,
        "count": len(items[:limit]),
        "items": items[:limit],
    }


@router.get("/{content_id}")
async def get_content(
    content_id: str,
    user_id: str = Query(...),
    include_raw: bool = Query(False),
):
    """Get a specific content item (must belong to user)."""
    query = """
        SELECT
            um.id AS user_material_id,
            um.user_id,
            um.content_id,
            um.status,
            um.storage_path,
            um.uploaded_at,
            ci.content_hash,
            ci.title,
            ci.media_type,
            ci.word_count,
            ci.raw_text,
            ci.topics,
            ci.created_at AS content_created_at
        FROM user_materials um
        JOIN content_items ci ON ci.id = um.content_id
        WHERE um.user_id = $1 AND um.content_id = $2
        LIMIT 1
    """
    try:
        row = await fetchrow(query, user_id, content_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")
    if not row:
        raise HTTPException(status_code=404, detail="Content not found")

    item = dict(row)
    item["content_id"] = str(item["content_id"])
    item["user_material_id"] = str(item["user_material_id"])
    if not include_raw:
        item.pop("raw_text", None)

    return item
