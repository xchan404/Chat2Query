"""Plain text parser."""

import logging
from pathlib import Path

from services.documents.parsers.pdf_parser import ParsedDocument, ParsedPage

logger = logging.getLogger(__name__)


def parse_txt(file_path: str | Path, file_name: str | None = None) -> ParsedDocument:
    """Extract text from plain text files."""
    path = Path(file_path)
    fname = file_name or path.name

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    pages = [ParsedPage(page_number=1, text=text)] if text.strip() else []

    logger.info(f"Parsed TXT: {fname}, {len(text)} characters")

    return ParsedDocument(
        file_name=fname,
        pages=pages,
        total_pages=1,
        metadata={"char_count": len(text)},
    )
