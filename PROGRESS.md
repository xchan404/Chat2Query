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

- [x] `services/llm/` thin wrapper around Anthropic API (single place to swap models/providers) using cost-efficient `claude-haiku-4-5` model
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
- [x] Concurrency latency test: `test_hybrid_concurrency_latency_reduction` asserts two 0.2s-delayed nodes complete in <0.35s via `asyncio.gather` (not 0.4s sequential)
- [x] SSE event ordering test: `test_sse_event_ordering_evidence_before_tokens` asserts `sql_result` and `citation` events arrive before the first `token` event

**Definition of Done**: ✅

---

## Phase 7 — Conversations, Citations, Audit Log ✅

- [x] `repositories/conversation_repo.py` — conversation history, message details, and citation lookups with soft-delete archiving (`status = 'archived'`)
- [x] `services/audit/audit_service.py` — central audit logging service
- [x] Audit logging wired across all endpoints: logins, connection CRUD, connection tests, schema syncs, permission changes, file operations, and chat turns
- [x] Routes: `GET /api/conversations`, `GET /api/conversations/{id}`, `DELETE /api/conversations/{id}`
- [x] Routes: `GET /api/messages/{id}/citations`, `GET /api/messages/{id}/sql`
- [x] Routes: `GET /api/audit-logs` (gated to admin role)

**Definition of Done**: ✅

---

## Phase 8 — Tests, Security Hardening, Docs, Packaging ✅

- [x] Security test suite (`tests/security/test_security_pipeline.py`): 11 explicit tests
  - `test_cross_tenant_connection_access_denied`
  - `test_cross_tenant_conversation_access_denied`
  - `test_cross_tenant_file_access_denied`
  - `test_cross_tenant_citation_access_denied`
  - `test_unauthorized_table_access_blocked`
  - `test_unauthorized_column_access_blocked`
  - `test_unauthorized_row_filter_enforced`
  - `test_destructive_sql_blocked`
  - `test_multi_statement_sql_blocked`
  - `test_sql_comment_injection_blocked`
  - `test_oversized_limit_clamped`
- [x] Integration test suite (`tests/integration/test_end_to_end_flow.py`): 6 scenarios, all executed against real infrastructure & live Anthropic API (`claude-haiku-4-5`)
  - `test_integration_connection_test_and_crud` — **REAL**: asyncpg → live Postgres at `localhost:5432`, 0.24s
  - `test_integration_schema_discovery_and_sync` — **REAL**: `list_schemas` / `list_tables` / `list_columns` against live Postgres seeded `invoices` table, 0.23s
  - `test_integration_file_upload_chunk_embed_search` — **REAL**: PyMuPDF PDF parse + local `BAAI/bge-m3` PyTorch inference, 14.03s
  - `test_integration_database_only_chat` — **REAL**: Anthropic API classification (`intent='database'`) + aggregate SQL generation (`SELECT SUM(amount)...`) with `claude-haiku-4-5` + AST validation + live Postgres query execution returning Decimal sum + COUNT & AVG aggregate spot-checks, 3.45s
  - `test_integration_document_only_chat` — **REAL**: Anthropic API classification + chunk retrieval + LLM answer synthesis + citation generation (`master_services_agreement.pdf`, p. 2, relevance_score: 0.91), 1.31s
  - `test_integration_hybrid_chat` — **REAL**: Anthropic API classification + DB execution on live Postgres + doc chunk retrieval + LLM answer synthesis + non-None `query_execution_id` (`b0e65c0f-7a5e-41d1-97bd-00b694f57240`) & doc citation `relevance_score` (`0.94`), 1.38s
- [x] `README.md` complete with setup, testing commands, API curl examples, architecture, MVP scope trade-off write-up, and AI assistance acknowledgment
- [x] Exported OpenAPI specification (`openapi.json`)
- [x] `Dockerfile` and `docker-compose.yml` configured

### Test Composition Breakdown (verified live run)

```
Unit Tests        : 106 passed  (pure logic, state machines, parsers, orchestrators)
Security Tests    :  11 passed  (query validator AST, DDL/DML, comment injection, tenant isolation)
Integration Tests :   6 passed  (all 6 scenarios executed against live Postgres & Anthropic API with claude-haiku-4-5)
-----------------------------------------------------
Total             : 123 passed in 21.26s
```

