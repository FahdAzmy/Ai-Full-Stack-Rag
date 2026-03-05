# SPEC-03: Ingestion Pipeline

> **Status:** ✅ Complete  
> **Dependencies:** SPEC-02 (Document Upload) ✅  
> **Priority:** P0 — Critical Path  
> **Completed:** 2026-03-05

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

**File:** `src/models/db_scheams/DocumentChunk.py`

| Column | Type | Constraints | New? | Purpose |
|---|---|---|---|---|
| `id` | UUID | PK | ❌ | Primary key |
| `user_id` | UUID | FK → users.id | ❌ | Owner |
| `document_id` | UUID | FK → documents.id | ❌ | Parent document |
| `content` | Text | NOT NULL | ❌ | Chunk text content |
| `page_number` | Integer | nullable | ❌ | Source page number |
| `chunk_index` | Integer | NOT NULL, default=0 | ✅ | Order within document |
| `embedding` | Vector(1536) | nullable | ❌ | 1536-dim embedding |
| `created_at` | DateTime | default utcnow | ❌ | |

### Migration

```bash
alembic revision --autogenerate -m "add chunk_index to document_chunks"
alembic upgrade head
```

---

## Dependencies

**In `requirements.txt`:**

```
# PDF Processing
PyMuPDF==1.27.1

# Text Splitting
langchain-text-splitters==1.1.1

# OpenAI SDK (used via OpenRouter)
openai==2.24.0
```

---

## Config

**File:** `src/helpers/config.py` — Settings class includes:

```python
# OpenRouter (OpenAI-compatible API)
OPENROUTER_API_KEY: str = ""
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

# Embedding
EMBEDDING_MODEL: str = "openai/text-embedding-3-small"
EMBEDDING_DIMENSIONS: int = 1536

# PDF Safety Limits
MAX_PDF_PAGES: int = 1000
MAX_PDF_SIZE_MB: int = 20

# Chunking
CHUNK_SIZE: int = 800
CHUNK_OVERLAP: int = 120
MIN_CHUNK_LENGTH: int = 50
```

**File:** `.env` — includes:

```env
OPENROUTER_API_KEY=sk-or-your-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
EMBEDDING_MODEL=openai/text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
CHUNK_SIZE=800
CHUNK_OVERLAP=120
```

---

## Implemented Services

### Service 1: PDF Parser ✅

**File:** `src/services/pdf_parser.py`

Responsibilities:
- Extract text page-by-page from PDF using PyMuPDF
- Extract PDF metadata (title, author, creation date)
- Count total pages

Production hardening beyond spec:
- **Context manager** (`with fitz.open(...)`) for safe resource handling
- **File size protection** (`MAX_PDF_SIZE_MB` from settings)
- **Page limit protection** (`MAX_PDF_PAGES` from settings)
- **Error normalization** — all errors become `ValueError`
- **Helper functions** (`_validate_file_size`, `_open_pdf`) to reduce duplication

---

### Service 2: Text Chunker ✅

**File:** `src/services/chunker.py`

Responsibilities:
- Split extracted text into overlapping chunks using `RecursiveCharacterTextSplitter`
- Preserve page number for each chunk
- Add `[Page N]` prefix to each chunk for LLM context awareness
- Filter out tiny fragments (< `MIN_CHUNK_LENGTH` chars)

Production hardening beyond spec:
- **Safe dict access** (`page_data.get("text")` instead of `page_data["text"]`)
- **Text normalization** before splitting (collapse whitespace, normalize line breaks)
- **Semantic separators** (`\n\n`, `\n`, `. `, `? `, `! `, `; `, `: `, ` `)
- **Configurable limits** via settings (CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_LENGTH)

| Parameter | Value | Reason |
|---|---|---|
| `chunk_size` | 800 | ~200 tokens — fits well in LLM context alongside other chunks |
| `chunk_overlap` | 120 | Prevents losing context at chunk boundaries |
| `min_length` | 50 | Filters out noise like headers, page numbers |
| Separators | `\n\n` → `\n` → `. ` → `? ` → `! ` → ` ` | Prefers semantic breaks |

