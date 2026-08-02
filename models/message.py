"""Message model."""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Message(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sources_used: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    message_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    citations = relationship("MessageCitation", back_populates="message", cascade="all, delete-orphan")
    query_execution = relationship("QueryExecution", back_populates="message", uselist=False)
