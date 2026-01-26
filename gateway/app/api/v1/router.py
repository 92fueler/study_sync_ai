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

api_router = APIRouter()

api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_router.include_router(generate_router, prefix="/generate", tags=["generate"])
api_router.include_router(profile_router, prefix="/profile", tags=["profile"])
api_router.include_router(artifacts_router, prefix="/artifacts", tags=["artifacts"])
api_router.include_router(queue_router, prefix="/queue", tags=["queue"])
api_router.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
