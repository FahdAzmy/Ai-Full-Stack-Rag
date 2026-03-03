"""
Authentication controller - business logic for auth operations.
"""

from fastapi import HTTPException, status, BackgroundTasks, Response, Cookie

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.helpers.config import settings
from src.helpers.errorHandler import AppException
from src.helpers.errorCodes import ErrorCode
from src.helpers.successMessages import SuccessMessage
from src.helpers.logging_config import get_logger, mask_email


from src.models.db_scheams.user import User
from src.models.schemas.user_schema import (
    UserCreate,
    UserResponse,
    VerifyCodeRequest,
    ResendCodeRequest,
    LoginRequest,
    LoginResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    RefreshTokenResponse,
)
from src.helpers.security import (
    hash_password,
    generate_verification_code,
    generate_access_token,
    verify_password,
    generate_refresh_token,
    verify_refresh_token,
    verify_access_token,
)
from src.helpers.email_service import send_verification_email, send_password_reset_email

logger = get_logger("auth.controller")


async def signup(
    user_data: UserCreate, db: AsyncSession, background_tasks: BackgroundTasks
) -> UserResponse:
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session
        background_tasks: FastAPI background tasks for async email

    Returns:
        Created user response

    Raises:
        HTTPException: If email already exists
    """
    masked = mask_email(user_data.email)
    logger.info("Signup attempt for email=%s", masked)

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.warning("Signup rejected — email already exists: %s", masked)
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST, code=ErrorCode.EMAIL_ALREADY_EXISTS
        )

    # Create new user with verification code
    verification_code = generate_verification_code()
    hashed_pwd = hash_password(user_data.password)

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_pwd,
        verification_token=verification_code,  # Store 6-digit code
        is_active=False,
        is_verified=False,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logger.info("User created successfully: id=%s, email=%s", new_user.id, masked)

    # Send verification code email in background
    background_tasks.add_task(
        send_verification_email,
        email=new_user.email,
        code=verification_code,
        name=new_user.name,
    )
    logger.info("Verification email queued for email=%s", masked)

    return UserResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,
        is_verified=new_user.is_verified,
        created_at=new_user.created_at,
    )


async def verify_email(verify_data: VerifyCodeRequest, db: AsyncSession) -> dict:
    """
    Verify user email with the 6-digit code.

    Args:
        verify_data: Email and verification code
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If code is invalid or email not found
    """
    masked = mask_email(verify_data.email)
    logger.info("Email verification attempt for email=%s", masked)

    # Find user by email
    result = await db.execute(select(User).where(User.email == verify_data.email))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("Verification failed — user not found: email=%s", masked)
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND, code=ErrorCode.USER_NOT_FOUND
        )

    if user.is_verified:
        logger.warning("Verification rejected — already verified: user_id=%s", user.id)
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.EMAIL_ALREADY_VERIFIED,
        )

    # Check verification code
    if user.verification_token != verify_data.code:
        logger.warning("Verification failed — invalid code for user_id=%s", user.id)
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.INVALID_VERIFICATION_CODE,
        )

    # Verify user
    user.is_verified = True
    user.is_active = True
    user.verification_token = None  # Clear the code after use

    await db.commit()

    logger.info("Email verified successfully: user_id=%s", user.id)
    return {"message": SuccessMessage.EMAIL_VERIFIED}


async def resend_verification_code(
    resend_data: ResendCodeRequest, db: AsyncSession, background_tasks: BackgroundTasks
) -> dict:
    """
    Resend verification code to user email.

    Args:
        resend_data: Email
        db: Database session
        background_tasks: FastAPI background tasks

    Returns:
        Success message

    Raises:
        HTTPException: If user not found or already verified
    """
    masked = mask_email(resend_data.email)
    logger.info("Resend verification code request for email=%s", masked)

    # Find user by email
    result = await db.execute(select(User).where(User.email == resend_data.email))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("Resend code failed — user not found: email=%s", masked)
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND, code=ErrorCode.USER_NOT_FOUND
        )

    if user.is_verified:
        logger.warning("Resend code rejected — already verified: user_id=%s", user.id)
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.EMAIL_ALREADY_VERIFIED,
        )

    # Generate new verification code
    new_code = generate_verification_code()

    # Update user
    user.verification_token = new_code
    await db.commit()

    # Send new code email in background
    background_tasks.add_task(
        send_verification_email,
        email=user.email,
        code=new_code,
        name=user.name,
    )

    logger.info("New verification code sent to user_id=%s, email=%s", user.id, masked)
    return {"message": SuccessMessage.VERIFICATION_CODE_RESENT}


async def login(
    login_data: LoginRequest, response: Response, db: AsyncSession
) -> LoginResponse:
    """
    Login user with email and password.

    Args:
        login_data: Email and password
        db: Database session

    Returns:
        Access token and token type

    Raises:
        HTTPException: If user not found or invalid credentials
    """
    masked = mask_email(login_data.email)
    logger.info("Login attempt for email=%s", masked)

    # Find user by email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(login_data.password, user.hashed_password):
        logger.warning("Login failed — invalid credentials for email=%s", masked)
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED, code=ErrorCode.INVALID_CREDENTIALS
        )
    # Generate access token
    access_token = generate_access_token(user.id)
    refresh_token = generate_refresh_token(user.id)

    # Set refresh token in httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    logger.info("Login successful: user_id=%s, email=%s", user.id, masked)

    return LoginResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            is_verified=user.is_verified,
            created_at=user.created_at,
        ),
        token_type="bearer",
    )


async def refresh_access_token(
    response: Response,
    refresh_token: str = Cookie(None),  # قراءة الكوكيز
    db: AsyncSession = None,
) -> LoginResponse:
    """
    Refresh access token using refresh token from cookie.

    Args:
        response: FastAPI Response object
        refresh_token: Refresh token from cookie
        db: Database session

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    logger.info("Token refresh attempt")

    if not refresh_token:
        logger.warning("Token refresh failed — no refresh token in cookie")
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.REFRESH_TOKEN_NOT_FOUND,
        )

    # Verify refresh token
    payload = verify_refresh_token(refresh_token)
    user_id = payload.get("user_id")

    logger.info("Refresh token verified for user_id=%s", user_id)

    # Generate new tokens
    new_access_token = generate_access_token(user_id)
    new_refresh_token = generate_refresh_token(user_id)

    # Update refresh token in cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    logger.info("Tokens refreshed successfully for user_id=%s", user_id)
    return RefreshTokenResponse(access_token=new_access_token, token_type="bearer")