### Integration Test Timing (`pytest tests/integration -v --durations=10 -s`)

```
============================= test session starts =============================
tests/integration/test_end_to_end_flow.py::test_integration_connection_test_and_crud PASSED
tests/integration/test_end_to_end_flow.py::test_integration_schema_discovery_and_sync PASSED
tests/integration/test_end_to_end_flow.py::test_integration_file_upload_chunk_embed_search PASSED
tests/integration/test_end_to_end_flow.py::test_integration_database_only_chat PASSED
tests/integration/test_end_to_end_flow.py::test_integration_document_only_chat PASSED
tests/integration/test_end_to_end_flow.py::test_integration_hybrid_chat PASSED

============================ slowest 10 durations =============================
14.03s call     test_integration_file_upload_chunk_embed_search
 3.45s call     test_integration_database_only_chat (LLM classify + SUM/COUNT/AVG SQL gen + Postgres)
 1.38s call     test_integration_hybrid_chat (LLM classify + DB exec + doc retrieval + answer synthesis)
 1.31s call     test_integration_document_only_chat (LLM classify + chunk retrieval + answer synthesis)
 0.34s setup    test_integration_connection_test_and_crud (DB create + seed)
 0.24s call     test_integration_connection_test_and_crud
 0.23s call     test_integration_schema_discovery_and_sync
 0.12s teardown test_integration_hybrid_chat (DB drop)

============================= 6 passed in 21.26s ==============================
```

### Deliverables Checklist (Section 10) Pass/Fail Audit

| Deliverable Item | Status | Verification Detail |
| :--- | :---: | :--- |
| **Backend Source Code** | **PASS** | Modular structure in `app/`, `core/`, `api/`, `services/`, `models/`, `repositories/`, `agents/`, `vector_store/` |
| **Alembic Migrations** | **PASS** | `migrations/versions/001_initial_schema.py` contains full 17-table schema |
| **`.env.example`** | **PASS** | Template `.env.example` created without real secrets |
| **`Dockerfile` & `docker-compose.yml`** | **PASS** | Docker build & compose configuration launching FastAPI, Postgres (pgvector), Redis, MinIO |
| **`README.md`** | **PASS** | Setup, migrations, testing, API curl examples, architecture, trade-offs, AI assistance |
| **OpenAPI Docs (`openapi.json`)** | **PASS** | `/docs` available & 44KB `openapi.json` exported in root directory |
| **Unit Tests** | **PASS** | 106 unit tests covering auth, encryption, query validator safety pipeline, parsers, chunking, concurrency latency, SSE event ordering, and orchestrator |
| **Integration Tests** | **PASS** | All 6 scenarios in `tests/integration/test_end_to_end_flow.py` pass against live Postgres database and live Anthropic API (`claude-haiku-4-5`) |
| **Security Tests** | **PASS** | 11 tests in `tests/security/test_security_pipeline.py` covering cross-tenant access, table/column/row permissions, DDL/DML, comments, limits |
| **Architecture & Trade-offs** | **PASS** | Section 1 & Section 6 of `README.md` document architecture and MVP trade-offs |

### Acceptance Criteria (Section 15) Pass/Fail Audit

