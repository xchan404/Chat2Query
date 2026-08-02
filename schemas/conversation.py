"""Pydantic schemas for conversations, messages, and audit logs."""

import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field

from schemas.chat import CitationOut, SQLResultOut


class MessageOut(BaseModel):
    """Output model for a message in a conversation."""
    id: uuid.UUID
    conversation_id: uuid.UUID
    parent_message_id: Optional[uuid.UUID] = None
    role: str
    content: str
    intent: Optional[str] = None
    sources_used: list[str] = []
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    """Output model for a conversation list item."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str] = None
    summary: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ConversationDetailOut(BaseModel):
    """Output model for detailed conversation with messages."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str] = None
    summary: Optional[str] = None
    messages: list[MessageOut] = []
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AuditLogOut(BaseModel):
    """Output model for an audit log entry."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
