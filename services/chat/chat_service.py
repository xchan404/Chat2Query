"""Chat service — orchestrates graph execution and persists messages & citations.

Fulfills Phase 6 requirement: persists messages and populates message_citations
so message_id and citations returned in response are real, non-placeholder DB IDs.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.graph import run_chat_workflow
from agents.state import AgentState
from models.conversation import Conversation
from models.message import Message
from models.citation import MessageCitation

logger = logging.getLogger(__name__)


class ChatService:
    """Service handling chat execution, persistence, and response formatting."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def process_chat(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        question: str,
        connection_id: uuid.UUID | None = None,
        knowledge_base_id: uuid.UUID | None = None,
        conversation_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Process chat turn: create/fetch conversation -> save user message -> run graph -> persist assistant message & citations."""

        # 1. Resolve or create conversation
        if conversation_id is None:
            conv = Conversation(
                tenant_id=tenant_id,
                user_id=user_id,
                title=question[:100],
            )
            self.session.add(conv)
            await self.session.flush()
            conversation_id = conv.id
        else:
            # Verify conversation belongs to tenant
            stmt = select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id,
            )
            res = await self.session.execute(stmt)
            conv = res.scalar_one_or_none()
            if conv is None:
                conv = Conversation(
                    id=conversation_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    title=question[:100],
                )
                self.session.add(conv)
                await self.session.flush()

        # 1.5 Load recent chat history (prior turns) for context resolution
        chat_history: list[dict[str, str]] = []
        if conversation_id is not None:
            hist_stmt = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(10)
            )
            hist_res = await self.session.execute(hist_stmt)
            recent_msgs = list(reversed(list(hist_res.scalars().all())))
            for msg in recent_msgs:
                chat_history.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        # 2. Persist user message
        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=question,
        )
        self.session.add(user_msg)
        await self.session.flush()

        # 3. Build initial agent state and run workflow
        initial_state: AgentState = {
            "question": question,
            "tenant_id": str(tenant_id),
            "user_id": str(user_id),
            "connection_id": str(connection_id) if connection_id else None,
            "knowledge_base_id": str(knowledge_base_id) if knowledge_base_id else None,
            "conversation_id": str(conversation_id),
            "chat_history": chat_history,
        }

        final_state = await run_chat_workflow(initial_state, self.session)

        intent = final_state.get("intent", "general")
        answer = final_state.get("answer", "")
        sources_used = final_state.get("sources_used", [])
        raw_citations = final_state.get("citations", [])
        sql_result = final_state.get("sql_result")

        # 4. Persist assistant message
        assistant_msg = Message(
            conversation_id=conversation_id,
            parent_message_id=user_msg.id,
            role="assistant",
            content=answer,
            intent=intent,
            sources_used=sources_used,
        )
        self.session.add(assistant_msg)
        await self.session.flush()

        # Link QueryExecution row to Message if present
        if sql_result and sql_result.get("execution_id"):
            exec_id = uuid.UUID(sql_result["execution_id"])
            from models.query_execution import QueryExecution
            q_stmt = select(QueryExecution).where(QueryExecution.id == exec_id)
            q_res = await self.session.execute(q_stmt)
            q_record = q_res.scalar_one_or_none()
            if q_record:
                q_record.message_id = assistant_msg.id
                self.session.add(q_record)

        # 5. Persist message_citations
        citations_output = []
        for cite in raw_citations:
            source_type = cite.get("source_type", "general")

            if source_type == "database":
                q_exec_id = cite.get("query_execution_id")
                q_uuid = uuid.UUID(q_exec_id) if q_exec_id else None
                tbl_name = cite.get("table_name", "table")

                db_cite = MessageCitation(
                    message_id=assistant_msg.id,
                    source_type="database",
                    query_execution_id=q_uuid,
                    citation_metadata={"table_name": tbl_name},
                )
                self.session.add(db_cite)

                citations_output.append({
                    "source_type": "database",
                    "query_execution_id": str(q_uuid) if q_uuid else None,
                    "table_name": tbl_name,
                })

            elif source_type == "document":
                c_id = cite.get("chunk_id")
                c_uuid = uuid.UUID(c_id) if c_id else None
                f_name = cite.get("file_name")
                p_no = cite.get("page_number")
                snippet = cite.get("snippet")
                score = cite.get("relevance_score")

                doc_cite = MessageCitation(
                    message_id=assistant_msg.id,
                    source_type="document",
                    chunk_id=c_uuid,
                    file_name=f_name,
                    page_number=p_no,
                    excerpt=snippet,
                    relevance_score=score,
                )
                self.session.add(doc_cite)

                citations_output.append({
                    "source_type": "document",
                    "chunk_id": str(c_uuid) if c_uuid else None,
                    "file_name": f_name,
                    "page_number": p_no,
                    "snippet": snippet,
                })

        # Log audit event for chat turn
        from services.audit.audit_service import log_audit_event
        await log_audit_event(
            session=self.session,
            tenant_id=tenant_id,
            user_id=user_id,
            action="chat_turn_processed",
            resource_type="message",
            resource_id=str(assistant_msg.id),
            details={"intent": intent, "sources_used": sources_used, "citation_count": len(citations_output)},
            description=f"Chat question processed with intent '{intent}'",
        )

        await self.session.flush()
        await self.session.commit()

        # Format SQL output object for response contract (Section 9)
        sql_output = None
        if sql_result and (sql_result.get("generated_sql") or sql_result.get("normalized_sql")):
            sql_output = {
                "generated_sql": sql_result.get("generated_sql"),
                "normalized_sql": sql_result.get("normalized_sql"),
                "row_count": sql_result.get("row_count", 0),
                "rows": sql_result.get("rows", []),
            }

        return {
            "message_id": str(assistant_msg.id),
            "conversation_id": str(conversation_id),
            "intent": intent,
            "answer": answer,
            "sources_used": sources_used,
            "sql": sql_output,
            "citations": citations_output,
        }
