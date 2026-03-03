"""
Document database schema.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.helpers.db import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Supabase Storage object path
    file_size = Column(Integer, nullable=True)  # File size in bytes

    total_pages = Column(Integer, nullable=True)
    status = Column(String(20), default="uploading")
    # uploading → processing → ready | failed

    # Paper metadata (populated by SPEC-03 or user via PATCH)
    title = Column(String(500), nullable=True)
    author = Column(String(500), nullable=True)
    year = Column(String(10), nullable=True)
    journal = Column(String(500), nullable=True)
    doi = Column(String(255), nullable=True)
    abstract = Column(Text, nullable=True)

    error_message = Column(Text, nullable=True)  # Error details if status=failed

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    user = relationship("User", backref="documents")
    chunks = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete"
    )

    def __repr__(self):
        return f"<Document {self.file_name}>"
