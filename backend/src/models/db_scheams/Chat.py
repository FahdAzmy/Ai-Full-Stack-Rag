"""
Chat schema.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.helpers.db import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    title = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # relationships
    messages = relationship("Message", back_populates="chat", cascade="all, delete")

    def __repr__(self):
        return f"<Chat {self.id}>"
