"""Chunking service — splits parsed documents into embeddable chunks.

Page-number-aware: each chunk tracks which page(s) its content came from.
Sensible defaults: ~500 tokens (~2000 chars), 200-char overlap.
"""

import logging
from dataclasses import dataclass, field

from services.documents.parsers.pdf_parser import ParsedDocument, ParsedPage

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 2000  # ~500 tokens
DEFAULT_CHUNK_OVERLAP = 200


@dataclass
class Chunk:
    """A text chunk with source page number tracking."""
    chunk_index: int
    content: str
    page_number: int | None  # page the chunk primarily comes from
    metadata: dict = field(default_factory=dict)


def chunk_document(
    parsed: ParsedDocument,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    """Split a parsed document into overlapping chunks.

    For PDFs, page_number is accurately tracked per chunk.
    For other formats, page_number may be 1 or the sheet index.
    """
    if not parsed.pages:
        return []

    chunks: list[Chunk] = []
    chunk_index = 0

    for page in parsed.pages:
        text = page.text
        if not text.strip():
            continue

        # Split this page's text into chunks
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]

            if chunk_text.strip():
                chunks.append(Chunk(
                    chunk_index=chunk_index,
                    content=chunk_text.strip(),
                    page_number=page.page_number,
                    metadata={
                        "file_name": parsed.file_name,
                        "page_number": page.page_number,
                        "char_start": start,
                        "char_end": min(end, len(text)),
                    },
                ))
                chunk_index += 1

            # Advance by (chunk_size - overlap)
            start += chunk_size - chunk_overlap

            # If remaining text is too small, we've captured it
            if start >= len(text):
                break

    logger.info(
        f"Chunked '{parsed.file_name}': {len(chunks)} chunks "
        f"(size={chunk_size}, overlap={chunk_overlap})"
    )
    return chunks
