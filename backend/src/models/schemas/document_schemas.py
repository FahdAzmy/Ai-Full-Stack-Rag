"""
Pydantic schemas for Document Upload & Management (SPEC-02).
"""

from pydantic import BaseModel
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    """Response returned after a successful document upload."""

    id: str
    file_name: str
    file_size: int
    status: str
    message: str

    class Config:
        from_attributes = True


class DocumentListItem(BaseModel):
    """Single document item in a list response."""

    id: str
    file_name: str
    title: str | None = None
    author: str | None = None
    year: str | None = None
    status: str
    total_pages: int | None = None
    file_size: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response for listing documents."""

    documents: list[DocumentListItem]
    total: int


class DocumentDetail(DocumentListItem):
    """Full document detail response."""

    journal: str | None = None
    doi: str | None = None
    abstract: str | None = None
    error_message: str | None = None
    updated_at: datetime | None = None
    chunk_count: int = 0


class DocumentUpdateRequest(BaseModel):
    """Request body for updating document metadata."""

    title: str | None = None
    author: str | None = None
    year: str | None = None
    journal: str | None = None
    doi: str | None = None


class DocumentUpdateResponse(BaseModel):
    """Response after updating a document."""

    message: str
    id: str
