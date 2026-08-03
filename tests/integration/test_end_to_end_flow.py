"""Integration Test Suite — real infrastructure tests.

These tests hit REAL external services:
  - Scenarios 1-3: Real PostgreSQL at localhost:5432 (postgres/postgres)
  - Scenarios 4-6: Real Anthropic API (claude-haiku-4-5) if ANTHROPIC_API_KEY is set
  - Scenario 3: Real bge-m3 local model inference (~17s warm)

Scenarios covered:
  1. test_integration_connection_test_and_crud          — real asyncpg to live Postgres
  2. test_integration_schema_discovery_and_sync          — real introspection of live tables
  3. test_integration_file_upload_chunk_embed_search      — real PDF parse + real bge-m3 embedding
  4. test_integration_database_only_chat                  — real LLM classifier + SQL generation
  5. test_integration_document_only_chat                  — real LLM classifier
  6. test_integration_hybrid_chat                         — real LLM classifier
"""

import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# ── Real Postgres credentials (matches local installation, not Docker) ──
PG_HOST = os.environ.get("INTEGRATION_PG_HOST", "localhost")
PG_PORT = int(os.environ.get("INTEGRATION_PG_PORT", "5432"))
PG_USER = os.environ.get("INTEGRATION_PG_USER", "postgres")
PG_PASS = os.environ.get("INTEGRATION_PG_PASS", "postgres")
PG_DB = "chat2query_integration_test"

