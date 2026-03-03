"""
Pydantic schemas for User authentication.
Used for request validation and response serialization.
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Schema for user registration request."""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserResponse(BaseModel):
    """Schema for user response (excludes sensitive data)."""

    id: UUID
    name: str
    email: EmailStr
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy


class UserInDB(BaseModel):
    """Internal schema with hashed password."""

    id: UUID
    name: str
    email: EmailStr
    hashed_password: str
    is_active: bool
    is_verified: bool
    verification_token: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VerifyCodeRequest(BaseModel):
    """Schema for email verification request."""

    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResendCodeRequest(BaseModel):
    """Schema for resending verification code."""

    email: EmailStr


class LoginRequest(BaseModel):
    """Schema for user login request."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v:
            raise ValueError("Email is required")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("Password is required")
        return v


class LoginResponse(BaseModel):
    """Schema for user login response."""

    access_token: str
    token_type: str
    user: UserResponse

    class Config:
        from_attributes = True


class RefreshTokenResponse(BaseModel):
    """Schema for user login response."""

    access_token: str
    token_type: str

    class Config:
        from_attributes = True


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password meets requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v
