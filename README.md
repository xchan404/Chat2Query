# Text-to-SQL & Document Chat Platform

A production-grade, multi-tenant enterprise backend platform for natural language database queries (Text-to-SQL) and document retrieval (RAG), featuring a 8-step SQL Safety Pipeline, LangGraph orchestrator, and real-time SSE streaming.

---

## 1. Overview & Key Capabilities

- **Multi-Tenant Architecture**: Strict row-level and organization-level tenant isolation enforced on every query and API endpoint.
- **Live Database Adapters**: Read-only connection execution for PostgreSQL and MySQL, with connection pooling and credential encryption at rest.
- **SQL Safety Pipeline**: 8-step AST validation using `sqlglot` (rejects DDL/DML, stacked queries, unquoted comments, system schemas; injects row filters and clamps result set `LIMIT`).
- **Document RAG & Vector Search**: Per-page PDF, DOCX, XLSX/CSV, and TXT parsing with page-number-aware chunking and 1024-dimensional dense vector embeddings using `BAAI/bge-m3` via `pgvector`.
- **LangGraph Agent Orchestration**: Parallel execution of database and document branches (`asyncio.gather`), intent classification (`database`, `document`, `hybrid`, `clarification`, `general`), and context resolution across multi-turn chat history.
- **Real-Time Streaming**: Server-Sent Events (SSE) emitting typed frames (`intent`, `sql_result`, `citation`, `token`, `done`) for live UI evidence panel rendering.
- **Audit Logging**: Full audit trail recording connection tests, schema syncs, permission changes, logins, and chat turns.

---

## 2. Setup & Installation

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16 with `pgvector` extension

### Local Environment Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd Chat2Query
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file from `.env.example`:
   ```env
   DATABASE_URL=postgresql+asyncpg://platform_user:platform_pass@localhost:5432/platform
   REDIS_URL=redis://localhost:6379/0
   MINIO_ENDPOINT=localhost:9000
   MINIO_ACCESS_KEY=minioadmin
   MINIO_SECRET_KEY=minioadmin
   MINIO_BUCKET=platform-files
   JWT_SECRET=change-me-to-a-random-secret-in-production
   JWT_ALGORITHM=HS256
   CONNECTION_ENCRYPTION_KEY=change-me-generate-a-real-fernet-key
   ANTHROPIC_API_KEY=your-api-key-here
   EMBEDDING_MODEL=BAAI/bge-m3
   ```

5. **Run database migrations & seed demo data**:
   ```bash
   alembic upgrade head
   python scripts/seed_demo_data.py
   ```

6. **Run local server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## 3. Running with Docker Compose

Run the entire stack (FastAPI app, PostgreSQL with pgvector, Redis, MinIO) in containers:

```bash
docker-compose up --build
```

The application will be accessible at `http://localhost:8000`.

---

## 4. Testing

Run all unit, security, and integration test suites:

```bash
pytest tests/ -v
```

### Test Suites Included:
- **Unit Tests** (`tests/unit/`): Security helpers, encryption round-trip, query validator pipeline, document parsers, chunking page-number accuracy, chat orchestrator.
- **Security Tests** (`tests/security/`):
  - `test_cross_tenant_connection_access_denied`
  - `test_unauthorized_table_access_blocked`
  - `test_unauthorized_column_access_blocked`
  - `test_unauthorized_row_filter_enforced`
  - `test_destructive_sql_blocked`
  - `test_multi_statement_sql_blocked`
  - `test_sql_comment_injection_blocked`
  - `test_oversized_limit_clamped`
- **Integration Tests** (`tests/integration/`): End-to-end document ingestion, chunking, embedding, and hybrid retrieval.

---

## 5. API Documentation & Worked `curl` Examples

Interactive OpenAPI Swagger docs are available at `http://localhost:8000/docs`. The complete schema is exported in [openapi.json](file:///c:/Users/n/Desktop/Chat2Query/openapi.json).

### Worked `curl` Examples

#### 1. Authenticate (Login)
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "owner@acme.com", "password": "password123"}'
```

#### 2. Create & Sync Database Connection
```bash
# Create connection
curl -X POST "http://localhost:8000/api/database-connections" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Postgres",
    "database_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database_name": "production_db",
    "username": "readonly_user",
    "password": "secretpassword"
  }'

# Sync Schema
curl -X POST "http://localhost:8000/api/database-connections/<connection_id>/sync-schema" \
  -H "Authorization: Bearer <token>"
```

#### 3. Upload & Process Document
```bash
curl -X POST "http://localhost:8000/api/files/upload?knowledge_base_id=<kb_id>" \
  -H "Authorization: Bearer <token>" \
  -F "file=@master_contract.pdf"
```

#### 4. Execute Hybrid Chat (Sync)
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the total of all invoice payments in the database versus the contract value in the agreement?",
    "connection_id": "<connection_id>",
    "knowledge_base_id": "<kb_id>"
  }'
```

#### 5. Execute Hybrid Chat (SSE Stream)
```bash
curl -N -X POST "http://localhost:8000/api/chat/stream" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the total invoice payment amount?",
    "connection_id": "<connection_id>"
  }'
```

---

## 6. MVP Scope & Architectural Trade-offs

1. **2 Database Adapters vs 4**:
   - Implemented PostgreSQL and MySQL as representative SQL dialects (covering major ANSI and MySQL-specific variations). Oracle and SQL Server utilize the exact same abstract `BaseAdapter` interface for straightforward future extension.
2. **`pgvector` vs Dedicated Vector Database**:
   - Integrated `pgvector` within PostgreSQL to maintain single-database transactional consistency, unified backup procedures, and simplified tenant isolation via standard SQL `tenant_id` foreign keys without operating a separate vector cluster (e.g. Qdrant/Milvus).
3. **Synchronous Document Processing vs Distributed Task Queue**:
   - Document parsing, chunking, and embedding run inline inside FastAPI request execution for deterministic MVP processing status updates. **Trade-off Notice**: `POST /api/files/upload` execution blocks synchronously, causing up to ~14 seconds of HTTP request hanging for large multi-page PDFs while the PyTorch embedding runs. This is a deliberate simplification to remove external worker queue dependencies (Celery/Redis worker processes), representing a legitimate UX limitation rather than a bug. The pipeline is encapsulated in `services/documents/document_processor.py` for easy future offloading.
4. **Model Selection**:
   - Selected `BAAI/bge-m3` as a thread-safe singleton model (`_get_model()`) loaded once at startup to produce 1024-dimensional dense vectors suitable for multilingual and domain-specific retrieval.

---

## 7. AI Assistance Acknowledgment

This application was developed with pair-programming assistance from **Antigravity**, an AI agentic coding assistant designed by Google DeepMind. Antigravity assisted in architectural planning, SQL safety AST parsing logic, agent node workflow construction, and test suite generation.
