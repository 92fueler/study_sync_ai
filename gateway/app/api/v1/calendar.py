"""
Calendar API Endpoints

Local-first calendar for hackathon UI; external integration is stubbed.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db import fetch, fetchrow

router = APIRouter()


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class CalendarAccountCreate(BaseModel):
    user_id: str
    provider: str
    email: Optional[str] = None
    status: Optional[str] = "connected"
    auth_data: Optional[Dict[str, Any]] = None


class CalendarCreate(BaseModel):
    user_id: str
    provider: str = "local"
    external_id: Optional[str] = None
    name: str
    is_primary: Optional[bool] = False


class CalendarEventCreate(BaseModel):
    user_id: str
    provider: Optional[str] = "local"
    calendar_id: Optional[str] = None
    external_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    metadata: Optional[Dict[str, Any]] = None


@router.get("/accounts")
async def list_accounts(user_id: str = Query(...)):
    """List calendar accounts for a user."""
    query = "SELECT * FROM calendar_accounts WHERE user_id = $1 ORDER BY created_at DESC"
    try:
        rows = await fetch(query, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    items = [dict(row) for row in rows]
    for item in items:
        item["id"] = str(item["id"])
    return {"user_id": user_id, "items": items}


@router.post("/accounts")
async def create_account(request: CalendarAccountCreate):
    """Create/connect a calendar account (local stub)."""
    query = """
        INSERT INTO calendar_accounts (user_id, provider, email, status, auth_data)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
    """
    try:
        row = await fetchrow(
            query,
            request.user_id,
            request.provider,
            request.email,
            request.status,
            request.auth_data,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    result = dict(row)
    result["id"] = str(result["id"])
    return result


@router.post("/accounts/{account_id}/disconnect")
async def disconnect_account(account_id: str, user_id: str = Query(...)):
    """Disconnect a calendar account."""
    query = """
        UPDATE calendar_accounts
        SET status = 'disconnected', updated_at = NOW()
        WHERE id = $1 AND user_id = $2
        RETURNING *
    """
    try:
        row = await fetchrow(query, account_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Account not found")

    result = dict(row)
    result["id"] = str(result["id"])
    return result


@router.get("/calendars")
async def list_calendars(user_id: str = Query(...)):
    """List calendars for a user."""
    query = "SELECT * FROM calendar_calendars WHERE user_id = $1 ORDER BY created_at DESC"
    try:
        rows = await fetch(query, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    items = [dict(row) for row in rows]
    for item in items:
        item["id"] = str(item["id"])
    return {"user_id": user_id, "items": items}


@router.post("/calendars")
async def create_calendar(request: CalendarCreate):
    """Create a calendar entry."""
    query = """
        INSERT INTO calendar_calendars (user_id, provider, external_id, name, is_primary)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
    """
    try:
        row = await fetchrow(
            query,
            request.user_id,
            request.provider,
            request.external_id,
            request.name,
            request.is_primary,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    result = dict(row)
    result["id"] = str(result["id"])
    return result


@router.get("/events")
async def list_events(
    user_id: str = Query(...),
    time_min: Optional[str] = Query(None),
    time_max: Optional[str] = Query(None),
    calendar_id: Optional[str] = Query(None),
):
    """List calendar events in a time window."""
    filters: List[str] = ["user_id = $1"]
    params: List[Any] = [user_id]
    idx = 2

    if calendar_id:
        filters.append(f"calendar_id = ${idx}")
        params.append(calendar_id)
        idx += 1
    if time_min:
        filters.append(f"end_time >= ${idx}")
        params.append(_parse_dt(time_min))
        idx += 1
    if time_max:
        filters.append(f"start_time <= ${idx}")
        params.append(_parse_dt(time_max))
        idx += 1

    query = f"""
        SELECT * FROM calendar_events
        WHERE {' AND '.join(filters)}
        ORDER BY start_time ASC
    """

    try:
        rows = await fetch(query, *params)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    items = [dict(row) for row in rows]
    for item in items:
        item["id"] = str(item["id"])
        if item.get("calendar_id"):
            item["calendar_id"] = str(item["calendar_id"])
    return {"user_id": user_id, "items": items}


@router.post("/events")
async def create_event(request: CalendarEventCreate):
    """Create a calendar event."""
    query = """
        INSERT INTO calendar_events
            (user_id, provider, calendar_id, external_id, title, description, start_time, end_time, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
    """
    try:
        row = await fetchrow(
            query,
            request.user_id,
            request.provider,
            request.calendar_id,
            request.external_id,
            request.title,
            request.description,
            request.start_time,
            request.end_time,
            request.metadata,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    result = dict(row)
    result["id"] = str(result["id"])
    if result.get("calendar_id"):
        result["calendar_id"] = str(result["calendar_id"])
    return result


@router.delete("/events/{event_id}")
async def delete_event(event_id: str, user_id: str = Query(...)):
    """Delete a calendar event."""
    query = "DELETE FROM calendar_events WHERE id = $1 AND user_id = $2 RETURNING id"
    try:
        row = await fetchrow(query, event_id, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Event not found")

    return {"success": True}


@router.get("/availability")
async def get_availability(
    user_id: str = Query(...),
    time_min: str = Query(...),
    time_max: str = Query(...),
    duration_min: int = Query(25, ge=5, le=240),
    step_min: int = Query(30, ge=5, le=240),
):
    """Get available time slots between time_min and time_max."""
    start = _parse_dt(time_min)
    end = _parse_dt(time_max)
    duration = timedelta(minutes=duration_min)
    step = timedelta(minutes=step_min)

    query = """
        SELECT start_time, end_time
        FROM calendar_events
        WHERE user_id = $1 AND start_time < $2 AND end_time > $3
        ORDER BY start_time ASC
    """
    try:
        rows = await fetch(query, user_id, end, start)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    events = [(row["start_time"], row["end_time"]) for row in rows]

    slots: List[str] = []
    cursor = start
    while cursor + duration <= end:
        slot_end = cursor + duration
        overlaps = False
        for event_start, event_end in events:
            if cursor < event_end and slot_end > event_start:
                overlaps = True
                break
        if not overlaps:
            slots.append(cursor.isoformat())
        cursor += step

    return {"user_id": user_id, "slots": slots}
