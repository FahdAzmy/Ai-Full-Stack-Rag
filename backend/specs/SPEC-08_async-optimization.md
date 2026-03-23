# SPEC-08: Async Processing & Optimization

> **Status:** ✅ Done  
> **Dependencies:** SPEC-03 (Ingestion Pipeline)  
> **Priority:** P1 — Performance  
> **Estimated effort:** 3–4 days  
> **Note:** Can be developed in parallel with SPEC-05 and SPEC-06

---

## Overview

In v1 (SPEC-02 + SPEC-03), the ingestion pipeline runs **synchronously** — meaning the upload endpoint blocks until the PDF is fully processed. This works for small files but becomes a problem with large PDFs (200+ pages) or multiple concurrent users.

This spec converts the ingestion pipeline to **async background processing** using Celery + Redis, adds a hybrid search strategy, and introduces performance optimizations.

```
BEFORE (Sync — v1):
  Upload Request → Process PDF → Embed → Save → Response (60+ seconds!)

AFTER (Async — this spec):
  Upload Request → Queue Task → Response (< 1 second!)
                        │
                        ▼ (background)
                   Celery Worker → Process PDF → Embed → Save
```

---

## Part 1: Celery + Redis Setup

### Docker Compose Update

**File:** `docker/docker-compose.yml`

Add Redis and Celery worker services:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: postgres_db
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

> **Note:** The Celery worker runs natively (not in Docker) during development for easier debugging. In production, it should be containerized.

---

### New Dependencies

**Add to `requirements.txt`:**

```
# Task Queue
celery[redis]==5.4.0
redis==5.2.1
```

---

### Config Additions

**File:** `src/helpers/config.py` — add:

```python
# Redis / Celery
REDIS_URL: str = "redis://localhost:6379/0"
CELERY_BROKER_URL: str = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
```

**File:** `.env` — add:

```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

---

### Celery App Configuration

**New file:** `src/tasks/__init__.py`

```python
"""
Celery app configuration.
"""

from celery import Celery
from src.helpers.config import settings

celery_app = Celery(
    "scholargpt",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task settings
    task_track_started=True,
    task_acks_late=True,          # Acknowledge after completion (safer)
    worker_prefetch_multiplier=1,  # One task at a time per worker

    # Retry settings
    task_default_retry_delay=30,   # Wait 30s before retry
    task_max_retries=3,

    # Result settings
    result_expires=3600,           # Results expire after 1 hour
)

# Auto-discover tasks in src/tasks/
celery_app.autodiscover_tasks(["src.tasks"])
```

---

### Ingestion Task

**New file:** `src/tasks/ingestion.py`

```python
"""
Background task: Process a document through the ingestion pipeline.

This wraps the sync ingestion_service in a Celery task so it runs
in a background worker process instead of blocking the API.
"""
import asyncio
from src.tasks import celery_app
from src.helpers.db import AsyncSessionLocal
from src.helpers.logging_config import get_logger

logger = get_logger("celery.ingestion")


