"""Direct SSE Test using http.client to stream line-by-line.
"""
import http.client
import json

# 1. Login to get token
conn = http.client.HTTPConnection("localhost", 8000)
login_body = json.dumps({"username": "acme_admin", "password": "admin123"})
conn.request("POST", "/api/auth/login", login_body, {"Content-Type": "application/json"})
res = conn.getresponse()
tokens = json.loads(res.read())
token = tokens["access_token"]
print("1. Login OK, token obtained.")

# 2. Register connection
conn_body = json.dumps({
    "name": "F4-SSE-TEST",
    "database_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database_name": "platform",
    "username": "platform_user",
    "password": "platform_pass",
    "ssl_enabled": False,
})
conn.request("POST", "/api/database-connections", conn_body, {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
})
res_conn = conn.getresponse()
conn_data = json.loads(res_conn.read())
conn_id = conn_data.get("id")
print(f"2. Connection registered: {conn_id}")

# 3. Stream Chat Response via POST /api/chat/stream
stream_body = json.dumps({
    "question": "How many users exist in the users table?",
    "connection_id": conn_id,
})

conn.request("POST", "/api/chat/stream", stream_body, {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
})

res_stream = conn.getresponse()
print(f"3. Stream Status: {res_stream.status}")
print("   Events Received:")

events = []
while True:
    line = res_stream.readline()
    if not line:
        break
    line_str = line.decode("utf-8").strip()
    if line_str.startswith("event:"):
        ev_name = line_str.split(":")[1].strip()
        events.append(ev_name)
        print(f"     [EVENT]: {ev_name}")
    elif line_str.startswith("data:"):
        print(f"     [DATA ]: {line_str[6:][:100]}...")

print(f"\n4. Final SSE Event Sequence: {events}")

# Cleanup
if conn_id:
    conn.request("DELETE", f"/api/database-connections/{conn_id}", headers={"Authorization": f"Bearer {token}"})
    conn.getresponse().read()

print("5. Test complete.")
