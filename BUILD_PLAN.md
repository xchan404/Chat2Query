# Multi-Tenant Text-to-SQL & Document Chat Platform — Agent Build Plan

This document is the working brief for an AI coding agent (Claude Code or similar) building this
project from the assignment spec. It turns the spec into an ordered, checkable execution plan.

## 0. How to Use This Document

1. Drop this file at the repo root as `BUILD_PLAN.md` (or paste it as the first message / project
   instructions if your agent supports persistent context, e.g. `CLAUDE.md`).
2. Also create an empty `PROGRESS.md` with the phase checklist from Section 6 — have the agent tick
   items off as it completes them, and re-read it at the start of every session. This is what keeps a
   multi-day, multi-session build coherent.
3. Work **one phase at a time**. Do not let the agent start Phase N+1 until Phase N's Definition of
   Done is met — this is the single biggest failure mode for agent-built backends (half-finished
   layers everywhere, nothing fully working).
4. After each phase: read the diff yourself before moving on. You're accountable for the architecture
   decisions per the assignment's individual-work clause — treat the agent as a very fast pair
   programmer, not an autopilot. The assignment also asks you to acknowledge external tools/material
   used in the README, so log agent-assisted sections there as you go rather than reconstructing it at
   the end.

---

## 1. Scope Decisions for a 4-Day Solo Build

The spec describes a system that would realistically take a small team weeks to build well. To hit
every **acceptance criterion** in 4 days, cut infrastructure surface area, not correctness or security.

| Area | Full spec | Recommended MVP scope | Why |
|---|---|---|---|
| DB adapters | Postgres, SQL Server, MySQL, Oracle | **Postgres + MySQL**, built behind a real `adapters/base.py` interface | Proves "runtime-connectable, no source-code change" without burning a day on ODBC/Oracle client installs. Add mssql/oracle later if time remains — same interface, zero refactor. |
| Vector store | pgvector *or* Qdrant | **pgvector only** | One fewer container, one fewer client library, same acceptance criterion satisfied. |
| Background jobs | Celery or Dramatiq | **FastAPI `BackgroundTasks` + a `processing_status` state machine** on `files` | Async processing is what's graded, not the queue technology. Swap in Celery later as a stretch goal — the interface (`documents/upload_service.py` calling `document_processor.py`) doesn't change. |
| Observability | Prometheus + Grafana + OpenTelemetry | **Structured JSON logging + the `audit_logs`/`query_executions` tables** | The spec's actual traceability requirement is satisfied by the DB tables. Metrics dashboards are a stretch goal, not an acceptance criterion. |
| Document parsing | Docling | **Docling if it installs cleanly; fall back to `pypdf` + `python-docx` + `openpyxl` + plain text** per file type | Docling can be heavy/flaky to set up fast. Don't lose a day to it. |
| Embeddings | unspecified model | **`BAAI/bge-m3`** via `sentence-transformers` (or `FlagEmbedding`), run locally | Outputs 1024-dim vectors — matches the `VECTOR(1024)` column in the schema exactly, no dimension mismatch. Multilingual (handles Arabic + English), free, no external API dependency or rate limits during grading/demo. |
| LLM (classify / SQL-gen / RAG answer) | unspecified | **Anthropic Claude via API** — `claude-haiku-4-5` for cheap/fast intent classification, `claude-sonnet-5` for SQL generation and final answer synthesis | Keep it swappable behind a thin `services/llm/` interface so grading judges can't ding you for vendor lock-in, but this is the fastest path given your existing Anthropic tooling. |

Everything else in the spec (multi-tenancy, permissions, SQL validation, encryption, citations, audit
logs, hybrid orchestration) is graded directly and **must not be simplified**.

---

## 2. Final Tech Stack