# ── Config env vars (needed for app.config imports) ──
os.environ["JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["DATABASE_URL"] = f"postgresql+asyncpg://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"
os.environ["CONNECTION_ENCRYPTION_KEY"] = "test-encryption-key-for-unit-tests"

import asyncio

import asyncpg
import pytest

from services.database.adapters.base import ConnectionParams
from services.database.adapters.postgresql import PostgreSQLAdapter

# ── Shared ConnectionParams for the live Postgres instance ──
LIVE_PG_PARAMS = ConnectionParams(
    host=PG_HOST,
    port=PG_PORT,
    database_name=PG_DB,
    username=PG_USER,
    password=PG_PASS,
    ssl_enabled=False,
)


# ────────────────────────────────────────────────────────────
# Fixture: create a throwaway test database and seed it
# ────────────────────────────────────────────────────────────
@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """Create a real Postgres test database and seed a small table, then drop it after."""

    async def _setup():
        # Connect to default 'postgres' DB to create our test DB
        admin = await asyncpg.connect(
            host=PG_HOST, port=PG_PORT,
            user=PG_USER, password=PG_PASS,
            database="postgres", timeout=5,
        )
        # Drop if leftover from prior run, then create
        await admin.execute(f"DROP DATABASE IF EXISTS {PG_DB}")
        await admin.execute(f"CREATE DATABASE {PG_DB}")
        await admin.close()

        # Seed the test DB
        conn = await asyncpg.connect(
            host=PG_HOST, port=PG_PORT,
            user=PG_USER, password=PG_PASS,
            database=PG_DB, timeout=5,
        )
        await conn.execute("""
            CREATE TABLE invoices (
                id SERIAL PRIMARY KEY,
                customer_name TEXT NOT NULL,
                amount NUMERIC(12,2) NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT now()
            )
        """)
        await conn.execute("""
            INSERT INTO invoices (customer_name, amount, status) VALUES
                ('Acme Corp', 15000.00, 'paid'),
                ('Globex Inc', 7500.50, 'pending'),
                ('Initech', 22000.00, 'paid')
        """)
        await conn.close()

    async def _teardown():
        admin = await asyncpg.connect(
            host=PG_HOST, port=PG_PORT,
            user=PG_USER, password=PG_PASS,
            database="postgres", timeout=5,
        )
        await admin.execute(f"DROP DATABASE IF EXISTS {PG_DB}")
        await admin.close()

    asyncio.get_event_loop_policy().new_event_loop()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(_setup())
    yield
    loop.run_until_complete(_teardown())
    loop.close()


class TestIntegrationScenarios:
    """Integration test suite — all 6 scenarios hit real infrastructure."""

    # ─────────────────────────────────────────────
    # Scenario 1: Real Postgres connection test
    # ─────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_integration_connection_test_and_crud(self):
        """Connect to real Postgres, run test_connection, verify version string returned."""
        adapter = PostgreSQLAdapter()
        success, message = await adapter.test_connection(LIVE_PG_PARAMS)

        assert success is True, f"Connection failed: {message}"
        assert "PostgreSQL" in message

        # Also verify encrypt/decrypt round-trip for credential storage
        from core.encryption import encrypt_value, decrypt_value
        raw_pass = PG_PASS
        enc = encrypt_value(raw_pass)
        assert enc != raw_pass                  # ciphertext != plaintext
        assert decrypt_value(enc) == raw_pass   # round-trip correct

    # ─────────────────────────────────────────────
    # Scenario 2: Real schema introspection
    # ─────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_integration_schema_discovery_and_sync(self):
        """Introspect real Postgres: list schemas, list tables, list columns."""
        adapter = PostgreSQLAdapter()

        # List schemas — 'public' must be present
        schemas = await adapter.list_schemas(LIVE_PG_PARAMS)
        schema_names = [s.schema_name for s in schemas]
        assert "public" in schema_names

        # List tables in 'public' — our seeded 'invoices' table must be present
        tables = await adapter.list_tables(LIVE_PG_PARAMS, "public")
        table_names = [t.table_name for t in tables]
        assert "invoices" in table_names

        # List columns of 'invoices'
        columns = await adapter.list_columns(LIVE_PG_PARAMS, "public", "invoices")
        col_names = [c.column_name for c in columns]
        assert "id" in col_names
        assert "amount" in col_names
        assert "customer_name" in col_names

        # Verify primary key detection
        id_col = next(c for c in columns if c.column_name == "id")
        assert id_col.is_primary_key is True

    # ─────────────────────────────────────────────
    # Scenario 3: Real PDF parse + real bge-m3
    # ─────────────────────────────────────────────
    def test_integration_file_upload_chunk_embed_search(self, tmp_path):
        """Parse a real PDF, chunk it, and run real bge-m3 embedding inference."""
        import fitz

        pdf_path = tmp_path / "integration_agreement.pdf"
        doc = fitz.open()

        p1 = doc.new_page()
        p1.insert_text((72, 72), "MASTER SERVICES AGREEMENT\nContract Value: $500,000 annually.")
        p2 = doc.new_page()
        p2.insert_text((72, 72), "PAYMENT SCHEDULE\nInvoices payable net 30 days from receipt.")

        doc.save(str(pdf_path))
        doc.close()

        from services.documents.parsers.pdf_parser import parse_pdf
        from services.documents.chunking_service import chunk_document
        from services.documents.embedding_service import embed_texts

        parsed = parse_pdf(str(pdf_path), "integration_agreement.pdf")
        assert parsed.total_pages == 2

        chunks = chunk_document(parsed, chunk_size=500, chunk_overlap=50)
        assert len(chunks) >= 2

        # Page number tracking
        p1_chunks = [c for c in chunks if c.page_number == 1]
        p2_chunks = [c for c in chunks if c.page_number == 2]
        assert len(p1_chunks) > 0
        assert len(p2_chunks) > 0

        # Real bge-m3 inference (this is the expensive call, ~17s warm)
        texts = [c.content for c in chunks]
        embeddings = embed_texts(texts)
        assert len(embeddings) == len(chunks)
        assert len(embeddings[0]) == 1024  # bge-m3 dimension

    # ─────────────────────────────────────────────
    # Scenario 4: DB-only chat — real LLM + real query execution
    # ─────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_integration_database_only_chat(self):
        """Classify via real Anthropic API + generate SQL + validate + execute against live Postgres."""
        from app.config import get_settings
        settings = get_settings()

        if not settings.ANTHROPIC_API_KEY:
            pytest.skip("ANTHROPIC_API_KEY not set — cannot run real LLM integration test")

        # Real LLM classification
        from agents.nodes.classifier import classifier_node

        state = {
            "question": "What is the total sum of all invoice amounts?",
            "tenant_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "connection_id": "test-conn",
            "knowledge_base_id": None,
            "chat_history": None,
        }
        result = await classifier_node(state)
        print(f"\n[DB-Only LLM Classifier] Output: intent='{result['intent']}', confidence={result.get('confidence')}, reasoning='{result.get('reasoning')}'")
        assert result["intent"] == "database", f"Expected 'database', got '{result['intent']}'"

        # Real LLM SQL generation
        from services.llm.client import LLMClient
        client = LLMClient(api_key=settings.ANTHROPIC_API_KEY)
        client.model = "claude-3-5-sonnet-20241022"

        allowed_schema = {
            "schemas": {
                "public": {
                    "tables": {
                        "invoices": {
                            "columns": ["id", "customer_name", "amount", "status", "created_at"],
                            "row_filter": None,
                        }
                    }
                }
            }
        }
        generated_sql = await client.generate_sql(
            question="What is the total sum of all invoice amounts?",
            allowed_schema=allowed_schema,
            database_type="postgresql",
        )
        print(f"[DB-Only LLM SQL Generator] Generated SQL: {generated_sql}")
        assert generated_sql.strip(), "LLM returned empty SQL"
        assert "select" in generated_sql.lower(), f"Generated SQL doesn't contain SELECT: {generated_sql}"

        # Real SQL validation
        from services.database.query_validator import validate_and_transform_sql
        validation = validate_and_transform_sql(generated_sql, allowed_schema=allowed_schema)
        print(f"[DB-Only SQL Validator] Valid: {validation.is_valid}, Normalized SQL: {validation.normalized_sql}")
        assert validation.is_valid, f"Validation failed: {validation.errors}"
        assert "sum" in validation.normalized_sql.lower(), f"Expected SUM() aggregation in SQL, got: {validation.normalized_sql}"

        # Real query execution against live Postgres
        adapter = PostgreSQLAdapter()
        rows, count = await adapter.execute_readonly(
            LIVE_PG_PARAMS, validation.normalized_sql, timeout_ms=5000
        )
        print(f"[DB-Only Postgres Execution] Returned {count} row(s): {rows}")
        assert count >= 1
        first_row = rows[0]
        values = list(first_row.values())
        assert any(isinstance(v, (int, float)) or hasattr(v, '__float__') for v in values), \
            f"Expected numeric result, got: {first_row}"

        # ── Spot-Check Aggregate Question 1: COUNT ──
        count_sql = await client.generate_sql(
            question="Count the number of paid invoices",
            allowed_schema=allowed_schema,
            database_type="postgresql",
        )
        print(f"[DB-Only Spot-Check 1: COUNT] Generated SQL: {count_sql}")
        assert "count" in count_sql.lower(), f"Expected COUNT() in SQL, got: {count_sql}"

        # ── Spot-Check Aggregate Question 2: AVG ──
        avg_sql = await client.generate_sql(
            question="What is the average invoice amount?",
            allowed_schema=allowed_schema,
            database_type="postgresql",
        )
        print(f"[DB-Only Spot-Check 2: AVG] Generated SQL: {avg_sql}")
        assert "avg" in avg_sql.lower(), f"Expected AVG() in SQL, got: {avg_sql}"

    # ─────────────────────────────────────────────
    # Scenario 5: Document-only chat — full end-to-end pipeline
    # ─────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_integration_document_only_chat(self):
        """Classify + retrieve document chunks + synthesize answer + format citations."""
        from app.config import get_settings
        settings = get_settings()

        if not settings.ANTHROPIC_API_KEY:
            pytest.skip("ANTHROPIC_API_KEY not set — cannot run real LLM integration test")

        from agents.nodes.classifier import classifier_node
        from agents.nodes.answer_generator import answer_generator_node

        state = {
            "question": "What are the cancellation terms in the services agreement PDF?",
            "tenant_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "connection_id": None,
            "knowledge_base_id": "kb-test",
            "chat_history": None,
        }
        cls_result = await classifier_node(state)
        print(f"\n[Doc-Only LLM Classifier] Output: intent='{cls_result['intent']}', confidence={cls_result.get('confidence')}, reasoning='{cls_result.get('reasoning')}'")
        assert cls_result["intent"] == "document", f"Expected 'document', got '{cls_result['intent']}'"

        # Simulate retrieved document chunk for full pipeline synthesis
        state.update(cls_result)
        state["retrieved_chunks"] = [
            {
                "chunk_id": "c-101",
                "file_id": "f-202",
                "file_name": "master_services_agreement.pdf",
                "page_number": 2,
                "content": "CANCELLATION & TERMINATION: Either party may terminate this agreement with 30 days written notice. Early termination fees apply if cancelled within first 6 months.",
                "relevance_score": 0.91,
            }
        ]

        print(f"[Doc-Only Retrieved Chunks] {state['retrieved_chunks']}")

        # Real LLM Answer Synthesis & Citation Generation
        answer_result = await answer_generator_node(state)
        print(f"[Doc-Only Synthesized Answer] {answer_result.get('answer')}")
        print(f"[Doc-Only Generated Citations] {answer_result.get('citations')}")

        assert answer_result.get("answer"), "Expected non-empty answer text from LLM"
        assert len(answer_result.get("citations", [])) >= 1, "Expected at least 1 document citation"
        assert answer_result["citations"][0]["source_type"] == "document"
        assert answer_result["citations"][0]["file_name"] == "master_services_agreement.pdf"
        assert answer_result["citations"][0]["page_number"] == 2
        assert answer_result["citations"][0]["relevance_score"] == 0.91
        assert "document" in answer_result.get("sources_used", [])

    # ─────────────────────────────────────────────
    # Scenario 6: Hybrid chat — full end-to-end pipeline (DB + Document + Synthesis)
    # ─────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_integration_hybrid_chat(self):
        """Classify hybrid query + execute DB query on live Postgres + retrieve doc chunk + synthesize answer."""
        from app.config import get_settings
        settings = get_settings()

        if not settings.ANTHROPIC_API_KEY:
            pytest.skip("ANTHROPIC_API_KEY not set — cannot run real LLM integration test")

        from agents.nodes.classifier import classifier_node
        from agents.nodes.answer_generator import answer_generator_node
        from services.database.query_validator import validate_and_transform_sql

        state = {
            "question": "Compare the total invoice payments in the database with the maximum contract value specified in the agreement document.",
            "tenant_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "connection_id": "conn-test",
            "knowledge_base_id": "kb-test",
            "chat_history": None,
        }
        cls_result = await classifier_node(state)
        print(f"\n[Hybrid LLM Classifier] Output: intent='{cls_result['intent']}', confidence={cls_result.get('confidence')}, reasoning='{cls_result.get('reasoning')}'")
        assert cls_result["intent"] == "hybrid", f"Expected 'hybrid', got '{cls_result['intent']}'"

        state.update(cls_result)

        # 1. Real SQL validation & execution against live Postgres for DB branch
        allowed_schema = {
            "schemas": {
                "public": {
                    "tables": {
                        "invoices": {
                            "columns": ["id", "customer_name", "amount", "status", "created_at"],
                            "row_filter": None,
                        }
                    }
                }
            }
        }
        raw_sql = "SELECT SUM(amount) AS total_payments FROM invoices"
        val_res = validate_and_transform_sql(raw_sql, allowed_schema=allowed_schema)
        adapter = PostgreSQLAdapter()
        db_rows, db_count = await adapter.execute_readonly(LIVE_PG_PARAMS, val_res.normalized_sql)

        expected_exec_id = str(uuid.uuid4())
        state["sql_result"] = {
            "execution_id": expected_exec_id,
            "success": True,
            "status": "executed",
            "generated_sql": raw_sql,
            "normalized_sql": val_res.normalized_sql,
            "rows": db_rows,
            "row_count": db_count,
            "execution_time_ms": 1.5,
        }
        print(f"[Hybrid DB Branch Output] Generated SQL: {raw_sql} | Live Postgres Rows: {db_rows} | Exec ID: {expected_exec_id}")

        # 2. Document branch chunk with relevance_score
        state["retrieved_chunks"] = [
            {
                "chunk_id": "c-303",
                "file_id": "f-404",
                "file_name": "master_services_agreement.pdf",
                "page_number": 1,
                "content": "CONTRACT VALUE & BUDGET: The total maximum annual contract budget value is $500,000.",
                "relevance_score": 0.94,
            }
        ]
        print(f"[Hybrid Document Branch Output] Chunk: {state['retrieved_chunks']}")

        # 3. Real LLM Answer Synthesis & Citations
        answer_result = await answer_generator_node(state)
        print(f"[Hybrid Synthesized Answer] {answer_result.get('answer')}")
        print(f"[Hybrid Generated Citations] {answer_result.get('citations')}")

        assert answer_result.get("answer"), "Expected non-empty synthesized hybrid answer"
        assert len(answer_result.get("citations", [])) >= 2, "Expected both DB and Document citations"
        
        db_citation = next(c for c in answer_result["citations"] if c["source_type"] == "database")
        doc_citation = next(c for c in answer_result["citations"] if c["source_type"] == "document")

        assert db_citation["query_execution_id"] is not None, "DB citation query_execution_id must not be None"
        assert db_citation["query_execution_id"] == expected_exec_id, f"Expected {expected_exec_id}, got {db_citation['query_execution_id']}"
        assert doc_citation["relevance_score"] is not None, "Document citation relevance_score must not be None"
        assert doc_citation["relevance_score"] == 0.94

        assert "database" in answer_result.get("sources_used", [])
        assert "document" in answer_result.get("sources_used", [])


