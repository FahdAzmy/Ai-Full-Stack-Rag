"""
Test cases for Ingestion Pipeline (SPEC-03).
Following TDD: These tests are written BEFORE implementation.

Tests are organized by service:
  1. TestPdfParser       — PDF text & metadata extraction
  2. TestTextChunker     — Text splitting into overlapping chunks
  3. TestEmbeddingService — OpenAI embedding generation
  4. TestIngestionService — Full pipeline orchestration

All external dependencies (PyMuPDF, OpenAI, LangChain) are mocked.
"""

import uuid
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.helpers.security import hash_password
from src.models.db_scheams.user import User
from src.models.db_scheams.document import Document
from src.models.db_scheams.DocumentChunk import DocumentChunk


# ── Helpers ──────────────────────────────────────────────────────────────────


async def create_verified_user(
    db_session: AsyncSession, email: str = "pipeline@example.com"
) -> User:
    """Create a verified user in the DB and return the User object."""
    user = User(
        email=email,
        name="Pipeline Test User",
        hashed_password=hash_password("SecurePass123"),
        is_verified=True,
        verification_token="123456",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def create_document_record(
    db_session: AsyncSession,
    user: User,
    file_name: str = "test_paper.pdf",
    file_path: str = "/tmp/test_paper.pdf",
    status: str = "uploading",
) -> Document:
    """Insert a Document record directly into the DB for test setup."""
    doc = Document(
        id=uuid.uuid4(),
        user_id=user.id,
        file_name=file_name,
        file_path=file_path,
        status=status,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


# ═════════════════════════════════════════════════════════════════════════════
# 1. PDF PARSER TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestPdfParserExtractText:
    """Tests for pdf_parser.extract_text_from_pdf()."""

    # ── Scenario #1: Valid multi-page PDF → returns list of page dicts ────

    @pytest.mark.asyncio
    async def test_extract_text_valid_pdf(self):
        """Extract text from a valid PDF with multiple pages → list of {page, text}."""
        mock_page_1 = MagicMock()
        mock_page_1.get_text.return_value = "This is the first page content."

        mock_page_2 = MagicMock()
        mock_page_2.get_text.return_value = "Second page has more content here."

        mock_page_3 = MagicMock()
        mock_page_3.get_text.return_value = "Third page is the conclusion."

        mock_doc = MagicMock()
        mock_doc.page_count = 3
        mock_doc.__getitem__ = lambda self, idx: [
            mock_page_1,
            mock_page_2,
            mock_page_3,
        ][idx]
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)

        with patch("src.services.pdf_parser.fitz") as mock_fitz, patch(
            "src.services.pdf_parser.os.path.getsize", return_value=1024
        ):
            mock_fitz.open.return_value = mock_doc

            from src.services.pdf_parser import extract_text_from_pdf

            pages = extract_text_from_pdf("/fake/path.pdf")

        assert len(pages) == 3
        assert pages[0]["page"] == 1
        assert "first page" in pages[0]["text"]
        assert pages[1]["page"] == 2
        assert pages[2]["page"] == 3

    # ── Scenario #2: PDF with no extractable text → raises ValueError ────

    @pytest.mark.asyncio
    async def test_extract_text_no_text_pdf_raises(self):
        """Scanned/image PDF with no text → ValueError."""
        mock_page = MagicMock()
        mock_page.get_text.return_value = ""  # No text at all

        mock_doc = MagicMock()
        mock_doc.page_count = 3
        mock_doc.__getitem__ = lambda self, idx: mock_page
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)

        with patch("src.services.pdf_parser.fitz") as mock_fitz, patch(
            "src.services.pdf_parser.os.path.getsize", return_value=1024
        ):
            mock_fitz.open.return_value = mock_doc

            from src.services.pdf_parser import extract_text_from_pdf

            with pytest.raises(ValueError, match="no extractable text"):
                extract_text_from_pdf("/fake/scanned.pdf")

    # ── Scenario #3: Corrupted PDF → raises ValueError ───────────────────

    @pytest.mark.asyncio
    async def test_extract_text_corrupted_pdf_raises(self):
        """Corrupted PDF that can't be opened → ValueError."""
        with patch("src.services.pdf_parser.fitz") as mock_fitz, patch(
            "src.services.pdf_parser.os.path.getsize", return_value=1024
        ):
            mock_fitz.open.side_effect = Exception("Cannot open file")

            from src.services.pdf_parser import extract_text_from_pdf

            with pytest.raises(ValueError, match="Cannot open PDF"):
                extract_text_from_pdf("/fake/corrupted.pdf")

    # ── Scenario #4: Single-page PDF → returns list with 1 item ──────────

    @pytest.mark.asyncio
    async def test_extract_text_single_page(self):
        """Single-page PDF → list with exactly 1 entry."""
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Single page document content."

        mock_doc = MagicMock()
        mock_doc.page_count = 1
        mock_doc.__getitem__ = lambda self, idx: mock_page
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)

        with patch("src.services.pdf_parser.fitz") as mock_fitz, patch(
            "src.services.pdf_parser.os.path.getsize", return_value=1024
        ):
            mock_fitz.open.return_value = mock_doc

            from src.services.pdf_parser import extract_text_from_pdf

            pages = extract_text_from_pdf("/fake/single.pdf")

        assert len(pages) == 1
        assert pages[0]["page"] == 1
        assert pages[0]["text"] == "Single page document content."

    # ── Scenario #5: Pages with only whitespace are skipped ──────────────

    @pytest.mark.asyncio
    async def test_extract_text_skips_blank_pages(self):
        """Pages that contain only whitespace or empty text should be skipped."""
        mock_page_1 = MagicMock()
        mock_page_1.get_text.return_value = "Real content here."

        mock_page_2 = MagicMock()
        mock_page_2.get_text.return_value = "   \n\n\t  "  # Only whitespace

        mock_page_3 = MagicMock()
        mock_page_3.get_text.return_value = "More real content."

        mock_doc = MagicMock()
        mock_doc.page_count = 3
        mock_doc.__getitem__ = lambda self, idx: [
            mock_page_1,
            mock_page_2,
            mock_page_3,
        ][idx]
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)

        with patch("src.services.pdf_parser.fitz") as mock_fitz, patch(
            "src.services.pdf_parser.os.path.getsize", return_value=1024
        ):
            mock_fitz.open.return_value = mock_doc

            from src.services.pdf_parser import extract_text_from_pdf

            pages = extract_text_from_pdf("/fake/blanks.pdf")

        # Page 2 was blank, so only 2 pages returned
        assert len(pages) == 2
        assert pages[0]["page"] == 1
        assert pages[1]["page"] == 3  # Page 2 skipped


