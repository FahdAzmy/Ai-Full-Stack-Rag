"""
Document Chunk schema with vector embeddings.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Text, DateTime, ForeignKey, Integer, Computed
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from src.helpers.db import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)

    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    chunk_index = Column(Integer, nullable=False, default=0)

    # Vector embedding (text-embedding-3-small: 1536 dims)
    embedding = Column(Vector(1536))

    # Full-text search column (SPEC-08) — auto-generated from content
    content_tsv = Column(
        TSVECTOR,
        Computed("to_tsvector('english', content)", persisted=True),
        nullable=True,
    )

    created_at = Column(DateTime, default=datetime.utcnow)

    # relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<Chunk {self.id}>"