- **API**: FastAPI, async everywhere (`asyncpg` driver)
- **ORM/migrations**: SQLAlchemy 2.0 (async) + Alembic
- **DB**: PostgreSQL 16 with `pgvector` and `uuid-ossp` extensions
- **Cache**: Redis (session/rate-limit/short-lived schema cache)
- **Object storage**: MinIO (S3-compatible, local via Docker)
- **SQL parsing/validation**: SQLGlot
- **Orchestration**: LangGraph
- **Auth**: JWT (access + refresh), `passlib[bcrypt]` for password hashing, `python-jose` for JWT
- **Credential encryption**: `cryptography.fernet` (symmetric key from env var)
- **Embeddings**: `BAAI/bge-m3` (local, 1024-dim)
- **LLM**: Anthropic API (Haiku for classify, Sonnet for generation)
- **Streaming**: Server-Sent Events (`sse-starlette` or hand-rolled `StreamingResponse`)
- **Testing**: `pytest`, `pytest-asyncio`, `httpx.AsyncClient`
- **Containerization**: Docker + docker-compose

---

## 3. Repository Layout

Use the structure from the assignment as-is, with `schemas/` and `repositories/` filled in (the
assignment left these bare):

```
text-to-sql-platform/
|-- app/                          # main.py, config.py, dependencies.py, exceptions.py, logging_config.py
|-- api/routes/                   # as listed in assignment section 4
|-- core/                         # security.py, encryption.py, permissions.py, constants.py, tenant_context.py
|-- models/                       # SQLAlchemy models, one per table (assignment section 7)
|-- schemas/
|   |-- auth.py                   # LoginRequest, TokenPair, UserOut
|   |-- tenant.py, user.py, role.py
|   |-- connection.py             # ConnectionCreate/Update/Out, TestResult
|   |-- schema_metadata.py        # SchemaOut, TableOut, ColumnOut
|   |-- permission.py             # TablePermissionIn/Out, ColumnPermissionIn/Out
|   |-- file.py, knowledge_base.py
|   |-- conversation.py, message.py
|   |-- chat.py                   # ChatRequest, ChatResponse (matches section 9 contract exactly)
|   `-- citation.py
|-- repositories/
|   |-- base.py                   # generic CRUD repo, tenant-scoped by default
|   |-- tenant_repo.py, user_repo.py, role_repo.py
|   |-- connection_repo.py, schema_repo.py
|   |-- permission_repo.py
|   |-- file_repo.py, knowledge_base_repo.py, chunk_repo.py
|   |-- conversation_repo.py, message_repo.py
|   |-- query_execution_repo.py, citation_repo.py
|   `-- audit_repo.py
|-- services/                     # as listed in assignment section 4
|-- agents/                       # LangGraph graph.py, state.py, nodes/, prompts/
|-- storage/                      # MinIO client wrapper
|-- vector_store/                 # pgvector query helpers (similarity search, upsert)
|-- workers/                      # file-processing background task runner
|-- migrations/                   # Alembic
|-- tests/
|   |-- unit/
|   |-- integration/
|   `-- security/
|-- scripts/                      # seed_demo_data.py, create_admin.py
|-- .env.example
|-- alembic.ini
|-- requirements.txt
|-- Dockerfile
|-- docker-compose.yml
`-- README.md
```

**Repository pattern rule**: `repositories/base.py` should require a `tenant_id` on every query method
and never expose an escape hatch that queries without it. This is your single biggest lever for the
"data from one tenant cannot be accessed by another" acceptance criterion — enforce it in one place,
not scattered across services.

---

## 4. Infra Setup (Phase 0)

`docker-compose.yml` services: `api`, `postgres` (pgvector image, e.g. `pgvector/pgvector:pg16`),
`redis`, `minio`. No Qdrant, no Celery worker container for MVP (add later if time remains).

`.env.example` keys to include (no real values):
```
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/platform
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
MINIO_BUCKET=platform-files
JWT_SECRET=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CONNECTION_ENCRYPTION_KEY=
ANTHROPIC_API_KEY=
EMBEDDING_MODEL=BAAI/bge-m3
SQL_STATEMENT_TIMEOUT_MS=5000
SQL_MAX_ROWS=1000
```

