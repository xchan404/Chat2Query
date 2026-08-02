"""Repository for TablePermission and ColumnPermission."""

import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.permission import TablePermission, ColumnPermission


class PermissionRepository:
    """Repository for permission operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_table_permissions_by_connection(
        self, connection_id: uuid.UUID, role_ids: list[uuid.UUID] | None = None
    ) -> list[TablePermission]:
        """Get table permissions for a connection, optionally filtered by role IDs."""
        stmt = (
            select(TablePermission)
            .where(TablePermission.connection_id == connection_id)
            .options(selectinload(TablePermission.column_permissions))
        )
        if role_ids:
            stmt = stmt.where(TablePermission.role_id.in_(role_ids))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_table_permission_by_id(self, permission_id: uuid.UUID) -> TablePermission | None:
        """Get table permission by ID."""
        stmt = (
            select(TablePermission)
            .where(TablePermission.id == permission_id)
            .options(selectinload(TablePermission.column_permissions))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update_table_permission(
        self, permission: TablePermission
    ) -> TablePermission:
        """Save a table permission."""
        self.session.add(permission)
        await self.session.flush()
        return permission

    async def delete_table_permission(self, permission_id: uuid.UUID) -> bool:
        """Delete table permission by ID."""
        stmt = delete(TablePermission).where(TablePermission.id == permission_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
