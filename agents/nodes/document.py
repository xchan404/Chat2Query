"""Document RAG node — retrieves relevant chunks from pgvector vector store."""

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from agents.state import AgentState
from services.documents.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


async def document_node(state: AgentState, session: AsyncSession) -> dict[str, Any]:
    """LangGraph node: retrieve top-k document chunks for RAG."""
    question = state["question"]
    tenant_id = uuid.UUID(state["tenant_id"])
    kb_id_str = state.get("knowledge_base_id")

    kb_ids = [uuid.UUID(kb_id_str)] if kb_id_str else None

    retrieval_service = RetrievalService(session)
    chunks = await retrieval_service.retrieve(
        query=question,
        tenant_id=tenant_id,
        knowledge_base_ids=kb_ids,
        top_k=5,
        similarity_threshold=0.25,
    )

    logger.info(f"Document node retrieved {len(chunks)} chunks for query: '{question[:40]}...'")

    return {
        "retrieved_chunks": chunks,
    }
