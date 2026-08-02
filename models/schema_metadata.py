"""Schema metadata models: DatabaseSchema, DatabaseTable, DatabaseColumn."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DatabaseSchema(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "database_schemas"

    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("database_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    schema_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    connection = relationship("DatabaseConnection", back_populates="schemas")
    tables = relationship("DatabaseTable", back_populates="schema", cascade="all, delete-orphan")


class DatabaseTable(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "database_tables"

    schema_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("database_schemas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    table_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # TABLE, VIEW
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    table_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    schema = relationship("DatabaseSchema", back_populates="tables")
    columns = relationship("DatabaseColumn", back_populates="table", cascade="all, delete-orphan")


class DatabaseColumn(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "database_columns"

    table_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("database_tables.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str] = mapped_column(String(100), nullable=False)
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_primary_key: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_foreign_key: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    column_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    table = relationship("DatabaseTable", back_populates="columns")
