"""Verify backend audit-logs gate for admin vs non-admin user using ASGITransport."""

import asyncio
import httpx
from app.main import app

async def test_audit_logs_gate():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login as acme_admin
        resp = await client.post("/api/auth/login", json={"username": "acme_admin", "password": "admin123"})
        assert resp.status_code == 200, f"Admin login failed: {resp.text}"
        admin_token = resp.json()["access_token"]

        # 2. Login as acme_analyst
        resp = await client.post("/api/auth/login", json={"username": "acme_analyst", "password": "analyst123"})
        assert resp.status_code == 200, f"Analyst login failed: {resp.text}"
        analyst_token = resp.json()["access_token"]

        # 3. Call /api/audit-logs as admin -> should be 200 OK
        resp_admin = await client.get("/api/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
        print(f"Admin GET /api/audit-logs status: {resp_admin.status_code}")
        assert resp_admin.status_code == 200, f"Admin audit logs request failed: {resp_admin.text}"

        # 4. Call /api/audit-logs as analyst -> should be 403 Forbidden
        resp_analyst = await client.get("/api/audit-logs", headers={"Authorization": f"Bearer {analyst_token}"})
        print(f"Analyst GET /api/audit-logs status: {resp_analyst.status_code}")
        print(f"Analyst response body: {resp_analyst.json()}")
        assert resp_analyst.status_code == 403, f"Expected 403 Forbidden, got {resp_analyst.status_code}"

if __name__ == "__main__":
    asyncio.run(test_audit_logs_gate())
