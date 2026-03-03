# SPEC-04: Retrieval Layer

> **Status:** 🔲 Todo  
> **Dependencies:** SPEC-03 (Ingestion Pipeline)  
> **Priority:** P0 — Critical Path  
> **Estimated effort:** 2–3 days

---

## Overview

The Retrieval Layer is the heart of the RAG (Retrieval-Augmented Generation) system. When a user asks a question, this layer:

1. Converts the question into an embedding vector
2. Searches pgvector for the most similar document chunks
3. Builds a structured prompt with retrieved context + conversation history

This layer sits **between** the user's question and the LLM (SPEC-05). It does NOT call the LLM itself — it prepares the input for it.

```
User Question → [RETRIEVAL LAYER] → Structured Prompt → (to SPEC-05 LLM)
                   │
                   ├── Query Embedding
                   ├── Similarity Search (pgvector)
                   └── Context Builder (prompt assembly)
```

---

## Services to Create

### Service 1: Retrieval Service

**New file:** `src/services/retrieval_service.py`

Responsibilities:
- Convert user question to embedding vector
- Query pgvector for most similar chunks
- Filter by user_id (data isolation) and optionally by document_ids
- Return ranked results with metadata

```python
"""
Retrieval Service — Semantic search over document chunks using pgvector.

Uses cosine distance (<=> operator) to find the most relevant chunks
for a given query. All queries are scoped to the authenticated user's
documents to ensure data isolation.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.services.embedding_service import generate_single_embedding
from src.helpers.logging_config import get_logger

logger = get_logger("retrieval")


async def search_similar_chunks(
    query: str,
    user_id: str,
    db: AsyncSession,
    top_k: int = 5,
    similarity_threshold: float = 0.3,
    document_ids: list[str] | None = None,
) -> list[dict]:
    """
    Find the most relevant document chunks for a given query.

    Args:
        query: The user's question text.
        user_id: UUID of the authenticated user (for data isolation).
        db: Async database session.
        top_k: Maximum number of results to return (default: 5).
        similarity_threshold: Minimum cosine similarity score (default: 0.3).
        document_ids: Optional list of document UUIDs to search within.
                     If None, searches all user's documents.

    Returns:
        List of dicts, each containing:
        - chunk_id: UUID of the chunk
        - content: The chunk text
        - page_number: Source page in the PDF
        - chunk_index: Order within document
        - document_id: UUID of parent document
        - file_name: Original filename
        - title: Paper title
        - author: Paper author(s)
        - year: Publication year
        - journal: Journal name
        - doi: DOI if available
        - similarity: Cosine similarity score (0.0 to 1.0)

    Raises:
        Exception: If embedding generation or DB query fails.
    """
    # 1. Generate query embedding
    logger.info(f"Generating embedding for query: '{query[:80]}...'")
    query_embedding = generate_single_embedding(query)

    # 2. Format embedding for pgvector
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # 3. Build SQL query
    sql = """
        SELECT
            dc.id AS chunk_id,
            dc.content,
            dc.page_number,
            dc.chunk_index,
            dc.document_id,
            d.file_name,
            d.title,
            d.author,
            d.year,
            d.journal,
            d.doi,
            1 - (dc.embedding <=> :embedding::vector) AS similarity
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE dc.user_id = :user_id
          AND d.status = 'ready'
          AND 1 - (dc.embedding <=> :embedding::vector) >= :threshold
    """

    params = {
        "embedding": embedding_str,
        "user_id": user_id,
        "threshold": similarity_threshold,
        "top_k": top_k,
    }

    # Optional: filter by specific documents
    if document_ids:
        sql += " AND dc.document_id::text = ANY(:doc_ids)"
        params["doc_ids"] = document_ids

    sql += """
        ORDER BY dc.embedding <=> :embedding::vector ASC
        LIMIT :top_k
    """

    # 4. Execute query
    result = await db.execute(text(sql), params)
    rows = result.mappings().all()

    logger.info(f"Retrieved {len(rows)} chunks (threshold: {similarity_threshold})")

    # 5. Format results
    return [
        {
            "chunk_id": str(row["chunk_id"]),
            "content": row["content"],
            "page_number": row["page_number"],
            "chunk_index": row["chunk_index"],
            "document_id": str(row["document_id"]),
            "file_name": row["file_name"],
            "title": row["title"],
            "author": row["author"],
            "year": row["year"],
            "journal": row["journal"],
            "doi": row["doi"],
            "similarity": round(float(row["similarity"]), 4),
        }
        for row in rows
    ]
```