**Definition of Done**: `docker-compose up` brings up all four services; `GET /api/health` returns 200;
`alembic upgrade head` runs clean against the containerized Postgres.

---

## 5. Data Model

Use the schema in assignment section 7 verbatim as the source of truth — it's already well-designed
(tenant_id on every table, proper FKs with cascade rules, JSONB for flexible metadata). Two additions:

- Add a `processing_status` enum-like check constraint on `files` (`pending|processing|completed|failed`)
  since you're not using Celery — this field *is* your job queue state.
- If you skip Celery, add a small `processed_at`/`processing_started_at` pair so you can detect and
  retry stuck files.

Don't restructure the schema beyond this — matching it closely makes the "database migration files /
schema.sql" deliverable trivial to write up.

---

## 6. Build Phases

Check off in `PROGRESS.md` as each Definition of Done is met.

### Phase 1 — Foundations & Auth
- [ ] Project skeleton, `config.py` (pydantic-settings reading `.env`), `logging_config.py` (structured JSON logs)
- [ ] Alembic set up, initial migration = full schema from section 5
- [ ] `tenants`, `users`, `roles`, `user_roles` models + repos
- [ ] `core/security.py`: password hashing, JWT issue/verify, refresh rotation
- [ ] `core/tenant_context.py`: FastAPI dependency that extracts `tenant_id`/`user_id`/roles from the JWT and makes them available to every route via `Depends`
- [ ] Routes: `POST /api/auth/login`, `POST /api/auth/refresh`, `GET /api/auth/me`
- [ ] `scripts/seed_demo_data.py` — creates 2 tenants, a couple of users/roles each, so tenant isolation is testable from day one

**Definition of Done**: can register two tenants (via seed script), log in as a user in each, and confirm `GET /api/auth/me` returns correctly scoped identity. A token from tenant A rejected/irrelevant on any tenant-B-scoped resource (nothing to test yet except the principle — write a placeholder test).

### Phase 2 — Live DB Connections + Encryption
- [ ] `core/encryption.py`: Fernet encrypt/decrypt helpers for `encrypted_password` / `encrypted_connection_string`
- [ ] `services/database/adapters/base.py`: abstract adapter interface (`test_connection`, `list_schemas`, `list_tables`, `list_columns`, `execute_readonly`, dialect name for SQLGlot)
- [ ] `adapters/postgresql.py`, `adapters/mysql.py` implementations
- [ ] `services/database/connection_service.py` + `connection_tester.py`
- [ ] Routes: full CRUD on `/api/database-connections`, plus `POST /{id}/test`
- [ ] Connection pooling: a short-TTL cache of live connections keyed by `connection_id`, decrypted only in memory, never logged

