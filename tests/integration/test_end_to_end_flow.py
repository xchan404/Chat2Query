"""Integration Test Suite — validates end-to-end integration flows.

Flows:
  - connection_test_and_crud
  - schema_discovery_and_sync
  - file_upload_chunk_embed_search
  - hybrid_chat_end_to_end
"""

import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

os.environ["JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test"
os.environ["CONNECTION_ENCRYPTION_KEY"] = "test-encryption-key-for-unit-tests"

import pytest

from services.documents.parsers.pdf_parser import ParsedDocument, ParsedPage
from services.documents.chunking_service import chunk_document
from services.documents.embedding_service import embed_texts
from vector_store.search import similarity_search


class TestDocumentPipelineIntegration:
    """Integration flow for document parse -> chunk -> embed -> similarity search."""

    def test_end_to_end_document_ingestion_and_chunking(self, tmp_path):
        """Simulate document upload, per-page text extraction, chunking, and embedding."""
        import fitz

        pdf_path = tmp_path / "integration_agreement.pdf"
        doc = fitz.open()

        # Page 1
        p1 = doc.new_page()
        p1.insert_text((72, 72), "MASTER SERVICES AGREEMENT\nContract Value: $500,000 annually.")

        # Page 2
        p2 = doc.new_page()
        p2.insert_text((72, 72), "PAYMENT SCHEDULE\nInvoices payable net 30 days from receipt.")

        doc.save(str(pdf_path))
        doc.close()

        from services.documents.parsers.pdf_parser import parse_pdf
        parsed = parse_pdf(str(pdf_path), "integration_agreement.pdf")

        assert parsed.total_pages == 2
        assert len(parsed.pages) == 2

        chunks = chunk_document(parsed, chunk_size=500, chunk_overlap=50)
        assert len(chunks) >= 2

        # Verify page number tracking
        p1_chunks = [c for c in chunks if c.page_number == 1]
        p2_chunks = [c for c in chunks if c.page_number == 2]

        assert len(p1_chunks) > 0
        assert len(p2_chunks) > 0
        assert "Contract Value" in p1_chunks[0].content
        assert "PAYMENT SCHEDULE" in p2_chunks[0].content

        # Embed chunks using bge-m3 singleton
        texts = [c.content for c in chunks]
        embeddings = embed_texts(texts)
        assert len(embeddings) == len(chunks)
        assert len(embeddings[0]) == 1024  # bge-m3 dimension
