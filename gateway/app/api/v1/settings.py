"""
Settings API Endpoints

User-configurable preferences stored directly in DB.
"""

from typing import Any, Dict, Optional

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import fetchrow

router = APIRouter()


class SettingsUpdate(BaseModel):
    theme: Optional[str] = None
    notifications: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    study_preferences: Optional[Dict[str, Any]] = None


def _settings_row_to_dict(row) -> Dict[str, Any]:
    settings = dict(row)
    settings["created_at"] = settings.get("created_at")
    settings["updated_at"] = settings.get("updated_at")
    for field in ("notifications", "study_preferences"):
        if isinstance(settings.get(field), str):
            try:
                settings[field] = json.loads(settings[field])
            except Exception:
                pass
    return settings


@router.get("/{user_id}")
async def get_settings(user_id: str):
    """Get user settings (defaults if missing)."""
    query = "SELECT * FROM user_settings WHERE user_id = $1"
    try:
        row = await fetchrow(query, user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        return {
            "user_id": user_id,
            "theme": "light",
            "notifications": {"in_app": True, "email": False, "push": False},
            "timezone": None,
            "study_preferences": None,
        }

    return _settings_row_to_dict(row)


@router.patch("/{user_id}")
async def update_settings(user_id: str, update: SettingsUpdate):
    """Update settings (upsert)."""
    update_values = update.model_dump(exclude_unset=True)
    if not update_values:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Check existing row
    try:
        existing = await fetchrow("SELECT user_id FROM user_settings WHERE user_id = $1", user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    if existing:
        updates = []
        params = []
        idx = 1
        for field, value in update_values.items():
            if field in {"notifications", "study_preferences"} and value is not None:
                value = json.dumps(value)
            updates.append(f"{field} = ${idx}")
            params.append(value)
            idx += 1
        updates.append("updated_at = NOW()")

        query = f"""
            UPDATE user_settings
            SET {', '.join(updates)}
            WHERE user_id = ${idx}
            RETURNING *
        """
        try:
            row = await fetchrow(query, *params, user_id)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        except Exception:
            raise HTTPException(status_code=500, detail="Database error")
        return _settings_row_to_dict(row)

    # Insert new
    query = """
        INSERT INTO user_settings (user_id, theme, notifications, timezone, study_preferences)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
    """
    try:
        row = await fetchrow(
            query,
            user_id,
            update_values.get("theme"),
            json.dumps(update_values.get("notifications")) if update_values.get("notifications") is not None else None,
            update_values.get("timezone"),
            json.dumps(update_values.get("study_preferences")) if update_values.get("study_preferences") is not None else None,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    return _settings_row_to_dict(row)
