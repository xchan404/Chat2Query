"""Database connection model."""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DatabaseConnection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "database_connections"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    database_type: Mapped[str] = mapped_column(String(50), nullable=False)  # postgresql, mysql
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(nullable=False)
    database_name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_connection_string: Mapped[str | None] = mapped_column(Text, nullable=True)
    ssl_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    connection_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="connections")
    schemas = relationship("DatabaseSchema", back_populates="connection", cascade="all, delete-orphan")
    table_permissions = relationship("TablePermission", back_populates="connection", cascade="all, delete-orphan")
    query_executions = relationship("QueryExecution", back_populates="connection", cascade="all, delete-orphan")
