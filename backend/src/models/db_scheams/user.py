"""
User database schema for SQLAlchemy ORM.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID

from src.helpers.db import Base


class User(Base):
    """User model for authentication system."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Email verification
    is_active = Column(Boolean, default=False)  # Set True after email verification
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    role = Column(String(20), default="user")  # user | admin
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.email}>"
