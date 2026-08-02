"""Seed script — creates 2 tenants, users, and roles for testing.

Run: python -m scripts.seed_demo_data
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_factory, engine
from core.security import hash_password
from models.tenant import Tenant
from models.user import User
from models.role import Role


async def seed() -> None:
    """Create demo tenants, users, and roles."""
    async with async_session_factory() as session:
        async with session.begin():
            # --- Tenant A: Acme Corp ---
            tenant_a = Tenant(name="Acme Corp", slug="acme-corp")
            session.add(tenant_a)
            await session.flush()

            role_admin_a = Role(tenant_id=tenant_a.id, name="admin", description="Full access")
            role_analyst_a = Role(tenant_id=tenant_a.id, name="analyst", description="Read-only data access")
            session.add_all([role_admin_a, role_analyst_a])
            await session.flush()

            admin_a = User(
                tenant_id=tenant_a.id,
                email="admin@acme.com",
                username="acme_admin",
                password_hash=hash_password("admin123"),
                full_name="Alice Admin",
            )
            analyst_a = User(
                tenant_id=tenant_a.id,
                email="analyst@acme.com",
                username="acme_analyst",
                password_hash=hash_password("analyst123"),
                full_name="Andy Analyst",
            )
            session.add_all([admin_a, analyst_a])
            await session.flush()

            admin_a.roles.append(role_admin_a)
            analyst_a.roles.append(role_analyst_a)

            # --- Tenant B: Globex Inc ---
            tenant_b = Tenant(name="Globex Inc", slug="globex-inc")
            session.add(tenant_b)
            await session.flush()

            role_admin_b = Role(tenant_id=tenant_b.id, name="admin", description="Full access")
            role_analyst_b = Role(tenant_id=tenant_b.id, name="analyst", description="Read-only data access")
            session.add_all([role_admin_b, role_analyst_b])
            await session.flush()

            admin_b = User(
                tenant_id=tenant_b.id,
                email="admin@globex.com",
                username="globex_admin",
                password_hash=hash_password("admin123"),
                full_name="Bob Boss",
            )
            analyst_b = User(
                tenant_id=tenant_b.id,
                email="analyst@globex.com",
                username="globex_analyst",
                password_hash=hash_password("analyst123"),
                full_name="Gina Graphs",
            )
            session.add_all([admin_b, analyst_b])
            await session.flush()

            admin_b.roles.append(role_admin_b)
            analyst_b.roles.append(role_analyst_b)

    print("✅ Seed data created successfully!")
    print()
    print("Tenant A: Acme Corp (slug: acme-corp)")
    print("  - acme_admin / admin123 (role: admin)")
    print("  - acme_analyst / analyst123 (role: analyst)")
    print()
    print("Tenant B: Globex Inc (slug: globex-inc)")
    print("  - globex_admin / admin123 (role: admin)")
    print("  - globex_analyst / analyst123 (role: analyst)")


if __name__ == "__main__":
    asyncio.run(seed())