class TestPdfParserExtractMetadata:
    """Tests for pdf_parser.extract_metadata()."""

    # ── Scenario #9: Extract metadata (title, author, year, total_pages) ─

    @pytest.mark.asyncio
    async def test_extract_metadata_full(self):
        """PDF with full metadata → all fields populated."""
        mock_doc = MagicMock()
        mock_doc.metadata = {
            "title": "Deep Learning in Medicine",
            "author": "John Smith",
            "creationDate": "D:20200315120000+00'00'",
        }
        mock_doc.page_count = 25
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)

        with patch("src.services.pdf_parser.fitz") as mock_fitz, patch(
            "src.services.pdf_parser.os.path.getsize", return_value=1024
        ):
            mock_fitz.open.return_value = mock_doc

            from src.services.pdf_parser import extract_metadata

            meta = extract_metadata("/fake/paper.pdf")

        assert meta["title"] == "Deep Learning in Medicine"
        assert meta["author"] == "John Smith"
        assert meta["year"] == "2020"
        assert meta["total_pages"] == 25

    # ── Scenario #10: PDF with no metadata → fields are None ─────────────

    @pytest.mark.asyncio
    async def test_extract_metadata_empty(self):
        """PDF with no metadata → title, author, year are None."""
        mock_doc = MagicMock()
        mock_doc.metadata = {}
        mock_doc.page_count = 5
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)

        with patch("src.services.pdf_parser.fitz") as mock_fitz, patch(
            "src.services.pdf_parser.os.path.getsize", return_value=1024
        ):
            mock_fitz.open.return_value = mock_doc

            from src.services.pdf_parser import extract_metadata

            meta = extract_metadata("/fake/no_meta.pdf")

        assert meta["title"] is None
        assert meta["author"] is None
        assert meta["year"] is None
        assert meta["total_pages"] == 5

    @pytest.mark.asyncio
    async def test_extract_metadata_partial(self):
        """PDF with some metadata → only available fields populated."""
        mock_doc = MagicMock()
        mock_doc.metadata = {
            "title": "Survey Paper",
            "author": "",  # Empty author
            "creationDate": "",  # No date
        }
        mock_doc.page_count = 10
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)

        with patch("src.services.pdf_parser.fitz") as mock_fitz, patch(
            "src.services.pdf_parser.os.path.getsize", return_value=1024
        ):
            mock_fitz.open.return_value = mock_doc

            from src.services.pdf_parser import extract_metadata

            meta = extract_metadata("/fake/partial.pdf")

        assert meta["title"] == "Survey Paper"
        assert meta["author"] is None  # Empty string → None
        assert meta["year"] is None
        assert meta["total_pages"] == 10

    @pytest.mark.asyncio
    async def test_extract_metadata_none_metadata(self):
        """PDF where doc.metadata returns None → all fields None (except total_pages)."""
        mock_doc = MagicMock()
        mock_doc.metadata = None
        mock_doc.page_count = 7
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)

        with patch("src.services.pdf_parser.fitz") as mock_fitz, patch(
            "src.services.pdf_parser.os.path.getsize", return_value=1024
        ):
            mock_fitz.open.return_value = mock_doc

            from src.services.pdf_parser import extract_metadata

            meta = extract_metadata("/fake/none_meta.pdf")

        assert meta["title"] is None
        assert meta["author"] is None
        assert meta["year"] is None
        assert meta["total_pages"] == 7


class TestPdfParserHelpers:
    """Tests for pdf_parser._clean_text() and _extract_year()."""

    @pytest.mark.asyncio
    async def test_clean_text_normalizes_whitespace(self):
        """Multiple newlines/spaces collapsed; control chars removed."""
        from src.services.pdf_parser import _clean_text

        text = "Hello\n\n\n\n\nWorld   test\x00hidden"
        result = _clean_text(text)
        assert "\n\n\n" not in result
        assert "  " not in result
        assert "\x00" not in result
        assert "Hello" in result
        assert "World" in result

    @pytest.mark.asyncio
    async def test_clean_text_empty_returns_empty(self):
        """Empty or None input → empty string."""
        from src.services.pdf_parser import _clean_text

        assert _clean_text("") == ""
        assert _clean_text(None) == ""

    @pytest.mark.asyncio
    async def test_extract_year_valid_date(self):
        """Extract year from standard PDF date string."""
        from src.services.pdf_parser import _extract_year

        assert _extract_year("D:20200315120000+00'00'") == "2020"
        assert _extract_year("D:20191201") == "2019"

    @pytest.mark.asyncio
    async def test_extract_year_empty_returns_none(self):
        """Empty or None date string → None."""
        from src.services.pdf_parser import _extract_year

        assert _extract_year("") is None
        assert _extract_year(None) is None

    @pytest.mark.asyncio
    async def test_extract_year_no_year_in_string(self):
        """String with no 4-digit number → None."""
        from src.services.pdf_parser import _extract_year

        assert _extract_year("no-date-here") is None


