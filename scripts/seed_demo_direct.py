"""Seed script — direct SQL version for local dev without async ORM lazy-load issues.

Run: python scripts/seed_demo_direct.py
"""

import asyncio
import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://platform_user:platform_pass@localhost:5432/platform",
)
# Strip asyncpg+ prefix for raw asyncpg
PG_DSN = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").replace(
    "postgresql+psycopg2://", "postgresql://"
)


async def seed() -> None:
    conn = await asyncpg.connect(PG_DSN)

    try:
        # Check if already seeded
        existing = await conn.fetchval("SELECT COUNT(*) FROM tenants")
        if existing > 0:
            print(f"⚠️  Database already has {existing} tenant(s) — skipping seed.")
            print("   Delete the tenants table data first if you want to re-seed.")
            return

        print("Seeding demo data...")

        # ── Tenant A: Acme Corp ──────────────────────────────────────────────
        tenant_a_id = await conn.fetchval(
            "INSERT INTO tenants (name, slug) VALUES ($1, $2) RETURNING id",
            "Acme Corp", "acme-corp",
        )

        role_admin_a_id = await conn.fetchval(
            "INSERT INTO roles (tenant_id, name, description) VALUES ($1, $2, $3) RETURNING id",
            tenant_a_id, "admin", "Full access",
        )
        role_analyst_a_id = await conn.fetchval(
            "INSERT INTO roles (tenant_id, name, description) VALUES ($1, $2, $3) RETURNING id",
            tenant_a_id, "analyst", "Read-only data access",
        )

        # Hash passwords using bcrypt directly (same as core/security.py)
        import bcrypt
        admin_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
        analyst_hash = bcrypt.hashpw(b"analyst123", bcrypt.gensalt()).decode()

        admin_a_id = await conn.fetchval(
            """INSERT INTO users (tenant_id, email, username, password_hash, full_name)
               VALUES ($1, $2, $3, $4, $5) RETURNING id""",
            tenant_a_id, "admin@acme.com", "acme_admin", admin_hash, "Alice Admin",
        )
        analyst_a_id = await conn.fetchval(
            """INSERT INTO users (tenant_id, email, username, password_hash, full_name)
               VALUES ($1, $2, $3, $4, $5) RETURNING id""",
            tenant_a_id, "analyst@acme.com", "acme_analyst", analyst_hash, "Andy Analyst",
        )

        await conn.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
            admin_a_id, role_admin_a_id,
        )
        await conn.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
            analyst_a_id, role_analyst_a_id,
        )

        # ── Tenant B: Globex Inc ─────────────────────────────────────────────
        tenant_b_id = await conn.fetchval(
            "INSERT INTO tenants (name, slug) VALUES ($1, $2) RETURNING id",
            "Globex Inc", "globex-inc",
        )

        role_admin_b_id = await conn.fetchval(
            "INSERT INTO roles (tenant_id, name, description) VALUES ($1, $2, $3) RETURNING id",
            tenant_b_id, "admin", "Full access",
        )
        role_analyst_b_id = await conn.fetchval(
            "INSERT INTO roles (tenant_id, name, description) VALUES ($1, $2, $3) RETURNING id",
            tenant_b_id, "analyst", "Read-only data access",
        )

        admin_b_id = await conn.fetchval(
            """INSERT INTO users (tenant_id, email, username, password_hash, full_name)
               VALUES ($1, $2, $3, $4, $5) RETURNING id""",
            tenant_b_id, "admin@globex.com", "globex_admin", admin_hash, "Bob Boss",
        )
        analyst_b_id = await conn.fetchval(
            """INSERT INTO users (tenant_id, email, username, password_hash, full_name)
               VALUES ($1, $2, $3, $4, $5) RETURNING id""",
            tenant_b_id, "analyst@globex.com", "globex_analyst", analyst_hash, "Gina Graphs",
        )

        await conn.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
            admin_b_id, role_admin_b_id,
        )
        await conn.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
            analyst_b_id, role_analyst_b_id,
        )

        print("✅ Seed data created successfully!")
        print()
        print("Tenant A: Acme Corp (slug: acme-corp)")
        print("  - acme_admin   / admin123   (role: admin)")
        print("  - acme_analyst / analyst123 (role: analyst)")
        print()
        print("Tenant B: Globex Inc (slug: globex-inc)")
        print("  - globex_admin   / admin123   (role: admin)")
        print("  - globex_analyst / analyst123 (role: analyst)")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
