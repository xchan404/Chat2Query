"""Pydantic schemas for Chat endpoints matching Section 9 contract."""

import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for sync and streaming chat endpoints."""
    question: str = Field(..., min_length=1)
    connection_id: Optional[uuid.UUID] = None
    knowledge_base_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None


class SQLResultOut(BaseModel):
    """SQL result schema in chat response."""
    generated_sql: Optional[str] = None
    normalized_sql: Optional[str] = None
    row_count: int = 0
    rows: list[dict[str, Any]] = []


class CitationOut(BaseModel):
    """Citation schema in chat response."""
    source_type: str  # database, document
    query_execution_id: Optional[str] = None
    table_name: Optional[str] = None
    chunk_id: Optional[str] = None
    file_name: Optional[str] = None
    page_number: Optional[int] = None
    snippet: Optional[str] = None


class ChatResponse(BaseModel):
    """Full chat response matching Section 9 contract shape exactly."""
    message_id: str
    conversation_id: str
    intent: str
    answer: str
    sources_used: list[str] = []
    sql: Optional[SQLResultOut] = None
    citations: list[CitationOut] = []
