"""Tenant repository — not tenant-scoped (tenants are the root entity)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.tenant import Tenant


class TenantRepository:
    """Repository for tenant operations. Not scoped by tenant_id
    since tenants are the root entity."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        """Get a tenant by ID."""
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Tenant | None:
        """Get a tenant by slug."""
        stmt = select(Tenant).where(Tenant.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, tenant: Tenant) -> Tenant:
        """Create a new tenant."""
        self.session.add(tenant)
        await self.session.flush()
        await self.session.refresh(tenant)
        return tenant

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[Tenant]:
        """List all tenants."""
        stmt = select(Tenant).limit(limit).offset(offset).order_by(Tenant.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
