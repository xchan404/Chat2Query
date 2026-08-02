"""pgvector similarity search — scoped by tenant_id + knowledge_base_id."""

import logging
import uuid
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector

from models.document_chunk import DocumentChunk
from services.documents.embedding_service import embed_single

logger = logging.getLogger(__name__)


async def similarity_search(
    session: AsyncSession,
    query_text: str,
    tenant_id: uuid.UUID,
    knowledge_base_ids: list[uuid.UUID] | None = None,
    top_k: int = 5,
    similarity_threshold: float = 0.3,
) -> list[dict[str, Any]]:
    """Search for similar chunks using cosine similarity via pgvector.

    Scoped by tenant_id and optionally by knowledge_base_id(s).
    Returns chunks sorted by descending similarity with metadata.
    """
    # Embed the query
    query_embedding = embed_single(query_text)

    # Build query with cosine distance operator (<=>)
    # pgvector cosine distance: 1 - cosine_similarity
    # Lower distance = more similar
    stmt = (
        select(
            DocumentChunk,
            DocumentChunk.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .where(DocumentChunk.tenant_id == tenant_id)
        .where(DocumentChunk.embedding.isnot(None))
    )

    if knowledge_base_ids:
        stmt = stmt.where(DocumentChunk.knowledge_base_id.in_(knowledge_base_ids))

    # Order by distance (ascending = most similar first)
    stmt = stmt.order_by("distance").limit(top_k)

    result = await session.execute(stmt)
    rows = result.all()

    chunks = []
    for chunk, distance in rows:
        similarity = 1.0 - distance  # Convert distance to similarity score
        if similarity < similarity_threshold:
            continue
        chunks.append({
            "chunk_id": str(chunk.id),
            "file_id": str(chunk.file_id),
            "knowledge_base_id": str(chunk.knowledge_base_id),
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "page_number": chunk.page_number,
            "similarity_score": round(similarity, 4),
            "metadata": chunk.chunk_metadata or {},
        })

    logger.info(
        f"Similarity search: query='{query_text[:50]}...', "
        f"found {len(chunks)} relevant chunks (threshold={similarity_threshold})"
    )
    return chunks
