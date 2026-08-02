"""Repository for Conversation, Message, and Citation operations."""

import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.conversation import Conversation
from models.message import Message
from models.citation import MessageCitation
from models.query_execution import QueryExecution


class ConversationRepository:
    """Repository handling conversations and message history."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_conversations(
        self, tenant_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Conversation]:
        """List active tenant conversations ordered by creation date."""
        stmt = (
            select(Conversation)
            .where(
                Conversation.tenant_id == tenant_id,
                Conversation.status == "active",
            )
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_conversation_detail(
        self, tenant_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> Conversation | None:
        """Get conversation with message history loaded."""
        stmt = (
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id,
            )
            .options(selectinload(Conversation.messages))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_conversation(
        self, tenant_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> bool:
        """Soft-delete conversation by setting status='archived' to preserve citation & audit trails."""
        conv = await self.get_conversation_detail(tenant_id, conversation_id)
        if conv is None:
            return False
        conv.status = "archived"
        self.session.add(conv)
        await self.session.flush()
        return True

    async def get_message_citations(
        self, tenant_id: uuid.UUID, message_id: uuid.UUID
    ) -> list[MessageCitation]:
        """Get citations for a specific message, ensuring tenant isolation via join."""
        stmt = (
            select(MessageCitation)
            .join(Message, MessageCitation.message_id == Message.id)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                MessageCitation.message_id == message_id,
                Conversation.tenant_id == tenant_id,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_message_query_execution(
        self, tenant_id: uuid.UUID, message_id: uuid.UUID
    ) -> QueryExecution | None:
        """Get SQL query execution details for a specific message."""
        stmt = (
            select(QueryExecution)
            .where(
                QueryExecution.message_id == message_id,
                QueryExecution.tenant_id == tenant_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
