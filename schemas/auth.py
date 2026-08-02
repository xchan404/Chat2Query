"""Auth-related Pydantic schemas."""

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request body."""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class TokenPair(BaseModel):
    """JWT access + refresh token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Refresh token request body."""
    refresh_token: str


class UserOut(BaseModel):
    """User information returned from /me and other endpoints."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    username: str
    full_name: str | None = None
    is_active: bool = True
    roles: list[str] = []
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
