"""
Authentication routes for FastAPI.
"""

from fastapi import APIRouter, Depends, BackgroundTasks, status, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from src.helpers.db import get_db
from src.models.schemas.user_schema import (
    UserCreate,
    UserResponse,
    VerifyCodeRequest,
    ResendCodeRequest,
    LoginResponse,
    LoginRequest,
    RefreshTokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from src.controllers.auth_controller import (
    signup,
    verify_email,
    resend_verification_code,
    login,
    refresh_access_token,
    forgot_password,
    reset_password,
    get_profile,
)
from src.helpers.security import get_current_user
from src.helpers.logging_config import get_logger

logger = get_logger("auth.routes")

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Register a new user.

    - **name**: User's full name (1-100 characters)
    - **email**: Valid email address (must be unique)
    - **password**: Password (minimum 8 characters)

    Returns the created user info. A verification code will be sent via email.
    """
    return await signup(user_data, db, background_tasks)


@router.post("/verify-code", status_code=status.HTTP_200_OK)
async def verify_user_email(
    verify_data: VerifyCodeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Verify user email with 6-digit code.

    - **email**: User's email address
    - **code**: 6-digit verification code sent via email

    Returns success message if verification is successful.
    """
    return await verify_email(verify_data, db)


@router.post("/resend-code", status_code=status.HTTP_200_OK)
async def resend_code(
    resend_data: ResendCodeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Resend verification code to user email.

    - **email**: User's email address

    Returns success message if code is resent successfully.
    """
    return await resend_verification_code(resend_data, db, background_tasks)


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_user(
    login_data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    Login user with email and password.

    - **email**: User's email address
    - **password**: User's password

    Returns access token and token type.
    """
    return await login(login_data, response, db)


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_endpoint(
    response: Response,
    refresh_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    return await refresh_access_token(response, refresh_token, db)


@router.post("/logout")
async def logout_endpoint(response: Response):
    """Logout user by clearing refresh token cookie."""
    response.delete_cookie(key="refresh_token", path="/")
    logger.info("User logged out — refresh token cookie cleared")
    return {"message": "Logged out successfully"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password_endpoint(
    forgot_data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Request password reset code.

    - **email**: User's email address

    Sends a 6-digit reset code to the user's email.
    """
    return await forgot_password(forgot_data, db, background_tasks)


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password_endpoint(
    reset_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Reset password with verification code.

    - **email**: User's email address
    - **code**: 6-digit reset code from email
    - **new_password**: New password (minimum 8 characters)

    Returns success message if password is reset successfully.
    """
    return await reset_password(reset_data, db)


@router.get("/profile", response_model=UserResponse)
async def profile_endpoint(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get current user profile information.

    Requires a valid JWT access token in the Authorization header:
    `Authorization: Bearer <token>`
    """
    return await get_profile(current_user)
