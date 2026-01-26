"""
Gateway Configuration

Environment variables and settings for the gateway service.
"""

import os
from typing import List
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Application settings loaded from environment variables."""
    
    # Service config
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    
    # CORS
    cors_origins: List[str] = field(default_factory=lambda: 
        os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","))
    
    # Database
    supabase_url: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_service_key: str = field(default_factory=lambda: os.getenv("SUPABASE_SERVICE_KEY", ""))
    
    # Redis
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379"))
    
    # Gemini
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    
    # Agent URLs
    ingestion_agent_url: str = field(default_factory=lambda: 
        os.getenv("INGESTION_AGENT_URL", "http://localhost:8001"))
    profile_agent_url: str = field(default_factory=lambda: 
        os.getenv("PROFILE_AGENT_URL", "http://localhost:8002"))
    synthesis_agent_url: str = field(default_factory=lambda: 
        os.getenv("SYNTHESIS_AGENT_URL", "http://localhost:8003"))
    planner_agent_url: str = field(default_factory=lambda: 
        os.getenv("PLANNER_AGENT_URL", "http://localhost:8004"))
    orchestrator_agent_url: str = field(default_factory=lambda: 
        os.getenv("ORCHESTRATOR_AGENT_URL", "http://localhost:8005"))


settings = Settings()