# ═════════════════════════════════════════════════════════════════════════════
# 2. TEXT CHUNKER TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestTextChunker:
    """Tests for chunker.chunk_document()."""

    # ── Scenario #5: Verify chunk count is reasonable ─────────────────────

    @pytest.mark.asyncio
    async def test_chunk_document_produces_chunks(self):
        """A multi-page document should produce multiple chunks."""
        pages = [
            {"page": 1, "text": "A " * 500},  # ~1000 chars → should produce ≥1 chunk
            {"page": 2, "text": "B " * 500},
        ]

        with patch("src.services.chunker.settings") as mock_settings:
            mock_settings.CHUNK_SIZE = 800
            mock_settings.CHUNK_OVERLAP = 100
            mock_settings.MIN_CHUNK_LENGTH = 50

            from src.services.chunker import chunk_document

            chunks = chunk_document(pages)

        assert len(chunks) > 0
        # Each chunk should have the required keys
        for chunk in chunks:
            assert "content" in chunk
            assert "page_number" in chunk
            assert "chunk_index" in chunk

    # ── Scenario #6: Verify chunks have page numbers ─────────────────────

    @pytest.mark.asyncio
    async def test_chunks_preserve_page_numbers(self):
        """Each chunk should have the correct source page_number."""
        pages = [
            {"page": 1, "text": "Content from page one. " * 50},
            {"page": 2, "text": "Content from page two. " * 50},
            {"page": 3, "text": "Content from page three. " * 50},
        ]

        with patch("src.services.chunker.settings") as mock_settings:
            mock_settings.CHUNK_SIZE = 800
            mock_settings.CHUNK_OVERLAP = 100
            mock_settings.MIN_CHUNK_LENGTH = 50

            from src.services.chunker import chunk_document

            chunks = chunk_document(pages)

        # All chunks from page 1 should have page_number=1, etc.
        page_numbers = {c["page_number"] for c in chunks}
        assert 1 in page_numbers
        assert 2 in page_numbers
        assert 3 in page_numbers

    # ── Scenario #7: Verify chunks are ordered ───────────────────────────

    @pytest.mark.asyncio
    async def test_chunk_indices_are_sequential(self):
        """chunk_index should start at 0 and increase sequentially."""
        pages = [
            {"page": 1, "text": "Some text content. " * 100},
            {"page": 2, "text": "More text content. " * 100},
        ]

        with patch("src.services.chunker.settings") as mock_settings:
            mock_settings.CHUNK_SIZE = 800
            mock_settings.CHUNK_OVERLAP = 100
            mock_settings.MIN_CHUNK_LENGTH = 50

            from src.services.chunker import chunk_document

            chunks = chunk_document(pages)

        indices = [c["chunk_index"] for c in chunks]
        assert indices[0] == 0
        # Check sequential ordering
        for i in range(1, len(indices)):
            assert indices[i] == indices[i - 1] + 1

    # ── Business Rule: Minimum chunk size of 50 chars ────────────────────

    @pytest.mark.asyncio
    async def test_tiny_fragments_are_filtered_out(self):
        """Chunks shorter than 50 characters should be discarded."""
        pages = [
            {"page": 1, "text": "OK"},  # Too short after splitting
            {
                "page": 2,
                "text": "This is a sufficiently long paragraph that should produce valid chunks for the system. "
                * 20,
            },
        ]

        with patch("src.services.chunker.settings") as mock_settings:
            mock_settings.CHUNK_SIZE = 800
            mock_settings.CHUNK_OVERLAP = 100
            mock_settings.MIN_CHUNK_LENGTH = 50

            from src.services.chunker import chunk_document

            chunks = chunk_document(pages)

        # All returned chunks should be ≥ 50 chars
        for chunk in chunks:
            assert len(chunk["content"]) >= 50

    # ── Edge case: Empty pages list → empty chunks ───────────────────────

    @pytest.mark.asyncio
    async def test_empty_pages_returns_empty_list(self):
        """If no pages provided, return empty list."""
        with patch("src.services.chunker.settings") as mock_settings:
            mock_settings.CHUNK_SIZE = 800
            mock_settings.CHUNK_OVERLAP = 100
            mock_settings.MIN_CHUNK_LENGTH = 50

            from src.services.chunker import chunk_document

            chunks = chunk_document([])

        assert chunks == []

    # ── Verify chunk content is not empty ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_chunks_have_non_empty_content(self):
        """Every returned chunk should have non-empty, non-whitespace content."""
        pages = [
            {"page": 1, "text": "This is a reasonable paragraph. " * 40},
        ]

        with patch("src.services.chunker.settings") as mock_settings:
            mock_settings.CHUNK_SIZE = 800
            mock_settings.CHUNK_OVERLAP = 100
            mock_settings.MIN_CHUNK_LENGTH = 50

            from src.services.chunker import chunk_document

            chunks = chunk_document(pages)

        for chunk in chunks:
            assert chunk["content"].strip() != ""


