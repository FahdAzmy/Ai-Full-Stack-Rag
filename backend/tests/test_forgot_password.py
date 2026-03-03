"""
Tests for Forgot Password functionality.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.helpers.security import hash_password
from src.models.db_scheams.user import User


def get_error_code(response_json: dict) -> str:
    """
    Extract error code from response, handling both formats:
    - {"detail": {"code": "ERROR_CODE"}}   (AppException format)
    - {"detail": "some string"}            (plain HTTPException format)
    """
    detail = response_json.get("detail", "")
    if isinstance(detail, dict):
        return detail.get("code", "")
    return str(detail)


class TestForgotPassword:
    """Test cases for POST /auth/forgot-password endpoint."""

    @pytest.mark.asyncio
    async def test_forgot_password_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test successful forgot password request sends reset code."""
        # Create verified user
        user = User(
            email="forgot@example.com",
            name="Forgot User",
            hashed_password=hash_password("OldPassword123"),
            is_verified=True,
            verification_token=None,
        )
        db_session.add(user)
        await db_session.commit()

        # Request password reset
        response = await client.post(
            "/auth/forgot-password",
            json={"email": "forgot@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # The controller returns SuccessMessage.PASSWORD_RESET_CODE_SENT
        assert data["message"] == "PASSWORD_RESET_CODE_SENT"

        # Verify reset code was stored in database
        await db_session.refresh(user)
        assert user.verification_token is not None
        assert len(user.verification_token) == 6

    @pytest.mark.asyncio
    async def test_forgot_password_user_not_found(self, client: AsyncClient):
        """Test forgot password with non-existent email returns 404."""
        response = await client.post(
            "/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )

        assert response.status_code == 404
        error_code = get_error_code(response.json())
        assert error_code == "USER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_forgot_password_missing_email(self, client: AsyncClient):
        """Test forgot password without email returns 422."""
        response = await client.post(
            "/auth/forgot-password",
            json={},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_forgot_password_invalid_email(self, client: AsyncClient):
        """Test forgot password with invalid email format returns 422."""
        response = await client.post(
            "/auth/forgot-password",
            json={"email": "invalid-email"},
        )

        assert response.status_code == 422


class TestResetPassword:
    """Test cases for POST /auth/reset-password endpoint."""

    @pytest.mark.asyncio
    async def test_reset_password_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test successful password reset with valid code."""
        # Create user with reset code
        user = User(
            email="reset@example.com",
            name="Reset User",
            hashed_password=hash_password("OldPassword123"),
            is_verified=True,
            verification_token="123456",
        )
        db_session.add(user)
        await db_session.commit()

        # Reset password
        response = await client.post(
            "/auth/reset-password",
            json={
                "email": "reset@example.com",
                "code": "123456",
                "new_password": "NewPassword456",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "PASSWORD_RESET_SUCCESS"

        # Verify password was changed and token cleared
        await db_session.refresh(user)
        assert user.verification_token is None

        # Verify can login with new password
        login_response = await client.post(
            "/auth/login",
            json={"email": "reset@example.com", "password": "NewPassword456"},
        )
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_reset_password_invalid_code(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test reset password with invalid code returns 400."""
        # Create user with reset code
        user = User(
            email="reset@example.com",
            name="Reset User",
            hashed_password=hash_password("OldPassword123"),
            is_verified=True,
            verification_token="123456",
        )
        db_session.add(user)
        await db_session.commit()

        # Try reset with wrong code
        response = await client.post(
            "/auth/reset-password",
            json={
                "email": "reset@example.com",
                "code": "999999",
                "new_password": "NewPassword456",
            },
        )

        assert response.status_code == 400
        error_code = get_error_code(response.json())
        assert error_code == "INVALID_RESET_CODE"

    @pytest.mark.asyncio
    async def test_reset_password_user_not_found(self, client: AsyncClient):
        """Test reset password with non-existent email returns 404."""
        response = await client.post(
            "/auth/reset-password",
            json={
                "email": "nonexistent@example.com",
                "code": "123456",
                "new_password": "NewPassword456",
            },
        )

        assert response.status_code == 404
        error_code = get_error_code(response.json())
        assert error_code == "USER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_reset_password_missing_fields(self, client: AsyncClient):
        """Test reset password with missing fields returns 422."""
        # Missing new_password
        response = await client.post(
            "/auth/reset-password",
            json={"email": "reset@example.com", "code": "123456"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_reset_password_weak_password(self, client: AsyncClient):
        """Test reset password with weak password returns 422."""
        response = await client.post(
            "/auth/reset-password",
            json={
                "email": "reset@example.com",
                "code": "123456",
                "new_password": "short",  # Less than 8 characters
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_reset_password_no_reset_code(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test reset password when user has no reset code returns 400."""
        # Create user without reset code
        user = User(
            email="noreset@example.com",
            name="No Reset User",
            hashed_password=hash_password("OldPassword123"),
            is_verified=True,
            verification_token=None,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/auth/reset-password",
            json={
                "email": "noreset@example.com",
                "code": "123456",
                "new_password": "NewPassword456",
            },
        )

        assert response.status_code == 400
        error_code = get_error_code(response.json())
        assert error_code == "INVALID_RESET_CODE"
