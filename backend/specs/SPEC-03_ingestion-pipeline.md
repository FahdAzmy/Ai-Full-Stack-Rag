# SPEC-03: Ingestion Pipeline

> **Status:** 🔲 Todo  
> **Dependencies:** SPEC-02 (Document Upload) ✅  
> **Priority:** P0 — Critical Path  
> **Estimated effort:** 4–5 days

---

## Overview

Convert uploaded PDFs into searchable vector embeddings stored in pgvector. This is the core data preparation pipeline:

```
PDF file → Extract Text → Extract Metadata → Chunk Text → Generate Embeddings → Save to DB
```

This spec is triggered **after** a document is uploaded (SPEC-02). When the upload endpoint creates a Document record, this pipeline runs to process it.

---

## Pipeline Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    INGESTION PIPELINE                         │
│                                                              │
│  ┌───────────┐    ┌───────────┐    ┌────────────────────┐   │
│  │ PDF File  │───►│ Text      │───►│ Metadata           │   │
│  │           │    │ Extractor │    │ Extractor           │   │
│  └───────────┘    └─────┬─────┘    └────────┬───────────┘   │
│                         │                    │               │
│                         ▼                    ▼               │
│                   ┌───────────┐    ┌────────────────────┐   │
│                   │ Chunker   │    │ Update Document    │   │
│                   │           │    │ metadata in DB     │   │
│                   └─────┬─────┘    └────────────────────┘   │
│                         │                                    │
│                         ▼                                    │
│                   ┌───────────┐                              │
│                   │ Embedding │                              │
│                   │ Generator │                              │
│                   └─────┬─────┘                              │
│                         │                                    │
│                         ▼                                    │
│                   ┌───────────┐                              │
│                   │ Save to   │                              │
│                   │ pgvector  │                              │
│                   └───────────┘                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Database Changes

### Modify `document_chunks` table

**File:** `src/models/db_scheams/DocumeCnthunk.py`

| Column | Type | Constraints | New? | Purpose |
|---|---|---|---|---|
| `id` | UUID | PK | ❌ | Primary key |
| `user_id` | UUID | FK → users.id | ❌ | Owner |
| `document_id` | UUID | FK → documents.id | ❌ | Parent document |
| `content` | Text | NOT NULL | ❌ | Chunk text content |
| `page_number` | Integer | nullable | ❌ | Source page number |
| `chunk_index` | Integer | NOT NULL | ✅ | Order within document |
| `embedding` | Vector(1536) | nullable | ❌ | 1536-dim embedding |
| `created_at` | DateTime | default utcnow | ❌ | |

### Migration

```bash
alembic revision --autogenerate -m "add chunk_index to document_chunks"
alembic upgrade head
```

---

## New Dependencies

**Add to `requirements.txt`:**

```
# PDF Processing
PyMuPDF==1.25.3

# Text Splitting
langchain-text-splitters==0.3.8

# OpenAI (Embeddings + LLM)
openai==1.75.0
```

**Install:**
```bash
pip install PyMuPDF langchain-text-splitters openai
pip freeze > requirements.txt  # or manually add versions
```

---

## Config Additions

**File:** `src/helpers/config.py` — add to `Settings` class:

```python
# OpenAI
OPENAI_API_KEY: str

# Embedding
EMBEDDING_MODEL: str = "text-embedding-3-small"
EMBEDDING_DIMENSIONS: int = 1536

# Chunking
CHUNK_SIZE: int = 800
CHUNK_OVERLAP: int = 100
```

**File:** `.env` — add:

```env
OPENAI_API_KEY=sk-your-key-here
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
CHUNK_SIZE=800
CHUNK_OVERLAP=100
```

---

## Services to Create

### Service 1: PDF Parser

**New file:** `src/services/pdf_parser.py`

Responsibilities:
- Extract text page-by-page from PDF
- Extract PDF metadata (title, author, creation date)
- Count total pages

