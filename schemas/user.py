"""User Pydantic schemas."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for creating a user."""
    email: str = Field(..., max_length=255)
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6)
    full_name: str | None = None


class UserOut(BaseModel):
    """Schema for user output."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    username: str
    full_name: str | None = None
    is_active: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
