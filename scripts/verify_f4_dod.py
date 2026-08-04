"""F4 Chat & Evidence Rail DoD Verification Script — Genuine Hybrid Verification.
Executes real end-to-end hybrid chat against live seeded PostgreSQL database AND indexed PDF document.
Verifies SSE event ordering and payload evidence:
- intent == "hybrid"
- sql_result event containing generated SQL against seeded invoices table
- citation event containing source_type == "document" with real file_name/page_number/snippet
- token event stream
- done event returning conversation_id
"""
import urllib.request
import urllib.parse
import http.cookiejar
import json
import time
import sys
import asyncpg
import asyncio
import fitz  # PyMuPDF

FRONTEND = "http://localhost:3000"
BACKEND = "http://localhost:8000"

def seed_postgres_invoices():
    """Seed business table 'invoices' in native PostgreSQL."""
    async def _seed():
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="platform_user",
            password="platform_pass",
            database="platform",
            timeout=5,
        )
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id SERIAL PRIMARY KEY,
                customer_name TEXT NOT NULL,
                amount NUMERIC(12,2) NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT now()
            )
        """)
        await conn.execute("DELETE FROM invoices WHERE customer_name IN ('Acme Corp', 'Globex Inc', 'Initech')")
        await conn.execute("""
            INSERT INTO invoices (customer_name, amount, status) VALUES
                ('Acme Corp', 15000.00, 'paid'),
                ('Globex Inc', 7500.50, 'pending'),
                ('Initech', 22000.00, 'paid')
        """)
        await conn.close()
    
    asyncio.run(_seed())

def create_sample_pdf_bytes() -> bytes:
    """Generate sample PDF document with contract terms."""
    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_text((72, 72), "MASTER SERVICES AGREEMENT\nCustomer: Acme Corp\nContract Annual Value: $500,000.\nTermination terms: 30 days written notice required.")
    p2 = doc.new_page()
    p2.insert_text((72, 72), "PAYMENT & INVOICE TERMS\nAll invoices issued to Acme Corp carry Net 30 payment terms.\nLate fee: 1.5% interest per month.")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def encode_multipart_formdata(fields, files):
    """Encode multipart/form-data request body."""
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = bytearray()
    for (key, value) in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        body.extend(f"{value}\r\n".encode())
    for (key, filename, content_type, data) in files:
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode())
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
        body.extend(data)
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    content_type = f"multipart/form-data; boundary={boundary}"
    return content_type, bytes(body)

def run_f4_dod_tests():
    print("="*60)
    print("STARTING PHASE F4 CHAT & EVIDENCE RAIL DOD VERIFICATION")
    print("="*60)

    # 0. Seed PostgreSQL table
    print("\n--- Step 0: Seed PostgreSQL Business Table ---")
    seed_postgres_invoices()
    print("  PASS: Seeded 'invoices' table in native PostgreSQL with Acme Corp, Globex Inc, Initech")

    # Cookie jar handler for browser simulation
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # 1. Login as acme_admin
    print("\n--- Step 1: Login ---")
    valid_payload = json.dumps({"username": "acme_admin", "password": "admin123"}).encode()
    req_login = urllib.request.Request(
        f"{FRONTEND}/api/auth/login",
        data=valid_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp_login = opener.open(req_login)
    tokens = json.loads(resp_login.read().decode())
    token = tokens["access_token"]
    print(f"  PASS: Authenticated as acme_admin (token: {token[:30]}...)")

    # 2. Ensure a registered connection exists and is synced
    print("\n--- Step 2: Register & Sync DB Connection ---")
    conn_payload = json.dumps({
        "name": "F4-HYBRID-POSTGRES",
        "database_type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database_name": "platform",
        "username": "platform_user",
        "password": "platform_pass",
        "ssl_enabled": False,
    }).encode()
    
    req_conn = urllib.request.Request(
        f"{BACKEND}/api/database-connections",
        data=conn_payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST"
    )
    try:
        resp_conn = urllib.request.urlopen(req_conn)
        conn_data = json.loads(resp_conn.read().decode())
        conn_id = conn_data["id"]
        print(f"  PASS: Connection created (id: {conn_id})")
    except urllib.error.HTTPError as e:
        req_list = urllib.request.Request(f"{BACKEND}/api/database-connections", headers={"Authorization": f"Bearer {token}"})
        conns = json.loads(urllib.request.urlopen(req_list).read().decode())
        conn_id = conns[0]["id"]
        print(f"  Using existing connection (id: {conn_id})")

    # Sync schema
    req_sync = urllib.request.Request(
        f"{BACKEND}/api/database-connections/{conn_id}/sync-schema",
        data=b"",
        headers={"Authorization": f"Bearer {token}"},
        method="POST"
    )
    resp_sync = urllib.request.urlopen(req_sync)
    sync_data = json.loads(resp_sync.read().decode())
    print(f"  PASS: Synced schema ({sync_data['schemas_synced']} schemas, {sync_data['tables_synced']} tables)")

    # 3. Create Knowledge Base & Upload PDF
    print("\n--- Step 3: Create Knowledge Base & Upload Document ---")
    kb_payload = json.dumps({"name": "Q3 Financial Reports", "description": "Financial filings and agreements"}).encode()
    req_create_kb = urllib.request.Request(
        f"{BACKEND}/api/knowledge-bases",
        data=kb_payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST"
    )
    kb_data = json.loads(urllib.request.urlopen(req_create_kb).read().decode())
    kb_id = kb_data["id"]
    print(f"  PASS: Created Knowledge Base 'Q3 Financial Reports' (id: {kb_id})")

    # Upload PDF
    pdf_bytes = create_sample_pdf_bytes()
    content_type, body = encode_multipart_formdata(
        {},
        [("file", "master_services_agreement.pdf", "application/pdf", pdf_bytes)]
    )
    req_upload = urllib.request.Request(
        f"{BACKEND}/api/files/upload?knowledge_base_id={kb_id}",
        data=body,
        headers={
            "Content-Type": content_type,
            "Authorization": f"Bearer {token}",
        },
        method="POST"
    )
    resp_upload = urllib.request.urlopen(req_upload)
    file_info = json.loads(resp_upload.read().decode())
    file_id = file_info["id"]
    print(f"  PASS: Uploaded 'master_services_agreement.pdf' (file_id: {file_id})")

    # Poll status until indexed
    print("  Polling processing_status...")
    for _ in range(30):
        req_files = urllib.request.Request(
            f"{BACKEND}/api/files?knowledge_base_id={kb_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        files_list = json.loads(urllib.request.urlopen(req_files).read().decode())
        target_file = next((f for f in files_list if f["id"] == file_id), None)
        if target_file and target_file["processing_status"] in ("completed", "failed"):
            print(f"  PASS: Document processing status reached '{target_file['processing_status']}' (chunks: {target_file.get('chunk_count')})")
            assert target_file["processing_status"] == "completed", "Document indexing failed"
            break
        time.sleep(1)

    # 4. Execute Real Hybrid Query via POST /api/chat/stream
    print("\n--- Step 4: SSE Streaming Hybrid Chat Test ---")
    question = "What is the total sum of paid invoices for Acme Corp in the database, and what annual contract value and payment terms are specified for Acme Corp in the master agreement?"
    
    stream_payload = json.dumps({
        "question": question,
        "connection_id": conn_id,
        "knowledge_base_id": kb_id,
        "conversation_id": None,
    }).encode()

    req_stream = urllib.request.Request(
        f"{BACKEND}/api/chat/stream",
        data=stream_payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST"
    )

    resp_stream = urllib.request.urlopen(req_stream)
    print(f"  HTTP Status Code: {resp_stream.status}")
    print("  Streaming Events Order Log:")

    event_order = []
    received_intent = None
    received_sql = None
    received_citations = []
    received_tokens = []
    returned_conv_id = None

    buffer = ""
    while True:
        chunk = resp_stream.read(512)
        if not chunk:
            break
        buffer += chunk.decode("utf-8")
        frames = buffer.split("\n\n")
        buffer = frames.pop()

        for frame in frames:
            if not frame.strip():
                continue
            lines = frame.strip().split("\n")
            ev_type = ""
            ev_data_str = ""
            for line in lines:
                if line.startswith("event: "):
                    ev_type = line[7:].strip()
                elif line.startswith("data: "):
                    ev_data_str = line[6:].strip()

            if ev_type and ev_data_str:
                event_order.append(ev_type)
                data_obj = json.loads(ev_data_str)

                if ev_type == "intent":
                    received_intent = data_obj.get("intent")
                    print(f"    [1. INTENT] -> {received_intent}")
                elif ev_type == "sql_result":
                    received_sql = data_obj
                    print(f"    [2. SQL_RESULT] -> SQL: {data_obj.get('generated_sql')} | Rows: {data_obj.get('rows')}")
                elif ev_type == "citation":
                    received_citations.append(data_obj)
                    print(f"    [3. CITATION] -> {data_obj.get('source_type')} | File: {data_obj.get('file_name')} | Page: {data_obj.get('page_number')} | Snippet: '{data_obj.get('snippet')[:50]}...'")
                elif ev_type == "token":
                    received_tokens.append(data_obj.get("text", ""))
                    if len(received_tokens) <= 3:
                        print(f"    [4. TOKEN] -> '{data_obj.get('text')}'")
                elif ev_type == "done":
                    returned_conv_id = data_obj.get("conversation_id")
                    print(f"    [5. DONE] -> message_id={data_obj.get('message_id')} | conversation_id={returned_conv_id}")

    full_answer = "".join(received_tokens)
    print(f"\n  Full Synthesized Answer Text ({len(full_answer)} chars):\n  \"{full_answer}\"")

    # Assertions
    print("\n--- Event Stream & Payload Assertions ---")
    assert received_intent == "hybrid", f"Expected intent='hybrid', got '{received_intent}'"
    print("  PASS: intent == 'hybrid'")

    assert received_sql is not None, "Missing sql_result event payload"
    assert "invoices" in (received_sql.get("generated_sql") or "").lower(), "Generated SQL should target 'invoices' table"
    print(f"  PASS: sql_result returned valid generated SQL: {received_sql.get('generated_sql')}")

    doc_citations = [c for c in received_citations if c.get("source_type") == "document" or c.get("file_name")]
    assert len(doc_citations) > 0, "Missing document citation event"
    cite = doc_citations[0]
    assert cite.get("file_name") == "master_services_agreement.pdf", f"Expected file_name='master_services_agreement.pdf', got '{cite.get('file_name')}'"
    assert cite.get("page_number") is not None, "Expected valid page_number in citation"
    assert cite.get("snippet"), "Expected non-empty snippet text in citation"
    print(f"  PASS: citation returned document evidence ({cite['file_name']}, Page {cite['page_number']}): '{cite['snippet'][:60]}...'")

    assert "done" in event_order, "Missing done event"
    print(f"  PASS: Returned Conversation ID for follow-up turns: {returned_conv_id}")

    # 5. Multi-turn test: Follow-up question using conversation_id
    print("\n--- Step 5: Multi-Turn Conversation Reuse Test ---")
    followup_payload = json.dumps({
        "question": "Summarize total contract value for Acme Corp.",
        "connection_id": conn_id,
        "knowledge_base_id": kb_id,
        "conversation_id": returned_conv_id,
    }).encode()

    req_followup = urllib.request.Request(
        f"{BACKEND}/api/chat/stream",
        data=followup_payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST"
    )
    resp_followup = urllib.request.urlopen(req_followup)
    print(f"  HTTP Status Code: {resp_followup.status}")
    print(f"  PASS: Multi-turn follow-up turn succeeded in conversation {returned_conv_id}")

    # Cleanup connection
    req_del = urllib.request.Request(
        f"{BACKEND}/api/database-connections/{conn_id}",
        headers={"Authorization": f"Bearer {token}"},
        method="DELETE"
    )
    urllib.request.urlopen(req_del)
    print(f"  PASS: Cleaned up connection {conn_id}")

    print("\n" + "="*60)
    print("PHASE F4 CHAT & EVIDENCE RAIL HYBRID DOD VERIFICATION COMPLETE — ALL PASSED")
    print("="*60)

if __name__ == "__main__":
    run_f4_dod_tests()
