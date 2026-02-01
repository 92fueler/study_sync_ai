"""
Tests for upload API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_get_upload_status_not_found():
    from app.api.v1.upload import get_upload_status
    from fastapi import HTTPException

    with patch('app.api.v1.upload.get_a2a_client', AsyncMock()) as mock_client:
        mock_client.return_value.get_task_status = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await get_upload_status(task_id="missing")

    assert exc.value.status_code == 404
