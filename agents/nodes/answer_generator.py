"""Answer generator node — synthesizes human answer and constructs citations list.

Complies strictly with Section 9 response contract shape.
"""

import json
import logging
import re
from typing import Any

import httpx

from agents.state import AgentState
from app.config import get_settings

logger = logging.getLogger(__name__)


async def answer_generator_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: generate final human response and citations."""
    intent = state.get("intent", "general")
    question = state["question"]
    sql_result = state.get("sql_result")
    retrieved_chunks = state.get("retrieved_chunks") or []
    combined_context = state.get("combined_context", "")

    sources_used: list[str] = []
    citations: list[dict[str, Any]] = []

    # Process Database citations & sources
    if sql_result and sql_result.get("success"):
        sources_used.append("database")
        exec_id = sql_result.get("execution_id")
        norm_sql = sql_result.get("normalized_sql", "")

        # Extract table names from normalized SQL or result
        match_table = re.search(r"FROM\s+([^\s;]+)", norm_sql, re.IGNORECASE) if norm_sql else None
        table_name = match_table.group(1) if match_table else "database_table"

        citations.append({
            "source_type": "database",
            "query_execution_id": exec_id,
            "table_name": table_name,
        })

    # Process Document citations & sources
    if retrieved_chunks:
        sources_used.append("document")
        for chunk in retrieved_chunks:
            fname = chunk.get("metadata", {}).get("file_name", "document")
            page_no = chunk.get("page_number")
            chunk_id = chunk.get("chunk_id")
            content = chunk.get("content", "")
            snippet = content[:200] + "..." if len(content) > 200 else content
            sim_score = chunk.get("similarity_score")

            citations.append({
                "source_type": "document",
                "chunk_id": chunk_id,
                "file_name": fname,
                "page_number": page_no,
                "snippet": snippet,
                "relevance_score": sim_score,
            })

    # Handle Clarification intent
    if intent == "clarification":
        clarify_msg = state.get("reasoning") or (
            "Your question is ambiguous. Could you please specify whether you would like to query "
            "a specific database connection or search an uploaded document set?"
        )
        return {
            "answer": clarify_msg,
            "sources_used": [],
            "citations": [],
        }

    # Handle General intent
    if intent == "general":
        return {
            "answer": "Hello! I am your AI pair assistant for database Text-to-SQL queries and document retrieval. How can I help you today?",
            "sources_used": [],
            "citations": [],
        }

    # Generate answer using LLM or rule-based synthesis
    settings = get_settings()
    api_key = settings.ANTHROPIC_API_KEY

    answer = ""
    if api_key:
        try:
            sys_prompt = "You are an intelligent data analyst. Answer the user's question clearly using the provided context."
            user_prompt = f"User Question: {question}\n\nContext:\n{combined_context}\n\nProvide a clear, accurate, and concise answer:"

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 512,
                        "system": sys_prompt,
                        "messages": [{"role": "user", "content": user_prompt}],
                    },
                )
                if resp.status_code == 200:
                    answer = resp.json()["content"][0]["text"].strip()
        except Exception as e:
            logger.warning(f"Answer generation LLM fallback due to: {e}")

    if not answer:
        # Fallback text synthesis if LLM key is absent/fails
        answer_parts = []
        if sql_result and sql_result.get("success"):
            rows = sql_result.get("rows", [])
            count = sql_result.get("row_count", 0)
            answer_parts.append(f"Database query executed successfully. Found {count} row(s). Data preview: {json.dumps(rows[:3])}")
        elif sql_result and not sql_result.get("success"):
            errs = ", ".join(sql_result.get("errors", []))
            answer_parts.append(f"Database query could not be executed: {errs}")

        if retrieved_chunks:
            answer_parts.append(f"Retrieved {len(retrieved_chunks)} relevant document snippet(s). Top snippet: '{retrieved_chunks[0].get('content', '')[:150]}...'")

        answer = "\n\n".join(answer_parts) if answer_parts else "No relevant information found."

    return {
        "answer": answer,
        "sources_used": list(set(sources_used)),
        "citations": citations,
    }
