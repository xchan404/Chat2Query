"""Hybrid merger node — combines database SQL results and document chunk context."""

import json
import logging
from typing import Any

from agents.state import AgentState

logger = logging.getLogger(__name__)


def hybrid_merger_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: synthesize context from DB execution and Document retrieval."""
    sql_result = state.get("sql_result")
    retrieved_chunks = state.get("retrieved_chunks") or []

    combined_parts = []

    # Part 1: Database Execution Result
    if sql_result and sql_result.get("success"):
        rows = sql_result.get("rows", [])
        row_count = sql_result.get("row_count", 0)
        norm_sql = sql_result.get("normalized_sql", "")
        combined_parts.append(
            f"=== DATABASE QUERY RESULT ===\n"
            f"Executed SQL: {norm_sql}\n"
            f"Returned Rows Count: {row_count}\n"
            f"Data:\n{json.dumps(rows[:10], indent=2)}"
        )
    elif sql_result and not sql_result.get("success"):
        errors = sql_result.get("errors", [])
        combined_parts.append(
            f"=== DATABASE QUERY ATTEMPT (REJECTED/FAILED) ===\n"
            f"Errors: {', '.join(errors)}"
        )

    # Part 2: Document Chunks
    if retrieved_chunks:
        doc_summaries = []
        for i, chunk in enumerate(retrieved_chunks, start=1):
            fname = chunk.get("metadata", {}).get("file_name", "document")
            page_no = chunk.get("page_number")
            page_str = f", Page {page_no}" if page_no else ""
            content = chunk.get("content", "")
            doc_summaries.append(f"[{i}] File: {fname}{page_str}\nContent: {content}")

        combined_parts.append(
            f"=== DOCUMENT RETRIEVAL RESULTS ===\n" + "\n\n".join(doc_summaries)
        )

    combined_context = "\n\n".join(combined_parts)
    logger.info("Hybrid merger synthesized combined context")

    return {
        "combined_context": combined_context,
    }