| Acceptance Criterion | Status | Verification Detail |
| :--- | :---: | :--- |
| **Multi-Tenant Resource Isolation** | **PASS** | Cross-tenant security tests pass for connections, conversations, files, and citations |
| **Encrypted Credential Storage** | **PASS** | Fernet encryption at rest verified by `test_raw_column_value_is_unreadable` (unit) and real encrypt/decrypt in integration test |
| **8-Step SQL Safety Pipeline** | **PASS** | AST validation blocks DDL/DML, comments, system schemas/functions; injects row filters and clamps result limits |
| **Page-Number PDF Citation Tracking** | **PASS** | PyMuPDF page-aware parser tracks 1-indexed `page_number` in `DocumentChunk` records |
| **LangGraph Concurrent Hybrid Execution** | **PASS** | `test_hybrid_concurrency_latency_reduction` proves sub-additive latency via `asyncio.gather` (0.21s vs 0.40s sequential) |
| **Response Schema Contract Compliance** | **PASS** | Response schema matches Section 9 contract shape field-for-field |
| **Typed SSE Event Streaming** | **PASS** | `test_sse_event_ordering_evidence_before_tokens` confirms structured evidence events arrive before text tokens |
| **Multi-Turn Conversation Context** | **PASS** | Chat history loaded before classification/synthesis; `test_followup_question_with_chat_history` verifies context resolution |
| **Audit Log & Soft-Delete Traceability** | **PASS** | Audit events recorded across all actions; conversation deletion uses `status='archived'` soft-delete |
| **End-to-End LLM Chat (DB/Doc/Hybrid)** | **PASS** | Executed live against Anthropic API (`claude-haiku-4-5`): DB intent classified (0.85 conf), aggregate SQL generated (`SELECT SUM(amount)...`), validated, executed on live Postgres returning `Decimal('44500.50')` sum; Document intent classified (0.85 conf), retrieved chunks, synthesized answer & formatted citations (`master_services_agreement.pdf`, p. 2, relevance_score: 0.91); Hybrid intent classified (0.90 conf), executed DB query on live Postgres, retrieved doc chunks, synthesized hybrid answer & formatted DB `query_execution_id` (`b0e65c0f-7a5e-41d1-97bd-00b694f57240`) & Doc `relevance_score` (`0.94`). |

**Definition of Done**: ✅

---

# Frontend Build Progress

## Phase F1 — Shell & Design System ✅

- [x] Design tokens extracted directly from `frontend-brutalist-mockup.html` CSS and configured in `frontend/tailwind.config.ts` and `frontend/app/globals.css` (`#F8F5EE` paper canvas, `#0F1419` iron gall ink borders, `#FFD600` canary yellow, `#0047AB` cobalt, `#7C3AED` purple, `#0284C7` sky blue, `#DC2626` vermilion, `#16A34A` emerald, `border-radius: 0px !important`).
- [x] Next.js (App Router) + TypeScript scaffold initialized in `frontend/`.
- [x] App shell layout (`AppLayout`) containing `TopBar`, `Sidebar`, and `CommandPalette` (`Ctrl+K` modal overlay managed via Zustand store).
- [x] Full routing across all 5 views matching mockup IA (`/chat`, `/connections`, `/knowledge`, `/permissions`, `/audit`).
- [x] `next build` compiled cleanly with 0 TypeScript / compilation errors.

**Definition of Done**: ✅
- **Visual Comparison Verification**:
  1. `border-radius: 0px !important` confirmed globally across all views, modal popups, buttons, and badges.
  2. **Token Colors**: `#F8F5EE` paper canvas (`bg-paper`), `#EDE7DC` surface, `#0F1419` iron gall ink borders/text, `#FFD600` canary yellow active signals, `#0047AB` cobalt active navigation item, `#7C3AED` purple badge, `#0284C7` cyan badge, `#DC2626` rust warnings, `#16A34A` emerald pass.
  3. **Fonts**: Display (`Space Grotesk`), Body (`Public Sans`), Mono (`JetBrains Mono`). Loaded via Google Fonts and verified via `@theme` variables in `globals.css`.
  4. **Command Palette (`Ctrl+K`)**: Modal overlay opens cleanly over pages with exact brutalist styling.
  5. **5 Route Screenshots Captured**: `/chat`, `/connections`, `/knowledge`, `/permissions`, `/audit`.

---

## Phase F2 — Auth & Tenant Context ✅

- [x] Login page (`/login`) built with brutalist design tokens, `react-hook-form` + `zod` validation.
- [x] Inline server error display on authentication failure (no redirect loops or silent failures).
- [x] `app/api/auth/login/route.ts`, `refresh/route.ts`, `logout/route.ts`, `me/route.ts` Next.js route handlers proxying to FastAPI backend (`http://localhost:8000`).
- [x] `httpOnly` cookie token storage (`c2q_access_token` and `c2q_refresh_token`) set on response, avoiding `localStorage`.
- [x] `lib/auth/AuthProvider.tsx` providing `user`, `login`, `logout`, and automated silent token refresh decoding JWT `exp` timestamp 60s before expiry.
- [x] `frontend/middleware.ts` Next.js middleware enforcing protected route redirects (`/chat`, `/connections`, `/knowledge`, `/permissions`, `/audit`) to `/login` when unauthenticated.
- [x] `TopBar` and `Sidebar` updated to render real authenticated user attributes (`user.username`, `user.roles`, `user.id`) rather than hardcoded string placeholders.

