"""Database connections routes — full CRUD + test endpoint."""

import logging
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import NotFoundError
from core.tenant_context import CurrentUser, get_current_user
from schemas.connection import (
    ConnectionCreate,
    ConnectionOut,
    ConnectionUpdate,
    TestResult,
)
from services.database.adapters.registry import get_adapter
from services.database.connection_service import ConnectionService
from services.database.connection_tester import test_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/database-connections", tags=["connections"])


@router.post("", response_model=ConnectionOut, status_code=201)
async def create_connection(
    data: ConnectionCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConnectionOut:
    """Create a new database connection. Password is encrypted at rest."""
    service = ConnectionService(db)
    conn = await service.create_connection(
        tenant_id=uuid.UUID(current_user.tenant_id),
        data=data,
    )
    return ConnectionOut.model_validate(conn)


@router.get("", response_model=list[ConnectionOut])
async def list_connections(
    limit: int = 100,
    offset: int = 0,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ConnectionOut]:
    """List all database connections for the current tenant."""
    service = ConnectionService(db)
    connections = await service.list_connections(
        tenant_id=uuid.UUID(current_user.tenant_id),
        limit=limit,
        offset=offset,
    )
    return [ConnectionOut.model_validate(c) for c in connections]


@router.get("/{connection_id}", response_model=ConnectionOut)
async def get_connection(
    connection_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConnectionOut:
    """Get a specific database connection by ID."""
    service = ConnectionService(db)
    conn = await service.get_connection(
        tenant_id=uuid.UUID(current_user.tenant_id),
        connection_id=connection_id,
    )
    return ConnectionOut.model_validate(conn)


@router.put("/{connection_id}", response_model=ConnectionOut)
async def update_connection(
    connection_id: uuid.UUID,
    data: ConnectionUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConnectionOut:
    """Update a database connection. Re-encrypts password if changed."""
    service = ConnectionService(db)
    conn = await service.update_connection(
        tenant_id=uuid.UUID(current_user.tenant_id),
        connection_id=connection_id,
        data=data,
    )
    return ConnectionOut.model_validate(conn)


@router.delete("/{connection_id}", status_code=204)
async def delete_connection(
    connection_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a database connection."""
    service = ConnectionService(db)
    await service.delete_connection(
        tenant_id=uuid.UUID(current_user.tenant_id),
        connection_id=connection_id,
    )


@router.post("/{connection_id}/test", response_model=TestResult)
async def test_connection_endpoint(
    connection_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TestResult:
    """Test a database connection. Decrypts credentials transiently in memory."""
    service = ConnectionService(db)
    conn = await service.get_connection(
        tenant_id=uuid.UUID(current_user.tenant_id),
        connection_id=connection_id,
    )

    # Decrypt credentials in memory only
    params = service.get_decrypted_params(conn)

    success, message, latency_ms = await test_connection(
        database_type=conn.database_type,
        params=params,
    )

    return TestResult(
        success=success,
        message=message,
        latency_ms=latency_ms,
    )
