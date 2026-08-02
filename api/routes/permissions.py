"""Table and column permission management routes."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import NotFoundError
from core.tenant_context import CurrentUser, get_current_user, require_role
from models.permission import TablePermission, ColumnPermission
from repositories.permission_repo import PermissionRepository
from schemas.permission import TablePermissionCreate, TablePermissionOut

router = APIRouter(prefix="/api/permissions", tags=["permissions"])


@router.post("/tables", response_model=TablePermissionOut, status_code=201)
async def create_table_permission(
    data: TablePermissionCreate,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> TablePermissionOut:
    """Grant or configure table permissions for a role."""
    repo = PermissionRepository(db)
    tp = TablePermission(
        role_id=data.role_id,
        connection_id=data.connection_id,
        schema_name=data.schema_name,
        table_name=data.table_name,
        access_type=data.access_type,
        row_filter=data.row_filter,
    )

    for cp_in in data.column_permissions:
        cp = ColumnPermission(
            role_id=data.role_id,
            column_name=cp_in.column_name,
            is_allowed=cp_in.is_allowed,
            is_masked=cp_in.is_masked,
        )
        tp.column_permissions.append(cp)

    saved = await repo.create_or_update_table_permission(tp)
    return TablePermissionOut.model_validate(saved)


@router.get("/connections/{connection_id}", response_model=list[TablePermissionOut])
async def list_connection_permissions(
    connection_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TablePermissionOut]:
    """List configured table permissions for a connection."""
    repo = PermissionRepository(db)
    perms = await repo.get_table_permissions_by_connection(connection_id)
    return [TablePermissionOut.model_validate(p) for p in perms]


@router.delete("/tables/{permission_id}", status_code=204)
async def delete_table_permission(
    permission_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a table permission by ID."""
    repo = PermissionRepository(db)
    deleted = await repo.delete_table_permission(permission_id)
    if not deleted:
        raise NotFoundError("Table permission not found")