def _run_async(coro):
    """Run async code inside a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    name="tasks.process_document",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def process_document_task(self, document_id: str):
    """
    Celery task to process a document.

    Args:
        document_id: UUID of the document to process.

    Retries:
        Up to 3 times with 30-second delays on failure.
    """
    logger.info(f"[Task {self.request.id}] Starting document processing: {document_id}")

    try:
        _run_async(_process(document_id))
        logger.info(f"[Task {self.request.id}] Document {document_id} processed successfully")

    except Exception as exc:
        logger.error(f"[Task {self.request.id}] Failed: {str(exc)}")
        # Mark as failed in DB before retrying
        _run_async(_mark_failed(document_id, str(exc)))
        raise self.retry(exc=exc)


async def _process(document_id: str):
    """Run the ingestion pipeline with a fresh DB session."""
    from src.services.ingestion_service import process_document

    async with AsyncSessionLocal() as db:
        await process_document(document_id, db)


async def _mark_failed(document_id: str, error: str):
    """Mark a document as failed in the database."""
    from sqlalchemy import select, update
    from src.models.db_scheams.document import Document

    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(status="failed", error_message=error)
        )
        await db.commit()
```

---

### Update Upload Endpoint

**File:** `src/controllers/document_controller.py`

Change the upload method from sync to async processing:

```python
# BEFORE (v1 — synchronous):
from src.services.ingestion_service import process_document
await process_document(str(document.id), db)

# AFTER (this spec — async):
from src.tasks.ingestion import process_document_task
process_document_task.delay(str(document.id))
```

The upload endpoint now returns **immediately** with status `"processing"`, and the actual work happens in the Celery worker.

---

### Running the Celery Worker

**Development command:**

```bash
# Terminal 1: Start Redis (via Docker)
docker-compose -f docker/docker-compose.yml up redis -d

# Terminal 2: Start Celery worker
cd backend
source venv/bin/activate   # or venv\Scripts\activate on Windows
celery -A src.tasks worker --loglevel=info --concurrency=2
```

**Monitoring tasks:**

```bash
# Watch tasks in real-time
celery -A src.tasks events

# Check active tasks
celery -A src.tasks inspect active

# Check registered tasks
celery -A src.tasks inspect registered
```

---

## Part 2: Document Status Polling

Since processing now happens in the background, the frontend needs to know when a document is ready.

### Status Endpoint (already defined in SPEC-02)

`GET /documents/{id}` returns the current status. The frontend polls this endpoint.

### Polling Strategy (Frontend)

```typescript
// In DocumentSidebar.tsx
useEffect(() => {
  const hasProcessing = documents.some(d => d.status === "processing");

  if (hasProcessing) {
    const interval = setInterval(() => {
      dispatch(fetchDocuments());  // Re-fetch document list
    }, 5000);  // Poll every 5 seconds

    return () => clearInterval(interval);
  }
}, [documents]);
```

### Future Enhancement: WebSocket (not in this spec)

For a more efficient approach, consider WebSocket notifications:
```python
# Future: Send WebSocket message when document is ready
await websocket_manager.send_to_user(
    user_id, {"type": "document_ready", "document_id": str(doc.id)}
)
```

---

## Part 3: Hybrid Search

Combine vector similarity search with keyword search for better retrieval.

### Add Full-Text Search Column

**Migration:**

```sql
-- Add tsvector column (auto-generated from content)
ALTER TABLE document_chunks
ADD COLUMN content_tsv tsvector
GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;

-- Create GIN index for fast full-text search
CREATE INDEX idx_chunks_content_tsv
ON document_chunks
USING gin(content_tsv);
```

### Update Retrieval Service

**File:** `src/services/retrieval_service.py` — add hybrid search:

```python
async def hybrid_search(
    query: str,
    user_id: str,
    db: AsyncSession,
    top_k: int = 5,
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3,
    document_ids: list[str] | None = None,
) -> list[dict]:
    """
    Hybrid search combining vector similarity and keyword matching.

    Ranking formula:
      combined_score = (vector_weight × cosine_similarity) + (keyword_weight × keyword_rank)

    Args:
        vector_weight: Weight for semantic similarity (default 0.7)
        keyword_weight: Weight for keyword relevance (default 0.3)
    """
    query_embedding = generate_single_embedding(query)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    sql = text("""
        SELECT
            dc.id AS chunk_id,
            dc.content,
            dc.page_number,
            dc.chunk_index,
            dc.document_id,
            d.file_name, d.title, d.author, d.year, d.journal, d.doi,
            1 - (dc.embedding <=> :embedding::vector) AS vector_score,
            COALESCE(ts_rank(dc.content_tsv, plainto_tsquery('english', :query_text)), 0) AS keyword_score,
            (
                :vector_weight * (1 - (dc.embedding <=> :embedding::vector)) +
                :keyword_weight * COALESCE(ts_rank(dc.content_tsv, plainto_tsquery('english', :query_text)), 0)
            ) AS combined_score
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE dc.user_id = :user_id
          AND d.status = 'ready'
        ORDER BY combined_score DESC
        LIMIT :top_k
    """)

    result = await db.execute(sql, {
        "embedding": embedding_str,
        "query_text": query,
        "user_id": user_id,
        "vector_weight": vector_weight,
        "keyword_weight": keyword_weight,
        "top_k": top_k,
    })

    # ... format results same as before
```

**When to use which strategy:**

| Strategy | When to use | Strengths |
|---|---|---|
| Vector only (SPEC-04) | Default, semantic understanding | Catches paraphrases, synonyms |
| Hybrid (this spec) | Queries with specific terms | Better for exact matches, names, acronyms |

---

## Part 4: Database Indexing

### pgvector Index

```sql
-- IVFFlat index for approximate nearest neighbor
-- Create AFTER you have data (needs ~1000+ rows for good performance)
CREATE INDEX idx_chunks_embedding_ivfflat
ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

| Data size | Index type | Notes |
|---|---|---|
| < 10K chunks | None needed | Exact search is fast enough |
| 10K – 1M chunks | IVFFlat | Good balance of speed and accuracy |
| > 1M chunks | HNSW | Best accuracy but more memory |

### Standard Indexes

```sql
-- Speed up user-scoped queries
CREATE INDEX idx_chunks_user ON document_chunks(user_id);
CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_documents_user ON documents(user_id);
CREATE INDEX idx_messages_chat ON messages(chat_id);
CREATE INDEX idx_chats_user ON chats(user_id);
```

---

## File Structure

### New Files to Create

| File | Purpose |
|---|---|
| `src/tasks/__init__.py` | Celery app configuration |
| `src/tasks/ingestion.py` | Background ingestion task |

### Files to Modify

| File | Change |
|---|---|
| `docker/docker-compose.yml` | Add Redis service |
| `src/helpers/config.py` | Add Redis/Celery settings |
| `src/controllers/document_controller.py` | Switch from sync to async processing |
| `src/services/retrieval_service.py` | Add hybrid search function |
| `requirements.txt` | Add celery, redis |
| `.env` | Add `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` |

---

## Business Rules

1. **Celery retry policy:** Failed tasks retry up to 3 times with 30-second delays. After max retries, the document stays in `"failed"` status.
2. **One task per document:** Don't allow re-processing a document that's already `"processing"`. Check status before queuing.
3. **Worker concurrency:** Default 2 concurrent tasks per worker to avoid overloading the embedding API.
4. **Hybrid search weights:** 70% semantic (vector) + 30% keyword. These are tunable.
5. **Index creation timing:** pgvector IVFFlat index should only be created after sufficient data exists (~1000+ chunks).

---

## Test Scenarios

| # | Scenario | Expected Result |
|---|---|---|
| 1 | Upload returns immediately | Response in < 1 second, status "processing" |
| 2 | Celery processes the document | Status changes to "ready" after processing |
| 3 | Celery handles failure | Status "failed", error_message set, retries exhausted |
| 4 | Celery retries on transient error | Retry up to 3 times |
| 5 | Redis connection lost | Graceful error, tasks queued when Redis returns |
| 6 | Multiple concurrent uploads | All queued and processed in order |
| 7 | Hybrid search finds keyword matches | Results include keyword-relevant chunks |
| 8 | Hybrid search with rare term | Better results than vector-only search |
| 9 | Database indexes speed up queries | Measured query time improvement |

---

## Acceptance Criteria

- [ ] Redis container runs via Docker Compose
- [ ] Celery worker starts and connects to Redis
- [ ] Upload endpoint returns immediately (< 1 second)
- [ ] Documents are processed in the background by Celery
- [ ] Failed tasks retry up to 3 times
- [ ] Permanently failed documents show error message
- [ ] Frontend polling detects when documents become "ready"
- [ ] Hybrid search combines vector + keyword results
- [ ] Full-text search index (GIN) is created on document_chunks
- [ ] Standard indexes are created for common query patterns
- [ ] Worker concurrency is configurable
- [ ] Celery task logs are captured with request IDs