**Definition of Done**: create a connection to a real local Postgres and a real local MySQL via the API, `test` endpoint returns success/failure correctly, credentials are unreadable in the DB (verify by querying the raw column and confirming it's ciphertext), and a new DB type can be added by writing one new adapter file + registering it in a dialect map — no other file changes.

### Phase 3 — Schema Discovery & Permissions
- [ ] `services/database/schema_discovery.py` + `metadata_cache.py`: introspect via adapter, populate `database_schemas`/`database_tables`/`database_columns`
- [ ] Routes: `POST /{id}/sync-schema`, `GET /{id}/schemas`, `GET /{id}/tables`
- [ ] `table_permissions` / `column_permissions` models + repos + CRUD routes
- [ ] `core/permissions.py`: given `(user, connection_id)`, resolve the effective `allowed_schema` dict (merging role-level and user-level grants, matching the shape in assignment section 6)

**Definition of Done**: sync schema on a real connection and see it cached in the app DB (not re-queried from source on every request); grant a role read access to 2 of 5 tables in a test DB; confirm the resolved `allowed_schema` for that role only contains those 2 tables and their permitted columns.

### Phase 4 — Text-to-SQL + Validation + Execution
- [ ] `services/llm/` thin wrapper around the Anthropic API (single place to swap models/providers)
- [ ] `services/database/query_validator.py` — see Section 7 below, this is the security-critical piece
- [ ] `services/database/query_executor.py` — executes via **read-only** DB role, enforces `SQL_STATEMENT_TIMEOUT_MS` and `SQL_MAX_ROWS`, writes a `query_executions` row regardless of outcome
- [ ] `services/database/dialect_resolver.py` — maps `connection.database_type` to the right SQLGlot dialect
- [ ] Basic single-source chat path wired end-to-end: NL question → filtered schema → SQL gen → validate → execute → row_count + preview back to caller (no LangGraph yet — that's Phase 6, prove the mechanics first)

**Definition of Done**: ask a natural-language question against the seeded DB, get back validated SQL and real rows. Ask a question that would touch a column you didn't grant — confirm generation/validation refuses it. Ask for a `DROP TABLE` outright — confirm it never reaches the source DB and is logged as rejected in `query_executions`.

### Phase 5 — File Ingestion + Embedding + Retrieval
- [ ] `services/documents/parsers/` — PDF, DOCX, XLSX/CSV, TXT extractors
- [ ] `services/documents/chunking_service.py` — sensible defaults (e.g. ~500 tokens, overlap), page-number-aware for PDFs
- [ ] `services/documents/embedding_service.py` — loads `bge-m3` once at startup, embeds chunk batches
- [ ] `services/documents/upload_service.py` + `document_processor.py` — orchestrates parse → chunk → embed → store, updates `files.processing_status` at each stage (this is your job-queue substitute)
- [ ] `vector_store/` — pgvector similarity search (cosine) scoped by `tenant_id` + `knowledge_base_id`
- [ ] `services/documents/retrieval_service.py` + a lightweight reranker (can start as similarity-score-only, upgrade to cross-encoder rerank as stretch)
- [ ] Routes: `/api/files/upload`, list/get/delete, `/reprocess`; `/api/knowledge-bases` CRUD

**Definition of Done**: upload a PDF, confirm chunks + embeddings appear in `document_chunks`, ask a question and get back relevant chunks with correct `file_name` + `page_number` for citation.

### Phase 6 — LangGraph Orchestrator, Hybrid Chat, Streaming
- [ ] `agents/state.py` — shared graph state (question, tenant/user context, selected connections/KBs, classified intent, retrieved schema, generated SQL, retrieved chunks, final answer, citations)
- [ ] `agents/nodes/` — request classifier (general/database/document/hybrid/clarification), source selector, the single generic database agent node (per assignment section 6 — **do not** build per-table agents), document RAG node, hybrid merger, final answer generator
- [ ] `agents/graph.py` — wires nodes per the flow in assignment section 5, runs DB + document retrieval in parallel for hybrid
- [ ] Routes: `POST /api/chat` (sync) and `POST /api/chat/stream` (SSE)
- [ ] Response shape matches assignment section 9 exactly (`answer`, `intent`, `sources_used`, `sql`, `citations`)

**Definition of Done**: the exact hybrid example from the assignment (invoice totals vs. contract value) works end-to-end and returns a response matching the documented contract shape.

### Phase 7 — Conversations, Citations, Audit Log
- [ ] `conversations`/`messages` persistence wired into the chat flow (every turn saved, `parent_message_id` chained)
- [ ] `message_citations` populated from both SQL and document sources per turn
- [ ] `audit_logs` — write an entry for every connection test, schema sync, permission change, and chat request (action, resource, ip, request_id)
- [ ] Routes: `/api/conversations` CRUD, `/api/messages/{id}/citations`, `/api/messages/{id}/sql`

**Definition of Done**: full conversation history round-trips through `GET /api/conversations/{id}`; every chat turn is traceable to its `query_execution_id` and/or `chunk_id`s via the citations endpoint.

### Phase 8 — Tests, Security Hardening Pass, Docs, Packaging
- [ ] Unit tests: `query_validator` (every case in Section 7 below), `permissions` resolution logic
- [ ] Integration tests: connection test, schema sync, file upload→search, DB-only chat, document-only chat, hybrid chat
- [ ] Security tests (explicit, named so a grader can find them): cross-tenant access blocked, unauthorized table/column blocked, unauthorized row blocked (row_filter), destructive SQL blocked, multi-statement SQL blocked, SQL comment injection blocked
- [ ] `README.md` per Section 11 below
- [ ] Final `docker-compose.yml` + `Dockerfile` pass — clean `docker-compose up` from scratch
- [ ] OpenAPI: FastAPI gives you `/docs` for free — export it (`openapi.json`) and write 3-4 example `curl` requests into the README for the graders who won't spin up Swagger

**Definition of Done**: every item in Section 10 (Deliverables Checklist) below is checked.

---

## 7. SQL Safety Pipeline (implement exactly, this is graded closely)

In `services/database/query_validator.py`:

1. **Parse**: `sqlglot.parse(sql, dialect=connection_dialect)` — reject if parsing fails or returns more
   than one statement (blocks stacked/multi-statement injection).
2. **Statement type check**: walk the parsed AST's root — only `SELECT`, `WITH`, `EXPLAIN` allowed.
   Reject on `DROP`/`TRUNCATE`/`ALTER`/`CREATE`/`GRANT`/`REVOKE`/`EXEC`/`CALL`/`COPY`/`ATTACH`/`DETACH`
   and on any DML (`INSERT`/`UPDATE`/`DELETE`) unless the connection/table permission explicitly allows
   write and a separate approved-write workflow is used (not the normal chat path).
3. **Comment stripping check**: reject if the raw SQL (pre-parse) contains `--` or `/* */` outside of
   string literals — don't rely on the parser alone to catch comment-based injection tricks.
2. **Reference extraction**: walk the AST for every `Table` and `Column` node; resolve fully-qualified
   names against `dialect_resolver` output.
3. **Permission check**: for each referenced table/column, confirm it exists in the request's resolved
   `allowed_schema` (from Phase 3). Any miss → reject with a specific, loggable reason (never silently
   drop the reference).
4. **System schema block**: reject references to `pg_catalog`, `information_schema`,
   `mysql`/`sys`/`performance_schema`, or anything matching an admin-function name list.
5. **Row filter injection**: for each referenced table with a `row_filter` in `table_permissions`,
   rewrite the AST to AND that filter into the `WHERE` clause (AST manipulation via SQLGlot, never
   string concatenation) — this must happen *after* validation and *cannot* be something the LLM's
   generated SQL can override, since it's applied server-side regardless of what the LLM produced.
6. **Limit enforcement**: if no `LIMIT` present, inject `LIMIT {SQL_MAX_ROWS}`; if a `LIMIT` is present
   and exceeds the max, clamp it.
7. **Execute**: only via a **read-only** DB role/credential, with `statement_timeout` (Postgres) or
   equivalent set per `SQL_STATEMENT_TIMEOUT_MS`.
8. **Log everything**: `generated_sql`, `normalized_sql` (post-rewrite), `validation_status`,
   `validation_errors`, `applied_row_filters`, `referenced_tables`, `referenced_columns` — into
   `query_executions` regardless of whether execution happened.

Write the unit tests for this module *first* (or alongside) — it's the single piece most likely to get
close grading scrutiny, and it's fully testable without a live DB (feed it strings, assert on
`validation_status`/`validation_errors`).

---

## 8. Security Checklist (verify explicitly before submission)

- [ ] Every repository method requires and filters by `tenant_id` — no exceptions
- [ ] JWT claims carry `tenant_id`; every route resolves tenant from the token, never from a request body/query param
- [ ] Connection credentials encrypted at rest (verified by direct DB inspection), decrypted only transiently in memory
- [ ] Read-only DB credentials used for all normal chat execution; a write-capable credential is never used outside an explicitly separate, approved workflow
- [ ] Sensitive columns (`is_sensitive` flag) masked in: LLM prompts, query result previews, logs, and final answers — implement one `mask_value()` helper used everywhere, don't reimplement masking per call site
- [ ] No stack traces or secrets ever returned in an API error response (central exception handler in `app/exceptions.py`)
- [ ] Rate limiting or at least a sane timeout on `/api/chat` to prevent runaway LLM/DB cost
- [ ] `.env.example` contains no real secrets; `.gitignore` excludes `.env`

---

## 9. Testing Plan

- **Unit** (`tests/unit/`): `query_validator` (all reject/accept cases), `permissions` resolution, encryption round-trip, chunking boundaries
- **Integration** (`tests/integration/`): connection CRUD+test against a real Dockerized Postgres/MySQL, schema sync, file upload → chunk → embed → retrieve, DB-only chat, document-only chat, hybrid chat (the invoice/contract example)
- **Security** (`tests/security/`): cross-tenant read attempt (assert 403/empty, never a leak), unauthorized table/column, unauthorized row (row_filter bypass attempt), destructive SQL, multi-statement SQL, SQL-comment injection attempt, oversized `LIMIT` request

Name test functions descriptively (`test_cross_tenant_connection_access_denied`, not `test_1`) — makes
the "security tests demonstrating..." deliverable self-evidently satisfied on a quick scan.

---

## 10. Deliverables Checklist (mirrors assignment Section 14)

- [ ] Backend source code, modular structure as above
- [ ] `migrations/` (Alembic) — or exported `schema.sql`
- [ ] `.env.example`, no real secrets
- [ ] `Dockerfile` + `docker-compose.yml`
- [ ] `README.md` — setup, migrate, run, test, API usage
- [ ] OpenAPI docs (`/docs` + exported `openapi.json`) + example `curl` requests
- [ ] Unit tests for validators + permission logic
- [ ] Integration tests: connection test, schema discovery, file processing, DB chat, document chat, hybrid chat
- [ ] Security tests: unauthorized tables/columns/rows/destructive SQL all blocked
- [ ] Short architecture write-up + diagram (can reuse/adapt the assignment's own diagram, redrawn in your own words)

---

## 11. README Outline

1. Overview (what it does, 3-4 sentences)
2. Architecture summary + diagram
3. Setup: prerequisites, `docker-compose up`, `alembic upgrade head`, seed script
4. Running: how to start the API, where `/docs` lives
5. Testing: `pytest tests/unit`, `pytest tests/integration`, `pytest tests/security`
6. API usage: 3-4 worked `curl` examples (login → create connection → sync schema → chat)
7. Design decisions & trade-offs: explicitly document the Section 1 MVP-scope choices (2 adapters not 4, pgvector not Qdrant, background tasks not Celery) and why — graders read this well; it reads as engineering judgment, not laziness, *if you explain it*
8. Acknowledgments: note that implementation was AI-agent-assisted (per the assignment's own disclosure requirement), and what you designed/decided vs. what the agent scaffolded

---

## 12. Kickoff Prompts (copy-paste per phase)

```
Read BUILD_PLAN.md and PROGRESS.md in full before doing anything.
Implement Phase 1 exactly as specified in Section 6. Do not touch files outside Phase 1's scope.
When done, run the tests, update PROGRESS.md, and stop for review — do not start Phase 2.
```

```
Read BUILD_PLAN.md and PROGRESS.md. Phase 1-3 are marked complete — verify that by skimming the
relevant files, then implement Phase 4 (Text-to-SQL + Validation + Execution), paying special
attention to Section 7 (SQL Safety Pipeline) — implement it exactly as described, it will be tested
closely. Stop after Phase 4's Definition of Done is met.
```

Reuse this pattern for each remaining phase, always pointing back at the relevant Section 6 entry.

---

## 13. Frontend — Design System & Build Plan

A mockup implementing this system is in `frontend-mockup.html` (open it directly in a browser —
it's a real, interactive static prototype, not a screenshot). Everything below documents the
decisions behind it so the agent building the real frontend stays consistent.

### 13.1 Design philosophy

The obvious default for this product is a centered chat column that looks like every other AI
wrapper — bubbles, a purple accent, a single stream of prose you have to trust blindly. That's
wrong for this specific product: the entire value proposition is *auditability*. Every answer is
either a validated SQL execution or a cited document chunk, and the spec requires both to be
traceable. So the UI should look less like a chatbot and more like a **data control room** — an
instrument panel where every reading is backed by a visible source, not a hidden one.

**Signature element — the evidence rail**: a persistent right-hand panel, always visible (not a
modal, not a "sources" link you have to click), that shows the live SQL query, its execution time
and row count, and the exact document excerpt with page number, updating in real time as the
conversation progresses. This isn't decoration — it's the direct visual expression of the
platform's core requirement ("the LLM cannot bypass access controls," "every answer traceable to
execution records and/or chunks"). Nothing about the layout works without it.

Secondary signature detail: small corner-bracket marks on evidence cards (like calibration marks
on an instrument reading) — reinforces "this is a measurement, not a claim."

### 13.2 Design tokens

```css
--ink-0:  #12181F;  /* page background */
--ink-1:  #1A222C;  /* panel surface (sidebar, rail) */
--ink-2:  #212B37;  /* elevated / hover surface */
--ink-3:  #2A3542;  /* nested elevation */
--line:   #2E3947;  /* default hairline border */
--line-strong: #3C4957;

--text-hi:  #E8EAED;  /* primary text */
--text-mid: #A7B0BD;  /* secondary text */
--text-low: #6B7684;  /* muted / metadata / timestamps */

--amber: #E8A33D;   /* evidence / hybrid / verified — the accent */
--cyan:  #5CB2C2;   /* database-sourced content, structural elements */
--sage:  #7DB989;   /* success / connected / validated states */
--brick: #DB6156;   /* error / denied / blocked states */

--font-display: 'IBM Plex Mono';  /* headers, labels, SQL, data, timestamps */
--font-body:    'IBM Plex Sans';  /* prose, chat text, descriptions */
--radius: 6px;
```

Rationale: dark ink-blue base (not pure black) reads as "operations," not "sci-fi AI." Mono type
for structure/headers (not just code) is the one deliberate typographic risk — it signals
"instrument," not "chat app," on sight. Amber is reserved for evidence/verified states only —
resist the urge to use it as a general brand color, or it stops meaning anything. This palette
intentionally avoids the three patterns that read as "generic AI-generated design": warm
cream + terracotta, black + acid-green/neon, and broadsheet hairline-newspaper layouts.

### 13.3 Information architecture

| Screen | Purpose |
|---|---|
| Login / tenant select | Auth, then land in the last-used or default tenant |
| **Chat** (default) | Conversation + persistent evidence rail — the core screen |
| Connections | CRUD + test + schema sync for live DB connections |
| Knowledge bases | Upload, processing status, per-KB file management |
| Permissions | Table/column grant matrix per role, row-filter display |
| Audit log | Searchable/filterable action log |

Layout shell: fixed left nav (workspace switcher + 5 sections) + main content + evidence rail
(chat only — other screens use the freed width). Top bar carries active connection/KB scope
chips and the command palette trigger (Ctrl/Cmd+K) — quick-jump between sections and actions
without hunting through nav, since operators will live in this tool all day.

### 13.4 Frontend tech stack

- **Framework**: Next.js (App Router) + TypeScript — matches your UniHub stack, minimal new tooling
- **Styling**: Tailwind CSS, configured with the tokens above as custom theme values (not inline hex)
- **Component primitives**: Radix UI (unstyled, accessible) or shadcn/ui as a base, restyled to the token system — don't hand-roll dialogs/dropdowns/toggles from scratch, accessibility is easy to get wrong
- **Data/streaming**: native `EventSource` (or a small wrapper) for `/api/chat/stream`; TanStack Query for everything else (connections, files, permissions, audit — all standard REST CRUD)
- **SQL syntax highlighting**: Shiki or `react-syntax-highlighter`
- **State**: Zustand for UI-local state (active view, command palette open/closed, evidence rail contents); TanStack Query owns server state — don't duplicate server data into Zustand
- **Icons**: keep the restrained approach from the mockup (dots, corner brackets, minimal geometric marks) rather than importing a big icon library — it's part of the visual identity, not a gap to fill

### 13.5 Component inventory

`Sidebar`, `TopBar` (scope chips + command trigger), `CommandPalette`, `MessageThread`,
`MessageRow` (variant: db / document / hybrid, driven by `sources_used` from the chat response),
`Composer`, `EvidenceRail`, `SqlEvidenceCard`, `CitationEvidenceCard`, `ConnectionCard`,
`ConnectionTestButton` (owns its own pending/success/error state), `FileCard`, `UploadDropzone`,
`PermissionMatrix`, `PermissionToggle`, `AuditLogRow`, `StatusPill` (ok/warn/err variants used
everywhere — connections, files, audit — one component, not reimplemented per screen).

### 13.6 Frontend build phases

Run these alongside or after the matching backend phase — each depends on its backend API existing.

- [ ] **F1 — Shell**: Next.js scaffold, Tailwind theme from tokens, `Sidebar` + `TopBar` + routing between the 5 views, `CommandPalette` (client-only, no backend yet). *DoD: navigating between sections works, matches the mockup visually.*
- [ ] **F2 — Auth**: login screen, tenant context (React context/provider reading the JWT), protected routes. *DoD: can log in against Phase 1 backend, wrong credentials show an inline error, not a redirect loop.*
- [ ] **F3 — Connections**: `ConnectionCard` grid wired to real CRUD + test endpoint, schema browser (simple tree, expandable). *DoD: create/test/delete a real connection through the UI.*
- [ ] **F4 — Chat + evidence rail**: `MessageThread`, `Composer`, SSE streaming into message text, `EvidenceRail` populated from the real `sql`/`citations` response fields. *DoD: the invoice/contract hybrid example works end-to-end through the real UI, not the mockup's fake data.*
- [ ] **F5 — Knowledge bases**: upload flow with real progress/processing-status polling, `FileCard` reflecting real `processing_status` values. *DoD: upload a real PDF, watch it move from pending → processing → indexed in the UI without a manual refresh.*
- [ ] **F6 — Permissions**: `PermissionMatrix` wired to real table/column permission endpoints, per-role. *DoD: toggling a permission in the UI actually changes what that role's chat queries can touch.*
- [ ] **F7 — Audit log**: filterable/searchable log view. *DoD: an action taken anywhere in the app (test connection, upload file, send chat) shows up here within the session.*
- [ ] **F8 — Polish pass**: keyboard focus visibility, `prefers-reduced-motion` respected, mobile breakpoint (sidebar collapses, evidence rail becomes a slide-over — see the mockup's `@media (max-width: 860px)` block for the pattern), loading/empty/error states for every list view.

### 13.7 Accessibility & responsive floor (non-negotiable, not a stretch goal)

- Every interactive element keyboard-reachable, visible focus ring (the mockup uses `outline: 2px solid var(--amber)`)
- Color is never the only signal — status pills carry text ("Connected", not just a colored dot), evidence card type is labeled, not just colored
- `prefers-reduced-motion` disables the streaming-text and transition effects
- Mobile: sidebar → icon-only rail, evidence rail → slide-over drawer with a toggle (exact CSS pattern in the mockup)
