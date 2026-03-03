# SPEC-09: Testing Strategy

> **Status:** 🔲 Todo (incremental — tests are written per spec)  
> **Dependencies:** Each test file depends on its corresponding spec  
> **Priority:** P0 — runs in parallel with every spec  
> **Note:** This is NOT a standalone phase — tests are written **with** each feature

---

## Overview

### الفلسفة: "كل Spec يتسلم مع Tests"

الـ testing مش مرحلة منفصلة في الآخر — كل Spec Kit لما يتنفذ، الـ tests بتاعته بتتكتب **في نفس الوقت**.

```
SPEC-02 (Upload) → implement → write tests → verify ✅ → done
SPEC-03 (Ingestion) → implement → write tests → verify ✅ → done
... وهكذا
```

### أنواع الـ Tests

```
┌─────────────────────────────────────────────────┐
│                 TESTING PYRAMID                  │
│                                                 │
│                    ╱╲                            │
│                   ╱  ╲         E2E Tests         │
│                  ╱ 5% ╲        (few, slow)       │
│                 ╱──────╲                         │
│                ╱        ╲                        │
│               ╱   25%    ╲     Integration Tests │
│              ╱────────────╲    (API endpoints)   │
│             ╱              ╲                     │
│            ╱     70%        ╲   Unit Tests       │
│           ╱──────────────────╲  (fast, many)     │
│                                                 │
└─────────────────────────────────────────────────┘
```

| النوع | إيه بيختبر | السرعة | الكمية |
|---|---|---|---|
| **Unit Tests** | function واحدة بمعزل عن الباقي | ⚡ سريع جداً | كتير (~70%) |
| **Integration Tests** | API endpoint كامل (route → controller → DB) | 🔄 متوسط | متوسط (~25%) |
| **E2E Tests** | سيناريو كامل من البداية للنهاية | 🐢 بطيء | قليل (~5%) |

---

## الـ Setup الحالي ✅

عندك أساس ممتاز:

| Component | Status | File |
|---|---|---|
| pytest.ini | ✅ Configured | `pytest.ini` |
| conftest.py | ✅ Done | `tests/conftest.py` |
| Test DB | ✅ Configured | `TEST_DATABASE_URL` in `.env` |
| Async support | ✅ Ready | `pytest-asyncio` with `asyncio_mode = auto` |
| Test client | ✅ Ready | `httpx.AsyncClient` with ASGI transport |
| DB cleanup | ✅ Done | Cleans `users` table after each test |

### ما يحتاج تحديث في الـ Setup

الـ `conftest.py` الحالي بيمسح `users` بس. لما نضيف جداول جديدة، نحتاج نمسح الكل:

```python
# الحالي:
await conn.execute(text("DELETE FROM users"))

# المطلوب (بعد إضافة كل الجداول):
await conn.execute(text("DELETE FROM messages"))
await conn.execute(text("DELETE FROM chats"))
await conn.execute(text("DELETE FROM document_chunks"))
await conn.execute(text("DELETE FROM documents"))
await conn.execute(text("DELETE FROM users"))
```

> الترتيب مهم! امسح الجداول اللي فيها Foreign Keys الأول.

---

## Test File Structure

```
tests/
├── conftest.py                     # ✅ EXISTS — Global fixtures (DB, client, auth helpers)
├── __init__.py                     # ✅ EXISTS
│
├── # Auth tests (ALREADY DONE)
├── test_auth.py                    # ✅ EXISTS — Registration + verification
├── test_login.py                   # ✅ EXISTS — Login + JWT
├── test_forgot_password.py         # ✅ EXISTS — Password reset
│
├── # Document tests (SPEC-02)
├── test_document_upload.py         # 🔲 Upload validation + storage
├── test_document_crud.py           # 🔲 List, get, update, delete
│
├── # Ingestion tests (SPEC-03)
├── test_pdf_parser.py              # 🔲 PDF text extraction
├── test_chunker.py                 # 🔲 Text chunking logic
├── test_embedding_service.py       # 🔲 Embedding generation
├── test_ingestion_pipeline.py      # 🔲 Full pipeline integration
│
├── # Retrieval tests (SPEC-04)
├── test_retrieval.py               # 🔲 Semantic search + context builder
│
├── # Chat tests (SPEC-05)
├── test_chat_crud.py               # 🔲 Chat create, list, delete
├── test_chat_query.py              # 🔲 RAG query pipeline
│
├── # Citation tests (SPEC-06)
├── test_citations.py               # 🔲 APA, MLA, BibTeX formatting
│
├── # E2E tests
├── test_e2e_flow.py                # 🔲 Upload → Process → Query → Cite
│
└── fixtures/                       # 🔲 Test data
    ├── sample.pdf                  # Small real PDF for testing
    ├── empty.pdf                   # PDF with no text
    ├── large.pdf                   # 50+ page PDF
    └── not_a_pdf.txt               # Non-PDF file for rejection tests
```

