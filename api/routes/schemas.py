"""Schema metadata routes."""

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from core.tenant_context import CurrentUser, get_current_user
from schemas.schema_metadata import SchemaOut, SyncSchemaResponse
from services.database.schema_discovery import SchemaDiscoveryService

router = APIRouter(prefix="/api/database-connections", tags=["schemas"])


@router.post("/{connection_id}/sync-schema", response_model=SyncSchemaResponse)
async def sync_schema(
    connection_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SyncSchemaResponse:
    """Introspect database schema via connection adapter and cache metadata."""
    service = SchemaDiscoveryService(db)
    return await service.sync_schema(
        tenant_id=uuid.UUID(current_user.tenant_id),
        connection_id=connection_id,
    )


@router.get("/{connection_id}/schemas", response_model=list[SchemaOut])
async def get_schemas(
    connection_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SchemaOut]:
    """Get discovered schema metadata for a connection."""
    service = SchemaDiscoveryService(db)
    return await service.get_schemas(
        tenant_id=uuid.UUID(current_user.tenant_id),
        connection_id=connection_id,
    )
