"""
Security utilities for password hashing and token generation.
Uses bcrypt directly for compatibility with newer bcrypt versions.
"""

import secrets
import bcrypt
import uuid
from src.helpers.config import settings
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError
from datetime import datetime, timedelta
from typing import Dict, AsyncGenerator
from fastapi import HTTPException, Response, Depends, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.helpers.db import get_db
from src.models.db_scheams.user import User
from src.helpers.logging_config import get_logger

logger = get_logger("auth.security")


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string
    """
    # Encode password to bytes and hash with bcrypt
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def generate_verification_code() -> str:
    """
    Generate a 6-digit verification code for email verification.

    Returns:
        6-digit numeric code as string
    """
    return str(secrets.randbelow(900000) + 100000)  # Ensures 6 digits (100000-999999)


def generate_access_token(user_id: str | int) -> str:
    """
    Generate a JWT access token for a user.

    Args:
        user_id: User ID to include in the token

    Returns:
        JWT access token
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),  # issued at
        "type": "access",
    }
    logger.info(
        "Access token generated for user_id=%s, expires_in=%d min",
        user_id,
        settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def generate_refresh_token(user_id: str | int) -> str:
    """
    Generate a JWT refresh token for a user.

    Args:
        user_id: User ID to include in the token

    Returns:
        JWT refresh token
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "user_id": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    logger.info(
        "Refresh token generated for user_id=%s, expires_in=%d days",
        user_id,
        settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )
    return jwt.encode(payload, settings.REFRESH_SECRET_KEY, algorithm="HS256")


def verify_access_token(token: str) -> Dict:
    """
    Verify and decode access token.

    Args:
        token: JWT access token

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            logger.warning("Access token verification failed — wrong token type")
            raise HTTPException(status_code=401, detail="Invalid token type")
        logger.info("Access token verified for user_id=%s", payload.get("user_id"))
        return payload
    except ExpiredSignatureError:
        logger.warning("Access token verification failed — token expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        logger.warning("Access token verification failed — invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_refresh_token(token: str) -> Dict:
    """
    Verify and decode refresh token.

    Args:
        token: JWT refresh token

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            logger.warning("Refresh token verification failed — wrong token type")
            raise HTTPException(status_code=401, detail="Invalid token type")
        logger.info("Refresh token verified for user_id=%s", payload.get("user_id"))
        return payload
    except ExpiredSignatureError:
        logger.warning("Refresh token verification failed — token expired")
        raise HTTPException(status_code=401, detail="Refresh token has expired")
    except JWTError:
        logger.warning("Refresh token verification failed — invalid token")
        raise HTTPException(status_code=401, detail="Invalid refresh token")


security = HTTPBearer()


async def get_current_user(
    credentials=Depends(security), db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from a JWT token.

    Args:
        credentials: HTTPBearer credentials (the token)
        db: Database session

    Returns:
        The User object if token is valid

    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    token = credentials.credentials

    try:
        # Decode the token using the secret key and HS256 algorithm
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            logger.warning("get_current_user — token missing user_id")
            raise HTTPException(
                status_code=401, detail="Invalid token: missing user_id"
            )
    except ExpiredSignatureError:
        logger.warning("get_current_user — token expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        logger.warning("get_current_user — invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("get_current_user — user not found for user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    logger.info("Authenticated user_id=%s", user_id)
    return user