```python
"""
PDF Parser — Extract text and metadata from PDF files using PyMuPDF.
"""
import re
import fitz  # PyMuPDF


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Extract text page-by-page from a PDF.

    Returns:
        [{"page": 1, "text": "..."}, {"page": 2, "text": "..."}, ...]

    Raises:
        ValueError: If the file cannot be opened or has no extractable text.
    """
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise ValueError(f"Cannot open PDF: {str(e)}")

    pages = []
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text("text")
        cleaned = _clean_text(text)
        if cleaned:
            pages.append({
                "page": page_num + 1,
                "text": cleaned,
            })

    doc.close()

    if not pages:
        raise ValueError("PDF contains no extractable text. It may be a scanned document.")

    return pages


def extract_metadata(file_path: str) -> dict:
    """
    Extract metadata from PDF file properties.

    Returns:
        {
            "title": str | None,
            "author": str | None,
            "year": str | None,
            "total_pages": int,
        }
    """
    doc = fitz.open(file_path)
    meta = doc.metadata or {}
    total_pages = doc.page_count
    doc.close()

    return {
        "title": meta.get("title", "").strip() or None,
        "author": meta.get("author", "").strip() or None,
        "year": _extract_year(meta.get("creationDate", "")),
        "total_pages": total_pages,
    }


def _clean_text(text: str) -> str:
    """Clean extracted text: normalize whitespace, remove control chars."""
    if not text:
        return ""
    # Replace multiple newlines with double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Replace multiple spaces with single space
    text = re.sub(r' {2,}', ' ', text)
    # Remove control characters except newline and tab
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text.strip()


def _extract_year(date_str: str) -> str | None:
    """Extract 4-digit year from PDF date string like 'D:20200315120000'."""
    if not date_str:
        return None
    match = re.search(r'(\d{4})', date_str)
    return match.group(1) if match else None
```

---

### Service 2: Text Chunker

**New file:** `src/services/chunker.py`

Responsibilities:
- Split extracted text into overlapping chunks
- Preserve page number for each chunk
- Use RecursiveCharacterTextSplitter for intelligent splitting

```python
"""
Text Chunker — Split document text into overlapping chunks.

Strategy:
  - Chunk size: 800 characters (configurable)
  - Overlap: 100 characters (configurable)
  - Splits on: paragraphs → sentences → words (in order of priority)
  - Each chunk retains its source page number
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.helpers.config import settings


def chunk_document(pages: list[dict]) -> list[dict]:
    """
    Split document pages into overlapping chunks.

    Args:
        pages: [{"page": 1, "text": "..."}, ...]

    Returns:
        [
            {"content": "...", "page_number": 1, "chunk_index": 0},
            {"content": "...", "page_number": 1, "chunk_index": 1},
            {"content": "...", "page_number": 2, "chunk_index": 2},
            ...
        ]
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,       # 800
        chunk_overlap=settings.CHUNK_OVERLAP,  # 100
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
        length_function=len,
        is_separator_regex=False,
    )

    chunks = []
    chunk_index = 0

    for page_data in pages:
        page_text = page_data["text"]
        page_num = page_data["page"]

        # Split this page's text
        page_chunks = splitter.split_text(page_text)

        for chunk_text in page_chunks:
            chunk_text = chunk_text.strip()
            if chunk_text and len(chunk_text) >= 50:  # Skip tiny fragments
                chunks.append({
                    "content": chunk_text,
                    "page_number": page_num,
                    "chunk_index": chunk_index,
                })
                chunk_index += 1

    return chunks
```

**Why these parameters?**

| Parameter | Value | Reason |
|---|---|---|
| `chunk_size` | 800 | ~200 tokens — fits well in LLM context alongside other chunks |
| `chunk_overlap` | 100 | Prevents losing context at chunk boundaries |
| `min_length` | 50 | Filters out noise like headers, page numbers |
| Separators | `\n\n` → `\n` → `. ` → ` ` | Prefers splitting at paragraph breaks, then sentences |

---

### Service 3: Embedding Generator

**New file:** `src/services/embedding_service.py`

Responsibilities:
- Generate embeddings using OpenAI text-embedding-3-small
- Batch processing (max 100 per API call)
- Error handling and retry logic

