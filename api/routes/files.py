"""File upload, listing, deletion, and reprocessing routes."""

import uuid
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import NotFoundError
from core.tenant_context import CurrentUser, get_current_user
from repositories.file_repo import FileRepository
from schemas.file import FileOut
from services.documents.upload_service import handle_upload, reprocess_file

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload", response_model=FileOut, status_code=201)
async def upload_file(
    knowledge_base_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileOut:
    """Upload and process a document file.

    Supported types: PDF, DOCX, XLSX, CSV, TXT.
    Processing: parse → chunk → embed → store (synchronous).
    """
    file_record = await handle_upload(
        session=db,
        upload=file,
        tenant_id=uuid.UUID(current_user.tenant_id),
        knowledge_base_id=knowledge_base_id,
        user_id=uuid.UUID(current_user.user_id),
    )
    from services.audit.audit_service import log_audit_event
    await log_audit_event(
        session=db,
        tenant_id=uuid.UUID(current_user.tenant_id),
        user_id=uuid.UUID(current_user.user_id),
        action="file_uploaded",
        resource_type="file",
        resource_id=str(file_record.id),
        details={"file_name": file_record.file_name, "chunk_count": file_record.chunk_count},
        description=f"File '{file_record.file_name}' uploaded and processed",
    )
    await db.commit()
    return FileOut.model_validate(file_record)


@router.get("", response_model=list[FileOut])
async def list_files(
    knowledge_base_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FileOut]:
    """List files in a knowledge base."""
    repo = FileRepository(db)
    files = await repo.list_by_knowledge_base(
        uuid.UUID(current_user.tenant_id),
        knowledge_base_id,
    )
    return [FileOut.model_validate(f) for f in files]


@router.get("/{file_id}", response_model=FileOut)
async def get_file(
    file_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileOut:
    """Get file details by ID."""
    repo = FileRepository(db)
    f = await repo.get_by_id(uuid.UUID(current_user.tenant_id), file_id)
    if f is None:
        raise NotFoundError("File not found")
    return FileOut.model_validate(f)


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a file and its chunks."""
    repo = FileRepository(db)
    deleted = await repo.delete_by_id(uuid.UUID(current_user.tenant_id), file_id)
    if not deleted:
        raise NotFoundError("File not found")

    from services.audit.audit_service import log_audit_event
    await log_audit_event(
        session=db,
        tenant_id=uuid.UUID(current_user.tenant_id),
        user_id=uuid.UUID(current_user.user_id),
        action="file_deleted",
        resource_type="file",
        resource_id=str(file_id),
        description=f"File '{file_id}' deleted",
    )
    await db.commit()
    await db.commit()


@router.post("/{file_id}/reprocess", response_model=FileOut)
async def reprocess_file_endpoint(
    file_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileOut:
    """Re-process an existing file (e.g. after model upgrade)."""
    repo = FileRepository(db)
    f = await repo.get_by_id(uuid.UUID(current_user.tenant_id), file_id)
    if f is None:
        raise NotFoundError("File not found")
    updated = await reprocess_file(db, f)
    await db.commit()
    return FileOut.model_validate(updated)
