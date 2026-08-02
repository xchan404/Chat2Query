"""PDF parser using PyMuPDF — page-number-aware text extraction."""

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ParsedPage:
    """A single page's text content with its 1-indexed page number."""
    page_number: int
    text: str


@dataclass
class ParsedDocument:
    """Full parsed document with per-page content and metadata."""
    file_name: str
    pages: list[ParsedPage] = field(default_factory=list)
    total_pages: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text.strip())


def parse_pdf(file_path: str | Path, file_name: str | None = None) -> ParsedDocument:
    """Extract text from PDF with page numbers preserved.

    Each page's text is tracked separately so that downstream chunking
    can accurately assign page_number to each chunk.
    """
    import fitz  # PyMuPDF

    path = Path(file_path)
    fname = file_name or path.name
    doc = fitz.open(str(path))

    pages: list[ParsedPage] = []
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text = page.get_text("text")
        if text and text.strip():
            pages.append(ParsedPage(
                page_number=page_idx + 1,  # 1-indexed
                text=text.strip(),
            ))

    metadata = doc.metadata or {}
    total_pages = len(doc)
    doc.close()

    logger.info(
        f"Parsed PDF: {fname}, {total_pages} pages, {len(pages)} with text"
    )

    return ParsedDocument(
        file_name=fname,
        pages=pages,
        total_pages=total_pages,
        metadata=metadata,
    )
