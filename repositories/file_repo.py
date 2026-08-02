"""Repository for File and KnowledgeBase CRUD."""

import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.file import File
from models.knowledge_base import KnowledgeBase


class KnowledgeBaseRepository:
    """Repository for KnowledgeBase operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tenant_id: uuid.UUID, name: str, description: str | None = None) -> KnowledgeBase:
        kb = KnowledgeBase(
            tenant_id=tenant_id,
            name=name,
            description=description,
        )
        self.session.add(kb)
        await self.session.flush()
        return kb

    async def list_by_tenant(self, tenant_id: uuid.UUID) -> list[KnowledgeBase]:
        stmt = (
            select(KnowledgeBase)
            .where(KnowledgeBase.tenant_id == tenant_id)
            .order_by(KnowledgeBase.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, tenant_id: uuid.UUID, kb_id: uuid.UUID) -> KnowledgeBase | None:
        stmt = select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_id(self, tenant_id: uuid.UUID, kb_id: uuid.UUID) -> bool:
        stmt = delete(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0


class FileRepository:
    """Repository for File operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, tenant_id: uuid.UUID, file_id: uuid.UUID) -> File | None:
        stmt = select(File).where(
            File.id == file_id,
            File.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_knowledge_base(
        self, tenant_id: uuid.UUID, knowledge_base_id: uuid.UUID
    ) -> list[File]:
        stmt = (
            select(File)
            .where(
                File.tenant_id == tenant_id,
                File.knowledge_base_id == knowledge_base_id,
            )
            .order_by(File.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_id(self, tenant_id: uuid.UUID, file_id: uuid.UUID) -> bool:
        stmt = delete(File).where(
            File.id == file_id,
            File.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
