"""Pydantic schemas for files and knowledge bases."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    """Create a knowledge base."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class KnowledgeBaseOut(BaseModel):
    """Output model for knowledge base."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class FileOut(BaseModel):
    """Output model for file."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    knowledge_base_id: uuid.UUID
    file_name: str
    file_type: str
    file_size: int
    processing_status: str
    processing_error: str | None = None
    chunk_count: int | None = 0
    file_metadata: dict | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ChunkOut(BaseModel):
    """Output model for a document chunk (used in retrieval results)."""
    chunk_id: str
    file_id: str
    knowledge_base_id: str
    chunk_index: int
    content: str
    page_number: int | None = None
    similarity_score: float | None = None
    metadata: dict = {}
