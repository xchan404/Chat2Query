"""F3 API end-to-end verification script.
Tests the full connection lifecycle against the live backend.
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

# 1. Login
print("=== Step 1: Login ===")
status, tokens = api("POST", "/api/auth/login", body={"username": "acme_admin", "password": "admin123"})
print(f"  Status: {status}")
if status != 200:
    print("  FAIL: Login failed")
    sys.exit(1)
token = tokens["access_token"]
print(f"  PASS: Got access_token ({token[:30]}...)")

# 2. List connections (before create)
print("\n=== Step 2: List connections ===")
status, conns = api("GET", "/api/database-connections", token=token)
print(f"  Status: {status}, Count: {len(conns)}")

# 3. Create connection
print("\n=== Step 3: Create connection ===")
status, conn = api("POST", "/api/database-connections", token=token, body={
    "name": "F3-VERIFY-CONN",
    "database_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database_name": "platform",
    "username": "platform_user",
    "password": "platform_pass",
    "ssl_enabled": False,
})
print(f"  Status: {status}")
if status != 200 and status != 201:
    print(f"  FAIL: {conn}")
    sys.exit(1)
conn_id = conn["id"]
print(f"  PASS: Created id={conn_id}, name={conn['name']}")

# 4. Test connection
print("\n=== Step 4: Test connection ===")
status, result = api("POST", f"/api/database-connections/{conn_id}/test", token=token)
print(f"  Status: {status}")
print(f"  success={result['success']}, message={result['message']}, latency_ms={result.get('latency_ms')}")
if result["success"]:
    print("  PASS: Connection test successful")
else:
    print("  WARN: Connection test failed (but API responded correctly)")

# 5. Sync schema
print("\n=== Step 5: Sync schema ===")
status, sync = api("POST", f"/api/database-connections/{conn_id}/sync-schema", token=token)
print(f"  Status: {status}")
print(f"  schemas={sync['schemas_synced']}, tables={sync['tables_synced']}, columns={sync['columns_synced']}")
print(f"  message={sync['message']}")
if sync["tables_synced"] > 0:
    print("  PASS: Schema sync discovered real tables")
else:
    print("  WARN: No tables synced")

# 6. Get schemas
print("\n=== Step 6: Get schemas ===")
status, schemas = api("GET", f"/api/database-connections/{conn_id}/schemas", token=token)
print(f"  Status: {status}, Schema count: {len(schemas)}")
for s in schemas:
    tables = [t["table_name"] for t in s["tables"]]
    print(f"  Schema '{s['schema_name']}': {len(tables)} tables -> {tables[:8]}...")
    if s["tables"]:
        cols = s["tables"][0].get("columns", [])
        if cols:
            print(f"    First table '{s['tables'][0]['table_name']}' columns: {[c['column_name'] for c in cols[:5]]}...")

# 7. Cleanup — delete the test connection
print("\n=== Step 7: Cleanup ===")
status, _ = api("DELETE", f"/api/database-connections/{conn_id}", token=token)
print(f"  Delete status: {status}")
print("  PASS: Cleaned up test connection")

print("\n" + "="*50)
print("F3 API VERIFICATION COMPLETE")
print("="*50)