---

## Common Test Fixtures (conftest.py additions)

### Authenticated User Helper

```python
@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Register a user, verify them, login, and return auth headers."""
    # 1. Register
    await client.post("/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "TestPassword123!",
    })

    # 2. Verify email (directly in DB for tests)
    async with TestSessionLocal() as session:
        from sqlalchemy import update
        from src.models.db_scheams.user import User
        await session.execute(
            update(User)
            .where(User.email == "test@example.com")
            .values(is_active=True, is_verified=True)
        )
        await session.commit()

    # 3. Login
    response = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "TestPassword123!",
    })
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def second_user_headers(client: AsyncClient) -> dict:
    """Create a second authenticated user (for isolation tests)."""
    await client.post("/auth/register", json={
        "name": "Other User",
        "email": "other@example.com",
        "password": "OtherPassword123!",
    })

    async with TestSessionLocal() as session:
        from sqlalchemy import update
        from src.models.db_scheams.user import User
        await session.execute(
            update(User)
            .where(User.email == "other@example.com")
            .values(is_active=True, is_verified=True)
        )
        await session.commit()

    response = await client.post("/auth/login", json={
        "email": "other@example.com",
        "password": "OtherPassword123!",
    })
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}
```

### Sample PDF Fixture

```python
import io

@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Create a minimal valid PDF for testing."""
    # Using PyMuPDF to create a test PDF in memory
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "This is a test document about deep learning.\n\n"
        "Deep learning is a subset of machine learning that uses neural networks "
        "with multiple layers to learn representations of data.\n\n"
        "Convolutional Neural Networks (CNNs) are particularly effective for "
        "image recognition tasks in medical imaging.")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def sample_pdf_file(sample_pdf_bytes) -> io.BytesIO:
    """Create a file-like object for upload testing."""
    return io.BytesIO(sample_pdf_bytes)
```

---

## Test Details Per Spec

### Tests for SPEC-02: Document Upload

**File:** `tests/test_document_upload.py`

```python
"""Tests for document upload and validation."""
import pytest
import io
from httpx import AsyncClient


class TestDocumentUpload:
    """Test PDF upload endpoint: POST /documents/upload"""

    async def test_upload_valid_pdf(self, client: AsyncClient, auth_headers, sample_pdf_bytes):
        """✅ Upload a valid PDF → 201, file saved, DB record created."""
        response = await client.post(
            "/documents/upload",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] in ("processing", "ready")
        assert data["file_name"] == "test.pdf"
        assert "id" in data

    async def test_upload_non_pdf(self, client: AsyncClient, auth_headers):
        """❌ Upload .txt file → 400 error."""
        response = await client.post(
            "/documents/upload",
            files={"file": ("test.txt", b"not a pdf", "text/plain")},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    async def test_upload_empty_file(self, client: AsyncClient, auth_headers):
        """❌ Upload empty file → 400 error."""
        response = await client.post(
            "/documents/upload",
            files={"file": ("empty.pdf", b"", "application/pdf")},
            headers=auth_headers,
        )
        assert response.status_code == 400

    async def test_upload_without_auth(self, client: AsyncClient, sample_pdf_bytes):
        """❌ Upload without token → 401."""
        response = await client.post(
            "/documents/upload",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 401

    async def test_upload_creates_db_record(self, client, auth_headers, sample_pdf_bytes, db_session):
        """✅ Upload creates a Document record in the database."""
        response = await client.post(
            "/documents/upload",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers,
        )
        doc_id = response.json()["id"]

        # Verify in DB
        from sqlalchemy import select
        from src.models.db_scheams.document import Document
        result = await db_session.execute(
            select(Document).where(Document.id == doc_id)
        )
        doc = result.scalar_one_or_none()
        assert doc is not None
        assert doc.file_name == "test.pdf"
```