---

### Service 3: Embedding Generator ✅

**File:** `src/services/embedding_service.py`

Responsibilities:
- Generate embeddings via OpenRouter (OpenAI-compatible API)
- Batch processing (max 100 per API call)
- Error handling and retry logic

Architecture (SOLID refactored):
- **`EmbeddingService` class** — injectable via constructor (DIP)
- **Module-level facade functions** — backward-compatible entry points

Production hardening beyond spec:
- **Input sanitization** — removes None, empty strings, whitespace-only
- **Text normalization** — collapses whitespace for better embeddings
- **Text truncation** (`MAX_TEXT_LENGTH = 8000`) to prevent token limit errors
- **Retry with exponential backoff** — 3 attempts: 1s → 2s → 4s
- **Request timeout** — 30s on the OpenAI client
- **Empty response validation** — raises if API returns no data
- **Logging** — batch sizes, retry warnings, error details

---

### Service 4: Ingestion Orchestrator ✅

**File:** `src/services/ingestion_service.py`

This is the **main pipeline** that ties everything together.

Architecture (SOLID refactored):
- **`IngestionPipeline` class** — 10 focused sub-methods (SRP)
- **Dependency injection** — accepts custom parser/chunker/embedder (DIP)
- **Module-level `process_document()` facade** — backward-compatible entry point

Production hardening beyond spec:
- **Race condition guard** — only processes documents with `status == "uploading"`
- **File existence check** before processing
- **Async-safe embedding** — `asyncio.to_thread()` for blocking HTTP calls
- **Chunk limit** — `MAX_CHUNKS = 5000` protection
- **Bulk insert** — `db.add_all()` instead of individual `db.add()`
- **Proper rollback** — `await db.rollback()` before setting "failed" status
- **Structured logging** — `[doc=ID]` prefix on every log message
- **Atomic writes** — chunks + status in single commit

---

### Additional Files Created ✅

| File | Purpose |
|---|---|
| `src/services/protocols.py` | Protocol interfaces (DIP contracts) |
| `src/helpers/text_utils.py` | Shared text sanitization utilities |

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

### Files Created

| File | Purpose | Lines |
|---|---|---|
| `src/services/__init__.py` | Make services a package | Empty |
| `src/services/pdf_parser.py` | PDF text & metadata extraction | ~129 |
| `src/services/chunker.py` | Text splitting into chunks | ~94 |
| `src/services/embedding_service.py` | OpenAI embedding generation (class + facade) | ~177 |
| `src/services/ingestion_service.py` | Pipeline orchestrator (class + facade) | ~267 |
| `src/services/protocols.py` | Protocol interfaces (DIP) | ~73 |
| `src/helpers/text_utils.py` | Shared text sanitization | ~55 |

### Files Modified

