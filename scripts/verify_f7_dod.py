"""Definition of Done Verification Script for Phase F7 (Audit Log View).

Proves:
1. Non-admin user (acme_analyst) is blocked by backend with 403 Forbidden on GET /api/audit-logs.
2. Admin user (acme_admin) can access GET /api/audit-logs (200 OK).
3. A real action (creating a database connection) generates an audit entry.
4. The audit entry immediately appears in the audit logs list.
"""

import asyncio
import httpx
from app.main import app

async def verify_f7_dod():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("=== Step 1: Login as Non-Admin (acme_analyst) & Admin (acme_admin) ===")
        res_analyst = await client.post("/api/auth/login", json={"username": "acme_analyst", "password": "analyst123"})
        assert res_analyst.status_code == 200, f"Analyst login failed: {res_analyst.text}"
        analyst_token = res_analyst.json()["access_token"]
        print("[OK] Analyst login successful")

        res_admin = await client.post("/api/auth/login", json={"username": "acme_admin", "password": "admin123"})
        assert res_admin.status_code == 200, f"Admin login failed: {res_admin.text}"
        admin_token = res_admin.json()["access_token"]
        print("[OK] Admin login successful")

        print("\n=== Step 2: Test Backend Direct Gate (403 for Non-Admin) ===")
        res_analyst_gate = await client.get("/api/audit-logs", headers={"Authorization": f"Bearer {analyst_token}"})
        print(f"Analyst GET /api/audit-logs status code: {res_analyst_gate.status_code}")
        print(f"Analyst GET /api/audit-logs response body: {res_analyst_gate.json()}")
        assert res_analyst_gate.status_code == 403, f"Expected 403, got {res_analyst_gate.status_code}"
        assert res_analyst_gate.json()["detail"] == "Role 'admin' required"
        print("[OK] Backend Authorization Gate verified: 403 Forbidden for non-admin user")

        print("\n=== Step 3: Fetch Initial Audit Logs as Admin ===")
        res_admin_initial = await client.get("/api/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_admin_initial.status_code == 200
        initial_logs = res_admin_initial.json()
        initial_count = len(initial_logs)
        print(f"[OK] Initial Audit Logs count for Admin: {initial_count}")

        print("\n=== Step 4: Perform a Real Action (Create Database Connection) ===")
        import uuid
        conn_name = f"Audit Test Conn {str(uuid.uuid4())[:6]}"
        conn_payload = {
          "name": conn_name,
          "database_type": "postgresql",
          "host": "localhost",
          "port": 5432,
          "database_name": "platform",
          "username": "platform_user",
          "password": "platform_pass"
        }
        create_conn_res = await client.post(
            "/api/database-connections",
            json=conn_payload,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Create connection status: {create_conn_res.status_code}")
        assert create_conn_res.status_code == 201, f"Create connection failed: {create_conn_res.text}"
        conn_id = create_conn_res.json()["id"]
        print(f"[OK] Connection created with ID: {conn_id}")

        print("\n=== Step 5: Verify New Event Appears in Audit Logs ===")
        res_admin_updated = await client.get("/api/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_admin_updated.status_code == 200
        updated_logs = res_admin_updated.json()
        print(f"[OK] Updated Audit Logs count for Admin: {len(updated_logs)}")

        latest_entry = updated_logs[0] if len(updated_logs) > 0 else None
        print(f"\nLatest Audit Log Entry:\n  ID: {latest_entry['id']}\n  Action: {latest_entry['action']}\n  Resource Type: {latest_entry['resource_type']}\n  Resource ID: {latest_entry['resource_id']}\n  Description: {latest_entry['description']}\n  Timestamp: {latest_entry['created_at']}")
        
        assert len(updated_logs) > initial_count, "Expected new audit log entry to be created!"
        assert latest_entry["action"] == "connection_created"
        assert latest_entry["resource_id"] == conn_id
        print("\n[SUCCESS] Phase F7 Definition of Done completely verified!")

if __name__ == "__main__":
    asyncio.run(verify_f7_dod())
