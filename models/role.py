"""Role model and user_roles association table."""

import uuid

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Association table for many-to-many User <-> Role
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "roles"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles")
    table_permissions = relationship("TablePermission", back_populates="role", cascade="all, delete-orphan")
    column_permissions = relationship("ColumnPermission", back_populates="role", cascade="all, delete-orphan")