# ═════════════════════════════════════════════════════════════════════════════
# 3. EMBEDDING SERVICE TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestEmbeddingService:
    """Tests for embedding_service.generate_embeddings() and generate_single_embedding()."""

    def _make_mock_embedding_response(self, count: int, dim: int = 1536):
        """Create a mock OpenAI embeddings response with `count` embeddings."""
        mock_response = MagicMock()
        data_items = []
        for i in range(count):
            item = MagicMock()
            item.index = i
            item.embedding = [0.1] * dim
            data_items.append(item)
        mock_response.data = data_items
        return mock_response

    # ── Scenario #8: Verify embeddings are 1536-dim ──────────────────────

    @pytest.mark.asyncio
    async def test_generate_embeddings_returns_correct_dimensions(self):
        """Each embedding should be a list of 1536 floats."""
        texts = ["Hello world", "Another text"]

        with patch("src.services.embedding_service.client") as mock_client, patch(
            "src.services.embedding_service.settings"
        ) as mock_settings:
            mock_settings.EMBEDDING_MODEL = "openai/text-embedding-3-small"
            mock_settings.EMBEDDING_DIMENSIONS = 1536
            mock_client.embeddings.create.return_value = (
                self._make_mock_embedding_response(2)
            )

            from src.services.embedding_service import generate_embeddings

            embeddings = generate_embeddings(texts)

        assert len(embeddings) == 2
        for emb in embeddings:
            assert len(emb) == 1536
            assert all(isinstance(v, float) for v in emb)

    # ── Empty input → empty output ───────────────────────────────────────

    @pytest.mark.asyncio
    async def test_generate_embeddings_empty_input(self):
        """Empty text list → empty embeddings list, no API call."""
        with patch("src.services.embedding_service.client") as mock_client:
            from src.services.embedding_service import generate_embeddings

            embeddings = generate_embeddings([])

        assert embeddings == []
        mock_client.embeddings.create.assert_not_called()

    # ── Batch processing: >100 texts are batched ─────────────────────────

    @pytest.mark.asyncio
    async def test_generate_embeddings_batches_large_input(self):
        """More than 100 texts should be split into multiple API calls."""
        texts = [f"Text {i}" for i in range(150)]  # 150 texts → 2 batches

        with patch("src.services.embedding_service.client") as mock_client, patch(
            "src.services.embedding_service.settings"
        ) as mock_settings:
            mock_settings.EMBEDDING_MODEL = "openai/text-embedding-3-small"
            mock_settings.EMBEDDING_DIMENSIONS = 1536

            # First batch: 100, second batch: 50
            mock_client.embeddings.create.side_effect = [
                self._make_mock_embedding_response(100),
                self._make_mock_embedding_response(50),
            ]

            from src.services.embedding_service import generate_embeddings

            embeddings = generate_embeddings(texts)

        assert len(embeddings) == 150
        assert mock_client.embeddings.create.call_count == 2

    # ── Single text: exactly 100 → single batch ─────────────────────────

    @pytest.mark.asyncio
    async def test_generate_embeddings_exactly_100(self):
        """Exactly 100 texts → single API call."""
        texts = [f"Text {i}" for i in range(100)]

        with patch("src.services.embedding_service.client") as mock_client, patch(
            "src.services.embedding_service.settings"
        ) as mock_settings:
            mock_settings.EMBEDDING_MODEL = "openai/text-embedding-3-small"
            mock_settings.EMBEDDING_DIMENSIONS = 1536
            mock_client.embeddings.create.return_value = (
                self._make_mock_embedding_response(100)
            )

            from src.services.embedding_service import generate_embeddings

            embeddings = generate_embeddings(texts)

        assert len(embeddings) == 100
        assert mock_client.embeddings.create.call_count == 1

    # ── generate_single_embedding: convenience wrapper ───────────────────

    @pytest.mark.asyncio
    async def test_generate_single_embedding(self):
        """generate_single_embedding returns a single vector."""
        with patch("src.services.embedding_service.client") as mock_client, patch(
            "src.services.embedding_service.settings"
        ) as mock_settings:
            mock_settings.EMBEDDING_MODEL = "openai/text-embedding-3-small"
            mock_settings.EMBEDDING_DIMENSIONS = 1536
            mock_client.embeddings.create.return_value = (
                self._make_mock_embedding_response(1)
            )

            from src.services.embedding_service import generate_single_embedding

            embedding = generate_single_embedding("Hello world")

        assert len(embedding) == 1536
        assert isinstance(embedding, list)

    # ── Scenario #11: Invalid API key → raises exception ─────────────────

    @pytest.mark.asyncio
    async def test_generate_embeddings_api_error_propagates(self):
        """If OpenRouter API call fails, the exception should propagate after retries."""
        with patch("src.services.embedding_service.client") as mock_client, patch(
            "src.services.embedding_service.settings"
        ) as mock_settings, patch("src.services.embedding_service.time.sleep"):
            mock_settings.EMBEDDING_MODEL = "openai/text-embedding-3-small"
            mock_settings.EMBEDDING_DIMENSIONS = 1536
            mock_client.embeddings.create.side_effect = Exception("Invalid API key")

            from src.services.embedding_service import generate_embeddings

            with pytest.raises(Exception, match="Invalid API key"):
                generate_embeddings(["Some text"])

    # ── Embeddings maintain order ────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_embeddings_maintain_order(self):
        """Embeddings should be returned in the same order as input texts."""
        texts = ["First", "Second", "Third"]

        # Create response with shuffled indices to verify ordering logic
        mock_response = MagicMock()
        data_items = []
        # Return items out of order (index 2, 0, 1)
        for idx, orig_idx in enumerate([2, 0, 1]):
            item = MagicMock()
            item.index = orig_idx
            item.embedding = [float(orig_idx)] * 1536  # Unique per index
            data_items.append(item)
        mock_response.data = data_items

        with patch("src.services.embedding_service.client") as mock_client, patch(
            "src.services.embedding_service.settings"
        ) as mock_settings:
            mock_settings.EMBEDDING_MODEL = "openai/text-embedding-3-small"
            mock_settings.EMBEDDING_DIMENSIONS = 1536
            mock_client.embeddings.create.return_value = mock_response

            from src.services.embedding_service import generate_embeddings

            embeddings = generate_embeddings(texts)

        # After sorting by index, the first embedding should be index 0
        assert embeddings[0][0] == 0.0
        assert embeddings[1][0] == 1.0
        assert embeddings[2][0] == 2.0


