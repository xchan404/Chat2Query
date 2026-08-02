"""Audit log listing API route."""

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from core.tenant_context import CurrentUser, require_role
from schemas.conversation import AuditLogOut
from services.audit.audit_service import list_audit_logs

router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])


@router.get("", response_model=list[AuditLogOut])
async def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLogOut]:
    """List audit log entries for the current tenant."""
    logs = await list_audit_logs(
        session=db,
        tenant_id=uuid.UUID(current_user.tenant_id),
        limit=limit,
        offset=offset,
    )
    return [AuditLogOut.model_validate(log) for log in logs]
