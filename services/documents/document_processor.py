"""Document processor — orchestrates parse → chunk → embed → store.

Updates files.processing_status at each stage:
  pending → processing → completed | failed
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from models.document_chunk import DocumentChunk
from models.file import File
from services.documents.chunking_service import chunk_document
from services.documents.embedding_service import embed_texts
from services.documents.parsers.pdf_parser import parse_pdf, ParsedDocument
from services.documents.parsers.docx_parser import parse_docx
from services.documents.parsers.spreadsheet_parser import parse_xlsx, parse_csv
from services.documents.parsers.text_parser import parse_txt

logger = logging.getLogger(__name__)

PARSER_MAP = {
    "pdf": parse_pdf,
    "docx": parse_docx,
    "doc": parse_docx,
    "xlsx": parse_xlsx,
    "xls": parse_xlsx,
    "csv": parse_csv,
    "txt": parse_txt,
    "text": parse_txt,
    "md": parse_txt,
    "markdown": parse_txt,
}


def _get_parser(file_type: str):
    """Get the appropriate parser for a file type."""
    parser = PARSER_MAP.get(file_type.lower())
    if parser is None:
        raise ValueError(f"Unsupported file type: {file_type}")
    return parser


async def process_file(
    session: AsyncSession,
    file_record: File,
) -> int:
    """Process a file: parse → chunk → embed → store chunks.

    Updates the File record's processing_status at each stage.
    Returns the number of chunks created.
    """
    try:
        # Mark as processing
        file_record.processing_status = "processing"
        file_record.processing_started_at = datetime.now(timezone.utc)
        session.add(file_record)
        await session.flush()

        # Step 1: Parse
        parser = _get_parser(file_record.file_type)
        parsed = parser(file_record.storage_path, file_record.file_name)

        if not parsed.pages:
            file_record.processing_status = "completed"
            file_record.processed_at = datetime.now(timezone.utc)
            file_record.chunk_count = 0
            session.add(file_record)
            await session.flush()
            return 0

        # Step 2: Chunk
        chunks = chunk_document(parsed)

        if not chunks:
            file_record.processing_status = "completed"
            file_record.processed_at = datetime.now(timezone.utc)
            file_record.chunk_count = 0
            session.add(file_record)
            await session.flush()
            return 0

        # Step 3: Embed (batch)
        texts = [c.content for c in chunks]
        embeddings = embed_texts(texts)

        # Step 4: Store chunks with embeddings
        for chunk, embedding in zip(chunks, embeddings):
            db_chunk = DocumentChunk(
                file_id=file_record.id,
                tenant_id=file_record.tenant_id,
                knowledge_base_id=file_record.knowledge_base_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_number=chunk.page_number,
                embedding=embedding,
                chunk_metadata=chunk.metadata,
            )
            session.add(db_chunk)

        # Update file record
        file_record.processing_status = "completed"
        file_record.processed_at = datetime.now(timezone.utc)
        file_record.chunk_count = len(chunks)
        file_record.file_metadata = {
            "total_pages": parsed.total_pages,
            "chunk_count": len(chunks),
            "parser_metadata": parsed.metadata,
        }
        session.add(file_record)
        await session.flush()

        logger.info(
            f"Processed file '{file_record.file_name}': "
            f"{len(chunks)} chunks with embeddings stored"
        )
        return len(chunks)

    except Exception as e:
        logger.error(f"File processing failed for '{file_record.file_name}': {e}")
        file_record.processing_status = "failed"
        file_record.processing_error = str(e)
        session.add(file_record)
        await session.flush()
        raise
