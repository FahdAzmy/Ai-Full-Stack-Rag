"""
Document controller — business logic for document operations (SPEC-02).
"""

import uuid
import os

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.tasks.ingestion import process_document_task

from src.models.db_scheams.document import Document
from src.models.db_scheams.DocumentChunk import DocumentChunk
from src.models.schemas.document_schemas import (
    DocumentUploadResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentDetail,
    DocumentUpdateRequest,
    DocumentUpdateResponse,
)
from src.models.db_scheams.user import User
from src.helpers.config import settings
from src.helpers import storage
from src.helpers.logging_config import get_logger

logger = get_logger("documents.controller")


# ═════════════════════════════════════════════════════════════════════════════
#  Private helpers
# ═════════════════════════════════════════════════════════════════════════════


async def _get_user_document(
    document_id: str,
    current_user: User,
    db: AsyncSession,
) -> Document:
    """Fetch a document by ID and verify ownership.

    Raises:
        HTTPException 404: Document not found.
        HTTPException 403: Document belongs to another user.
    """
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if doc.user_id != current_user.id:
        logger.warning(
            "Access denied: user=%s tried to access doc=%s owned by user=%s",
            current_user.id,
            document_id,
            doc.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return doc


def _validate_pdf_upload(file: UploadFile, content: bytes) -> None:
    """Validate that the uploaded file is a valid, non-empty PDF within size limits.

    Raises:
        HTTPException 400: If validation fails.
    """
    filename = file.filename or ""

    # 1. Extension check
    _, ext = os.path.splitext(filename)
    if ext.lower() != ".pdf":
        logger.warning("Upload rejected — not a PDF: %s", filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF files are accepted. Got: {ext}",
        )

    # 2. MIME type check (secondary — matches spec requirement)
    if file.content_type and file.content_type != "application/pdf":
        logger.warning(
            "Upload rejected — wrong MIME type: %s (%s)",
            filename,
            file.content_type,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF files are accepted. Got MIME type: {file.content_type}",
        )

    # 3. Empty file check
    if len(content) == 0:
        logger.warning("Upload rejected — empty file: %s", filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    # 4. File size check
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    file_size = len(content)
    if file_size > max_bytes:
        size_mb = round(file_size / (1024 * 1024), 1)
        logger.warning(
            "Upload rejected — too large: %s (%.1f MB > %d MB)",
            filename,
            size_mb,
            settings.MAX_FILE_SIZE_MB,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB. Got: {size_mb}MB",
        )


# ═════════════════════════════════════════════════════════════════════════════
#  Public API — called by routes
# ═════════════════════════════════════════════════════════════════════════════


async def upload_document(
    file: UploadFile,
    current_user: User,
    db: AsyncSession,
) -> DocumentUploadResponse:
    """Upload a PDF: validate → create DB record → upload to Supabase Storage.

    If storage upload fails after DB record is created, the record is
    rolled back (cleaned up) and a 500 error is returned.
    """
    # ── Validate ─────────────────────────────────────────────────────────
    content = await file.read()
    _validate_pdf_upload(file, content)

    original_filename = file.filename or ""
    file_size = len(content)

    # ── Create DB record ─────────────────────────────────────────────────
    document_id = uuid.uuid4()
    storage_path = f"{current_user.id}/{document_id}.pdf"

    doc = Document(
        id=document_id,
        user_id=current_user.id,
        file_name=original_filename,
        file_path=storage_path,
        file_size=file_size,
        status="uploading",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    logger.info(
        "Document record created: id=%s user=%s file=%s size=%d",
        document_id,
        current_user.id,
        original_filename,
        file_size,
    )

    # ── Upload to Supabase Storage ───────────────────────────────────────
    try:
        storage.upload(content, storage_path)
    except Exception as e:
        logger.error("Storage upload failed for doc=%s: %s", document_id, str(e))
        await db.delete(doc)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to storage",
        )

    # ── Queue background processing (SPEC-08) ────────────────────────────
    # Business Rule #2: Don't allow re-processing a document already "processing"
    if doc.status == "processing":
        logger.warning("Document %s is already processing, skipping queue.", document_id)
        return DocumentUploadResponse(
            id=str(document_id),
            file_name=original_filename,
            file_size=file_size,
            status="processing",
            message="Document is already being processed.",
        )

    # Pipeline runs in a Celery worker: uploading → processing → ready/failed
    # The upload returns immediately with status="processing".
    process_document_task.delay(str(document_id))

    # Update status in DB so frontend polls see "processing" immediately
    doc.status = "processing"
    await db.commit()

    # ── Return response ──────────────────────────────────────────────────
    logger.info(
        "Upload complete, processing queued: doc=%s", document_id
    )
    return DocumentUploadResponse(
        id=str(document_id),
        file_name=original_filename,
        file_size=file_size,
        status="processing",
        message="Upload successful. Processing queued.",
    )


async def list_documents(
    current_user: User,
    db: AsyncSession,
    status_filter: str | None = None,
) -> DocumentListResponse:
    """List all documents belonging to the current user, optionally filtered by status."""
    query = select(Document).where(Document.user_id == current_user.id)

    if status_filter:
        query = query.where(Document.status == status_filter)

    query = query.order_by(Document.created_at.desc())

    result = await db.execute(query)
    docs = result.scalars().all()

    logger.info(
        "Listed %d documents for user=%s (filter=%s)",
        len(docs),
        current_user.id,
        status_filter,
    )

    items = [
        DocumentListItem(
            id=str(doc.id),
            file_name=doc.file_name,
            title=doc.title,
            author=doc.author,
            year=doc.year,
            status=doc.status,
            total_pages=doc.total_pages,
            file_size=doc.file_size,
            created_at=doc.created_at,
        )
        for doc in docs
    ]

    return DocumentListResponse(documents=items, total=len(items))


async def get_document(
    document_id: str,
    current_user: User,
    db: AsyncSession,
) -> DocumentDetail:
    """Get detailed info about a specific document, including chunk count."""
    doc = await _get_user_document(document_id, current_user, db)

    # Count chunks
    chunk_result = await db.execute(
        select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == doc.id)
    )
    chunk_count = chunk_result.scalar() or 0

    logger.info("Get document detail: doc=%s chunks=%d", document_id, chunk_count)

    return DocumentDetail(
        id=str(doc.id),
        file_name=doc.file_name,
        title=doc.title,
        author=doc.author,
        year=doc.year,
        status=doc.status,
        total_pages=doc.total_pages,
        file_size=doc.file_size,
        created_at=doc.created_at,
        journal=doc.journal,
        doi=doc.doi,
        abstract=doc.abstract,
        error_message=doc.error_message,
        updated_at=doc.updated_at,
        chunk_count=chunk_count,
    )


async def update_document(
    document_id: str,
    update_data: DocumentUpdateRequest,
    current_user: User,
    db: AsyncSession,
) -> DocumentUpdateResponse:
    """Update document metadata. Only explicitly provided fields are changed."""
    doc = await _get_user_document(document_id, current_user, db)

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(doc, field, value)

    await db.commit()
    await db.refresh(doc)

    logger.info(
        "Document updated: doc=%s fields=%s", document_id, list(update_dict.keys())
    )

    return DocumentUpdateResponse(
        message="Document updated successfully",
        id=str(doc.id),
    )


async def delete_document(
    document_id: str,
    current_user: User,
    db: AsyncSession,
) -> dict:
    """Delete a document: remove from storage, then delete DB record + cascaded chunks.

    If storage deletion fails, DB records are still deleted (per spec rule #7).
    Orphaned storage files are acceptable and can be cleaned up periodically.
    """
    doc = await _get_user_document(document_id, current_user, db)
    storage_path = doc.file_path

    # 1. Try to delete from Supabase Storage (tolerate failure)
    try:
        storage.delete(storage_path)
    except Exception as e:
        logger.warning(
            "Storage delete failed for doc=%s path=%s: %s (continuing with DB cleanup)",
            document_id,
            storage_path,
            str(e),
        )

    # 2. Delete DB record (cascade deletes chunks)
    await db.delete(doc)
    await db.commit()

    logger.info("Document deleted: doc=%s", document_id)

    return {"message": "Document and all associated data deleted successfully"}
