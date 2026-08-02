"""Audit logging service — records entries for security, compliance, and auditing."""

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.audit_log import AuditLog

logger = logging.getLogger(__name__)


async def log_audit_event(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
    description: str | None = None,
) -> AuditLog:
    """Create and persist an AuditLog record."""
    entry = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        request_id=request_id,
        details=details,
        description=description,
    )
    session.add(entry)
    await session.flush()
    logger.info(
        f"AuditLog created: action='{action}', resource='{resource_type}:{resource_id}', user='{user_id}'"
    )
    return entry


async def list_audit_logs(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """List audit logs for a tenant."""
    stmt = (
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
