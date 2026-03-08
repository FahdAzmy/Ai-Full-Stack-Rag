"""
Retrieval Service — Semantic search over document chunks using pgvector.

Uses cosine distance (<=> operator) to find the most relevant chunks
for a given query. All queries are scoped to the authenticated user's
documents to ensure data isolation.
"""
import uuid as uuid_mod

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.services.embedding_service import generate_single_embedding
from src.helpers.logging_config import get_logger

logger = get_logger("retrieval")


def _validate_embedding(embedding: list) -> None:
    """Ensure embedding is a list of numbers (guard against injection)."""
    if not embedding or not isinstance(embedding, list):
        raise ValueError("Embedding must be a non-empty list of numbers.")
    if not all(isinstance(x, (int, float)) for x in embedding):
        raise ValueError("Embedding contains non-numeric values.")


def _validate_user_id(user_id: str) -> None:
    """Ensure user_id is a valid UUID string."""
    try:
        uuid_mod.UUID(user_id)
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid user_id format: {user_id}")


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
        ValueError: If query is not a string or user_id is not a valid UUID.
        Exception: If embedding generation or DB query fails.
    """
    # ── Input validation ─────────────────────────────────────────────────
    if not isinstance(query, str):
        raise ValueError("Query must be a string.")

    _validate_user_id(user_id)

    # 1. Generate query embedding
    query_preview = query[:80] if query else "(empty)"
    logger.info("Generating embedding for query: '%s...'", query_preview)
    query_embedding = generate_single_embedding(query)

    # 2. Validate & format embedding for pgvector
    _validate_embedding(query_embedding)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # 3. Build SQL query using CTE to compute cosine distance only once
    # NOTE: We use CAST(:embedding AS vector) instead of :embedding::vector
    # because asyncpg confuses the :: cast syntax with the bind parameter prefix.
    sql = """
        WITH scored AS (
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
                1 - (dc.embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE dc.user_id = :user_id
              AND d.status = 'ready'
    """

    params: dict = {
        "embedding": embedding_str,
        "user_id": user_id,
        "threshold": similarity_threshold,
        "top_k": top_k,
    }

    # Optional: filter by specific documents
    if document_ids:
        sql += " AND CAST(dc.document_id AS text) = ANY(:doc_ids)"
        params["doc_ids"] = document_ids

    sql += """
        )
        SELECT * FROM scored
        WHERE similarity >= :threshold
        ORDER BY similarity DESC
        LIMIT :top_k
    """

    # 4. Execute query
    result = await db.execute(text(sql), params)
    rows = result.mappings().all()

    logger.info("Retrieved %d chunks (threshold: %s)", len(rows), similarity_threshold)

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
