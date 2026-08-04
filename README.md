<div align="center">

<a href="https://github.com/xchan404/Chat2Query">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=600&size=40&pause=1000&color=FFFFFF&center=true&vCenter=true&width=800&lines=CHAT2QUERY+%2F%2F+CONTROL+ENGINE;Enterprise+Multi-Tenant+Data;Text-to-SQL+%2B+Document+RAG" alt="Typing SVG" />
</a>

<p align="center">
  <b>Transform natural language into safe, tenant-isolated SQL queries and dense vector document search with real-time SSE evidence transparency.</b>
</p>

[![Next.js](https://img.shields.io/badge/Next.js-16.2-black?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16_pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-FF6F00?style=for-the-badge&logo=chainlink&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![TailwindCSS](https://img.shields.io/badge/Styling-Serious_Enterprise-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Pytest](https://img.shields.io/badge/Tests-123_Passed-2EA44F?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/)

</div>

<br/>

## 📖 Table of Contents
- [📖 Table of Contents](#-table-of-contents)
- [🖼️ Visual Demos](#-visual-demos)
- [✨ Key Capabilities](#-key-capabilities)
- [🏗️ System Architecture](#️-system-architecture)
- [🛡️ 8-Step SQL Safety Pipeline](#️-8-step-sql-safety-pipeline)
- [🚀 Quick Start Guide](#-quick-start-guide)
- [🐳 Docker Compose Deployment](#-docker-compose-deployment)
- [🧪 Testing & Quality Assurance](#-testing--quality-assurance)
- [📡 API Usage (`curl`)](#-api-usage-curl)
- [💡 MVP Architectural Trade-offs & Documented Notices](#-mvp-architectural-trade-offs--documented-notices)

---

## 🖼️ Visual Demos

Here is **Chat2Query** operating cleanly in real time, featuring a high-contrast Serious Enterprise UI:

| 1. Real-Time Chat Query & Evidence Ledger | 2. Fine-Grained RBAC & Schema Permission Matrix |
| :---: | :---: |
| ![Chat Workspace Demo](images/serious_enterprise_chat.png) | ![Permissions Matrix Demo](images/serious_enterprise_permissions.png) |
| *Live natural language query execution, intent routing, and exposed SQL AST evidence panel* | *Table-level read/write/none access, row-level SQL filters, and column masking* |

---

## ✨ Key Capabilities

- 🛡️ **8-Step AST SQL Safety Pipeline**: Validates raw SQL through `sqlglot` before execution. Rejects DDL/DML, stacked queries, unquoted comment injections, system catalog access, and enforces tenant row filters and result set limit clamping.
- ⚡ **LangGraph Agent Orchestration**: Parallelized branch execution (`asyncio.gather`) combining SQL generation, document dense vector retrieval (`BAAI/bge-m3`), intent classification, and multi-turn context resolution.
- 📡 **Real-Time SSE Streaming**: Emits typed Server-Sent Event frames (`intent`, `sql_result`, `citation`, `token`, `done`) powering live exposed evidence ledger panels on the frontend.
- 🔒 **Multi-Tenant Isolation**: Enforces organization-level and row-level tenant boundary isolation on every database adapter query, document vector lookup, and REST endpoint.
- 🏢 **Serious Enterprise UI**: Built with Next.js 16 (App Router) and Tailwind CSS. Features a Bloomberg/SAP-inspired data-dense layout, Charcoal Obsidian palettes, pure white surfaces, and full keyboard accessibility.
- 📜 **Audit Trail & Governance**: Comprehensive audit logging recording connection tests, schema syncs, role-based permission mutations, file uploads, logins, and chat turns.
- ⚠️ **Resilient LLM Error Handling**: Safely intercepts upstream LLM provider outages (e.g., Anthropic API credit exhaustion) and securely bubbles graceful, descriptive error boundaries to the client UI instead of defaulting to unverified hallucinatory fallbacks.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Client ["Frontend (Next.js 16 + React Query + Tailwind)"]
        UI["Neo-Brutalist UI"]
        CmdK["Command Palette (Ctrl+K)"]
        Rail["Exposed Evidence Ledger"]
    end

    subgraph API ["Backend Gateway (FastAPI)"]
        Auth["JWT & Tenant Middleware"]
        Router["REST & SSE Endpoints"]
        Audit["Audit Logging Service"]
    end

    subgraph Engine ["LangGraph Orchestrator Engine"]
        Classifier["Intent Node (classifier_node)"]
        DBNode["SQL Generation Node (sql_node)"]
        DocNode["RAG Vector Node (rag_node)"]
        Synthesizer["Response Synthesis Node"]
    end

    subgraph Security ["SQL Safety Pipeline (sqlglot AST)"]
        ASTCheck["1. Single Statement Check"]
        TypeCheck["2. SELECT-only AST Check"]
        SchemaCheck["3. Schema Permitted Check"]
        TenantCheck["4. Row Filter Injection (tenant_id)"]
        LimitCheck["5. LIMIT Clamping (max 100)"]
    end

    subgraph Data ["Data Stores & Adapters"]
        PG[("Platform Postgres (pgvector)")]
        TargetDB[("Live Adapters (Postgres / MySQL)")]
        MinIO[("MinIO File Storage")]
    end

    UI -->|"POST /api/chat/stream"| Router
    Router --> Auth
    Auth --> Classifier
    Classifier --> DBNode
    Classifier --> DocNode
    DBNode --> Security
    Security -->|"Safe SQL"| TargetDB
    DocNode -->|"bge-m3 Embeddings"| PG
    Synthesizer -->|"SSE Token Stream"| Rail
    Router --> Audit
    Audit --> PG
```

---

## 🛡️ 8-Step SQL Safety Pipeline

Every database query generated by the LLM **MUST** pass all 8 steps of the `sqlglot` AST safety validator before touching a live database connection:

1. **Single Statement Validation**: Rejects multi-statement queries containing `;` chaining.
2. **Read-Only AST Validation**: Ensures the top-level AST node is strictly a `Select` statement (blocks `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`).
3. **Comment Injection Filtering**: Strips `--` and `/* */` comments that attempt to bypass AST parsing rules.
4. **Forbidden Schema & System Table Protection**: Rejects access to `information_schema`, `pg_catalog`, `mysql`, `sys`, and system functions (`pg_sleep()`, `version()`).
5. **Role & Schema Permission Enforcement**: Checks table permissions against tenant-configured RBAC rules.
6. **Automatic Row-Filter Injection**: Injects tenant `WHERE` clauses (e.g. `tenant_id = 'acme'`) into the AST dynamically.
7. **Column-Level Allowed & Masked Controls**: Strips unauthorized columns or applies SQL masking expressions (e.g. `MD5(email)` or `NULL`).
8. **Result-Set LIMIT Clamping**: Enforces hard upper limits on query results (defaults to `LIMIT 100`) to prevent memory exhaustion.

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 16** (with `pgvector` extension) or Docker Desktop

### 1. Repository Setup

```bash
git clone https://github.com/xchan404/Chat2Query.git
cd Chat2Query
```

### 2. Backend Environment & Dependencies

```bash
# Create and activate Python virtual environment
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
```

Create a `.env` file in the root directory:

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
ANTHROPIC_API_KEY=sk-ant-dummy
EMBEDDING_MODEL=BAAI/bge-m3
```

Run database migrations and seed demo data:

```bash
alembic upgrade head
python scripts/seed_demo_data.py
```

Start the backend server:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Frontend Setup

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 🐳 Docker Compose Deployment

To launch the full containerized stack (FastAPI Backend, Next.js Frontend, Postgres 16 + pgvector, Redis, MinIO):

```bash
docker-compose up --build
```

- **Frontend UI**: `http://localhost:3000`
- **Backend API Docs**: `http://localhost:8000/docs`

---

## 🧪 Testing & Quality Assurance

Run the comprehensive 123-test suite covering unit logic, AST security rules, encryption, and end-to-end integration flows:

```bash
pytest tests/ -v
```

### Test Suite Breakdown
- **Unit Tests** (`tests/unit/`): AST query validator, Fernet connection encryption, document chunking page accuracy, chat orchestrator nodes.
- **Security Tests** (`tests/security/`): Cross-tenant access denial, DDL/DML rejection, comment injection blocking, column masking, row-filter enforcement.
- **Integration Tests** (`tests/integration/`): End-to-end document parsing, vector store insertion, and SSE stream orchestration.

---

## 📡 API Usage (`curl`)

### 1. Authenticate (Login)
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "acme_admin", "password": "admin123"}'
```

### 2. Register Live Database Connection
```bash
curl -X POST "http://localhost:8000/api/database-connections" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Analytics",
    "database_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database_name": "platform",
    "username": "platform_user",
    "password": "platform_pass"
  }'
```

### 3. Execute Real-Time SSE Chat Query
```bash
curl -N -X POST "http://localhost:8000/api/chat/stream" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What database tables exist in the schema and what are their total row counts?"
  }'
```

---

## 💡 MVP Architectural Trade-offs & Documented Notices

1. **Synchronous Upload Request Blocking**:
   - `POST /api/files/upload` executes document parsing, chunking, and dense vector embedding synchronously inline during request execution. **Trade-off Notice**: Uploading large multi-page PDFs can block the HTTP response for up to ~14 seconds while embedding runs. This was a deliberate design choice to avoid complex external task worker queue dependencies (Celery/Redis worker processes) for MVP simplicity.
2. **pgvector Native Local Fallback**:
   - In environments where native local PostgreSQL lacks the `pgvector` extension, vector embedding columns silently degrade to standard `text`. For dense vector similarity search, run the provided `docker-compose.yml` environment containing `pgvector/pgvector:pg16`.
3. **Anthropic API Credits Requirement**:
   - The Text-to-SQL generation engine relies directly on the Anthropic API (Claude 3.5). In order for natural language queries to be successfully converted into SQL, your `ANTHROPIC_API_KEY` must have a positive credit balance. If your account is out of credits, the API will return a 400 Bad Request error, which the backend will catch and return as a graceful error message to the frontend UI. Ensure you top up credits at `console.anthropic.com`.

---

<div align="center">

<p>
  <b>Built for Enterprise Rigor</b><br/>
  <a href="https://github.com/xchan404/Chat2Query/issues">Report Bug</a> &bull; <a href="https://github.com/xchan404/Chat2Query/issues">Request Feature</a>
</p>

</div>