**File:** `tests/test_document_crud.py`

```python
"""Tests for document CRUD operations."""

class TestDocumentList:
    """Test document listing: GET /documents/"""

    async def test_list_empty(self, client, auth_headers):
        """List with no documents → empty array."""
        response = await client.get("/documents/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["documents"] == []
        assert response.json()["total"] == 0

    async def test_list_with_documents(self, client, auth_headers, sample_pdf_bytes):
        """List after uploading → returns documents."""
        # Upload 2 documents
        await client.post("/documents/upload",
            files={"file": ("doc1.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers)
        await client.post("/documents/upload",
            files={"file": ("doc2.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers)

        response = await client.get("/documents/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 2

    async def test_list_isolation(self, client, auth_headers, second_user_headers, sample_pdf_bytes):
        """User A cannot see User B's documents."""
        # User A uploads
        await client.post("/documents/upload",
            files={"file": ("doc_a.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers)

        # User B lists → should be empty
        response = await client.get("/documents/", headers=second_user_headers)
        assert response.json()["total"] == 0


class TestDocumentDelete:
    """Test document deletion: DELETE /documents/{id}"""

    async def test_delete_own_document(self, client, auth_headers, sample_pdf_bytes):
        """✅ Delete own document → 200, record removed."""
        upload = await client.post("/documents/upload",
            files={"file": ("doc.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers)
        doc_id = upload.json()["id"]

        response = await client.delete(f"/documents/{doc_id}", headers=auth_headers)
        assert response.status_code == 200

        # Verify deleted
        get_response = await client.get(f"/documents/{doc_id}", headers=auth_headers)
        assert get_response.status_code == 404

    async def test_delete_other_users_document(self, client, auth_headers, second_user_headers, sample_pdf_bytes):
        """❌ Cannot delete another user's document → 403."""
        upload = await client.post("/documents/upload",
            files={"file": ("doc.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers)
        doc_id = upload.json()["id"]

        response = await client.delete(f"/documents/{doc_id}", headers=second_user_headers)
        assert response.status_code == 403
```

---

### Tests for SPEC-03: Ingestion Pipeline (Unit Tests)

**File:** `tests/test_pdf_parser.py`

```python
"""Unit tests for PDF text extraction."""
import pytest


class TestPdfParser:
    """Test PDF parsing functions in isolation."""

    def test_extract_text_valid_pdf(self, sample_pdf_bytes, tmp_path):
        """✅ Extract text from valid PDF."""
        from src.services.pdf_parser import extract_text_from_pdf

        # Write to temp file
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(sample_pdf_bytes)

        pages = extract_text_from_pdf(str(pdf_path))
        assert len(pages) >= 1
        assert pages[0]["page"] == 1
        assert len(pages[0]["text"]) > 0

    def test_extract_metadata(self, sample_pdf_bytes, tmp_path):
        """✅ Extract metadata from PDF."""
        from src.services.pdf_parser import extract_metadata

        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(sample_pdf_bytes)

        metadata = extract_metadata(str(pdf_path))
        assert "total_pages" in metadata
        assert metadata["total_pages"] >= 1

    def test_extract_text_invalid_file(self, tmp_path):
        """❌ Non-PDF file raises ValueError."""
        from src.services.pdf_parser import extract_text_from_pdf

        bad_file = tmp_path / "not_a_pdf.txt"
        bad_file.write_text("this is not a pdf")

        with pytest.raises(ValueError, match="Cannot open PDF"):
            extract_text_from_pdf(str(bad_file))
```

**File:** `tests/test_chunker.py`

