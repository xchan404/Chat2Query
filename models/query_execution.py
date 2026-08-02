"""Query execution model for audit trail."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class QueryExecution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "query_executions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("database_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    generated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_status: Mapped[str] = mapped_column(String(50), nullable=False)  # approved, rejected, error
    validation_errors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    applied_row_filters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    referenced_tables: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    referenced_columns: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    connection = relationship("DatabaseConnection", back_populates="query_executions")
    message = relationship("Message", back_populates="query_execution")
