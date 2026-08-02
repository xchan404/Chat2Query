"""Knowledge base model."""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeBase(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "knowledge_bases"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    kb_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="knowledge_bases")
    files = relationship("File", back_populates="knowledge_base", cascade="all, delete-orphan")
