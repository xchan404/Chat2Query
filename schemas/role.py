"""Role Pydantic schemas."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    """Schema for creating a role."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class RoleOut(BaseModel):
    """Schema for role output."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
