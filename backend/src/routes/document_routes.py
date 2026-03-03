"""
Document routes for FastAPI (SPEC-02).
"""

from fastapi import APIRouter, Depends, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.helpers.db import get_db
from src.helpers.security import get_current_user
from src.models.schemas.document_schemas import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDetail,
    DocumentUpdateRequest,
    DocumentUpdateResponse,
)
from src.controllers.document_controller import (
    upload_document,
    list_documents,
    get_document,
    update_document,
    delete_document,
)
from src.helpers.logging_config import get_logger

logger = get_logger("documents.routes")

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document_endpoint(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """
    Upload a PDF research paper.

    - **file**: PDF file (max 50MB)

    Requires a valid JWT access token in the Authorization header.
    Returns document info with processing status.
    """
    return await upload_document(file, current_user, db)


@router.get(
    "/",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_documents_endpoint(
    status_filter: str | None = Query(None, alias="status"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """
    List all documents for the current user.

    - **status** (optional): Filter by status — uploading, processing, ready, failed

    Requires a valid JWT access token in the Authorization header.
    """
    return await list_documents(current_user, db, status_filter)


@router.get(
    "/{document_id}",
    response_model=DocumentDetail,
    status_code=status.HTTP_200_OK,
)
async def get_document_endpoint(
    document_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentDetail:
    """
    Get detailed information about a specific document.

    - **document_id**: UUID of the document

    Requires a valid JWT access token in the Authorization header.
    """
    return await get_document(document_id, current_user, db)


@router.patch(
    "/{document_id}",
    response_model=DocumentUpdateResponse,
    status_code=status.HTTP_200_OK,
)
async def update_document_endpoint(
    document_id: str,
    update_data: DocumentUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentUpdateResponse:
    """
    Update document metadata (title, author, year, journal, doi).

    All fields are optional — only provided fields are updated.

    Requires a valid JWT access token in the Authorization header.
    """
    return await update_document(document_id, update_data, current_user, db)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_document_endpoint(
    document_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a document, its file from storage, and all associated chunks.

    Requires a valid JWT access token in the Authorization header.
    """
    return await delete_document(document_id, current_user, db)