```python
"""
Embedding Service — Generate vector embeddings using OpenAI API.

Model: text-embedding-3-small
Dimensions: 1536
Max batch size: 100 texts per API call
"""
from openai import OpenAI
from src.helpers.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (each is a list of 1536 floats).

    Raises:
        Exception: If the OpenAI API call fails after retries.
    """
    if not texts:
        return []

    all_embeddings = []
    batch_size = 100  # OpenAI limit

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=batch,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )

        # Sort by index to maintain order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        batch_embeddings = [item.embedding for item in sorted_data]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings


def generate_single_embedding(text: str) -> list[float]:
    """
    Generate embedding for a single text.
    Convenience wrapper for queries.
    """
    result = generate_embeddings([text])
    return result[0]
```

---

### Service 4: Ingestion Orchestrator

**New file:** `src/services/ingestion_service.py`

This is the **main pipeline** that ties everything together:

```python
"""
Ingestion Service — Orchestrates the full document processing pipeline.

Pipeline: PDF → Extract Text → Extract Metadata → Chunk → Embed → Save

This is called after a document is uploaded (SPEC-02).
In v1, it runs synchronously. In SPEC-08, it runs via Celery.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.services.pdf_parser import extract_text_from_pdf, extract_metadata
from src.services.chunker import chunk_document
from src.services.embedding_service import generate_embeddings
from src.models.db_scheams.document import Document
from src.models.db_scheams.DocumeCnthunk import DocumentChunk
from src.helpers.logging_config import get_logger

logger = get_logger("ingestion")


async def process_document(document_id: str, db: AsyncSession) -> None:
    """
    Full ingestion pipeline for a single document.

    Steps:
        1. Load document record from DB
        2. Update status to "processing"
        3. Extract metadata from PDF
        4. Extract text from PDF
        5. Chunk the text
        6. Generate embeddings for all chunks
        7. Save chunks to DB
        8. Update status to "ready"

    On failure:
        - Status set to "failed"
        - Error message saved to document record
    """
    # 1. Load document
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    if not document:
        logger.error(f"Document {document_id} not found")
        return

    try:
        # 2. Update status
        document.status = "processing"
        await db.commit()

        logger.info(f"Processing document: {document.file_name} ({document_id})")

        # 3. Extract metadata
        metadata = extract_metadata(document.file_path)
        document.title = document.title or metadata.get("title")
        document.author = document.author or metadata.get("author")
        document.year = document.year or metadata.get("year")
        document.total_pages = metadata.get("total_pages")

        # 4. Extract text
        pages = extract_text_from_pdf(document.file_path)
        logger.info(f"Extracted text from {len(pages)} pages")

        # 5. Chunk
        chunks = chunk_document(pages)
        logger.info(f"Created {len(chunks)} chunks")

        if not chunks:
            document.status = "failed"
            document.error_message = "No usable text chunks could be extracted"
            await db.commit()
            return

        # 6. Generate embeddings
        texts = [c["content"] for c in chunks]
        embeddings = generate_embeddings(texts)
        logger.info(f"Generated {len(embeddings)} embeddings")

        # 7. Save chunks to DB
        for chunk_data, embedding in zip(chunks, embeddings):
            db_chunk = DocumentChunk(
                user_id=document.user_id,
                document_id=document.id,
                content=chunk_data["content"],
                page_number=chunk_data["page_number"],
                chunk_index=chunk_data["chunk_index"],
                embedding=embedding,
            )
            db.add(db_chunk)

        # 8. Mark as ready
        document.status = "ready"
        await db.commit()
        logger.info(f"Document {document_id} processed successfully: {len(chunks)} chunks")

    except ValueError as e:
        # Known errors (bad PDF, no text, etc.)
        document.status = "failed"
        document.error_message = str(e)
        await db.commit()
        logger.warning(f"Document {document_id} failed: {e}")

    except Exception as e:
        # Unexpected errors
        document.status = "failed"
        document.error_message = f"Unexpected error: {str(e)}"
        await db.commit()
        logger.exception(f"Document {document_id} failed with unexpected error")
        raise
```

---

## Integration with SPEC-02

After the upload endpoint saves the file, it calls the ingestion pipeline:

```python
# In document_controller.py upload method, after saving file and creating DB record:

from src.services.ingestion_service import process_document

# v1: Synchronous processing (simple, but blocks the request)
await process_document(str(document.id), db)

# v2 (SPEC-08): Async processing via Celery
# from src.tasks.ingestion import process_document_task
# process_document_task.delay(str(document.id))
```

