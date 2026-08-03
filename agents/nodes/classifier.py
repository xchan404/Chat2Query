"""Request classifier node — categorizes user question into intent.

Intents:
  - database: query structured tabular database
  - document: search unstructured files / contracts / PDFs
  - hybrid: combine SQL query and document retrieval
  - clarification: prompt user for missing details or ambiguous context
  - general: casual greeting or general conversation
"""

import json
import logging
import re
from typing import Any

import httpx

from agents.state import AgentState
from app.config import get_settings

logger = logging.getLogger(__name__)


def _rule_based_classify(
    question: str,
    connection_id: str | None,
    knowledge_base_id: str | None,
    chat_history: list[dict[str, str]] | None = None,
) -> tuple[str, float, str]:
    """Heuristic fallback rule-based classifier."""
    q_lower = question.lower()

    # Vague / ambiguous question check -> clarification (only if no chat history context)
    vague_phrases = ["show me data", "get info", "tell me something", "help me", "query it", "run a check"]
    if any(q_lower.strip() == phrase for phrase in vague_phrases) and not (connection_id or knowledge_base_id) and not chat_history:
        return (
            "clarification",
            0.95,
            "Question is too ambiguous without specifying target database connection or document knowledge base.",
        )

    # General conversation check
    greetings = ["hi", "hello", "hey", "who are you", "what can you do", "thanks", "thank you"]
    if q_lower.strip() in greetings or len(q_lower.strip().split()) <= 2 and q_lower.strip() in greetings:
        return ("general", 0.99, "Casual greeting or general question.")

    # Check for follow-up phrasing referencing prior turn
    followup_indicators = ["what about", "how about", "that number", "last month", "the previous", "those invoices", "same customer", "for that", "and for"]
    is_followup = any(ind in q_lower for ind in followup_indicators) and bool(chat_history)

    # Keywords for DB vs Documents
    db_keywords = ["total", "count", "sum", "average", "avg", "invoice", "invoices", "payment", "amount", "revenue", "table", "sql", "rows", "database", "orders", "customers", "users"]
    doc_keywords = ["contract", "clause", "document", "pdf", "agreement", "terms", "policy", "section", "file", "word", "text", "pdf", "docx", "article", "provision"]

    has_db = any(re.search(r"\b" + kw + r"\b", q_lower) for kw in db_keywords)
    has_doc = any(re.search(r"\b" + kw + r"\b", q_lower) for kw in doc_keywords)

    if has_db and has_doc:
        return ("hybrid", 0.90, "Question references both structured database data and unstructured document terms.")
    elif is_followup:
        # Infer context from prior turn in chat_history
        last_turn_text = " ".join(m.get("content", "").lower() for m in chat_history[-2:])
        has_prior_db = any(kw in last_turn_text for kw in db_keywords)
        has_prior_doc = any(kw in last_turn_text for kw in doc_keywords)

        if has_prior_db and has_prior_doc:
            return ("hybrid", 0.88, "Follow-up question referencing prior hybrid conversation turn.")
        elif has_prior_db or connection_id:
            return ("database", 0.85, "Follow-up question referencing prior database context.")
        elif has_prior_doc or knowledge_base_id:
            return ("document", 0.85, "Follow-up question referencing prior document context.")

    if has_db or connection_id:
        return ("database", 0.85, "Question targets structured tabular data.")
    elif has_doc or knowledge_base_id:
        return ("document", 0.85, "Question targets unstructured document content.")

    return ("database" if connection_id else ("document" if knowledge_base_id else "general"), 0.70, "Default classification based on available sources.")


async def classifier_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: classify question intent."""
    question = state["question"]
    conn_id = state.get("connection_id")
    kb_id = state.get("knowledge_base_id")
    chat_history = state.get("chat_history")

    settings = get_settings()
    api_key = settings.ANTHROPIC_API_KEY

    # Rule-based fast path or fallback
    intent, confidence, reasoning = _rule_based_classify(question, conn_id, kb_id, chat_history)

    if api_key and not intent == "clarification":
        try:
            prompt = f"""Classify the user's question into EXACTLY ONE of these intents:
1. "database": Question asks for data, counts, sums, or tables from a database.
2. "document": Question asks about text, terms, clauses, or facts in uploaded documents/PDFs.
3. "hybrid": Question explicitly compares or combines database numbers/invoices with document terms/contracts.
4. "clarification": Question is too vague, ambiguous, or incomplete to answer safely.
5. "general": Casual greeting, thanks, or general meta question.

Context provided:
- Database connection ID: {conn_id or 'None'}
- Knowledge base ID: {kb_id or 'None'}
Question: {question}

Return JSON with format: {{"intent": "...", "confidence": 0.95, "reasoning": "..."}}"""

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-haiku-4-5",
                        "max_tokens": 150,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                if resp.status_code == 200:
                    text = resp.json()["content"][0]["text"]
                    match = re.search(r"\{.*\}", text, re.DOTALL)
                    if match:
                        parsed = json.loads(match.group(0))
                        intent = parsed.get("intent", intent)
                        confidence = float(parsed.get("confidence", confidence))
                        reasoning = parsed.get("reasoning", reasoning)
        except Exception as e:
            logger.warning(f"LLM classification fallback due to: {e}")

    logger.info(f"Classified question: intent='{intent}', confidence={confidence}, reasoning='{reasoning}'")

    return {
        "intent": intent,
        "confidence": confidence,
        "reasoning": reasoning,
    }
