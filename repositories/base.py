"""Generic tenant-scoped CRUD repository.

Every query method requires tenant_id — no escape hatch.
This is the single enforcement point for cross-tenant data isolation.
"""

import uuid
from typing import Generic, Sequence, Type, TypeVar

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Base repository providing tenant-scoped CRUD operations."""

    def __init__(self, model: Type[ModelT], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, tenant_id: uuid.UUID, entity_id: uuid.UUID) -> ModelT | None:
        """Get a single entity by ID, scoped to tenant."""
        stmt = select(self.model).where(
            self.model.id == entity_id,
            self.model.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, tenant_id: uuid.UUID, *, limit: int = 100, offset: int = 0) -> Sequence[ModelT]:
        """List all entities for a tenant with pagination."""
        stmt = (
            select(self.model)
            .where(self.model.tenant_id == tenant_id)
            .limit(limit)
            .offset(offset)
            .order_by(self.model.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, entity: ModelT) -> ModelT:
        """Create a new entity. Caller must set tenant_id on the entity."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update_by_id(
        self, tenant_id: uuid.UUID, entity_id: uuid.UUID, values: dict
    ) -> ModelT | None:
        """Update an entity by ID, scoped to tenant."""
        stmt = (
            update(self.model)
            .where(
                self.model.id == entity_id,
                self.model.tenant_id == tenant_id,
            )
            .values(**values)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def delete_by_id(self, tenant_id: uuid.UUID, entity_id: uuid.UUID) -> bool:
        """Delete an entity by ID, scoped to tenant. Returns True if deleted."""
        stmt = delete(self.model).where(
            self.model.id == entity_id,
            self.model.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def count(self, tenant_id: uuid.UUID) -> int:
        """Count entities for a tenant."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(self.model).where(
            self.model.tenant_id == tenant_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