| File | Change |
|---|---|
| `src/models/db_scheams/DocumentChunk.py` | Added `chunk_index` column |
| `src/helpers/config.py` | Added OpenRouter, embedding, chunking, PDF safety settings |
| `requirements.txt` | Added PyMuPDF, langchain-text-splitters, openai |
| `.env` | Added `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, embedding/chunking vars |

---

## Business Rules

1. **Minimum chunk size:** Chunks shorter than `MIN_CHUNK_LENGTH` (default 50) characters are discarded (noise like headers, page numbers).
2. **Page context:** Each chunk is prefixed with `[Page N]` for LLM context awareness.
3. **Metadata priority:** If user manually set metadata (via SPEC-02 PATCH), it takes priority over auto-extracted metadata (note the `or` logic in `document.title = document.title or metadata.get("title")`).
4. **Embedding model:** Using `openai/text-embedding-3-small` via OpenRouter with 1536 dimensions to match the existing `Vector(1536)` column definition.
5. **Batch size:** Embeddings are generated in batches of 100 to respect API limits.
6. **Error handling:** If extraction fails, the document status is set to `"failed"` and the error message is stored. The user can see why it failed via `GET /documents/{id}`.
7. **Race condition:** Only documents with `status == "uploading"` are processed. Prevents duplicate processing by multiple workers.
8. **Safety limits:** PDFs exceeding 1000 pages, 20 MB, or producing 5000+ chunks are rejected.
9. **Retry resilience:** Embedding API calls retry 3 times with exponential backoff (1s, 2s, 4s).

---

## Performance Expectations

| Metric | Target | Variables |
|---|---|---|
| 10-page PDF | ≤ 15 seconds | Text extraction + chunking + embedding |
| 50-page PDF | ≤ 60 seconds | Mostly embedding API latency |
| 200-page PDF | ≤ 4 minutes | Consider async processing (SPEC-08) |
| Embedding batch (100 chunks) | ≤ 5 seconds | OpenRouter API response time |

---

## Test Scenarios

| # | Scenario | Expected Result | Status |
|---|---|---|---|
| 1 | Process valid 10-page PDF | Status → "ready", chunks created with embeddings | ✅ |
| 2 | Process PDF with no text (scanned) | Status → "failed", error_message set | ✅ |
| 3 | Process PDF with only images | Status → "failed", error_message set | ✅ (covered by #2) |
| 4 | Process corrupted PDF file | Status → "failed", error_message set | ✅ |
| 5 | Verify chunk count is reasonable | 10-page paper → ~20-40 chunks | ✅ |
| 6 | Verify chunks have page numbers | Each chunk has correct `page_number` | ✅ |
| 7 | Verify chunks are ordered | `chunk_index` starts at 0 and increases | ✅ |
| 8 | Verify embeddings are 1536-dim | Each embedding vector has 1536 floats | ✅ |
| 9 | Verify metadata extraction | `title`, `author` populated from PDF metadata | ✅ |
| 10 | Large PDF (200 pages) | Completes without timeout | ✅ (safety limits enforced) |
| 11 | Invalid OpenRouter API key | Status → "failed", clear error message | ✅ |

Additional test scenarios implemented:
| # | Scenario | Status |
|---|---|---|
| 12 | Status transitions: uploading → processing → ready | ✅ |
| 13 | Status transitions: uploading → processing → failed | ✅ |
| 14 | Document not found → returns early | ✅ |
| 15 | User metadata takes priority over PDF metadata | ✅ |
| 16 | No usable chunks → status "failed" | ✅ |
| 17 | Chunks saved with all fields (user_id, doc_id, content, page, index, embedding) | ✅ |
| 18 | Embedding count mismatch → status "failed", no chunks saved | ✅ |
| 19 | Metadata extraction failure → status "failed" | ✅ |
| 20 | Chunk overlap is applied correctly | ✅ |

---

## Acceptance Criteria

- [x] PDF text is extracted correctly page-by-page
- [x] PDF metadata (title, author, year, pages) is extracted and saved to document record
- [x] Text is chunked with configurable size (800) and overlap (120)
- [x] Tiny fragments (< 50 chars) are filtered out
- [x] Each chunk has correct `page_number` and `chunk_index`
- [x] Embeddings are generated using openai/text-embedding-3-small via OpenRouter
- [x] Embeddings are 1536-dimensional vectors
- [x] Chunks are saved to `document_chunks` table with all fields populated
- [x] Document status transitions: `processing` → `ready` on success
- [x] Document status transitions: `processing` → `failed` on error
- [x] Failed documents have a meaningful `error_message`
- [x] Pipeline handles PDFs of varying sizes (1 page to 200+ pages)
- [x] Logging captures key steps: pages extracted, chunks created, embeddings generated
- [x] SOLID principles applied: SRP, OCP, DIP with Protocol interfaces
- [x] Production hardening: retry logic, timeouts, rollback, race condition guard
- [x] 42 tests passing (PDF parser + chunker + embedding + orchestrator + overlap)
