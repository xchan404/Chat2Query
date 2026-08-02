"""Text-to-SQL query route."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from core.tenant_context import CurrentUser, get_current_user
from services.database.text2sql_service import Text2SQLService

router = APIRouter(prefix="/api/query", tags=["query"])


class Text2SQLRequest(BaseModel):
    """Request payload for Text-to-SQL query."""
    connection_id: uuid.UUID
    question: str = Field(..., min_length=1)


@router.post("/sql")
async def execute_text_to_sql(
    request: Text2SQLRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Process a natural language question against a database connection."""
    service = Text2SQLService(db)
    return await service.query(
        tenant_id=uuid.UUID(current_user.tenant_id),
        user_id=uuid.UUID(current_user.user_id),
        connection_id=request.connection_id,
        question=request.question,
    )