```python
"""Unit tests for text chunking."""

class TestChunker:
    """Test chunking logic in isolation — NO external dependencies."""

    def test_chunk_basic(self):
        """✅ Text is split into chunks of correct size."""
        from src.services.chunker import chunk_document

        pages = [{"page": 1, "text": "A " * 500}]  # 1000 chars
        chunks = chunk_document(pages)

        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk["content"]) <= 900  # chunk_size + some tolerance
            assert chunk["page_number"] == 1
            assert "chunk_index" in chunk

    def test_chunk_preserves_page_number(self):
        """✅ Each chunk remembers which page it came from."""
        from src.services.chunker import chunk_document

        pages = [
            {"page": 1, "text": "Content from page one. " * 50},
            {"page": 2, "text": "Content from page two. " * 50},
        ]
        chunks = chunk_document(pages)

        page_numbers = {c["page_number"] for c in chunks}
        assert 1 in page_numbers
        assert 2 in page_numbers

    def test_chunk_index_ordering(self):
        """✅ Chunk indices are sequential starting from 0."""
        from src.services.chunker import chunk_document

        pages = [{"page": 1, "text": "Word " * 400}]
        chunks = chunk_document(pages)

        indices = [c["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_chunk_filters_tiny_fragments(self):
        """✅ Chunks < 50 chars are discarded."""
        from src.services.chunker import chunk_document

        pages = [{"page": 1, "text": "Hi"}]  # Too short
        chunks = chunk_document(pages)

        assert len(chunks) == 0

    def test_chunk_empty_input(self):
        """✅ Empty input returns empty list."""
        from src.services.chunker import chunk_document
        assert chunk_document([]) == []
```

---

### Tests for SPEC-06: Citation Engine (Pure Unit Tests)

**File:** `tests/test_citations.py`

```python
"""Unit tests for citation generation — pure logic, no DB or API needed."""
import pytest


class TestAPACitation:
    """Test APA citation formatting."""

    def test_single_author(self):
        from src.services.citation_service import CitationGenerator
        meta = {"author": "Smith, John", "year": "2020",
                "title": "Deep Learning", "journal": "AI Journal"}

        result = CitationGenerator.apa_reference(meta)
        assert "Smith, J." in result
        assert "(2020)" in result
        assert "Deep Learning" in result

    def test_two_authors(self):
        from src.services.citation_service import CitationGenerator
        meta = {"author": "Smith, John and Doe, Jane", "year": "2020",
                "title": "A Study", "journal": "Science"}

        result = CitationGenerator.apa_reference(meta)
        assert "&" in result  # APA uses & for two authors

    def test_three_authors(self):
        from src.services.citation_service import CitationGenerator
        meta = {"author": "Smith, John and Doe, Jane and Johnson, Bob",
                "year": "2020", "title": "A Study"}

        result = CitationGenerator.apa_reference(meta)
        assert "Smith" in result and "Doe" in result and "Johnson" in result

    def test_inline_single(self):
        from src.services.citation_service import CitationGenerator
        meta = {"author": "Smith, John", "year": "2020"}

        result = CitationGenerator.apa_inline(meta)
        assert result == "(Smith, 2020)"

    def test_inline_three_plus(self):
        from src.services.citation_service import CitationGenerator
        meta = {"author": "Smith, John and Doe, Jane and Johnson, Bob",
                "year": "2020"}

        result = CitationGenerator.apa_inline(meta)
        assert result == "(Smith et al., 2020)"

    def test_missing_year(self):
        from src.services.citation_service import CitationGenerator
        meta = {"author": "Smith, John", "title": "A Study"}

        result = CitationGenerator.apa_reference(meta)
        assert "n.d." in result

    def test_with_doi(self):
        from src.services.citation_service import CitationGenerator
        meta = {"author": "Smith, John", "year": "2020",
                "title": "A Study", "doi": "10.1234/test"}

        result = CitationGenerator.apa_reference(meta)
        assert "doi.org" in result


class TestBibTeX:
    """Test BibTeX generation."""

    def test_article_with_journal(self):
        from src.services.citation_service import CitationGenerator
        meta = {"author": "Smith, John", "year": "2020",
                "title": "Deep Learning", "journal": "AI Journal"}

        result = CitationGenerator.bibtex_entry(meta)
        assert result.startswith("@article{")
        assert "title={Deep Learning}" in result
        assert "year={2020}" in result

    def test_misc_without_journal(self):
        from src.services.citation_service import CitationGenerator
        meta = {"author": "Smith, John", "year": "2020",
                "title": "Deep Learning"}

        result = CitationGenerator.bibtex_entry(meta)
        assert result.startswith("@misc{")

    def test_key_generation(self):
        from src.services.citation_service import CitationGenerator
        meta = {"author": "Smith, John", "year": "2020",
                "title": "Deep Learning in Medicine"}

        result = CitationGenerator.bibtex_entry(meta)
        assert "smith2020deep" in result


class TestMLA:
    """Test MLA citation formatting."""

    def test_basic_mla(self):
        from src.services.citation_service import CitationGenerator
        meta = {"author": "Smith, John", "year": "2020",
                "title": "Deep Learning", "journal": "AI Journal"}

        result = CitationGenerator.mla_reference(meta)
        assert '"Deep Learning."' in result
        assert "2020" in result
```