**Key design decisions:**

| Decision | Rationale |
|---|---|
| `top_k = 5` | Balance between context coverage and prompt length |
| `similarity_threshold = 0.3` | Filters out irrelevant results; cosine similarity < 0.3 is usually noise |
| `d.status = 'ready'` | Only searches fully processed documents |
| Cosine distance `<=>` | pgvector's cosine distance operator; we convert to similarity via `1 - distance` |
| User filter always applied | Critical for data isolation — never return another user's chunks |

---

### Service 2: Context Builder

**New file:** `src/services/context_builder.py`

Responsibilities:
- Assemble the LLM prompt from retrieved chunks + conversation history
- Create source labels for each chunk
- Include system instructions specific to ScholarGPT's academic role

```python
"""
Context Builder — Assemble the LLM prompt from retrieved chunks.

Builds an OpenAI-compatible message list:
  [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "..."},       # history
      {"role": "assistant", "content": "..."},   # history
      {"role": "user", "content": "..."},        # current question
  ]
"""

SYSTEM_PROMPT_TEMPLATE = """You are ScholarGPT, an expert academic research assistant.
You help researchers and students find information in their uploaded research papers.

## YOUR RULES:
1. Answer ONLY based on the provided research context below. 
2. If the context does not contain enough information to answer, say:
   "I could not find enough information in your uploaded papers to answer this question."
3. ALWAYS cite which source you used by writing [Source N] in your answer.
4. Be precise, academic, and thorough in your responses.
5. Use clear formatting: bullet points, numbered lists, and headers when appropriate.
6. At the end of your answer, list all sources you referenced under "## References Used".

## RESEARCH CONTEXT FROM USER'S PAPERS:
{context}

## IMPORTANT:
- Do NOT make up information that is not in the context.
- Do NOT use your general knowledge — only the provided sources.
- If multiple sources discuss the same topic, synthesize them and cite all.
"""


def build_prompt(
    question: str,
    retrieved_chunks: list[dict],
    conversation_history: list[dict] | None = None,
    max_history_messages: int = 10,
) -> list[dict]:
    """
    Build a structured LLM prompt.

    Args:
        question: The user's current question.
        retrieved_chunks: Results from retrieval_service.search_similar_chunks().
        conversation_history: Previous messages in the chat.
            [{"role": "user"|"assistant", "content": "..."}, ...]
        max_history_messages: Max number of history messages to include.

    Returns:
        OpenAI-compatible message list ready for LLM.
    """
    # Build context string from retrieved chunks
    context = _build_context_string(retrieved_chunks)

    # System message
    system_content = SYSTEM_PROMPT_TEMPLATE.format(context=context)
    messages = [{"role": "system", "content": system_content}]

    # Add conversation history (limited)
    if conversation_history:
        recent = conversation_history[-max_history_messages:]
        for msg in recent:
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })

    # Add current question
    messages.append({"role": "user", "content": question})

    return messages


def _build_context_string(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a numbered context string.

    Example output:
    ---
    [Source 1] "Deep Learning in Medicine" by Smith, John (2020) — Page 15
    Content:
    Convolutional neural networks have shown remarkable performance...
    ---
    """
    if not chunks:
        return "(No relevant context found in uploaded papers.)"

    parts = []
    for i, chunk in enumerate(chunks, 1):
        # Build source label
        title = chunk.get("title") or chunk.get("file_name", "Unknown document")
        author = chunk.get("author") or "Unknown author"
        year = chunk.get("year") or "n.d."
        page = chunk.get("page_number", "?")
        similarity = chunk.get("similarity", 0)

        source_label = f'[Source {i}] "{title}" by {author} ({year}) — Page {page}'
        source_label += f" [relevance: {similarity:.0%}]"

        part = f"""---
{source_label}
Content:
{chunk['content']}"""
        parts.append(part)

    return "\n".join(parts) + "\n---"


def get_source_summary(chunks: list[dict]) -> list[dict]:
    """
    Create a concise summary of sources used, for the API response.

    Returns:
        [
            {
                "source_number": 1,
                "title": "Deep Learning in Medicine",
                "author": "Smith, John",
                "year": "2020",
                "page_number": 15,
                "file_name": "deep_learning.pdf",
                "document_id": "a1b2c3d4-...",
                "chunk_id": "e5f6g7h8-...",
                "similarity": 0.87,
                "excerpt": "Convolutional neural networks have shown..."
            },
            ...
        ]
    """
    summaries = []
    for i, chunk in enumerate(chunks, 1):
        summaries.append({
            "source_number": i,
            "title": chunk.get("title") or chunk.get("file_name"),
            "author": chunk.get("author"),
            "year": chunk.get("year"),
            "page_number": chunk.get("page_number"),
            "file_name": chunk.get("file_name"),
            "document_id": chunk.get("document_id"),
            "chunk_id": chunk.get("chunk_id"),
            "similarity": chunk.get("similarity"),
            "excerpt": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
        })
    return summaries
```

