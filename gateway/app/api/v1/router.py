"""
API Router Aggregation

Combines all v1 API routes.
"""

from fastapi import APIRouter

from app.api.v1.upload import router as upload_router
from app.api.v1.generate import router as generate_router
from app.api.v1.profile import router as profile_router
from app.api.v1.artifacts import router as artifacts_router
from app.api.v1.queue import router as queue_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.content import router as content_router
from app.api.v1.chat import router as chat_router
from app.api.v1.learning_plans import router as learning_plans_router
from app.api.v1.settings import router as settings_router
from app.api.v1.search import router as search_router
from app.api.v1.calendar import router as calendar_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.notes import router as notes_router
from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.audio import router as audio_router
from app.api.v1.dev import router as dev_router
from app.core.config import settings

api_router = APIRouter()

api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_router.include_router(generate_router, prefix="/generate", tags=["generate"])
api_router.include_router(profile_router, prefix="/profile", tags=["profile"])
api_router.include_router(artifacts_router, prefix="/artifacts", tags=["artifacts"])
api_router.include_router(queue_router, prefix="/queue", tags=["queue"])
api_router.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(content_router, prefix="/content", tags=["content"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(learning_plans_router, prefix="/learning-plans", tags=["learning-plans"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(search_router, prefix="/search", tags=["search"])
api_router.include_router(calendar_router, prefix="/calendar", tags=["calendar"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(notes_router, prefix="/notes", tags=["notes"])
api_router.include_router(ingestion_router, prefix="/ingestion", tags=["ingestion"])
api_router.include_router(audio_router, prefix="/audio", tags=["audio"])
api_router.include_router(video_router, prefix="/video", tags=["video"])
if settings.debug or settings.enable_dev_endpoints:
    api_router.include_router(dev_router, prefix="/dev", tags=["dev"])
