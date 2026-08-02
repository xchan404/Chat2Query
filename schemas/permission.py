"""Permission Pydantic models."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ColumnPermissionCreate(BaseModel):
    """Create or update column permission."""
    column_name: str = Field(..., min_length=1, max_length=255)
    is_allowed: bool = True
    is_masked: bool = False


class ColumnPermissionOut(BaseModel):
    """Output model for column permission."""
    id: uuid.UUID
    table_permission_id: uuid.UUID
    role_id: uuid.UUID
    column_name: str
    is_allowed: bool
    is_masked: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class TablePermissionCreate(BaseModel):
    """Create or update table permission."""
    role_id: uuid.UUID
    connection_id: uuid.UUID
    schema_name: str = Field(..., min_length=1, max_length=255)
    table_name: str = Field(..., min_length=1, max_length=255)
    access_type: str = Field("read", pattern="^(read|write|none)$")
    row_filter: str | None = None
    column_permissions: list[ColumnPermissionCreate] = []


class TablePermissionOut(BaseModel):
    """Output model for table permission."""
    id: uuid.UUID
    role_id: uuid.UUID
    connection_id: uuid.UUID
    schema_name: str
    table_name: str
    access_type: str
    row_filter: str | None = None
    column_permissions: list[ColumnPermissionOut] = []
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
