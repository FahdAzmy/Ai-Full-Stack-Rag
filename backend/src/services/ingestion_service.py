"""
Ingestion Service — Production-grade document ingestion pipeline.

Architecture:
  - IngestionPipeline class: orchestrates processing with sub-methods (SRP)
  - Supports dependency injection for PDF parser, chunker, embedder (DIP)
  - Module-level process_document() facade for backward compatibility

Pipeline: fetch → validate → extract metadata → extract text →
          chunk → embed (async) → store → update status

Status transitions:
  uploading → processing → ready   (success)
  uploading → processing → failed  (error)

Safety features:
  - Race condition guard (only processes "uploading" documents)
  - File existence check before processing
  - Async-safe embedding via asyncio.to_thread
  - Chunk limit protection (MAX_CHUNKS)
  - Bulk insertion via db.add_all
  - Proper rollback on failure
  - Structured logging with document ID
"""

import os
import asyncio
import logging
import tempfile
from typing import Callable
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_scheams.document import Document
from src.models.db_scheams.DocumentChunk import DocumentChunk
from src.services.pdf_parser import extract_text_from_pdf, extract_metadata
from src.services.chunker import chunk_document
from src.services.embedding_service import generate_embeddings
from src.helpers import storage

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
MAX_CHUNKS = 5000


