"""Message-specific lookup routes (citations & SQL execution details)."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import NotFoundError
from core.tenant_context import CurrentUser, get_current_user
from repositories.conversation_repo import ConversationRepository
from schemas.chat import CitationOut, SQLResultOut

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("/{message_id}/citations", response_model=list[CitationOut])
async def get_message_citations(
    message_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CitationOut]:
    """Get standalone list of citations for a specific message."""
    repo = ConversationRepository(db)
    citations = await repo.get_message_citations(
        tenant_id=uuid.UUID(current_user.tenant_id),
        message_id=message_id,
    )

    result = []
    for c in citations:
        result.append(CitationOut(
            source_type=c.source_type,
            query_execution_id=str(c.query_execution_id) if c.query_execution_id else None,
            table_name=c.citation_metadata.get("table_name") if c.citation_metadata else None,
            chunk_id=str(c.chunk_id) if c.chunk_id else None,
            file_name=c.file_name,
            page_number=c.page_number,
            snippet=c.excerpt,
        ))
    return result


@router.get("/{message_id}/sql", response_model=SQLResultOut)
async def get_message_sql(
    message_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SQLResultOut:
    """Get standalone SQL execution details for a specific message."""
    repo = ConversationRepository(db)
    q_exec = await repo.get_message_query_execution(
        tenant_id=uuid.UUID(current_user.tenant_id),
        message_id=message_id,
    )
    if q_exec is None:
        raise NotFoundError("No SQL execution record found for this message")

    return SQLResultOut(
        generated_sql=q_exec.generated_sql,
        normalized_sql=q_exec.normalized_sql,
        row_count=q_exec.row_count or 0,
        rows=[],
    )
