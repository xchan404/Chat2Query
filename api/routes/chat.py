"""Sync and SSE streaming chat API routes."""

import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from core.tenant_context import CurrentUser, get_current_user
from schemas.chat import ChatRequest, ChatResponse
from services.chat.chat_service import ChatService
from services.chat.stream_service import stream_chat_response

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat_sync(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Synchronous chat endpoint.

    Returns response matching assignment Section 9 contract shape exactly:
    message_id, conversation_id, intent, answer, sources_used, sql, citations.
    """
    service = ChatService(db)
    result = await service.process_chat(
        tenant_id=uuid.UUID(current_user.tenant_id),
        user_id=uuid.UUID(current_user.user_id),
        question=request.question,
        connection_id=request.connection_id,
        knowledge_base_id=request.knowledge_base_id,
        conversation_id=request.conversation_id,
    )
    return ChatResponse.model_validate(result)


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """SSE streaming chat endpoint emitting typed events (intent, sql_result, citation, token, done)."""
    generator = stream_chat_response(
        session=db,
        tenant_id=uuid.UUID(current_user.tenant_id),
        user_id=uuid.UUID(current_user.user_id),
        question=request.question,
        connection_id=request.connection_id,
        knowledge_base_id=request.knowledge_base_id,
        conversation_id=request.conversation_id,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