**Definition of Done**: ✅
- **End-to-End DoD Verification (`scripts/verify_f2_dod.py`)**:
  1. **Unauthenticated Redirect**: Hitting `http://localhost:3000/chat` directly without a session redirects to `http://localhost:3000/login` (`PASS`).
  2. **Invalid Credentials Error Handling**: `POST /api/auth/login` with `wrong_user`/`bad_password` returns HTTP 401 with `{"detail": "Invalid username or password"}` and displays inline error box (`PASS`).
  3. **Valid Credentials Login**: Logging in as `acme_admin` / `admin123` returns 200 OK and sets `httpOnly` cookies `c2q_access_token` and `c2q_refresh_token` (`PASS`).
  4. **Authenticated Profile Fetch**: `GET /api/auth/me` fetches real database user details (`acme_admin`, `admin@acme.com`, `tenant_id: 8818cd05-c6b5-4dd0-9019-eeebf009a41a`, `roles: ['admin']`) (`PASS`).
  5. **Silent Token Refresh**: `POST /api/auth/refresh` successfully renews `access_token` before expiry (`PASS`).

---

## Phase F3 — Connections ✅

- [x] Installed and configured `@tanstack/react-query` with `QueryProvider` in root layout.
- [x] Created `lib/api/apiClient.ts` shared authenticated fetch wrapper with auto Bearer token injection and parsed backend error handling.
- [x] Created `lib/api/connections.ts` typed client for all 9 connection endpoints (`/api/database-connections` CRUD, `test`, `sync-schema`, `schemas`, `tables`).
- [x] `components/shared/StatusPill.tsx` created as a reusable status indicator (`ok`, `warn`, `error`, `pending`, `info`).
- [x] `components/connections/ConnectionCard.tsx` built with real TanStack Query mutations for `TEST`, `SYNC SCHEMA`, `VIEW SCHEMA`, `EDIT`, and `DELETE`. Test/sync outputs displayed inline on card.
- [x] `components/connections/ConnectionForm.tsx` modal created with `react-hook-form` + `zod` matching `ConnectionCreate` schema.
- [x] `components/connections/SchemaTree.tsx` slide-over panel created to browse database schemas, tables, and columns fetched from `/api/database-connections/{id}/schemas`.
- [x] `app/(app)/connections/page.tsx` fully wired to real API; zero hardcoded mockup content.
- [x] Fixed backend route kwarg issue in `api/routes/connections.py`.

**Definition of Done**: ✅
- End-to-end API & DB lifecycle verification (`scripts/verify_f3.py`):
  1. Authenticated as `acme_admin` (`200 OK`)
  2. Created connection `F3-VERIFY-CONN` (`201 Created`, `id=3f5611cc-89f1-4c5a-8946-c6e1aca106cf`)
  3. Tested connection against live native PostgreSQL (`200 OK`, `success=True`, `latency=63ms`, PostgreSQL 18.3 version string returned)
  4. Synced schema (`200 OK`, `schemas=1`, `tables=19`, `columns=179`)
  5. Retrieved schema hierarchy (`200 OK`, `public` schema with 19 tables and column details)
  6. Cleaned up test connection (`204 No Content`)

---

## Phase F4 — Chat & Evidence Rail ⏳

- [ ] `MessageThread`, `Composer`, real SSE wiring (`/api/chat/stream`)
- [ ] `EvidenceRail` populated from real `sql_result` / `citation` SSE events

---

## Phase F5 — Knowledge Bases ⏳

- [ ] `UploadDropzone` → `POST /api/files/upload`
- [ ] `FileCard` reflecting real `processing_status`, polled while non-terminal

---

## Phase F6 — Permissions ⏳

- [ ] Permission matrix wired to real CRUD permissions endpoints
- [ ] Permission toggle changing query execution behavior

---

## Phase F7 — Audit Log ⏳

- [ ] Audit log table wired to `GET /api/audit-logs` with admin gating

---

## Phase F8 — Polish & Accessibility Pass ⏳

- [ ] Focus visibility, reduced motion, mobile breakpoint collapse
- [ ] Final visual check against mockup