class IngestionPipeline:
    """
    Orchestrates the document ingestion pipeline with clear sub-methods.

    Each pipeline step is a separate method (SRP), and dependencies
    can be injected for testing or swapping implementations (DIP).

    Args:
        document_id: UUID string of the document to process.
        db: Async database session.
        metadata_extractor: Callable to extract PDF metadata (default: extract_metadata).
        text_extractor: Callable to extract PDF text (default: extract_text_from_pdf).
        chunker: Callable to chunk text pages (default: chunk_document).
        embedder: Callable to generate embeddings (default: generate_embeddings).
    """

    def __init__(
        self,
        document_id: str,
        db: AsyncSession,
        *,
        metadata_extractor: Callable | None = None,
        text_extractor: Callable | None = None,
        chunker: Callable | None = None,
        embedder: Callable | None = None,
    ):
        self._document_id = document_id
        self._db = db
        self._document: Document | None = None

        # DI with defaults from module-level imports
        self._extract_metadata = metadata_extractor or extract_metadata
        self._extract_text = text_extractor or extract_text_from_pdf
        self._chunk = chunker or chunk_document
        self._embed = embedder or generate_embeddings

    # ── Pipeline Entry Point ─────────────────────────────────────────────

    async def run(self) -> None:
        """Execute the full ingestion pipeline."""
        if not await self._fetch_document():
            return

        if not self._can_process():
            return

        await self._set_status("processing")
        logger.info("[doc=%s] Processing started.", self._document_id)

        try:
            await self._process()
        except ValueError as e:
            await self._handle_failure(str(e))
        except Exception as e:
            await self._handle_failure(f"Unexpected error: {str(e)}")
            raise

    # ── Step 1: Fetch Document ───────────────────────────────────────────

    async def _fetch_document(self) -> bool:
        """Fetch the document from DB. Returns False if not found."""
        result = await self._db.execute(
            select(Document).where(Document.id == self._document_id)
        )
        self._document = result.scalar_one_or_none()

        if self._document is None:
            logger.warning("[doc=%s] Not found, skipping ingestion.", self._document_id)
            return False
        return True

    # ── Step 2: Race Condition Guard ─────────────────────────────────────

    def _can_process(self) -> bool:
        """Check if the document is in a processable state."""
        if self._document.status != "uploading":
            logger.warning(
                "[doc=%s] Status is '%s', expected 'uploading'. Skipping.",
                self._document_id,
                self._document.status,
            )
            return False
        return True

    # ── Step 3–12: Core Processing ───────────────────────────────────────

    async def _process(self) -> None:
        """Execute the core extraction → chunk → embed → save pipeline.

        Downloads the PDF from Supabase Storage to a temp file,
        processes it, then cleans up the temp file.
        """
        storage_path = self._document.file_path

        # Download PDF from Supabase to a temporary local file
        logger.info(
            "[doc=%s] Downloading from storage: %s", self._document_id, storage_path
        )
        try:
            pdf_bytes = await asyncio.to_thread(storage.download, storage_path)
        except Exception as e:
            raise ValueError(f"Failed to download document from storage: {str(e)}")

        # Write to temp file for PyMuPDF processing
        tmp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        try:
            tmp_file.write(pdf_bytes)
            tmp_file.close()
            local_path = tmp_file.name

            # Extract metadata (user-set values take priority)
            logger.info("[doc=%s] Extracting metadata.", self._document_id)
            metadata = self._extract_metadata(local_path)
            self._apply_metadata(metadata)

            # Extract text from PDF
            logger.info("[doc=%s] Extracting text.", self._document_id)
            pages = self._extract_text(local_path)

            # Chunk the text
            logger.info("[doc=%s] Chunking text.", self._document_id)
            chunks = self._chunk(pages)
            self._validate_chunks(chunks)

            # Generate embeddings (async-safe, batching handled by embedding service)
            logger.info(
                "[doc=%s] Generating embeddings for %d chunks.",
                self._document_id,
                len(chunks),
            )
            texts = [c["content"] for c in chunks]
            embeddings = await asyncio.to_thread(self._embed, texts)
            self._validate_embeddings(chunks, embeddings)

            # Save chunks + mark ready in single atomic commit
            await self._save_chunks(chunks, embeddings)
            await self._set_ready()

        finally:
            # Always clean up the temp file
            if os.path.exists(tmp_file.name):
                os.unlink(tmp_file.name)
                logger.info("[doc=%s] Temp file cleaned up.", self._document_id)

    # ── Metadata Helpers ─────────────────────────────────────────────────

    def _apply_metadata(self, metadata: dict) -> None:
        """Apply extracted metadata, preserving user-set values."""
        self._document.title = self._document.title or metadata.get("title")
        self._document.author = self._document.author or metadata.get("author")
        self._document.year = self._document.year or metadata.get("year")
        self._document.total_pages = metadata.get("total_pages")

    # ── Validation Helpers ───────────────────────────────────────────────

    def _validate_chunks(self, chunks: list[dict]) -> None:
        """Ensure chunks are non-empty and within limits."""
        if not chunks:
            raise ValueError("No usable text chunks generated from the document.")
        if len(chunks) > MAX_CHUNKS:
            raise ValueError(
                f"Document too large: {len(chunks)} chunks exceeds "
                f"limit of {MAX_CHUNKS}."
            )
        logger.info("[doc=%s] Generated %d chunks.", self._document_id, len(chunks))

    def _validate_embeddings(
        self, chunks: list[dict], embeddings: list[list[float]]
    ) -> None:
        """Ensure embedding count matches chunk count."""
        if len(embeddings) != len(chunks):
            raise ValueError(
                f"Embedding count mismatch: got {len(embeddings)} embeddings "
                f"for {len(chunks)} chunks."
            )

    # ── Database Operations ──────────────────────────────────────────────

    async def _save_chunks(
        self, chunks: list[dict], embeddings: list[list[float]]
    ) -> None:
        """Bulk-insert all DocumentChunk records."""
        logger.info("[doc=%s] Saving %d chunks.", self._document_id, len(chunks))
        chunk_objects = [
            DocumentChunk(
                user_id=self._document.user_id,
                document_id=self._document.id,
                content=chunk_data["content"],
                page_number=chunk_data["page_number"],
                chunk_index=chunk_data["chunk_index"],
                embedding=embedding,
            )
            for chunk_data, embedding in zip(chunks, embeddings)
        ]
        self._db.add_all(chunk_objects)

    async def _set_status(self, status: str) -> None:
        """Update document status and commit."""
        self._document.status = status
        await self._db.commit()

    async def _set_ready(self) -> None:
        """Mark document as ready and commit (atomic with chunk insert)."""
        self._document.status = "ready"
        self._document.error_message = None
        await self._db.commit()
        logger.info(
            "[doc=%s] Completed: processing finished successfully.",
            self._document_id,
        )

    async def _handle_failure(self, message: str) -> None:
        """Rollback pending changes, mark document as failed."""
        logger.error("[doc=%s] Processing failed: %s", self._document_id, message)
        await self._db.rollback()
        self._document.status = "failed"
        self._document.error_message = message
        await self._db.commit()


# ═════════════════════════════════════════════════════════════════════════════
# Backward-compatible module-level function
# ═════════════════════════════════════════════════════════════════════════════
# Tests mock extract_metadata, extract_text_from_pdf, chunk_document,
# generate_embeddings at the module level. The IngestionPipeline constructor
# defaults to these module-level names, so mocks are picked up automatically.


async def process_document(document_id: str, db: AsyncSession) -> None:
    """
    Process a document through the full ingestion pipeline.

    This is the backward-compatible entry point. For DI usage,
    construct an IngestionPipeline directly:

        pipeline = IngestionPipeline(
            document_id="...",
            db=session,
            embedder=my_custom_embedder,
        )
        await pipeline.run()
    """
    pipeline = IngestionPipeline(document_id, db)
    await pipeline.run()
