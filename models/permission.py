"""Permission models: TablePermission, ColumnPermission."""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TablePermission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "table_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("database_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    schema_name: Mapped[str] = mapped_column(String(255), nullable=False)
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    access_type: Mapped[str] = mapped_column(String(50), default="read", nullable=False)
    row_filter: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    role = relationship("Role", back_populates="table_permissions")
    connection = relationship("DatabaseConnection", back_populates="table_permissions")
    column_permissions = relationship("ColumnPermission", back_populates="table_permission", cascade="all, delete-orphan")


class ColumnPermission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "column_permissions"

    table_permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("table_permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_allowed: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_masked: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    table_permission = relationship("TablePermission", back_populates="column_permissions")
    role = relationship("Role", back_populates="column_permissions")
