"""
Chat API Endpoints

Streams agent responses to the client via SSE.
"""

from typing import Optional
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.a2a.client import get_a2a_client

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: str
    message: str
    agent: Optional[str] = "synthesis"


@router.post("")
async def chat_stream(request: ChatRequest):
    """Stream a chat response from an agent (SSE)."""
    a2a_client = await get_a2a_client()

    async def event_stream():
        try:
            async for chunk in a2a_client.stream_agent(
                agent_name=request.agent or "synthesis",
                message=request.message,
                user_id=request.user_id,
            ):
                yield chunk
        except Exception as e:
            error_msg = str(e) if str(e) else "Unknown error"
            payload = json.dumps({"error": error_msg})
            yield f"data: {payload}\n\n".encode("utf-8")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
