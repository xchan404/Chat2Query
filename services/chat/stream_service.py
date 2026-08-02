"""SSE Stream Service — emits typed SSE events for incremental frontend updates.

Events:
  - event: intent
  - event: sql_result
  - event: citation
  - event: token
  - event: done
  - event: error
"""

import json
import logging
import uuid
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from services.chat.chat_service import ChatService

logger = logging.getLogger(__name__)


def _format_sse_event(event_type: str, data: dict) -> str:
    """Format dictionary into an SSE event frame."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def stream_chat_response(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    question: str,
    connection_id: uuid.UUID | None = None,
    knowledge_base_id: uuid.UUID | None = None,
    conversation_id: uuid.UUID | None = None,
) -> AsyncGenerator[str, None]:
    """Stream chat response using typed SSE events for frontend evidence rail."""

    try:
        # Run chat workflow via ChatService
        chat_service = ChatService(session)
        result = await chat_service.process_chat(
            tenant_id=tenant_id,
            user_id=user_id,
            question=question,
            connection_id=connection_id,
            knowledge_base_id=knowledge_base_id,
            conversation_id=conversation_id,
        )

        # 1. Emit intent event
        yield _format_sse_event("intent", {"intent": result["intent"]})

        # 2. Emit SQL result event if database was queried
        if result.get("sql"):
            yield _format_sse_event("sql_result", result["sql"])

        # 3. Emit citation events incrementally
        for cite in result.get("citations", []):
            yield _format_sse_event("citation", cite)

        # 4. Stream token text chunks of the answer
        answer = result.get("answer", "")
        chunk_size = 20
        for i in range(0, len(answer), chunk_size):
            token_chunk = answer[i : i + chunk_size]
            yield _format_sse_event("token", {"text": token_chunk})

        # 5. Emit final done event with complete payload metadata
        yield _format_sse_event("done", {
            "message_id": result["message_id"],
            "conversation_id": result["conversation_id"],
            "intent": result["intent"],
            "sources_used": result["sources_used"],
        })

    except Exception as e:
        logger.error(f"SSE stream error: {e}")
        yield _format_sse_event("error", {"detail": str(e)})
