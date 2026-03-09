"""
Pydantic schemas for the Chat System (SPEC-05).
"""

import uuid as uuid_mod
from pydantic import BaseModel, field_validator
from datetime import datetime


class CreateChatRequest(BaseModel):
    title: str | None = None


class ChatListItem(BaseModel):
    id: str
    title: str | None
    created_at: datetime
    message_count: int
    last_message_at: datetime | None

    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    question: str
    document_ids: list[str] | None = None

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()

    @field_validator("document_ids")
    @classmethod
    def validate_document_ids(cls, v):
        if v:
            for doc_id in v:
                try:
                    uuid_mod.UUID(doc_id)
                except ValueError:
                    raise ValueError(f"Invalid document ID format: {doc_id}")
        return v


class SourceChunkResponse(BaseModel):
    source_number: int
    title: str | None = None
    author: str | None = None
    year: str | None = None
    page_number: int | None = None
    file_name: str | None = None
    document_id: str | None = None
    chunk_id: str | None = None
    similarity: float | None = None
    excerpt: str | None = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    source_chunks: list[dict] | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatDetailResponse(BaseModel):
    id: str
    title: str | None
    created_at: datetime
    messages: list[MessageResponse]

    class Config:
        from_attributes = True


class QueryResponse(BaseModel):
    message_id: str
    answer: str
    sources: list[dict]


class UpdateChatRequest(BaseModel):
    title: str
