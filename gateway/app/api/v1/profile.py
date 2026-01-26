"""
Profile API Endpoints

Handles user profile CRUD operations via ADK Profile Agent.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.a2a.client import get_a2a_client

router = APIRouter()


class StyleDNA(BaseModel):
    format_pref: str = "outline"
    tone: str = "eli5"
    uses_emoji: bool = False
    prefers_diagrams: bool = True


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
    
    if response.error_data:
        raise HTTPException(status_code=400, detail=response.error_data.get("message"))
    
    return {"success": True, "response": response.result}


@router.get("/{user_id}")
async def get_profile(user_id: str):
    """Get a user's profile."""
    a2a_client = await get_a2a_client()
    
    response = await a2a_client.run_agent(
        agent_name="profile",
        message=f"Get the profile for user_id: {user_id}",
        user_id=user_id
    )
    
    if response.error_data:
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
    
    if response.error_data:
        raise HTTPException(status_code=400, detail=response.error_data.get("message"))
    
    return {"success": True, "response": response.result}
