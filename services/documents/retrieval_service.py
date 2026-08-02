"""Retrieval service — retrieves relevant document chunks for a question.

Starts with similarity-score-only ranking (can upgrade to cross-encoder rerank).
"""

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from vector_store.search import similarity_search

logger = logging.getLogger(__name__)


class RetrievalService:
    """Retrieve relevant document chunks for RAG."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def retrieve(
        self,
        query: str,
        tenant_id: uuid.UUID,
        knowledge_base_ids: list[uuid.UUID] | None = None,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ) -> list[dict[str, Any]]:
        """Retrieve top-k relevant chunks sorted by similarity score.

        Currently uses cosine similarity directly.
        Upgrade path: add cross-encoder reranking on top of initial retrieval.
        """
        results = await similarity_search(
            session=self.session,
            query_text=query,
            tenant_id=tenant_id,
            knowledge_base_ids=knowledge_base_ids,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        # Basic reranking: already sorted by similarity in the vector search
        # Future: cross-encoder rerank here
        return results
