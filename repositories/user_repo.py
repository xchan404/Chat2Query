"""User repository — tenant-scoped."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.user import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user operations, scoped by tenant_id."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_username(self, tenant_id: uuid.UUID, username: str) -> User | None:
        """Get a user by username within a tenant."""
        stmt = (
            select(User)
            .where(
                User.tenant_id == tenant_id,
                User.username == username,
            )
            .options(selectinload(User.roles))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, tenant_id: uuid.UUID, email: str) -> User | None:
        """Get a user by email within a tenant."""
        stmt = select(User).where(
            User.tenant_id == tenant_id,
            User.email == email,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_roles(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> User | None:
        """Get a user by ID with their roles eagerly loaded."""
        stmt = (
            select(User)
            .where(
                User.id == user_id,
                User.tenant_id == tenant_id,
            )
            .options(selectinload(User.roles))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_across_tenants(self, user_id: uuid.UUID) -> User | None:
        """Get user by ID without tenant scoping — ONLY for login flow
        where the tenant_id is not yet known (user provides username,
        we look up which tenant they belong to).
        """
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_username_across_tenants(self, username: str) -> User | None:
        """Find user by username across all tenants — ONLY for login flow."""
        stmt = (
            select(User)
            .where(User.username == username)
            .options(selectinload(User.roles))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
