"""Repositories for DatabaseSchema, DatabaseTable, DatabaseColumn."""

import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.schema_metadata import DatabaseSchema, DatabaseTable, DatabaseColumn


class SchemaRepository:
    """Repository for schema metadata operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_schemas_by_connection(self, connection_id: uuid.UUID) -> list[DatabaseSchema]:
        """Get all schemas for a connection with tables and columns loaded."""
        stmt = (
            select(DatabaseSchema)
            .where(DatabaseSchema.connection_id == connection_id)
            .options(
                selectinload(DatabaseSchema.tables).selectinload(DatabaseTable.columns)
            )
            .order_by(DatabaseSchema.schema_name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_schema_by_name(
        self, connection_id: uuid.UUID, schema_name: str
    ) -> DatabaseSchema | None:
        """Get a schema by connection ID and name."""
        stmt = (
            select(DatabaseSchema)
            .where(
                DatabaseSchema.connection_id == connection_id,
                DatabaseSchema.schema_name == schema_name,
            )
            .options(
                selectinload(DatabaseSchema.tables).selectinload(DatabaseTable.columns)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def clear_schemas_by_connection(self, connection_id: uuid.UUID) -> None:
        """Clear all schema metadata for a connection prior to sync."""
        stmt = delete(DatabaseSchema).where(DatabaseSchema.connection_id == connection_id)
        await self.session.execute(stmt)
        await self.session.flush()

    async def save_schema(self, schema: DatabaseSchema) -> DatabaseSchema:
        """Save a database schema entity."""
        self.session.add(schema)
        await self.session.flush()
        return schema
