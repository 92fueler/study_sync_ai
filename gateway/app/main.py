"""
StudySync AI Gateway - Main FastAPI Application

Central orchestrator that routes requests to ADK agents via ADK runtime (sessions + /run).
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    print(f"Starting StudySync AI Gateway on port {settings.port}")
    yield
    # Shutdown
    try:
        from app.db import close_pool
        await close_pool()
    except Exception as e:
        print(f"Warning: failed to close DB pool: {e}")
    print("Shutting down StudySync AI Gateway")


app = FastAPI(
    title="StudySync AI Gateway",
    description="API Gateway for StudySync AI - Orchestrates ADK agents via ADK runtime",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health = {
        "status": "healthy",
        "service": "gateway"
    }
    
    # Check Redis connectivity
    try:
        from workers.queue import get_redis_connection
        conn = get_redis_connection()
        conn.ping()
        health["redis"] = "connected"
    except Exception as e:
        health["redis"] = f"disconnected: {str(e)}"
        health["status"] = "degraded"
    
    return health


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "StudySync AI Gateway",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
