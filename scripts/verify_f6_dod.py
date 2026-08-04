import asyncio
import uuid
import httpx
from pydantic import BaseModel

API_BASE = "http://localhost:8081"

async def main():
    print("--- Verifying F6 (Permissions) Cross-Phase DoD ---")
    async with httpx.AsyncClient() as client:
        # 1. Login
        login_resp = await client.post(f"{API_BASE}/api/auth/login", json={"username": "acme_admin", "password": "admin123"})
        if login_resp.status_code != 200:
            print(f"Login failed: {login_resp.text}")
            return
            
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get Me and Role IDs
        me_resp = await client.get(f"{API_BASE}/api/auth/me", headers=headers)
        roles_resp = await client.get(f"{API_BASE}/api/auth/roles", headers=headers)
        roles = roles_resp.json()
        
        # We'll apply permission on the 'admin' or first role
        target_role = next(r for r in roles if r["name"] == "admin")
        role_id = target_role["id"]
        
        # 2. Get connections
        conns_resp = await client.get(f"{API_BASE}/api/database-connections", headers=headers)
        conns = conns_resp.json()
        if not conns:
            # Create a test connection if none exists
            conn_payload = {
                "name": "F6 Test",
                "database_type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database_name": "platform",
                "username": "platform_user",
                "password": "platform_pass"
            }
            conn_resp = await client.post(f"{API_BASE}/api/database-connections", json=conn_payload, headers=headers)
            conn_id = conn_resp.json()["id"]
            await client.post(f"{API_BASE}/api/database-connections/{conn_id}/test", headers=headers)
            await client.post(f"{API_BASE}/api/database-connections/{conn_id}/sync-schema", headers=headers)
        else:
            conn_id = conns[0]["id"]

        print(f"Using Connection: {conn_id} and Role: {role_id} (admin)")

        # 3. Baseline query (should succeed if users exists and no block)
        baseline_payload = {
            "question": "How many users are there?",
            "connection_id": conn_id
        }
        
        # We can't guarantee users exist, but if we assume the standard seeded schema from progress:
        baseline_resp = await client.post(f"{API_BASE}/api/chat", json=baseline_payload, headers=headers)
        print("Baseline query status:", baseline_resp.status_code)
        # It could be 400 if the connection is not synced or whatever, let's just make sure we apply a block.
        
        # 4. Create Block Permission
        print("Creating block permission on public.users...")
        perm_payload = {
            "role_id": role_id,
            "connection_id": conn_id,
            "schema_name": "public",
            "table_name": "users",
            "access_type": "none",
            "row_filter": None,
            "column_permissions": []
        }
        
        perm_resp = await client.post(f"{API_BASE}/api/permissions/tables", json=perm_payload, headers=headers)
        if perm_resp.status_code != 201:
            print(f"Failed to create permission: {perm_resp.text}")
            return
            
        perm_id = perm_resp.json()["id"]
        print(f"Created permission: {perm_id}")
        
        # 5. Blocked query
        blocked_resp = await client.post(f"{API_BASE}/api/chat", json=baseline_payload, headers=headers)
        print("Blocked query status:", blocked_resp.status_code)
        print("Blocked query response:", blocked_resp.json() if blocked_resp.status_code == 200 else blocked_resp.text)
        
        # 6. Cleanup
        print(f"Deleting permission: {perm_id}")
        await client.delete(f"{API_BASE}/api/permissions/tables/{perm_id}", headers=headers)
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
