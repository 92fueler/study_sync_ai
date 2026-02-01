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

    row = {"id": "j1", "user_id": "user-1", "name": "Note", "job_type": "text", "status": "ingesting", "metadata": "{\"source\":\"ui\"}", "created_at": None, "updated_at": None}

    with patch('app.api.v1.ingestion.fetchrow', AsyncMock(return_value=row)):
        result = await create_ingestion_job(
            IngestionCreate(
                user_id="user-1",
                name="Note",
                job_type="text",
                metadata={"source": "ui"},
            )
        )

    assert result["id"] == "j1"
    assert result["metadata"]["source"] == "ui"


@pytest.mark.asyncio
async def test_update_ingestion_job():
    from app.api.v1.ingestion import update_ingestion_job, IngestionUpdate

    row = {"id": "j2", "user_id": "user-1", "name": "File", "job_type": "pdf", "status": "ready", "metadata": "{\"progress\":100}", "created_at": None, "updated_at": None}

    with patch('app.api.v1.ingestion.fetchrow', AsyncMock(return_value=row)):
        result = await update_ingestion_job(
            job_id="j2",
            user_id="user-1",
            update=IngestionUpdate(status="ready", metadata={"progress": 100}),
        )

    assert result["status"] == "ready"
    assert result["metadata"]["progress"] == 100