---

### Tests for SPEC-05: Chat Query (Integration)

**File:** `tests/test_chat_query.py`

```python
"""Integration tests for the RAG query pipeline."""

class TestChatQuery:
    """Test the full query flow: question → retrieval → LLM → response."""

    async def test_query_returns_answer_with_sources(
        self, client, auth_headers, uploaded_ready_document
    ):
        """✅ Full RAG flow: question → answer with sources."""
        # Create chat
        chat_res = await client.post("/chats/", headers=auth_headers)
        chat_id = chat_res.json()["id"]

        # Send query
        response = await client.post(
            f"/chats/{chat_id}/query",
            json={"question": "What is deep learning?"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert "answer" in data
        assert len(data["answer"]) > 0
        assert "sources" in data
        assert "message_id" in data

    async def test_query_no_documents(self, client, auth_headers):
        """❌ Query with no uploaded documents → 400."""
        chat_res = await client.post("/chats/", headers=auth_headers)
        chat_id = chat_res.json()["id"]

        response = await client.post(
            f"/chats/{chat_id}/query",
            json={"question": "What is deep learning?"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "no processed documents" in response.json()["detail"].lower()

    async def test_query_empty_question(self, client, auth_headers):
        """❌ Empty question → 400."""
        chat_res = await client.post("/chats/", headers=auth_headers)
        chat_id = chat_res.json()["id"]

        response = await client.post(
            f"/chats/{chat_id}/query",
            json={"question": ""},
            headers=auth_headers,
        )
        assert response.status_code in (400, 422)
```

---

### E2E Test: Full Flow

**File:** `tests/test_e2e_flow.py`

```python
"""End-to-end test: Upload → Process → Query → Get Citations"""

class TestE2EFlow:
    """Test the complete user journey."""

    async def test_full_research_flow(self, client, auth_headers, sample_pdf_bytes):
        """
        Complete flow:
        1. Upload PDF
        2. Wait for processing
        3. Create chat
        4. Ask question
        5. Get citations
        """
        # 1. Upload
        upload_res = await client.post("/documents/upload",
            files={"file": ("research.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers)
        assert upload_res.status_code == 201
        doc_id = upload_res.json()["id"]

        # 2. Verify processed (poll or check directly)
        doc_res = await client.get(f"/documents/{doc_id}", headers=auth_headers)
        assert doc_res.json()["status"] in ("processing", "ready")
        # In real test, poll until ready or use direct DB check

        # 3. Create chat
        chat_res = await client.post("/chats/", headers=auth_headers)
        assert chat_res.status_code == 201
        chat_id = chat_res.json()["id"]

        # 4. Query (only if document is ready)
        if doc_res.json()["status"] == "ready":
            query_res = await client.post(f"/chats/{chat_id}/query",
                json={"question": "What is this paper about?"},
                headers=auth_headers)
            assert query_res.status_code == 200
            msg_id = query_res.json()["message_id"]

            # 5. Get citations
            cite_res = await client.get(
                f"/citations/messages/{msg_id}",
                headers=auth_headers)
            assert cite_res.status_code == 200
            assert "citations" in cite_res.json()
```

---

## Mocking Strategy

### ما يتعملّه Mock | ما يتعملّوش Mock

