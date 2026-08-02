"""File model for uploaded documents."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class File(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "files"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    processing_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )  # CHECK constraint added in migration: pending|processing|completed|failed
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    chunk_count: Mapped[int | None] = mapped_column(default=0)
    file_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="files")
    chunks = relationship("DocumentChunk", back_populates="file", cascade="all, delete-orphan")