# ═════════════════════════════════════════════════════════════════════════════
# 4. INGESTION SERVICE (ORCHESTRATOR) TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestIngestionServiceProcessDocument:
    """Tests for ingestion_service.process_document() — the full pipeline."""

    # ── Scenario #1: Process valid PDF → status "ready", chunks created ──

    @pytest.mark.asyncio
    async def test_process_valid_document_success(self, db_session: AsyncSession):
        """
        Scenario #1: Process a valid PDF.
        Expected: status → "ready", chunks created with embeddings.
        """
        user = await create_verified_user(db_session)
        doc = await create_document_record(db_session, user, status="uploading")

        mock_pages = [
            {"page": 1, "text": "First page content. " * 50},
            {"page": 2, "text": "Second page content. " * 50},
        ]
        mock_metadata = {
            "title": "Test Paper",
            "author": "Jane Doe",
            "year": "2023",
            "total_pages": 2,
        }
        mock_chunks = [
            {
                "content": "Chunk zero content here that is long enough.",
                "page_number": 1,
                "chunk_index": 0,
            },
            {
                "content": "Chunk one content here that is also long enough.",
                "page_number": 1,
                "chunk_index": 1,
            },
            {
                "content": "Chunk two content from the second page of doc.",
                "page_number": 2,
                "chunk_index": 2,
            },
        ]
        mock_embeddings = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]

        with patch(
            "src.services.ingestion_service.storage.download", return_value=b"%PDF-fake"
        ), patch(
            "src.services.ingestion_service.extract_metadata",
            return_value=mock_metadata,
        ), patch(
            "src.services.ingestion_service.extract_text_from_pdf",
            return_value=mock_pages,
        ), patch(
            "src.services.ingestion_service.chunk_document", return_value=mock_chunks
        ), patch(
            "src.services.ingestion_service.generate_embeddings",
            return_value=mock_embeddings,
        ):

            from src.services.ingestion_service import process_document

            await process_document(str(doc.id), db_session)

        # Refresh document from DB
        await db_session.refresh(doc)

        # Status should be "ready"
        assert doc.status == "ready"

        # Metadata should be populated
        assert doc.title == "Test Paper"
        assert doc.author == "Jane Doe"
        assert doc.year == "2023"
        assert doc.total_pages == 2

        # Chunks should be created in DB
        result = await db_session.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
        )
        chunks = result.scalars().all()
        assert len(chunks) == 3

    # ── Scenario #2: PDF with no text → status "failed" ──────────────────

    @pytest.mark.asyncio
    async def test_process_scanned_pdf_fails(self, db_session: AsyncSession):
        """
        Scenario #2: Scanned/image PDF with no extractable text.
        Expected: status → "failed", error_message set.
        """
        user = await create_verified_user(db_session, "scan@example.com")
        doc = await create_document_record(db_session, user, status="uploading")

        mock_metadata = {
            "title": None,
            "author": None,
            "year": None,
            "total_pages": 5,
        }

        with patch(
            "src.services.ingestion_service.storage.download", return_value=b"%PDF-fake"
        ), patch(
            "src.services.ingestion_service.extract_metadata",
            return_value=mock_metadata,
        ), patch(
            "src.services.ingestion_service.extract_text_from_pdf"
        ) as mock_extract:
            mock_extract.side_effect = ValueError(
                "PDF contains no extractable text. It may be a scanned document."
            )

            from src.services.ingestion_service import process_document

            await process_document(str(doc.id), db_session)

        await db_session.refresh(doc)
        assert doc.status == "failed"
        assert doc.error_message is not None
        assert "no extractable text" in doc.error_message.lower()

    # ── Scenario #4: Corrupted PDF → status "failed" ─────────────────────

    @pytest.mark.asyncio
    async def test_process_corrupted_pdf_fails(self, db_session: AsyncSession):
        """
        Scenario #4: Corrupted PDF file.
        Expected: status → "failed", error_message set.
        """
        user = await create_verified_user(db_session, "corrupt@example.com")
        doc = await create_document_record(db_session, user, status="uploading")

        mock_metadata = {
            "title": None,
            "author": None,
            "year": None,
            "total_pages": 0,
        }

        with patch(
            "src.services.ingestion_service.storage.download", return_value=b"%PDF-fake"
        ), patch(
            "src.services.ingestion_service.extract_metadata",
            return_value=mock_metadata,
        ), patch(
            "src.services.ingestion_service.extract_text_from_pdf"
        ) as mock_extract:
            mock_extract.side_effect = ValueError("Cannot open PDF: file is corrupted")

            from src.services.ingestion_service import process_document

            await process_document(str(doc.id), db_session)

        await db_session.refresh(doc)
        assert doc.status == "failed"
        assert doc.error_message is not None
        assert "cannot open pdf" in doc.error_message.lower()

    # ── Status transition: uploading → processing → ready ────────────────

    @pytest.mark.asyncio
    async def test_status_transitions_to_processing_then_ready(
        self, db_session: AsyncSession
    ):
        """
        The document status should transition:
        uploading → processing → ready (on success).
        """
        user = await create_verified_user(db_session, "status@example.com")
        doc = await create_document_record(db_session, user, status="uploading")

        status_log = []

        original_commit = db_session.commit

        async def tracking_commit():
            """Track status changes on each commit."""
            await db_session.flush()
            status_log.append(doc.status)
            await original_commit()

        mock_pages = [{"page": 1, "text": "Page content. " * 50}]
        mock_metadata = {"title": None, "author": None, "year": None, "total_pages": 1}
        mock_chunks = [
            {
                "content": "A valid chunk with enough content to pass filter.",
                "page_number": 1,
                "chunk_index": 0,
            }
        ]
        mock_embeddings = [[0.1] * 1536]

        with patch(
            "src.services.ingestion_service.storage.download", return_value=b"%PDF-fake"
        ), patch(
            "src.services.ingestion_service.extract_metadata",
            return_value=mock_metadata,
        ), patch(
            "src.services.ingestion_service.extract_text_from_pdf",
            return_value=mock_pages,
        ), patch(
            "src.services.ingestion_service.chunk_document", return_value=mock_chunks
        ), patch(
            "src.services.ingestion_service.generate_embeddings",
            return_value=mock_embeddings,
        ), patch.object(
            db_session, "commit", side_effect=tracking_commit
        ):

            from src.services.ingestion_service import process_document

            await process_document(str(doc.id), db_session)

        # First commit sets "processing", last commit sets "ready"
        assert "processing" in status_log
        assert "ready" in status_log

    # ── Status transition: failure → processing → failed ─────────────────

    @pytest.mark.asyncio
    async def test_status_transitions_to_failed_on_error(
        self, db_session: AsyncSession
    ):
        """
        On failure, document status should be: processing → failed.
        """
        user = await create_verified_user(db_session, "fail@example.com")
        doc = await create_document_record(db_session, user, status="uploading")

        mock_metadata = {"title": None, "author": None, "year": None, "total_pages": 1}

        with patch(
            "src.services.ingestion_service.storage.download", return_value=b"%PDF-fake"
        ), patch(
            "src.services.ingestion_service.extract_metadata",
            return_value=mock_metadata,
        ), patch(
            "src.services.ingestion_service.extract_text_from_pdf"
        ) as mock_extract:
            mock_extract.side_effect = ValueError("PDF contains no extractable text.")

            from src.services.ingestion_service import process_document

            await process_document(str(doc.id), db_session)

        await db_session.refresh(doc)
        assert doc.status == "failed"
        assert doc.error_message is not None

    # ── Document not found → returns early, no crash ─────────────────────

    @pytest.mark.asyncio
    async def test_process_nonexistent_document(self, db_session: AsyncSession):
        """
        If the document ID doesn't exist in DB, the function should
        return early without raising.
        """
        fake_id = str(uuid.uuid4())

        with patch("src.services.ingestion_service.extract_metadata"), patch(
            "src.services.ingestion_service.extract_text_from_pdf"
        ), patch("src.services.ingestion_service.chunk_document"), patch(
            "src.services.ingestion_service.generate_embeddings"
        ):

            from src.services.ingestion_service import process_document

            # Should NOT raise
            await process_document(fake_id, db_session)

    # ── Business Rule #2: Metadata priority — user metadata preserved ────

    @pytest.mark.asyncio
    async def test_user_metadata_takes_priority(self, db_session: AsyncSession):
        """
        Business Rule #2: If user manually set metadata (via PATCH),
        it takes priority over auto-extracted metadata.
        """
        user = await create_verified_user(db_session, "priority@example.com")
        doc = await create_document_record(db_session, user, status="uploading")

        # Simulate user having already set title via PATCH
        doc.title = "User-Set Title"
        doc.author = "User-Set Author"
        await db_session.commit()
        await db_session.refresh(doc)

        mock_pages = [{"page": 1, "text": "Page content. " * 50}]
        mock_metadata = {
            "title": "PDF-Extracted Title",
            "author": "PDF-Extracted Author",
            "year": "2023",
            "total_pages": 1,
        }
        mock_chunks = [
            {
                "content": "A valid chunk with enough content for the system.",
                "page_number": 1,
                "chunk_index": 0,
            }
        ]
        mock_embeddings = [[0.1] * 1536]

        with patch(
            "src.services.ingestion_service.storage.download", return_value=b"%PDF-fake"
        ), patch(
            "src.services.ingestion_service.extract_metadata",
            return_value=mock_metadata,
        ), patch(
            "src.services.ingestion_service.extract_text_from_pdf",
            return_value=mock_pages,
        ), patch(
            "src.services.ingestion_service.chunk_document", return_value=mock_chunks
        ), patch(
            "src.services.ingestion_service.generate_embeddings",
            return_value=mock_embeddings,
        ):

            from src.services.ingestion_service import process_document

            await process_document(str(doc.id), db_session)

        await db_session.refresh(doc)

        # User-set values should be preserved (not overwritten)
        assert doc.title == "User-Set Title"
        assert doc.author == "User-Set Author"
        # Year was not set by user → should be filled from PDF
        assert doc.year == "2023"
        assert doc.total_pages == 1

    # ── No usable chunks → status "failed" ───────────────────────────────

    @pytest.mark.asyncio
    async def test_no_usable_chunks_sets_failed(self, db_session: AsyncSession):
        """
        If chunking returns no usable chunks (all <50 chars),
        document status should be "failed" with clear error message.
        """
        user = await create_verified_user(db_session, "nochunk@example.com")
        doc = await create_document_record(db_session, user, status="uploading")

        mock_pages = [{"page": 1, "text": "Short."}]
        mock_metadata = {"title": None, "author": None, "year": None, "total_pages": 1}
        mock_chunks = []  # Chunker returns empty after filtering

        with patch(
            "src.services.ingestion_service.storage.download", return_value=b"%PDF-fake"
        ), patch(
            "src.services.ingestion_service.extract_metadata",
            return_value=mock_metadata,
        ), patch(
            "src.services.ingestion_service.extract_text_from_pdf",
            return_value=mock_pages,
        ), patch(
            "src.services.ingestion_service.chunk_document", return_value=mock_chunks
        ):

            from src.services.ingestion_service import process_document

            await process_document(str(doc.id), db_session)

        await db_session.refresh(doc)
        assert doc.status == "failed"
        assert doc.error_message is not None
        assert "no usable text chunks" in doc.error_message.lower()

    # ── Scenario #11: OpenAI API failure → status "failed" ───────────────

    @pytest.mark.asyncio
    async def test_openai_failure_sets_failed_status(self, db_session: AsyncSession):
        """
        Scenario #11: Invalid OpenAI API key or API error.
        Expected: status → "failed", clear error message.
        """
        user = await create_verified_user(db_session, "apierr@example.com")
        doc = await create_document_record(db_session, user, status="uploading")

        mock_pages = [{"page": 1, "text": "Content. " * 100}]
        mock_metadata = {"title": None, "author": None, "year": None, "total_pages": 1}
        mock_chunks = [
            {
                "content": "A valid chunk with enough content for the system.",
                "page_number": 1,
                "chunk_index": 0,
            }
        ]

        with patch(
            "src.services.ingestion_service.storage.download", return_value=b"%PDF-fake"
        ), patch(
            "src.services.ingestion_service.extract_metadata",
            return_value=mock_metadata,
        ), patch(
            "src.services.ingestion_service.extract_text_from_pdf",
            return_value=mock_pages,
        ), patch(
            "src.services.ingestion_service.chunk_document", return_value=mock_chunks
        ), patch(
            "src.services.ingestion_service.generate_embeddings"
        ) as mock_embed:
            mock_embed.side_effect = Exception("Invalid API key")

            from src.services.ingestion_service import process_document

            with pytest.raises(Exception):
                await process_document(str(doc.id), db_session)

        await db_session.refresh(doc)
        assert doc.status == "failed"
        assert doc.error_message is not None
        assert (
            "unexpected error" in doc.error_message.lower()
            or "invalid api key" in doc.error_message.lower()
        )

    # ── Chunks saved with correct fields ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_chunks_saved_with_all_fields(self, db_session: AsyncSession):
        """
        Verify each saved DocumentChunk has:
        user_id, document_id, content, page_number, chunk_index, embedding.
        """
        user = await create_verified_user(db_session, "fields@example.com")
        doc = await create_document_record(db_session, user, status="uploading")

        mock_pages = [{"page": 1, "text": "Content. " * 100}]
        mock_metadata = {"title": None, "author": None, "year": None, "total_pages": 1}
        mock_chunks = [
            {
                "content": "First chunk content that is definitely long enough.",
                "page_number": 1,
                "chunk_index": 0,
            },
            {
                "content": "Second chunk content also long enough for system.",
                "page_number": 1,
                "chunk_index": 1,
            },
        ]
        mock_embeddings = [[0.1] * 1536, [0.2] * 1536]

        with patch(
            "src.services.ingestion_service.storage.download", return_value=b"%PDF-fake"
        ), patch(
            "src.services.ingestion_service.extract_metadata",
            return_value=mock_metadata,
        ), patch(
            "src.services.ingestion_service.extract_text_from_pdf",
            return_value=mock_pages,
        ), patch(
            "src.services.ingestion_service.chunk_document", return_value=mock_chunks
        ), patch(
            "src.services.ingestion_service.generate_embeddings",
            return_value=mock_embeddings,
        ):

            from src.services.ingestion_service import process_document

            await process_document(str(doc.id), db_session)

        result = await db_session.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
        )
        saved_chunks = result.scalars().all()

        assert len(saved_chunks) == 2
        for chunk in saved_chunks:
            assert chunk.user_id == user.id
            assert chunk.document_id == doc.id
            assert chunk.content is not None
            assert chunk.page_number is not None
            assert chunk.chunk_index is not None
            assert chunk.embedding is not None

    # ── Chunk indices match what we passed in ────────────────────────────

    @pytest.mark.asyncio
    async def test_chunk_index_saved_correctly(self, db_session: AsyncSession):
        """Saved chunks should have the correct chunk_index values (0, 1, 2...)."""
        user = await create_verified_user(db_session, "idx@example.com")
        doc = await create_document_record(db_session, user, status="uploading")

        mock_pages = [{"page": 1, "text": "Content. " * 100}]
        mock_metadata = {"title": None, "author": None, "year": None, "total_pages": 1}
        mock_chunks = [
            {
                "content": "Chunk at index zero with enough chars for the filter.",
                "page_number": 1,
                "chunk_index": 0,
            },
            {
                "content": "Chunk at index one with enough characters for filter.",
                "page_number": 1,
                "chunk_index": 1,
            },
            {
                "content": "Chunk at index two with enough characters for filter.",
                "page_number": 2,
                "chunk_index": 2,
            },
        ]
        mock_embeddings = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]

        with patch(
            "src.services.ingestion_service.storage.download", return_value=b"%PDF-fake"
        ), patch(
            "src.services.ingestion_service.extract_metadata",
            return_value=mock_metadata,
        ), patch(
            "src.services.ingestion_service.extract_text_from_pdf",
            return_value=mock_pages,
        ), patch(
            "src.services.ingestion_service.chunk_document", return_value=mock_chunks
        ), patch(
            "src.services.ingestion_service.generate_embeddings",
            return_value=mock_embeddings,
        ):

            from src.services.ingestion_service import process_document

            await process_document(str(doc.id), db_session)

        result = await db_session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == doc.id)
            .order_by(DocumentChunk.chunk_index)
        )
        saved_chunks = result.scalars().all()

        assert saved_chunks[0].chunk_index == 0
        assert saved_chunks[1].chunk_index == 1
        assert saved_chunks[2].chunk_index == 2

    # ── Edge Case: Embedding count mismatch → status "failed" ────────────

    @pytest.mark.asyncio
    async def test_embedding_count_mismatch_fails(self, db_session: AsyncSession):
        """
        Edge Case: If the number of generated embeddings does NOT match the
        number of text chunks, the pipeline must fail safely.

        The orchestrator uses `zip(chunks, embeddings)` — if embeddings are
        fewer than chunks, some chunks would be silently dropped. The service
        must validate counts and raise a ValueError on mismatch.

        Expected:
          - Document status → "failed"
          - error_message contains "embedding count mismatch" (or similar)
          - No chunks are saved to the database
        """
        user = await create_verified_user(db_session, "mismatch@example.com")
        doc = await create_document_record(db_session, user, status="uploading")

        mock_pages = [{"page": 1, "text": "Content. " * 100}]
        mock_metadata = {"title": None, "author": None, "year": None, "total_pages": 1}

        # 3 chunks but only 2 embeddings → mismatch!
        mock_chunks = [
            {
                "content": "First chunk with enough content for the filter rules.",
                "page_number": 1,
                "chunk_index": 0,
            },
            {
                "content": "Second chunk with enough content for the filter rules.",
                "page_number": 1,
                "chunk_index": 1,
            },
            {
                "content": "Third chunk with enough content for the filter rules.",
                "page_number": 1,
                "chunk_index": 2,
            },
        ]
        mock_embeddings = [[0.1] * 1536, [0.2] * 1536]  # Only 2!

        with patch(
            "src.services.ingestion_service.storage.download", return_value=b"%PDF-fake"
        ), patch(
            "src.services.ingestion_service.extract_metadata",
            return_value=mock_metadata,
        ), patch(
            "src.services.ingestion_service.extract_text_from_pdf",
            return_value=mock_pages,
        ), patch(
            "src.services.ingestion_service.chunk_document", return_value=mock_chunks
        ), patch(
            "src.services.ingestion_service.generate_embeddings",
            return_value=mock_embeddings,
        ):

            from src.services.ingestion_service import process_document

            # The pipeline may raise or handle internally — either way status must be "failed"
            try:
                await process_document(str(doc.id), db_session)
            except (ValueError, Exception):
                pass  # Some implementations re-raise

        await db_session.refresh(doc)
        assert doc.status == "failed"
        assert doc.error_message is not None
        assert (
            "mismatch" in doc.error_message.lower()
            or "embedding" in doc.error_message.lower()
        )

        # Verify NO chunks were saved to DB
        result = await db_session.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
        )
        saved_chunks = result.scalars().all()
        assert len(saved_chunks) == 0

    # ── Edge Case: Metadata extraction failure → status "failed" ─────────

    @pytest.mark.asyncio
    async def test_metadata_extraction_failure_fails_gracefully(
        self, db_session: AsyncSession
    ):
        """
        Edge Case: If extract_metadata() raises an exception (e.g., malformed
        metadata structure), the document must NOT stay stuck in "processing".

        Expected:
          - Document status → "failed"
          - error_message contains the original error text
          - No chunks saved to the database
        """
        user = await create_verified_user(db_session, "metafail@example.com")
        doc = await create_document_record(db_session, user, status="uploading")

        with patch(
            "src.services.ingestion_service.storage.download", return_value=b"%PDF-fake"
        ), patch("src.services.ingestion_service.extract_metadata") as mock_meta, patch(
            "src.services.ingestion_service.extract_text_from_pdf"
        ), patch(
            "src.services.ingestion_service.chunk_document"
        ), patch(
            "src.services.ingestion_service.generate_embeddings"
        ):
            mock_meta.side_effect = Exception("Metadata extraction failed")

            from src.services.ingestion_service import process_document

            # The pipeline may raise or handle internally
            try:
                await process_document(str(doc.id), db_session)
            except Exception:
                pass

        await db_session.refresh(doc)
        assert doc.status == "failed"
        assert doc.error_message is not None
        assert "metadata extraction failed" in doc.error_message.lower()

        # Verify NO chunks were saved to DB
        result = await db_session.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
        )
        saved_chunks = result.scalars().all()
        assert len(saved_chunks) == 0


