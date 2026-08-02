"""Connection repository — tenant-scoped."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.connection import DatabaseConnection
from repositories.base import BaseRepository


class ConnectionRepository(BaseRepository[DatabaseConnection]):
    """Repository for database connection operations, scoped by tenant_id."""

    def __init__(self, session: AsyncSession):
        super().__init__(DatabaseConnection, session)

    async def get_by_name(
        self, tenant_id: uuid.UUID, name: str
    ) -> DatabaseConnection | None:
        """Get a connection by name within a tenant."""
        stmt = select(DatabaseConnection).where(
            DatabaseConnection.tenant_id == tenant_id,
            DatabaseConnection.name == name,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(
        self, tenant_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[DatabaseConnection]:
        """List active connections for a tenant."""
        stmt = (
            select(DatabaseConnection)
            .where(
                DatabaseConnection.tenant_id == tenant_id,
                DatabaseConnection.is_active == True,
            )
            .limit(limit)
            .offset(offset)
            .order_by(DatabaseConnection.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
