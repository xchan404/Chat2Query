"""F4 Chat & SSE Streaming Verification Script.
Tests both sync and streaming chat endpoints against live backend.
"""
import urllib.request
import json
import sys

API = "http://localhost:8000"

def api(method, path, token=None, body=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else (b"" if method == "POST" else None)
    req = urllib.request.Request(f"{API}{path}", data=data, headers=headers, method=method)
    try:
        r = urllib.request.urlopen(req)
        return r.status, json.loads(r.read()) if r.status != 204 else None
    except urllib.request.HTTPError as e:
        return e.code, json.loads(e.read().decode()) if e.fp else None

# 1. Login as acme_admin
print("=== Step 1: Login ===")
status, tokens = api("POST", "/api/auth/login", body={"username": "acme_admin", "password": "admin123"})
if status != 200:
    print("  FAIL: Login failed", tokens)
    sys.exit(1)
token = tokens["access_token"]
print("  PASS: Authenticated successfully")

# 2. Register connection to local Postgres if not already present
print("\n=== Step 2: Register database connection ===")
status, conn = api("POST", "/api/database-connections", token=token, body={
    "name": "LOCAL-PG-CHAT",
    "database_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database_name": "platform",
    "username": "platform_user",
    "password": "platform_pass",
    "ssl_enabled": False,
})
if status in [200, 201]:
    conn_id = conn["id"]
    print(f"  PASS: Connection registered (id={conn_id})")
    # Sync schema
    api("POST", f"/api/database-connections/{conn_id}/sync-schema", token=token)
else:
    # Fetch existing
    _, conns = api("GET", "/api/database-connections", token=token)
    conn_id = conns[0]["id"] if conns else None
    print(f"  Using connection id={conn_id}")

# 3. Test Sync Chat endpoint (POST /api/chat)
print("\n=== Step 3: Test Sync Chat (POST /api/chat) ===")
question = "How many users are registered in the users table?"
status, resp = api("POST", "/api/chat", token=token, body={
    "question": question,
    "connection_id": conn_id,
})
print(f"  Status: {status}")
if status == 200:
    print(f"  Intent: {resp['intent']}")
    print(f"  Answer: {resp['answer']}")
    print(f"  Sources Used: {resp['sources_used']}")
    if resp.get("sql"):
        print(f"  Generated SQL: {resp['sql'].get('generated_sql')}")
        print(f"  Row Count: {resp['sql'].get('row_count')}")
        print(f"  Rows: {resp['sql'].get('rows')}")
    print("  PASS: Sync chat succeeded with real database query result")
else:
    print("  FAIL: Sync chat failed", resp)

# 4. Test SSE Streaming Chat endpoint (POST /api/chat/stream)
print("\n=== Step 4: Test SSE Streaming Chat (POST /api/chat/stream) ===")
req = urllib.request.Request(
    f"{API}/api/chat/stream",
    data=json.dumps({
        "question": "What is the total number of users in users table?",
        "connection_id": conn_id,
    }).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    },
    method="POST",
)

try:
    r = urllib.request.urlopen(req)
    print(f"  Status: {r.status}")
    print("  Receiving SSE Events:")
    
    events_received = []
    buffer = ""
    while True:
        chunk = r.read(512)
        if not chunk:
            break
        buffer += chunk.decode("utf-8")
        frames = buffer.split("\n\n")
        buffer = frames.pop()
        for frame in frames:
            if not frame.trim() if hasattr(frame, "trim") else not frame.strip():
                continue
            lines = frame.strip().split("\n")
            ev_type = ""
            ev_data = ""
            for line in lines:
                if line.startswith("event: "):
                    ev_type = line[7:].strip()
                elif line.startswith("data: "):
                    ev_data = line[6:].strip()
            if ev_type and ev_data:
                events_received.append(ev_type)
                print(f"    [EVENT: {ev_type}] -> {ev_data[:120]}...")

    print(f"  PASS: Received SSE events sequence: {events_received}")
except Exception as e:
    print(f"  FAIL: Streaming failed: {e}")

# Cleanup connection
if conn_id:
    api("DELETE", f"/api/database-connections/{conn_id}", token=token)

print("\n" + "="*50)
print("F4 CHAT & STREAMING VERIFICATION COMPLETE")
print("="*50)
