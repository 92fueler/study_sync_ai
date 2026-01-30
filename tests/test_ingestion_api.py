"""
Tests for ingestion API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_list_processing_jobs():
    from app.api.v1.ingestion import list_processing_jobs

    rows = [
        {"id": "j1", "user_id": "user-1", "name": "File", "job_type": "pdf", "status": "ingesting", "created_at": None, "updated_at": None},
    ]

    with patch('app.api.v1.ingestion.fetch', AsyncMock(return_value=rows)):
        result = await list_processing_jobs(user_id="user-1")

    assert result["count"] == 1


@pytest.mark.asyncio
async def test_create_ingestion_job():
    from app.api.v1.ingestion import create_ingestion_job, IngestionCreate

    row = {"id": "j1", "user_id": "user-1", "name": "Note", "job_type": "text", "status": "ingesting", "created_at": None, "updated_at": None}

    with patch('app.api.v1.ingestion.fetchrow', AsyncMock(return_value=row)):
        result = await create_ingestion_job(IngestionCreate(user_id="user-1", name="Note", job_type="text"))

    assert result["id"] == "j1"
