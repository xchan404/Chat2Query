"""Pydantic schemas for database connection CRUD."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ConnectionCreate(BaseModel):
    """Create a new database connection."""
    name: str = Field(..., min_length=1, max_length=255)
    database_type: str = Field(..., pattern="^(postgresql|mysql)$")
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    database_name: str = Field(..., min_length=1, max_length=255)
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)
    ssl_enabled: bool = False


class ConnectionUpdate(BaseModel):
    """Update an existing database connection."""
    name: str | None = Field(None, min_length=1, max_length=255)
    host: str | None = Field(None, min_length=1, max_length=255)
    port: int | None = Field(None, ge=1, le=65535)
    database_name: str | None = Field(None, min_length=1, max_length=255)
    username: str | None = Field(None, min_length=1, max_length=255)
    password: str | None = Field(None, min_length=1)
    ssl_enabled: bool | None = None


class ConnectionOut(BaseModel):
    """Connection data returned to the client.

    Note: password is NEVER returned — only the encrypted_password column
    exists in the DB, and we never expose that either.
    """
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    database_type: str
    host: str
    port: int
    database_name: str
    username: str
    ssl_enabled: bool
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class TestResult(BaseModel):
    """Result of a connection test."""
    success: bool
    message: str
    latency_ms: float | None = None
