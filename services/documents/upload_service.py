"""Upload service — handles file reception, storage, and processing trigger."""

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from models.file import File
from services.documents.document_processor import process_file

logger = logging.getLogger(__name__)

# Local file storage directory (production would use MinIO/S3)
UPLOAD_DIR = Path("uploads")


async def handle_upload(
    session: AsyncSession,
    upload: UploadFile,
    tenant_id: uuid.UUID,
    knowledge_base_id: uuid.UUID,
    user_id: uuid.UUID,
) -> File:
    """Receive an uploaded file, save to disk, create DB record, and process.

    Returns the File record after processing completes.
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Determine file type from extension
    file_name = upload.filename or "unknown"
    file_ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "txt"

    # Generate unique storage path
    file_id = uuid.uuid4()
    storage_path = str(UPLOAD_DIR / f"{tenant_id}" / f"{file_id}.{file_ext}")
    Path(storage_path).parent.mkdir(parents=True, exist_ok=True)

    # Save file to disk
    content = await upload.read()
    with open(storage_path, "wb") as f:
        f.write(content)

    file_size = len(content)

    # Create file record
    file_record = File(
        id=file_id,
        tenant_id=tenant_id,
        knowledge_base_id=knowledge_base_id,
        uploaded_by=user_id,
        file_name=file_name,
        file_type=file_ext,
        file_size=file_size,
        storage_path=storage_path,
        processing_status="pending",
    )
    session.add(file_record)
    await session.flush()

    # Process synchronously (the build plan calls this the "job-queue substitute")
    await process_file(session, file_record)

    return file_record


async def reprocess_file(
    session: AsyncSession,
    file_record: File,
) -> File:
    """Re-process an existing file (e.g., after model upgrade).

    Clears existing chunks and re-runs the pipeline.
    """
    from sqlalchemy import delete
    from models.document_chunk import DocumentChunk

    # Delete existing chunks
    stmt = delete(DocumentChunk).where(DocumentChunk.file_id == file_record.id)
    await session.execute(stmt)
    await session.flush()

    # Reset status
    file_record.processing_status = "pending"
    file_record.processing_error = None
    file_record.chunk_count = 0
    session.add(file_record)
    await session.flush()

    # Re-process
    await process_file(session, file_record)
    return file_record