# ═════════════════════════════════════════════════════════════════════════════
# 5. CHUNK OVERLAP VALIDATION TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestChunkOverlapValidation:
    """Verify that the chunker actually applies overlap between consecutive chunks."""

    @pytest.mark.asyncio
    async def test_chunk_overlap_is_applied(self):
        """
        Given a long text and chunk_overlap=100, the last 100 characters of
        chunk N should appear at the beginning of chunk N+1.

        This guarantees no context is lost at chunk boundaries.
        """
        # Build a deterministic long text (>2000 chars) from numbered sentences
        # so we can reliably verify overlap boundaries.
        sentences = [
            f"Sentence number {i} is part of this test document. " for i in range(60)
        ]
        long_text = "".join(sentences)  # ~3000 chars

        pages = [{"page": 1, "text": long_text}]

        with patch("src.services.chunker.settings") as mock_settings:
            mock_settings.CHUNK_SIZE = 800
            mock_settings.CHUNK_OVERLAP = 100
            mock_settings.MIN_CHUNK_LENGTH = 50

            from src.services.chunker import chunk_document

            chunks = chunk_document(pages)

        # Must produce more than 1 chunk to verify overlap
        assert len(chunks) > 1, (
            f"Expected >1 chunk from {len(long_text)} chars, " f"got {len(chunks)}"
        )

        # Verify overlap: strip [Page N] prefix, then compare tail/head
        overlap = mock_settings.CHUNK_OVERLAP  # 100
        import re

        def strip_page_prefix(content: str) -> str:
            """Remove [Page N] prefix from chunk content."""
            return re.sub(r"^\[Page \d+\] ", "", content)

        for i in range(len(chunks) - 1):
            chunk_current = strip_page_prefix(chunks[i]["content"])
            chunk_next = strip_page_prefix(chunks[i + 1]["content"])

            tail = chunk_current[-overlap:]
            head = chunk_next[:overlap]

            assert tail == head, (
                f"Overlap mismatch between chunk {i} and chunk {i+1}:\n"
                f"  tail({i}): {tail!r}\n"
                f"  head({i+1}): {head!r}"
            )

    @pytest.mark.asyncio
    async def test_chunk_overlap_produces_more_chunks_than_no_overlap(self):
        """
        With overlap enabled, the chunker should produce MORE chunks than
        if overlap were 0, because content is duplicated across boundaries.
        """
        sentences = [
            f"This is sentence {i} in a paragraph about testing. " for i in range(50)
        ]
        long_text = "".join(sentences)
        pages = [{"page": 1, "text": long_text}]

        # Chunks WITH overlap
        with patch("src.services.chunker.settings") as mock_settings:
            mock_settings.CHUNK_SIZE = 800
            mock_settings.CHUNK_OVERLAP = 100
            mock_settings.MIN_CHUNK_LENGTH = 50

            from src.services.chunker import chunk_document

            chunks_with_overlap = chunk_document(pages)

        # Chunks WITHOUT overlap
        with patch("src.services.chunker.settings") as mock_settings:
            mock_settings.CHUNK_SIZE = 800
            mock_settings.CHUNK_OVERLAP = 0
            mock_settings.MIN_CHUNK_LENGTH = 50

            from src.services.chunker import chunk_document

            chunks_no_overlap = chunk_document(pages)

        assert len(chunks_with_overlap) >= len(chunks_no_overlap), (
            f"Overlap chunks ({len(chunks_with_overlap)}) should be >= "
            f"no-overlap chunks ({len(chunks_no_overlap)})"
        )
