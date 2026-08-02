"""Conversation history CRUD API routes."""

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import NotFoundError
from core.tenant_context import CurrentUser, get_current_user
from repositories.conversation_repo import ConversationRepository
from schemas.conversation import ConversationOut, ConversationDetailOut

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationOut]:
    """List all conversations for the current tenant."""
    repo = ConversationRepository(db)
    convs = await repo.list_conversations(
        tenant_id=uuid.UUID(current_user.tenant_id),
        limit=limit,
        offset=offset,
    )
    return [ConversationOut.model_validate(c) for c in convs]


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationDetailOut:
    """Get conversation details with full message history."""
    repo = ConversationRepository(db)
    conv = await repo.get_conversation_detail(
        tenant_id=uuid.UUID(current_user.tenant_id),
        conversation_id=conversation_id,
    )
    if conv is None:
        raise NotFoundError("Conversation not found")
    return ConversationDetailOut.model_validate(conv)


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a conversation and its messages."""
    repo = ConversationRepository(db)
    deleted = await repo.delete_conversation(
        tenant_id=uuid.UUID(current_user.tenant_id),
        conversation_id=conversation_id,
    )
    if not deleted:
        raise NotFoundError("Conversation not found")
    await db.commit()