---

## Database Index (Performance)

Create a pgvector index for faster similarity search:

```sql
-- Add IVFFlat index for approximate nearest neighbor search
-- Do this AFTER you have some data (needs rows to build the index)
CREATE INDEX idx_chunks_embedding
ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**When to create this index:**
- After you have at least ~1000 chunks in the database
- IVFFlat needs data to build internal cluster lists
- Without this index, pgvector does exact search (slower but fine for < 10K chunks)

**Migration file for the index:**
```bash
alembic revision -m "add ivfflat index on document_chunks embedding"
```

---

## File Structure

### New Files to Create

| File | Purpose | Size |
|---|---|---|
| `src/services/retrieval_service.py` | Semantic search via pgvector | ~100 lines |
| `src/services/context_builder.py` | LLM prompt assembly | ~120 lines |

### No Files to Modify

This spec only creates new service files. No modifications to existing files needed.

---

## Business Rules

1. **Data isolation:** All searches are scoped to the authenticated user's documents via `WHERE dc.user_id = :user_id`. This is **non-negotiable**.
2. **Only search ready documents:** The `WHERE d.status = 'ready'` filter ensures we never search incomplete documents.
3. **Similarity threshold:** Results below 0.3 cosine similarity are discarded (too irrelevant to be useful).
4. **Document filtering:** Users can optionally filter by `document_ids` to search only specific papers.
5. **Source attribution:** Every chunk returned includes full metadata (title, author, year, page) for citation generation (SPEC-06).
6. **Context length management:** Max 5 chunks × ~800 chars = ~4000 chars of context, well within LLM limits.
7. **History limit:** Max 10 previous messages to avoid exceeding LLM context window.

---

## Test Scenarios

| # | Scenario | Expected Result |
|---|---|---|
| 1 | Search with relevant query | Returns chunks with similarity > 0.3, sorted by relevance |
| 2 | Search with irrelevant query | Returns empty or fewer results (below threshold) |
| 3 | Search with document_ids filter | Only returns chunks from specified documents |
| 4 | Search when user has no documents | Returns empty results gracefully |
| 5 | Search only returns "ready" documents | Processing/failed documents are excluded |
| 6 | User A cannot see User B's chunks | user_id filter enforced |
| 7 | Context builder with 5 chunks | Produces well-formatted prompt with numbered sources |
| 8 | Context builder with 0 chunks | Includes "(No relevant context found)" message |
| 9 | Context builder with history | History messages included in correct order |
| 10 | Context builder history limit | Only last 10 messages included |

---

## Acceptance Criteria

- [ ] User question is converted to a 1536-dim embedding
- [ ] pgvector cosine similarity search returns ranked results
- [ ] Results are filtered by `user_id` (data isolation)
- [ ] Results only include `status = 'ready'` documents
- [ ] Results below similarity threshold (0.3) are excluded
- [ ] Optional document_ids filtering works
- [ ] Each result includes full metadata (title, author, year, page, file_name)
- [ ] Context builder produces valid OpenAI-compatible message list
- [ ] System prompt includes numbered source labels
- [ ] Conversation history is included (limited to last 10 messages)
- [ ] Source summary function provides concise source metadata for API response
- [ ] Logging captures query details and result count
