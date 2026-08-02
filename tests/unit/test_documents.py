"""Unit tests for Phase 5: Parsers, Chunking, and Embedding Service."""

import os
import sys
import tempfile
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
from services.documents.parsers.text_parser import parse_txt
from services.documents.chunking_service import chunk_document, Chunk


class TestTextParser:
    """Test TXT parser."""

    def test_parse_txt_basic(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hello world\nThis is a test file.\nThird line.", encoding="utf-8")
        parsed = parse_txt(str(f), "test.txt")
        assert parsed.file_name == "test.txt"
        assert len(parsed.pages) == 1
        assert parsed.pages[0].page_number == 1
        assert "Hello world" in parsed.pages[0].text

    def test_parse_empty_txt(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        parsed = parse_txt(str(f))
        assert len(parsed.pages) == 0


class TestPDFParser:
    """Test PDF parser page tracking."""

    def test_parse_multi_page_pdf(self, tmp_path):
        """Create a multi-page PDF and verify page numbers are tracked."""
        import fitz  # PyMuPDF

        pdf_path = tmp_path / "multi_page.pdf"
        doc = fitz.open()  # new empty document

        # Page 1
        page1 = doc.new_page(width=612, height=792)
        page1.insert_text((72, 72), "Page 1 content: Introduction to the project")

        # Page 2
        page2 = doc.new_page(width=612, height=792)
        page2.insert_text((72, 72), "Page 2 content: Technical details and specifications")

        # Page 3
        page3 = doc.new_page(width=612, height=792)
        page3.insert_text((72, 72), "Page 3 content: Conclusion and references")

        doc.save(str(pdf_path))
        doc.close()

        from services.documents.parsers.pdf_parser import parse_pdf
        parsed = parse_pdf(str(pdf_path), "multi_page.pdf")

        assert parsed.file_name == "multi_page.pdf"
        assert parsed.total_pages == 3
        assert len(parsed.pages) == 3
        assert parsed.pages[0].page_number == 1
        assert parsed.pages[1].page_number == 2
        assert parsed.pages[2].page_number == 3
        assert "Introduction" in parsed.pages[0].text
        assert "Technical details" in parsed.pages[1].text
        assert "Conclusion" in parsed.pages[2].text


class TestChunkingService:
    """Test chunking with page-number tracking."""

    def test_chunk_single_page_within_limit(self):
        parsed = ParsedDocument(
            file_name="test.txt",
            pages=[ParsedPage(page_number=1, text="Short text content.")],
            total_pages=1,
        )
        chunks = chunk_document(parsed, chunk_size=2000)
        assert len(chunks) == 1
        assert chunks[0].page_number == 1
        assert chunks[0].chunk_index == 0
        assert chunks[0].content == "Short text content."

    def test_chunk_long_page_splits_correctly(self):
        long_text = "A" * 5000  # exceeds default chunk_size
        parsed = ParsedDocument(
            file_name="long.txt",
            pages=[ParsedPage(page_number=1, text=long_text)],
            total_pages=1,
        )
        chunks = chunk_document(parsed, chunk_size=2000, chunk_overlap=200)
        assert len(chunks) > 1
        # All chunks should have page_number=1
        for c in chunks:
            assert c.page_number == 1
        # Check overlap: adjacent chunks should share content
        assert chunks[0].content[-200:] in chunks[1].content or len(chunks[1].content) < 200

    def test_chunk_multi_page_preserves_page_numbers(self):
        """Each page's chunks must carry the correct page_number."""
        parsed = ParsedDocument(
            file_name="multi.pdf",
            pages=[
                ParsedPage(page_number=1, text="Page 1 text. " * 200),
                ParsedPage(page_number=2, text="Page 2 text. " * 200),
                ParsedPage(page_number=3, text="Page 3 text. " * 200),
            ],
            total_pages=3,
        )
        chunks = chunk_document(parsed, chunk_size=2000, chunk_overlap=200)
        assert len(chunks) > 3  # each page should produce >1 chunk

        page_numbers_seen = set()
        for c in chunks:
            page_numbers_seen.add(c.page_number)
            # Verify content matches page assignment
            if c.page_number == 1:
                assert "Page 1" in c.content
            elif c.page_number == 2:
                assert "Page 2" in c.content
            elif c.page_number == 3:
                assert "Page 3" in c.content

        assert page_numbers_seen == {1, 2, 3}

    def test_chunk_empty_document(self):
        parsed = ParsedDocument(file_name="empty.txt", pages=[], total_pages=0)
        chunks = chunk_document(parsed)
        assert len(chunks) == 0

    def test_chunk_metadata_includes_file_name_and_page(self):
        parsed = ParsedDocument(
            file_name="report.pdf",
            pages=[ParsedPage(page_number=5, text="Some content here")],
            total_pages=5,
        )
        chunks = chunk_document(parsed)
        assert len(chunks) == 1
        assert chunks[0].metadata["file_name"] == "report.pdf"
        assert chunks[0].metadata["page_number"] == 5


class TestPDFChunkPageNumberAccuracy:
    """Integration: parse a real multi-page PDF → chunk → verify page_number accuracy."""

    def test_parse_and_chunk_multi_page_pdf(self, tmp_path):
        """The specific test the user requested: verify page_number against a real multi-page PDF."""
        import fitz

        pdf_path = tmp_path / "contract.pdf"
        doc = fitz.open()

        # Page 1: Introduction
        p1 = doc.new_page(width=612, height=792)
        p1.insert_text((72, 72), "SERVICES AGREEMENT\n\nThis agreement is between Party A and Party B.")
        p1.insert_text((72, 150), "Section 1: Scope of Services\n" + "The contractor shall provide " * 50)

        # Page 2: Payment terms
        p2 = doc.new_page(width=612, height=792)
        p2.insert_text((72, 72), "Section 2: Payment Terms\n" + "Payment shall be made within 30 days " * 50)

        # Page 3: Termination
        p3 = doc.new_page(width=612, height=792)
        p3.insert_text((72, 72), "Section 3: Termination Clause\n" + "Either party may terminate " * 50)

        # Page 4: Signatures
        p4 = doc.new_page(width=612, height=792)
        p4.insert_text((72, 72), "Section 4: Signatures\nParty A: ___________\nParty B: ___________")

        doc.save(str(pdf_path))
        doc.close()

        from services.documents.parsers.pdf_parser import parse_pdf
        parsed = parse_pdf(str(pdf_path))

        assert parsed.total_pages == 4

        chunks = chunk_document(parsed, chunk_size=500, chunk_overlap=50)

        # Verify page_number accuracy
        page1_chunks = [c for c in chunks if c.page_number == 1]
        page2_chunks = [c for c in chunks if c.page_number == 2]
        page3_chunks = [c for c in chunks if c.page_number == 3]
        page4_chunks = [c for c in chunks if c.page_number == 4]

        assert len(page1_chunks) > 0, "Should have chunks from page 1"
        assert len(page2_chunks) > 0, "Should have chunks from page 2"
        assert len(page3_chunks) > 0, "Should have chunks from page 3"
        assert len(page4_chunks) > 0, "Should have chunks from page 4"

        # Content verification
        assert any("SERVICES AGREEMENT" in c.content for c in page1_chunks)
        assert any("Payment" in c.content for c in page2_chunks)
        assert any("Termination" in c.content or "terminate" in c.content for c in page3_chunks)
        assert any("Signatures" in c.content or "Party A" in c.content for c in page4_chunks)


class TestEmbeddingServiceSingleton:
    """Test embedding service singleton pattern (without loading the full model)."""

    def test_singleton_module_importable(self):
        from services.documents.embedding_service import embed_texts, embed_single, _get_model
        assert callable(embed_texts)
        assert callable(embed_single)
        assert callable(_get_model)

    def test_embed_texts_empty_returns_empty(self):
        from services.documents.embedding_service import embed_texts
        assert embed_texts([]) == []
