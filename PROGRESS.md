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
- Can register two tenants (via seed script)
- Can log in as a user in each
- `GET /api/auth/me` returns correctly scoped identity
- Token from tenant A carries different tenant_id than tenant B
- BaseRepository enforces tenant_id on every query method
- All 20 unit tests pass

**Notes**:
- Replaced `passlib[bcrypt]` with direct `bcrypt` — passlib is unmaintained and incompatible with bcrypt >= 4.1
- Full schema (all 17 tables) created in initial Alembic migration, but only auth tables have repos/routes — remaining tables are model stubs for later phases
- All models include the `processing_status` check constraint and `processing_started_at`/`processed_at` columns on `files` per Section 5

---

## Phase 2 — Live DB Connections + Encryption
- [ ] `core/encryption.py`: Fernet encrypt/decrypt helpers
- [ ] `services/database/adapters/base.py`: abstract adapter interface
- [ ] `adapters/postgresql.py`, `adapters/mysql.py` implementations
- [ ] `services/database/connection_service.py` + `connection_tester.py`
- [ ] Routes: full CRUD on `/api/database-connections`, plus `POST /{id}/test`
- [ ] Connection pooling: short-TTL cache of live connections

## Phase 3 — Schema Discovery & Permissions
- [ ] `services/database/schema_discovery.py` + `metadata_cache.py`
- [ ] Routes: `POST /{id}/sync-schema`, `GET /{id}/schemas`, `GET /{id}/tables`
- [ ] `table_permissions` / `column_permissions` models + repos + CRUD routes
- [ ] `core/permissions.py`: resolve effective `allowed_schema`

## Phase 4 — Text-to-SQL + Validation + Execution
- [ ] `services/llm/` thin wrapper around Anthropic API
- [ ] `services/database/query_validator.py` (SQL Safety Pipeline)
- [ ] `services/database/query_executor.py`
- [ ] `services/database/dialect_resolver.py`
- [ ] Basic single-source chat path wired end-to-end

## Phase 5 — File Ingestion + Embedding + Retrieval
- [ ] `services/documents/parsers/` — PDF, DOCX, XLSX/CSV, TXT
- [ ] `services/documents/chunking_service.py`
- [ ] `services/documents/embedding_service.py`
- [ ] `services/documents/upload_service.py` + `document_processor.py`
- [ ] `vector_store/` — pgvector similarity search
- [ ] `services/documents/retrieval_service.py`
- [ ] Routes: `/api/files/upload`, `/api/knowledge-bases` CRUD

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
