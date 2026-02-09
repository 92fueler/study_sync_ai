"""
Profile API Endpoints

Handles user profile CRUD operations via ADK Profile Agent.
"""

import json
from typing import Optional, List, Any, Dict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.a2a.client import get_a2a_client
from app.db import fetchrow

router = APIRouter()


class StyleDNA(BaseModel):
    format_pref: str = "outline"
    tone: str = "textbook"  # Updated default from "eli5" to "textbook"
    uses_emoji: bool = False
    prefers_diagrams: bool = True
    learning_preferences: List[str] = []  # NEW: analogies, real_world, concept_map, practice_set
    custom_style: str = ""  # NEW: User's custom style description


class CalendarContext(BaseModel):
    commute_times: Optional[List[str]] = None
    work_hours: Optional[str] = None
    timezone: Optional[str] = None


class ProfileCreate(BaseModel):
    user_id: str
    display_name: Optional[str] = None
    goals: Optional[List[str]] = None
    style_dna: Optional[StyleDNA] = None
    calendar_context: Optional[CalendarContext] = None


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    goals: Optional[List[str]] = None
    style_dna: Optional[StyleDNA] = None
    calendar_context: Optional[CalendarContext] = None


@router.post("")
async def create_profile(profile: ProfileCreate):
    """Create a new user profile."""
    a2a_client = await get_a2a_client()
    # One user = one session: allocate session ID at account creation.
    a2a_client.ensure_user_session(profile.user_id)
    
    message = f"""Create a new user profile:
- user_id: {profile.user_id}
- display_name: {profile.display_name}
- goals: {profile.goals or []}
- style_dna: {profile.style_dna.model_dump() if profile.style_dna else 'default'}
- calendar_context: {profile.calendar_context.model_dump() if profile.calendar_context else 'none'}"""
    
    response = await a2a_client.run_agent(
        agent_name="profile",
        message=message,
        user_id=profile.user_id
    )
    
    if response.error:
        raise HTTPException(status_code=400, detail=response.error.get("message"))
    
    return {"success": True, "response": response.result}


@router.get("/for-generation")
async def get_profile_for_generation(user_id: str = Query(..., alias="user_id")):
    """
    Return merged profile (user_profiles + user_settings) for workers.
    Used by the generation worker so it gets style_dna.formats from Learning DNA
    without relying on the profile agent's LLM response.
    """
    default_style_dna: Dict[str, Any] = {"format_pref": "outline", "tone": "textbook", "uses_emoji": False, "prefers_diagrams": True}
    try:
        row = await fetchrow("SELECT * FROM user_profiles WHERE user_id = $1", user_id)
        if not row:
            style_dna = dict(default_style_dna)
        else:
            style_dna = json.loads(row["style_dna"]) if row.get("style_dna") else dict(default_style_dna)
            if not isinstance(style_dna, dict):
                style_dna = dict(default_style_dna)
        settings_row = await fetchrow("SELECT study_preferences FROM user_settings WHERE user_id = $1", user_id)
        if settings_row and settings_row.get("study_preferences"):
            prefs = settings_row["study_preferences"]
            if isinstance(prefs, str):
                try:
                    prefs = json.loads(prefs)
                except Exception:
                    prefs = {}
            if isinstance(prefs, dict):
                if "formats" in prefs and prefs["formats"] is not None:
                    style_dna["formats"] = prefs["formats"]
                if prefs.get("cognitive_tone"):
                    style_dna["tone"] = prefs["cognitive_tone"]
        profile_version = int(row["profile_version"]) if row and row.get("profile_version") else 1
        return {"status": "success", "user_id": user_id, "style_dna": style_dna, "profile_version": profile_version}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}")
async def get_profile(user_id: str):
    """Get a user's profile."""
    a2a_client = await get_a2a_client()
    
    response = await a2a_client.run_agent(
        agent_name="profile",
        message=f"Get the profile for user_id: {user_id}",
        user_id=user_id
    )
    
    if response.error:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return response.result


@router.put("/{user_id}")
async def update_profile(user_id: str, update: ProfileUpdate):
    """Update a user's profile."""
    a2a_client = await get_a2a_client()
    
    update_fields = {}
    if update.display_name is not None:
        update_fields["display_name"] = update.display_name
    if update.goals is not None:
        update_fields["goals"] = update.goals
    if update.style_dna is not None:
        update_fields["style_dna"] = update.style_dna.model_dump()
    if update.calendar_context is not None:
        update_fields["calendar_context"] = update.calendar_context.model_dump()
    
    response = await a2a_client.run_agent(
        agent_name="profile",
        message=f"Update profile for user_id: {user_id} with: {update_fields}",
        user_id=user_id
    )
    
    if response.error:
        raise HTTPException(status_code=400, detail=response.error.get("message"))
    
    return {"success": True, "response": response.result}