| Service | Mock? | Why |
|---|---|---|
| **OpenAI API (embeddings)** | ✅ Yes (in unit tests) | Costs money, slow, needs API key |
| **OpenAI API (LLM)** | ✅ Yes (in unit tests) | Same as above |
| **Database** | ❌ No | Use real test DB for accuracy |
| **File system** | ❌ No (use tmp_path) | pytest's tmp_path handles cleanup |
| **PDF parser** | ❌ No | Fast, no external deps |
| **Chunker** | ❌ No | Pure logic, instant |
| **Citation generator** | ❌ No | Pure logic, instant |

### How to Mock OpenAI

```python
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_openai_embedding():
    """Mock OpenAI embedding API to return fake vectors."""
    fake_embedding = [0.1] * 1536  # 1536-dim fake vector

    with patch("src.services.embedding_service.client") as mock_client:
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=fake_embedding, index=0)]
        mock_client.embeddings.create.return_value = mock_response
        yield mock_client


@pytest.fixture
def mock_openai_llm():
    """Mock OpenAI chat completion API."""
    with patch("src.services.llm_service.client") as mock_client:
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="This is a test answer based on [Source 1]."))
        ]
        mock_response.usage = MagicMock(total_tokens=150)
        mock_client.chat.completions.create.return_value = mock_response
        yield mock_client
```

---

## Running Tests

### Commands

```bash
# Run all tests
pytest

# Run specific spec's tests
pytest tests/test_document_upload.py -v

# Run specific test class
pytest tests/test_citations.py::TestAPACitation -v

# Run specific test
pytest tests/test_citations.py::TestAPACitation::test_single_author -v

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Run only fast unit tests (exclude integration)
pytest tests/test_chunker.py tests/test_citations.py tests/test_pdf_parser.py -v

# Run with output (see print statements)
pytest -s
```

### CI-Friendly Command

```bash
pytest --tb=short --no-header -q
```

---

## Test Coverage Goals

| Module | Target Coverage | Notes |
|---|---|---|
| `services/citation_service.py` | **95%+** | Pure logic, easy to test |
| `services/chunker.py` | **95%+** | Pure logic, easy to test |
| `services/pdf_parser.py` | **90%+** | File I/O but deterministic |
| `controllers/document_controller.py` | **85%+** | Integration with DB |
| `controllers/chat_controller.py` | **80%+** | Complex flow with external APIs |
| `services/retrieval_service.py` | **80%+** | DB-dependent |
| `services/llm_service.py` | **70%+** | External API (mocked) |
| `routes/*.py` | **85%+** | Thin layer, tested via integration |
| **Overall** | **80%+** | |

---

## Dependencies for Testing

Already in `requirements.txt`:
```
pytest==8.0.2
pytest-asyncio==0.23.5
httpx==0.27.0
```

**Add these:**
```
pytest-cov==4.1.0        # Coverage reporting
pytest-mock==3.12.0      # Easier mocking
```

---

## Test Execution Per Spec

| When Implementing | Run These Tests |
|---|---|
| SPEC-02 (Upload) | `pytest tests/test_document_upload.py tests/test_document_crud.py -v` |
| SPEC-03 (Ingestion) | `pytest tests/test_pdf_parser.py tests/test_chunker.py tests/test_ingestion_pipeline.py -v` |
| SPEC-04 (Retrieval) | `pytest tests/test_retrieval.py -v` |
| SPEC-05 (Chat) | `pytest tests/test_chat_crud.py tests/test_chat_query.py -v` |
| SPEC-06 (Citations) | `pytest tests/test_citations.py -v` |
| All done | `pytest --cov=src -v` |

---

## Acceptance Criteria

- [ ] Test fixtures for authenticated users work (auth_headers)
- [ ] Test fixtures for sample PDFs work (sample_pdf_bytes)
- [ ] OpenAI mocking fixtures are available
- [ ] conftest.py cleans up all tables (not just users)
- [ ] Each spec has corresponding test files
- [ ] Unit tests run without external services (no OpenAI, no Redis)
- [ ] Integration tests use real test database
- [ ] Citation tests cover APA, MLA, BibTeX for 1, 2, 3+ authors
- [ ] Data isolation tests verify cross-user protection
- [ ] E2E test covers the full Upload → Query → Cite flow
- [ ] `pytest --cov=src` reports ≥ 80% overall coverage
- [ ] All tests pass in CI (GitHub Actions compatible)
