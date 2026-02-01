"""
Calendar API Endpoints

Local-first calendar with optional one-time Google Calendar import.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import json
import os
import urllib.parse

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db import fetch, fetchrow

router = APIRouter()


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _google_oauth_config() -> Dict[str, str]:
    return {
        "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", ""),
        "redirect_uri": os.getenv(
            "GOOGLE_OAUTH_REDIRECT_URI",
            "http://localhost:8000/api/v1/calendar/google/callback",
        ),
    }


def _require_google_config() -> Dict[str, str]:
    config = _google_oauth_config()
    if not config["client_id"] or not config["client_secret"]:
        raise HTTPException(status_code=400, detail="Google OAuth client is not configured")
    return config


async def _refresh_google_token(auth_data: Dict[str, Any]) -> Dict[str, Any]:
    config = _google_oauth_config()
    refresh_token = auth_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Missing refresh token")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Token refresh failed: {response.text}")

    token_data = response.json()
    expires_at = datetime.utcnow().timestamp() + token_data.get("expires_in", 3600)
    auth_data.update(
        {
            "access_token": token_data.get("access_token"),
            "expires_at": expires_at,
            "token_type": token_data.get("token_type", "Bearer"),
        }
    )
    return auth_data


def _needs_refresh(auth_data: Dict[str, Any]) -> bool:
    expires_at = auth_data.get("expires_at")
    if not expires_at:
        return True
    return datetime.utcnow().timestamp() > float(expires_at) - 60


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


class GoogleCalendarSyncRequest(BaseModel):
    user_id: str
    time_min: Optional[str] = None
    time_max: Optional[str] = None
    calendar_id: Optional[str] = None


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


@router.get("/google/auth-url")
async def google_auth_url(user_id: str = Query(...)):
    """Return a Google OAuth consent URL for one-time calendar import."""
    config = _require_google_config()
    state = urllib.parse.quote_plus(json.dumps({"user_id": user_id}))
    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar.readonly",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return {"auth_url": url}


@router.get("/google/callback")
async def google_oauth_callback(code: str = Query(...), state: str = Query(...)):
    """OAuth callback to exchange code for tokens and store account."""
    config = _require_google_config()
    try:
        state_data = json.loads(urllib.parse.unquote_plus(state))
        user_id = state_data.get("user_id")
    except Exception:
        user_id = None
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid state")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "redirect_uri": config["redirect_uri"],
                "grant_type": "authorization_code",
            },
        )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Token exchange failed: {response.text}")

    token_data = response.json()
    expires_at = datetime.utcnow().timestamp() + token_data.get("expires_in", 3600)
    auth_payload = {
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "scope": token_data.get("scope"),
        "token_type": token_data.get("token_type", "Bearer"),
        "expires_at": expires_at,
    }

    query = """
        INSERT INTO calendar_accounts (user_id, provider, email, status, auth_data)
        VALUES ($1, 'google', $2, 'connected', $3)
        RETURNING *
    """
    try:
        row = await fetchrow(query, user_id, None, auth_payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    result = dict(row)
    result["id"] = str(result["id"])
    return result


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


@router.post("/google/sync")
async def google_sync(request: GoogleCalendarSyncRequest):
    """One-time Google Calendar import into local cache."""
    _require_google_config()

    account = await fetchrow(
        "SELECT * FROM calendar_accounts WHERE user_id = $1 AND provider = 'google' AND status = 'connected' ORDER BY created_at DESC LIMIT 1",
        request.user_id,
    )
    if not account:
        raise HTTPException(status_code=400, detail="No connected Google account")

    auth_data = account.get("auth_data") if isinstance(account.get("auth_data"), dict) else None
    if not auth_data:
        raise HTTPException(status_code=400, detail="Missing auth data")

    if _needs_refresh(auth_data):
        auth_data = await _refresh_google_token(auth_data)
        await fetchrow(
            "UPDATE calendar_accounts SET auth_data = $1, updated_at = NOW() WHERE id = $2 RETURNING id",
            auth_data,
            account["id"],
        )

    headers = {"Authorization": f"Bearer {auth_data['access_token']}"}
    time_min = request.time_min or (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
    time_max = request.time_max or (datetime.utcnow() + timedelta(days=90)).isoformat() + "Z"

    async with httpx.AsyncClient(timeout=30) as client:
        cal_response = await client.get(
            "https://www.googleapis.com/calendar/v3/users/me/calendarList",
            headers=headers,
        )
    if cal_response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Calendar list failed: {cal_response.text}")

    calendars = cal_response.json().get("items", [])
    if request.calendar_id:
        calendars = [c for c in calendars if c.get("id") == request.calendar_id]

    imported_events = 0
    imported_calendars = 0
    for cal in calendars:
        cal_id = cal.get("id")
        if not cal_id:
            continue
        existing_calendar = await fetchrow(
            "SELECT id FROM calendar_calendars WHERE user_id = $1 AND external_id = $2",
            request.user_id,
            cal_id,
        )
        if existing_calendar:
            calendar_id = existing_calendar["id"]
        else:
            row = await fetchrow(
                """
                INSERT INTO calendar_calendars (user_id, provider, external_id, name, is_primary)
                VALUES ($1, 'google', $2, $3, $4)
                RETURNING id
                """,
                request.user_id,
                cal_id,
                cal.get("summary") or "Google Calendar",
                cal.get("primary", False),
            )
            calendar_id = row["id"]
            imported_calendars += 1

        async with httpx.AsyncClient(timeout=30) as client:
            events_response = await client.get(
                "https://www.googleapis.com/calendar/v3/calendars/{}/events".format(
                    urllib.parse.quote_plus(cal_id)
                ),
                headers=headers,
                params={
                    "timeMin": time_min,
                    "timeMax": time_max,
                    "singleEvents": "true",
                    "orderBy": "startTime",
                    "maxResults": 250,
                },
            )
        if events_response.status_code != 200:
            continue
        events = events_response.json().get("items", [])
        for event in events:
            external_id = event.get("id")
            start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
            end = event.get("end", {}).get("dateTime") or event.get("end", {}).get("date")
            if not start or not end:
                continue

            existing_event = await fetchrow(
                "SELECT id FROM calendar_events WHERE user_id = $1 AND external_id = $2",
                request.user_id,
                external_id,
            )
            if existing_event:
                await fetchrow(
                    """
                    UPDATE calendar_events
                    SET title = $1, description = $2, start_time = $3, end_time = $4, metadata = $5, updated_at = NOW()
                    WHERE id = $6
                    RETURNING id
                    """,
                    event.get("summary"),
                    event.get("description"),
                    _parse_dt(start),
                    _parse_dt(end),
                    event,
                    existing_event["id"],
                )
            else:
                await fetchrow(
                    """
                    INSERT INTO calendar_events
                        (user_id, provider, calendar_id, external_id, title, description, start_time, end_time, metadata)
                    VALUES ($1, 'google', $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                    """,
                    request.user_id,
                    calendar_id,
                    external_id,
                    event.get("summary"),
                    event.get("description"),
                    _parse_dt(start),
                    _parse_dt(end),
                    event,
                )
                imported_events += 1

    return {
        "user_id": request.user_id,
        "imported_calendars": imported_calendars,
        "imported_events": imported_events,
        "time_min": time_min,
        "time_max": time_max,
    }


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
