"""Role repository — tenant-scoped."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.role import Role
from repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """Repository for role operations, scoped by tenant_id."""

    def __init__(self, session: AsyncSession):
        super().__init__(Role, session)

    async def get_by_name(self, tenant_id: uuid.UUID, name: str) -> Role | None:
        """Get a role by name within a tenant."""
        stmt = select(Role).where(
            Role.tenant_id == tenant_id,
            Role.name == name,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
