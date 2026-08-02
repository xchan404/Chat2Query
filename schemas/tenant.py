"""Tenant Pydantic schemas."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    """Schema for creating a tenant."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)


class TenantOut(BaseModel):
    """Schema for tenant output."""
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
