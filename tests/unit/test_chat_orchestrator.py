"""Unit tests for Phase 6: LangGraph Orchestrator, Hybrid Chat, Clarification, SSE, and Response Contract."""

import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

os.environ["JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test"
os.environ["CONNECTION_ENCRYPTION_KEY"] = "test-encryption-key-for-unit-tests"

import pytest

from agents.nodes.classifier import _rule_based_classify
from agents.state import AgentState
from schemas.chat import ChatResponse, SQLResultOut, CitationOut
from services.chat.stream_service import _format_sse_event


class TestIntentClassifier:
    """Test intent classification rules."""

    def test_database_intent(self):
        intent, conf, reason = _rule_based_classify(
            "What is the total sum of all invoice amounts for customer 101?",
            connection_id="conn-123",
            knowledge_base_id=None,
        )
        assert intent == "database"

    def test_document_intent(self):
        intent, conf, reason = _rule_based_classify(
            "What are the cancellation terms and termination clause in the contract agreement PDF?",
            connection_id=None,
            knowledge_base_id="kb-123",
        )
        assert intent == "document"

    def test_hybrid_intent_invoice_vs_contract(self):
        """Test the exact invoice/contract hybrid question from assignment Section 9."""
        intent, conf, reason = _rule_based_classify(
            "What is the total of all invoice payments in the database versus the contract value stated in the agreement document?",
            connection_id="conn-1",
            knowledge_base_id="kb-1",
        )
        assert intent == "hybrid"

    def test_followup_question_with_chat_history(self):
        """A follow-up question that uses chat_history from prior turn resolves database intent correctly."""
        chat_history = [
            {"role": "user", "content": "What is the total of all invoice amounts for customer 101?"},
            {"role": "assistant", "content": "The total invoice amount is $50,000 across 5 invoices."},
        ]
        intent, conf, reason = _rule_based_classify(
            "what about last month?",
            connection_id=None,
            knowledge_base_id=None,
            chat_history=chat_history,
        )
        assert intent == "database"
        assert "follow-up" in reason.lower() or "prior" in reason.lower()

    def test_clarification_intent(self):
        """Ambiguous questions should produce a clarification intent, not a forced guess."""
        intent, conf, reason = _rule_based_classify(
            "show me data",
            connection_id=None,
            knowledge_base_id=None,
        )
        assert intent == "clarification"
        assert "ambiguous" in reason.lower()

    def test_general_intent(self):
        intent, conf, reason = _rule_based_classify(
            "hello",
            connection_id=None,
            knowledge_base_id=None,
        )
        assert intent == "general"


class TestResponseContractShape:
    """Verify response schema matches assignment Section 9 contract shape field-for-field."""

    def test_chat_response_contract_fields(self):
        """Test against the exact hybrid contract structure from assignment Section 9."""
        msg_id = str(uuid.uuid4())
        conv_id = str(uuid.uuid4())
        q_exec_id = str(uuid.uuid4())
        chunk_id = str(uuid.uuid4())

        payload = {
            "message_id": msg_id,
            "conversation_id": conv_id,
            "intent": "hybrid",
            "answer": "The total invoice payment in the database is $125,000, whereas the master contract agreement states a maximum budget limit of $150,000.",
            "sources_used": ["database", "document"],
            "sql": {
                "generated_sql": "SELECT SUM(amount) FROM invoices",
                "normalized_sql": "SELECT SUM(amount) AS total FROM invoices LIMIT 1000",
                "row_count": 1,
                "rows": [{"total": 125000}],
            },
            "citations": [
                {
                    "source_type": "database",
                    "query_execution_id": q_exec_id,
                    "table_name": "invoices",
                },
                {
                    "source_type": "document",
                    "chunk_id": chunk_id,
                    "file_name": "master_contract.pdf",
                    "page_number": 3,
                    "snippet": "Maximum annual contract budget limit is $150,000.",
                },
            ],
        }

        # Validates without throwing validation error
        res = ChatResponse.model_validate(payload)

        assert res.message_id == msg_id
        assert res.conversation_id == conv_id
        assert res.intent == "hybrid"
        assert res.sources_used == ["database", "document"]
        assert res.sql.generated_sql == "SELECT SUM(amount) FROM invoices"
        assert res.sql.row_count == 1
        assert len(res.citations) == 2

        # Check DB citation
        db_cite = res.citations[0]
        assert db_cite.source_type == "database"
        assert db_cite.query_execution_id == q_exec_id
        assert db_cite.table_name == "invoices"

        # Check Document citation
        doc_cite = res.citations[1]
        assert doc_cite.source_type == "document"
        assert doc_cite.file_name == "master_contract.pdf"
        assert doc_cite.page_number == 3
        assert doc_cite.chunk_id == chunk_id


class TestSSEStreamEvents:
    """Test typed SSE event formatting for frontend evidence rail."""

    def test_format_sse_intent_event(self):
        evt = _format_sse_event("intent", {"intent": "hybrid"})
        assert evt == 'event: intent\ndata: {"intent": "hybrid"}\n\n'

    def test_format_sse_sql_result_event(self):
        evt = _format_sse_event("sql_result", {"generated_sql": "SELECT 1", "row_count": 1})
        assert "event: sql_result\n" in evt
        assert '"generated_sql": "SELECT 1"' in evt

    def test_format_sse_citation_event(self):
        evt = _format_sse_event("citation", {"source_type": "document", "file_name": "test.pdf", "page_number": 2})
        assert "event: citation\n" in evt
        assert '"file_name": "test.pdf"' in evt

    def test_format_sse_done_event(self):
        evt = _format_sse_event("done", {"message_id": "m-123", "conversation_id": "c-456"})
        assert "event: done\n" in evt
        assert '"message_id": "m-123"' in evt


class TestHybridConcurrencyLatency:
    """Test that hybrid mode executes database and document branches in parallel, reducing latency."""

    @pytest.mark.asyncio
    async def test_hybrid_concurrency_latency_reduction(self, monkeypatch):
        """Mock DB node (0.2s delay) and Doc node (0.2s delay). Parallel execution should take ~0.2s, not 0.4s."""
        import asyncio
        import time
        from agents.graph import run_chat_workflow

        async def mock_db_node(state, session):
            await asyncio.sleep(0.20)
            return {"sql_result": {"success": True, "rows": [{"total": 100}], "row_count": 1}}

        async def mock_doc_node(state, session):
            await asyncio.sleep(0.20)
            return {"retrieved_chunks": [{"chunk_id": "c-1", "content": "text"}]}

        async def mock_classifier_node(state):
            return {"intent": "hybrid"}

        async def mock_answer_generator_node(state):
            return {"answer": "Answer"}

        monkeypatch.setattr("agents.graph.classifier_node", mock_classifier_node)
        monkeypatch.setattr("agents.graph.answer_generator_node", mock_answer_generator_node)
        monkeypatch.setattr("agents.graph.database_node", mock_db_node)
        monkeypatch.setattr("agents.graph.document_node", mock_doc_node)

        state = {
            "question": "Compare total invoice payments with contract terms",
            "tenant_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "connection_id": "conn-1",
            "knowledge_base_id": "kb-1",
        }

        start_t = time.monotonic()
        final_state = await run_chat_workflow(state, None)
        elapsed = time.monotonic() - start_t

        assert final_state["intent"] == "hybrid"
        # If run sequentially, 0.20 + 0.20 = 0.40s. Parallel execution takes ~0.20s (< 0.35s)
        assert elapsed < 0.35, f"Expected parallel execution under 0.35s, got {elapsed:.3f}s"


class TestSSEEventSequence:
    """Test that SSE stream emits structured evidence (sql_result, citation) BEFORE answer token streaming starts."""

    @pytest.mark.asyncio
    async def test_sse_event_ordering_evidence_before_tokens(self, monkeypatch):
        """Evidence rail cards (sql_result, citation) must arrive before text tokens."""
        from services.chat.stream_service import stream_chat_response

        # Mock chat service result
        async def mock_process_chat(self, tenant_id, user_id, question, **kwargs):
            return {
                "message_id": "msg-123",
                "conversation_id": "conv-123",
                "intent": "hybrid",
                "answer": "This is a detailed answer token string.",
                "sources_used": ["database", "document"],
                "sql": {"generated_sql": "SELECT 1", "row_count": 1, "rows": []},
                "citations": [{"source_type": "database", "table_name": "invoices"}],
            }

        monkeypatch.setattr("services.chat.chat_service.ChatService.process_chat", mock_process_chat)

        event_order = []
        gen = stream_chat_response(
            session=None,
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question="hybrid query",
        )

        async for frame in gen:
            lines = frame.strip().split("\n")
            for line in lines:
                if line.startswith("event: "):
                    event_order.append(line.replace("event: ", "").strip())

        # Assert sequence: intent -> sql_result -> citation -> token -> ... -> done
        assert "intent" in event_order
        assert "sql_result" in event_order
        assert "citation" in event_order
        assert "token" in event_order

        first_token_idx = event_order.index("token")
        sql_idx = event_order.index("sql_result")
        cite_idx = event_order.index("citation")

        # Evidence cards MUST arrive before the first text token
        assert sql_idx < first_token_idx
        assert cite_idx < first_token_idx

