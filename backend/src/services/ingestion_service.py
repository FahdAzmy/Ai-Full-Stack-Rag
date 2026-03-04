"""
Ingestion Service — Production-grade document ingestion pipeline.

Pipeline: fetch document → validate → extract metadata → extract text →
          chunk text → generate embeddings (batched, async) → store chunks → update status

Status transitions:
  uploading → processing → ready   (success)
  uploading → processing → failed  (error)

Safety features:
  - Race condition guard (only processes documents in "uploading" state)
  - File existence check before processing
  - Async-safe embedding generation via asyncio.to_thread
  - Batched embedding calls for memory efficiency
  - Chunk limit protection (MAX_CHUNKS = 5000)
  - Bulk chunk insertion via db.add_all
  - Proper rollback on failure
  - Structured logging with document ID
"""

import os
import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_scheams.document import Document
from src.models.db_scheams.DocumentChunk import DocumentChunk
from src.services.pdf_parser import extract_text_from_pdf, extract_metadata
from src.services.chunker import chunk_document
from src.services.embedding_service import generate_embeddings

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
EMBEDDING_BATCH_SIZE = 64
MAX_CHUNKS = 5000


async def process_document(document_id: str, db: AsyncSession) -> None:
    """
    Process a document through the full ingestion pipeline.

    Args:
        document_id: UUID string of the document to process.
        db: Async database session.
    """
    # ── 1. Fetch document from DB ────────────────────────────────────────
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if document is None:
        logger.warning("[doc=%s] Not found, skipping ingestion.", document_id)
        return

    # ── 2. Race condition guard ──────────────────────────────────────────
    if document.status != "uploading":
        logger.warning(
            "[doc=%s] Status is '%s', expected 'uploading'. Skipping.",
            document_id,
            document.status,
        )
        return

    # ── 3. Set status to "processing" (visible immediately) ──────────────
    document.status = "processing"
    await db.commit()
    logger.info("[doc=%s] Processing started.", document_id)

    try:
        file_path = document.file_path

        # ── 4. Verify file exists ────────────────────────────────────────
        if not os.path.exists(file_path):
            raise ValueError(f"Document file not found: {file_path}")

        # ── 5. Extract metadata ──────────────────────────────────────────
        logger.info("[doc=%s] Extracting metadata.", document_id)
        metadata = extract_metadata(file_path)

        # User-set values take priority over auto-extracted
        document.title = document.title or metadata.get("title")
        document.author = document.author or metadata.get("author")
        document.year = document.year or metadata.get("year")
        document.total_pages = metadata.get("total_pages")

        # ── 6. Extract text from PDF ─────────────────────────────────────
        logger.info("[doc=%s] Extracting text.", document_id)
        pages = extract_text_from_pdf(file_path)

        # ── 7. Chunk the text ────────────────────────────────────────────
        logger.info("[doc=%s] Chunking text.", document_id)
        chunks = chunk_document(pages)

        if not chunks:
            raise ValueError("No usable text chunks generated from the document.")

        # ── 8. Enforce chunk limit for large document protection ─────────
        if len(chunks) > MAX_CHUNKS:
            raise ValueError(
                f"Document too large: {len(chunks)} chunks exceeds "
                f"limit of {MAX_CHUNKS}."
            )

        logger.info("[doc=%s] Generated %d chunks.", document_id, len(chunks))

        # ── 9. Generate embeddings in batches (async-safe) ───────────────
        all_embeddings: list[list[float]] = []
        total_batches = -(-len(chunks) // EMBEDDING_BATCH_SIZE)  # ceil div

        for i in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
            batch_chunks = chunks[i : i + EMBEDDING_BATCH_SIZE]
            batch_texts = [c["content"] for c in batch_chunks]
            batch_num = (i // EMBEDDING_BATCH_SIZE) + 1

            logger.info(
                "[doc=%s] Embedding batch %d/%d (%d texts).",
                document_id,
                batch_num,
                total_batches,
                len(batch_texts),
            )
            # Offload blocking HTTP call to thread pool
            batch_embeddings = await asyncio.to_thread(generate_embeddings, batch_texts)
            all_embeddings.extend(batch_embeddings)

        # ── 10. Validate embedding count ─────────────────────────────────
        if len(all_embeddings) != len(chunks):
            raise ValueError(
                f"Embedding count mismatch: got {len(all_embeddings)} embeddings "
                f"for {len(chunks)} chunks."
            )

        # ── 11. Build chunk objects for bulk insert ──────────────────────
        logger.info("[doc=%s] Saving %d chunks.", document_id, len(chunks))
        chunk_objects = [
            DocumentChunk(
                user_id=document.user_id,
                document_id=document.id,
                content=chunk_data["content"],
                page_number=chunk_data["page_number"],
                chunk_index=chunk_data["chunk_index"],
                embedding=embedding,
            )
            for chunk_data, embedding in zip(chunks, all_embeddings)
        ]

        # ── 12. Atomic write: chunks + status in single commit ───────────
        db.add_all(chunk_objects)
        document.status = "ready"
        document.error_message = None
        await db.commit()

        logger.info("[doc=%s] Completed: %d chunks created.", document_id, len(chunks))

    except ValueError as e:
        # Known errors (no text, no chunks, mismatch, file missing, etc.)
        logger.error("[doc=%s] Processing failed: %s", document_id, str(e))
        await db.rollback()
        document.status = "failed"
        document.error_message = str(e)
        await db.commit()

    except Exception as e:
        # Unexpected errors (API failures, DB issues, etc.)
        logger.error(
            "[doc=%s] Unexpected error: %s", document_id, str(e), exc_info=True
        )
        await db.rollback()
        document.status = "failed"
        document.error_message = f"Unexpected error: {str(e)}"
        await db.commit()
        raise
