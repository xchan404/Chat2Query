"""Knowledge base CRUD routes."""

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import NotFoundError
from core.tenant_context import CurrentUser, get_current_user
from repositories.file_repo import KnowledgeBaseRepository
from schemas.file import KnowledgeBaseCreate, KnowledgeBaseOut

router = APIRouter(prefix="/api/knowledge-bases", tags=["knowledge-bases"])


@router.post("", response_model=KnowledgeBaseOut, status_code=201)
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBaseOut:
    """Create a new knowledge base."""
    repo = KnowledgeBaseRepository(db)
    kb = await repo.create(
        tenant_id=uuid.UUID(current_user.tenant_id),
        name=data.name,
        description=data.description,
    )
    await db.commit()
    return KnowledgeBaseOut.model_validate(kb)


@router.get("", response_model=list[KnowledgeBaseOut])
async def list_knowledge_bases(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeBaseOut]:
    """List all knowledge bases for the current tenant."""
    repo = KnowledgeBaseRepository(db)
    kbs = await repo.list_by_tenant(uuid.UUID(current_user.tenant_id))
    return [KnowledgeBaseOut.model_validate(kb) for kb in kbs]


@router.get("/{kb_id}", response_model=KnowledgeBaseOut)
async def get_knowledge_base(
    kb_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBaseOut:
    """Get a knowledge base by ID."""
    repo = KnowledgeBaseRepository(db)
    kb = await repo.get_by_id(uuid.UUID(current_user.tenant_id), kb_id)
    if kb is None:
        raise NotFoundError("Knowledge base not found")
    return KnowledgeBaseOut.model_validate(kb)


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(
    kb_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a knowledge base."""
    repo = KnowledgeBaseRepository(db)
    deleted = await repo.delete_by_id(uuid.UUID(current_user.tenant_id), kb_id)
    if not deleted:
        raise NotFoundError("Knowledge base not found")
    await db.commit()
