"""
Message schema.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Text, DateTime, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from src.helpers.db import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)

    role = Column(String(20), nullable=False)
    # user | assistant

    content = Column(Text, nullable=False)

    # Sources used to generate this response (assistant messages only)
    source_chunks = Column(JSON, nullable=True)

    # optional semantic memory
    embedding = Column(Vector(1536), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # relationships
    chat = relationship("Chat", back_populates="messages")

    def __repr__(self):
        return f"<Message {self.id}>"
