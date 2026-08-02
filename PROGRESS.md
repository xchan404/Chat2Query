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
- Schema sync introspects target DB and caches metadata in app DB & memory cache
- Table and column permission management routes implemented
- Effective `allowed_schema` resolution engine merges role-level permissions and masks sensitive columns

---

## Phase 4 — Text-to-SQL + Validation + Execution ✅

- [x] `services/llm/` thin wrapper around Anthropic API (single place to swap models/providers)
- [x] `services/database/query_validator.py` (SQL Safety Pipeline per Section 7)
- [x] `services/database/query_executor.py` — executes via read-only adapter, enforces `SQL_STATEMENT_TIMEOUT_MS` and `SQL_MAX_ROWS`, writes `query_executions` row
- [x] `services/database/dialect_resolver.py` — maps `connection.database_type` to SQLGlot dialect
- [x] Basic single-source chat path wired end-to-end (`POST /api/query/sql`)

**Definition of Done**: ✅
- SQL Safety Pipeline implements all 8 steps of Section 7:
  1. Comment stripping check (rejects unquoted `--` and `/* */`)
  2. Parse check (rejects parse errors and stacked/multi-statement SQL)
  3. Statement type check (allows only SELECT/UNION/SELECTABLE, rejects DDL/DML)
  4. Reference extraction (tables and columns, excluding WITH CTE aliases)
  5. Permission check against `allowed_schema`
  6. System schema & admin function block (`pg_catalog`, `information_schema`, `mysql`, `sys`, `pg_sleep`, etc.)
  7. Row filter injection (server-side AST rewrite ANDing `row_filter` into `WHERE`)
  8. Limit enforcement (injects `LIMIT max_rows` if missing or clamps if over limit)
- CTE (`WITH ... AS`) support validated and row filter/limit enforcement preserved.
- Sensitive column masking applied at query result preview layer (`_mask_rows`).

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
- `bge-m3` loaded once at startup as a singleton (`_get_model()`).
- PDF parsing extracts text per-page, preserving accurate `page_number` (1-indexed) in `DocumentChunk` records for multi-page documents.
- Chunks and 1024-dim embeddings stored in `document_chunks` table.
- 89 passing unit tests (including verification of multi-page PDF page number tracking and chunking accuracy).

---

## Phase 6 — LangGraph Orchestrator, Hybrid Chat, Streaming
- [ ] `agents/state.py`, `agents/nodes/`, `agents/graph.py`
- [ ] Routes: `POST /api/chat` (sync) and `POST /api/chat/stream` (SSE)
- [ ] Response shape matches assignment section 9

## Phase 7 — Conversations, Citations, Audit Log
- [ ] Conversations/messages persistence
- [ ] `message_citations` populated
- [ ] `audit_logs` for all actions
- [ ] Routes: `/api/conversations`, `/api/messages/{id}/citations`

## Phase 8 — Tests, Security Hardening, Docs, Packaging
- [ ] Unit tests for `query_validator`, permissions
- [ ] Integration tests
- [ ] Security tests
- [ ] `README.md`, `Dockerfile`, final `docker-compose.yml`
- [ ] OpenAPI export + example `curl` requests
