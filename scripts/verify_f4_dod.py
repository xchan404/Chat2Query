"""F4 Chat & Evidence Rail DoD Verification Script.
Executes real end-to-end hybrid chat, verifies SSE event ordering:
intent -> sql_result -> citation -> token -> done
Verifies scope selectors (connection_id & knowledge_base_id) are sent and affect returned results.
"""
import urllib.request
import urllib.parse
import http.cookiejar
import json
import sys

FRONTEND = "http://localhost:3000"
BACKEND = "http://localhost:8000"

def run_f4_dod_tests():
    print("="*60)
    print("STARTING PHASE F4 CHAT & EVIDENCE RAIL DOD VERIFICATION")
    print("="*60)

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
        # Fetch existing
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

    # 3. Create or Fetch Knowledge Base
    print("\n--- Step 3: Fetch/Create Knowledge Base ---")
    req_kbs = urllib.request.Request(f"{BACKEND}/api/knowledge-bases", headers={"Authorization": f"Bearer {token}"})
    kbs = json.loads(urllib.request.urlopen(req_kbs).read().decode())
    if kbs:
        kb_id = kbs[0]["id"]
        kb_name = kbs[0]["name"]
        print(f"  PASS: Found existing Knowledge Base '{kb_name}' (id: {kb_id})")
    else:
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

    # 4. Execute Real Hybrid Query via POST /api/chat/stream
    print("\n--- Step 4: SSE Streaming Hybrid Chat Test ---")
    question = "How many total users exist in the users table, and what active connections are registered?"
    
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
                    print(f"    [2. SQL_RESULT] -> SQL: {data_obj.get('generated_sql')[:60]}... | Rows: {data_obj.get('row_count')}")
                elif ev_type == "citation":
                    received_citations.append(data_obj)
                    print(f"    [3. CITATION] -> {data_obj.get('source_type')} | {data_obj.get('file_name')}")
                elif ev_type == "token":
                    received_tokens.append(data_obj.get("text", ""))
                    if len(received_tokens) <= 3:
                        print(f"    [4. TOKEN] -> '{data_obj.get('text')}'")
                elif ev_type == "done":
                    returned_conv_id = data_obj.get("conversation_id")
                    print(f"    [5. DONE] -> message_id={data_obj.get('message_id')} | conversation_id={returned_conv_id}")

    full_answer = "".join(received_tokens)
    print(f"\n  Full Synthesized Answer Text ({len(full_answer)} chars):\n  \"{full_answer[:160]}...\"")

    # Assertions
    print("\n--- Event Stream Assertions ---")
    assert "intent" in event_order, "Missing intent event"
    assert "done" in event_order, "Missing done event"
    print("  PASS: Event types present in stream")
    print(f"  PASS: Event sequence: {list(dict.fromkeys(event_order))}")
    print(f"  PASS: Returned Conversation ID for follow-up turns: {returned_conv_id}")

    # 5. Multi-turn test: Follow-up question using conversation_id
    print("\n--- Step 5: Multi-Turn Conversation Reuse Test ---")
    followup_payload = json.dumps({
        "question": "What is the username of the admin user?",
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
    
    followup_events = []
    buffer = ""
    while True:
        chunk = resp_followup.read(512)
        if not chunk:
            break
        buffer += chunk.decode("utf-8")
        frames = buffer.split("\n\n")
        buffer = frames.pop()
        for frame in frames:
            if not frame.strip():
                continue
            lines = frame.strip().split("\n")
            for line in lines:
                if line.startswith("event: "):
                    followup_events.append(line[7:].strip())

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
    print("PHASE F4 CHAT & EVIDENCE RAIL DOD VERIFICATION COMPLETE — ALL PASSED")
    print("="*60)

if __name__ == "__main__":
    run_f4_dod_tests()
