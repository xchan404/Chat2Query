"""Agent state definition for LangGraph orchestrator."""

import uuid
from typing import Any, TypedDict, Optional


class AgentState(TypedDict, total=False):
    """Shared state dictionary passed across agent nodes."""
    question: str
    tenant_id: str
    user_id: str
    connection_id: Optional[str]
    knowledge_base_id: Optional[str]
    conversation_id: Optional[str]
    chat_history: Optional[list[dict[str, str]]]

    # Classification
    intent: str  # "general" | "database" | "document" | "hybrid" | "clarification"
    confidence: float
    reasoning: str

    # Database node outputs
    allowed_schema: Optional[dict[str, Any]]
    sql_result: Optional[dict[str, Any]]

    # Document node outputs
    retrieved_chunks: Optional[list[dict[str, Any]]]

    # Merger / Synthesis outputs
    combined_context: Optional[str]

    # Final outputs
    answer: str
    sources_used: list[str]
    citations: list[dict[str, Any]]
    message_id: Optional[str]
