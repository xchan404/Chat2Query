"""Message citation model."""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MessageCitation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "message_citations"

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # database, document
    # For database citations
    query_execution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("query_executions.id", ondelete="SET NULL"),
        nullable=True,
    )
    # For document citations
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="SET NULL"),
        nullable=True,
    )
    file_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(nullable=True)
    citation_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    message = relationship("Message", back_populates="citations")