async def forgot_password(
    forgot_data: ForgotPasswordRequest,
    db: AsyncSession,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Send password reset code to user's email.

    Args:
        forgot_data: Email address
        db: Database session
        background_tasks: FastAPI background tasks for async email

    Returns:
        Success message

    Raises:
        HTTPException: If user not found
    """
    masked = mask_email(forgot_data.email)
    logger.info("Forgot password request for email=%s", masked)

    # Find user by email
    result = await db.execute(select(User).where(User.email == forgot_data.email))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("Forgot password failed — user not found: email=%s", masked)
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND, code=ErrorCode.USER_NOT_FOUND
        )

    # Generate reset code
    reset_code = generate_verification_code()

    # Store reset code in verification_token
    user.verification_token = reset_code
    await db.commit()

    # Send reset code email in background
    background_tasks.add_task(
        send_password_reset_email,
        email=user.email,
        code=reset_code,
        name=user.name,
    )

    logger.info("Password reset code sent to user_id=%s, email=%s", user.id, masked)
    return {"message": SuccessMessage.PASSWORD_RESET_CODE_SENT}


async def reset_password(
    reset_data: ResetPasswordRequest,
    db: AsyncSession,
) -> dict:
    """
    Reset user's password with verification code.

    Args:
        reset_data: Email, code, and new password
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If user not found or code is invalid
    """
    masked = mask_email(reset_data.email)
    logger.info("Password reset attempt for email=%s", masked)

    # Find user by email
    result = await db.execute(select(User).where(User.email == reset_data.email))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("Password reset failed — user not found: email=%s", masked)
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND, code=ErrorCode.USER_NOT_FOUND
        )

    # Check reset code
    if user.verification_token is None or user.verification_token != reset_data.code:
        logger.warning("Password reset failed — invalid code for user_id=%s", user.id)
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST, code=ErrorCode.INVALID_RESET_CODE
        )

    # Hash new password and update
    user.hashed_password = hash_password(reset_data.new_password)
    user.verification_token = None  # Clear the code after use
    await db.commit()

    logger.info("Password reset successful for user_id=%s, email=%s", user.id, masked)
    return {"message": SuccessMessage.PASSWORD_RESET_SUCCESS}


async def get_profile(current_user: User) -> UserResponse:
    """
    Get the profile information of the currently authenticated user.

    Args:
        current_user: The user object injected by the dependency

    Returns:
        User profile information
    """
    logger.info("Profile requested for user_id=%s", current_user.id)
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
    )
