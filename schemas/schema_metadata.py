"""Schema metadata Pydantic models."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ColumnOut(BaseModel):
    """Output model for database column metadata."""
    id: uuid.UUID
    table_id: uuid.UUID
    column_name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool
    is_foreign_key: bool
    is_sensitive: bool
    description: str | None = None

    model_config = {"from_attributes": True}


class TableOut(BaseModel):
    """Output model for database table metadata."""
    id: uuid.UUID
    schema_id: uuid.UUID
    table_name: str
    table_type: str | None = None
    row_count: int | None = None
    description: str | None = None
    columns: list[ColumnOut] = []

    model_config = {"from_attributes": True}


class SchemaOut(BaseModel):
    """Output model for database schema metadata."""
    id: uuid.UUID
    connection_id: uuid.UUID
    schema_name: str
    is_active: bool
    tables: list[TableOut] = []

    model_config = {"from_attributes": True}


class SyncSchemaResponse(BaseModel):
    """Response model for schema sync operation."""
    connection_id: uuid.UUID
    schemas_synced: int
    tables_synced: int
    columns_synced: int
    message: str
