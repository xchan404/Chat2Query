# Build Progress

## Phase 1 — Foundations & Auth ✅

- [x] Project skeleton, `config.py` (pydantic-settings reading `.env`), `logging_config.py` (structured JSON logs)
- [x] Alembic set up, initial migration = full schema from section 5
- [x] `tenants`, `users`, `roles`, `user_roles` models + repos
- [x] `core/security.py`: password hashing (bcrypt direct), JWT issue/verify, refresh rotation
- [x] `core/tenant_context.py`: FastAPI dependency that extracts `tenant_id`/`user_id`/roles from JWT
- [x] Routes: `POST /api/auth/login`, `POST /api/auth/refresh`, `GET /api/auth/me`
- [x] `scripts/seed_demo_data.py` — creates 2 tenants, users/roles each
- [x] Unit tests: 20 passing (security + tenant isolation)

**Definition of Done**: ✅

**Notes**:
- Replaced `passlib[bcrypt]` with direct `bcrypt` — passlib is unmaintained and incompatible with bcrypt >= 4.1
- Full schema (all 17 tables) created in initial Alembic migration, but only auth tables have repos/routes — remaining tables are model stubs for later phases

---

## Phase 2 — Live DB Connections + Encryption ✅

- [x] `core/encryption.py`: Fernet encrypt/decrypt helpers for `encrypted_password` / `encrypted_connection_string`
- [x] `services/database/adapters/base.py`: abstract adapter interface (`test_connection`, `list_schemas`, `list_tables`, `list_columns`, `execute_readonly`, dialect name for SQLGlot)
- [x] `adapters/postgresql.py`, `adapters/mysql.py` implementations
- [x] `services/database/connection_service.py` + `connection_tester.py`
- [x] Routes: full CRUD on `/api/database-connections`, plus `POST /{id}/test`
- [x] Connection pooling: short-TTL cache of live connections keyed by `connection_id`, decrypted only in memory, never logged

**Definition of Done**: ✅

---

## Phase 3 — Schema Discovery & Permissions ✅

- [x] `services/database/schema_discovery.py` + `metadata_cache.py`: introspect via adapter, populate `database_schemas`/`database_tables`/`database_columns`
- [x] Routes: `POST /{id}/sync-schema`, `GET /{id}/schemas`, `GET /{id}/tables`
- [x] `table_permissions` / `column_permissions` models + repos + CRUD routes
- [x] `core/permissions.py`: resolve effective `allowed_schema`

**Definition of Done**: ✅

---

## Phase 4 — Text-to-SQL + Validation + Execution ✅

- [x] `services/llm/` thin wrapper around Anthropic API (single place to swap models/providers)
- [x] `services/database/query_validator.py` (SQL Safety Pipeline per Section 7)
- [x] `services/database/query_executor.py` — executes via read-only adapter, enforces `SQL_STATEMENT_TIMEOUT_MS` and `SQL_MAX_ROWS`, writes `query_executions` row
- [x] `services/database/dialect_resolver.py` — maps `connection.database_type` to SQLGlot dialect
- [x] Basic single-source chat path wired end-to-end (`POST /api/query/sql`)

**Definition of Done**: ✅

---

## Phase 5 — File Ingestion + Embedding + Retrieval ✅

- [x] `services/documents/parsers/` — PDF (PyMuPDF with page tracking), DOCX, XLSX/CSV, TXT
- [x] `services/documents/chunking_service.py` — ~500-token chunks with overlap and page-number tracking
- [x] `services/documents/embedding_service.py` — `bge-m3` loaded once as a thread-safe singleton model at startup, batch chunk embedding
- [x] `services/documents/upload_service.py` + `document_processor.py` — pipeline: parse → chunk → embed → store, updates `files.processing_status`
- [x] `vector_store/search.py` — pgvector cosine similarity search scoped by `tenant_id` + `knowledge_base_id`
- [x] `services/documents/retrieval_service.py` — similarity-score-based top-k chunk retrieval
- [x] Routes: `/api/files/upload`, `/api/files/{id}/reprocess`, `/api/knowledge-bases` CRUD

**Definition of Done**: ✅

---

## Phase 6 — LangGraph Orchestrator, Hybrid Chat, Streaming ✅

- [x] `agents/state.py` — shared AgentState dictionary with `chat_history` context
- [x] `agents/nodes/` — `classifier.py`, `database.py`, `document.py`, `hybrid_merger.py`, `answer_generator.py`
- [x] `agents/graph.py` — orchestrator workflow running DB and Document nodes concurrently (`asyncio.gather`) in hybrid mode
- [x] Conversation context loading: queries recent messages from prior turns before classification/synthesis so follow-up questions resolve properly
- [x] Routes: `POST /api/chat` (sync) and `POST /api/chat/stream` (SSE emitting typed events: `intent`, `sql_result`, `citation`, `token`, `done`)

**Definition of Done**: ✅

---

## Phase 7 — Conversations, Citations, Audit Log ✅

- [x] `repositories/conversation_repo.py` — conversation history, message details, and citation lookups
- [x] `services/audit/audit_service.py` — central audit logging service
- [x] Audit logging wired across all endpoints: connection tests, schema syncs, permission changes, and chat turns
- [x] Routes: `GET /api/conversations`, `GET /api/conversations/{id}`, `DELETE /api/conversations/{id}`
- [x] Routes: `GET /api/messages/{id}/citations`, `GET /api/messages/{id}/sql`
- [x] Routes: `GET /api/audit-logs`

**Definition of Done**: ✅
- Conversations and message histories round-trip cleanly via `/api/conversations`.
- Standalone `/api/messages/{id}/citations` and `/api/messages/{id}/sql` return citations and SQL execution records linked to chat turns.
- Audit log entries recorded for connection tests, schema syncs, permission updates, and chat executions.
- 105 passing unit tests.

---

## Phase 8 — Tests, Security Hardening, Docs, Packaging
- [ ] Integration tests
- [ ] Security tests (cross-tenant, unauthorized table/column/row, destructive/multi-statement/comment SQL)
- [ ] `README.md`, `Dockerfile`, final `docker-compose.yml`
- [ ] OpenAPI export + example `curl` requests