---

## File Structure

### New Files to Create

| File | Purpose | Size |
|---|---|---|
| `src/services/__init__.py` | Make services a package | Empty |
| `src/services/pdf_parser.py` | PDF text & metadata extraction | ~80 lines |
| `src/services/chunker.py` | Text splitting into chunks | ~60 lines |
| `src/services/embedding_service.py` | OpenAI embedding generation | ~60 lines |
| `src/services/ingestion_service.py` | Pipeline orchestrator | ~100 lines |

### Files to Modify

| File | Change |
|---|---|
| `src/models/db_scheams/DocumeCnthunk.py` | Add `chunk_index` column |
| `src/helpers/config.py` | Add OpenAI and chunking settings |
| `requirements.txt` | Add PyMuPDF, langchain-text-splitters, openai |
| `.env` | Add `OPENAI_API_KEY` |

---

## Business Rules

1. **Minimum chunk size:** Chunks shorter than 50 characters are discarded (noise like headers, page numbers).
2. **Metadata priority:** If user manually set metadata (via SPEC-02 PATCH), it takes priority over auto-extracted metadata (note the `or` logic in `document.title = document.title or metadata.get("title")`).
3. **Embedding model:** Using OpenAI `text-embedding-3-small` with 1536 dimensions to match the existing `Vector(1536)` column definition.
4. **Batch size:** Embeddings are generated in batches of 100 to respect OpenAI API limits.
5. **Error handling:** If extraction fails, the document status is set to `"failed"` and the error message is stored. The user can see why it failed via `GET /documents/{id}`.
6. **Idempotency:** If re-processing is needed, old chunks should be deleted first (not implemented in v1 — handle in SPEC-08).

---

## Performance Expectations

| Metric | Target | Variables |
|---|---|---|
| 10-page PDF | ≤ 15 seconds | Text extraction + chunking + embedding |
| 50-page PDF | ≤ 60 seconds | Mostly embedding API latency |
| 200-page PDF | ≤ 4 minutes | Consider async processing (SPEC-08) |
| Embedding batch (100 chunks) | ≤ 5 seconds | OpenAI API response time |

---

## Test Scenarios

| # | Scenario | Expected Result |
|---|---|---|
| 1 | Process valid 10-page PDF | Status → "ready", chunks created with embeddings |
| 2 | Process PDF with no text (scanned) | Status → "failed", error_message set |
| 3 | Process PDF with only images | Status → "failed", error_message set |
| 4 | Process corrupted PDF file | Status → "failed", error_message set |
| 5 | Verify chunk count is reasonable | 10-page paper → ~20-40 chunks (depends on content density) |
| 6 | Verify chunks have page numbers | Each chunk has correct `page_number` |
| 7 | Verify chunks are ordered | `chunk_index` starts at 0 and increases |
| 8 | Verify embeddings are 1536-dim | Each embedding vector has 1536 floats |
| 9 | Verify metadata extraction | `title`, `author` populated from PDF metadata |
| 10 | Large PDF (200 pages) | Completes without timeout |
| 11 | Invalid OpenAI API key | Status → "failed", clear error message |

---

## Acceptance Criteria

- [ ] PDF text is extracted correctly page-by-page
- [ ] PDF metadata (title, author, year, pages) is extracted and saved to document record
- [ ] Text is chunked with 800-char size and 100-char overlap
- [ ] Tiny fragments (< 50 chars) are filtered out
- [ ] Each chunk has correct `page_number` and `chunk_index`
- [ ] Embeddings are generated using OpenAI text-embedding-3-small
- [ ] Embeddings are 1536-dimensional vectors
- [ ] Chunks are saved to `document_chunks` table with all fields populated
- [ ] Document status transitions: `processing` → `ready` on success
- [ ] Document status transitions: `processing` → `failed` on error
- [ ] Failed documents have a meaningful `error_message`
- [ ] Pipeline handles PDFs of varying sizes (1 page to 200+ pages)
- [ ] Logging captures key steps: pages extracted, chunks created, embeddings generated
