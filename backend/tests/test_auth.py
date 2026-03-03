"""
Test cases for authentication endpoints.
Following TDD: These tests are written BEFORE implementation.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.helpers.security import hash_password
from src.models.db_scheams.user import User


class TestSignUp:
    """Test cases for POST /auth/signup endpoint."""

    @pytest.mark.asyncio
    async def test_signup_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/auth/signup",
            json={
                "name": "Test User",
                "email": "testuser@example.com",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert data["name"] == "Test User"
        assert data["is_verified"] is False
        assert "id" in data
        assert "password" not in data  # Password should not be returned
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, client: AsyncClient):
        """Test registration with existing email returns 400."""
        # First registration
        await client.post(
            "/auth/signup",
            json={
                "name": "First User",
                "email": "duplicate@example.com",
                "password": "SecurePass123",
            },
        )

        # Second registration with same email
        response = await client.post(
            "/auth/signup",
            json={
                "name": "Second User",
                "email": "duplicate@example.com",
                "password": "AnotherPass123",
            },
        )

        assert response.status_code == 400
        data = response.json()
        error_code = (
            data["detail"]["code"]
            if isinstance(data["detail"], dict)
            else data["detail"]
        )
        assert (
            "EMAIL_ALREADY_EXISTS" == error_code
            or "already registered" in str(error_code).lower()
        )

    @pytest.mark.asyncio
    async def test_signup_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format returns 422."""
        response = await client.post(
            "/auth/signup",
            json={
                "name": "Test User",
                "email": "invalid-email",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_weak_password(self, client: AsyncClient):
        """Test registration with password < 8 chars returns 422."""
        response = await client.post(
            "/auth/signup",
            json={
                "name": "Test User",
                "email": "weakpass@example.com",
                "password": "short",
            },
        )

        assert response.status_code == 422
        # Check that the error mentions password length
        detail = str(response.json())
        assert "8" in detail or "password" in detail.lower()

    @pytest.mark.asyncio
    async def test_signup_missing_fields(self, client: AsyncClient):
        """Test registration with missing required fields returns 422."""
        # Missing email
        response = await client.post(
            "/auth/signup", json={"name": "Test User", "password": "SecurePass123"}
        )
        assert response.status_code == 422

        # Missing name
        response = await client.post(
            "/auth/signup",
            json={"email": "missing@example.com", "password": "SecurePass123"},
        )
        assert response.status_code == 422

        # Missing password
        response = await client.post(
            "/auth/signup", json={"name": "Test User", "email": "nopass@example.com"}
        )
        assert response.status_code == 422


class TestVerifyCode:
    """Test cases for POST /auth/verify-code endpoint."""

    @pytest.mark.asyncio
    async def test_verify_code_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test successful email verification with valid code."""
        # First, register a user
        signup_response = await client.post(
            "/auth/signup",
            json={
                "name": "Verify User",
                "email": "verify@example.com",
                "password": "SecurePass123",
            },
        )
        assert signup_response.status_code == 201

        # Get the verification code from the database
        result = await db_session.execute(
            select(User).where(User.email == "verify@example.com")
        )
        user = result.scalar_one()
        verification_code = user.verification_token

        # Verify with the code
        response = await client.post(
            "/auth/verify-code",
            json={"email": "verify@example.com", "code": verification_code},
        )

        assert response.status_code == 200
        assert "verified" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_verify_code_invalid(self, client: AsyncClient):
        """Test verification with invalid code returns 400."""
        # Register a user first
        await client.post(
            "/auth/signup",
            json={
                "name": "Invalid Code User",
                "email": "invalidcode@example.com",
                "password": "SecurePass123",
            },
        )

        # Try to verify with wrong code
        response = await client.post(
            "/auth/verify-code",
            json={"email": "invalidcode@example.com", "code": "000000"},
        )

        assert response.status_code == 400
        assert response.status_code == 400
        data = response.json()
        error_code = (
            data["detail"]["code"]
            if isinstance(data["detail"], dict)
            else data["detail"]
        )
        assert (
            "INVALID_VERIFICATION_CODE" == error_code
            or "invalid" in str(error_code).lower()
        )

    @pytest.mark.asyncio
    async def test_verify_code_user_not_found(self, client: AsyncClient):
        """Test verification with non-existent email returns 404."""
        response = await client.post(
            "/auth/verify-code",
            json={"email": "nonexistent@example.com", "code": "123456"},
        )

        assert response.status_code == 404
        assert response.status_code == 404
        data = response.json()
        error_code = (
            data["detail"]["code"]
            if isinstance(data["detail"], dict)
            else data["detail"]
        )
        assert "USER_NOT_FOUND" == error_code or "not found" in str(error_code).lower()

    @pytest.mark.asyncio
    async def test_verify_code_already_verified(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test verification of already verified user returns 400."""
        # Register a user
        await client.post(
            "/auth/signup",
            json={
                "name": "Already Verified",
                "email": "alreadyverified@example.com",
                "password": "SecurePass123",
            },
        )

        # Get code from DB
        result = await db_session.execute(
            select(User).where(User.email == "alreadyverified@example.com")
        )
        user = result.scalar_one()
        code = user.verification_token

        # First verification - should succeed
        first_response = await client.post(
            "/auth/verify-code",
            json={"email": "alreadyverified@example.com", "code": code},
        )
        assert first_response.status_code == 200

        # Second verification - should fail
        response = await client.post(
            "/auth/verify-code",
            json={"email": "alreadyverified@example.com", "code": code},
        )

        assert response.status_code == 400
        assert response.status_code == 400
        data = response.json()
        error_code = (
            data["detail"]["code"]
            if isinstance(data["detail"], dict)
            else data["detail"]
        )
        assert (
            "EMAIL_ALREADY_VERIFIED" == error_code
            or "already verified" in str(error_code).lower()
        )

    @pytest.mark.asyncio
    async def test_verify_code_invalid_format(self, client: AsyncClient):
        """Test verification with invalid code format returns 422."""
        response = await client.post(
            "/auth/verify-code",
            json={"email": "test@example.com", "code": "abc"},  # Not 6 digits
        )

        assert response.status_code == 422


class TestResendCode:
    """Test cases for POST /auth/resend-code endpoint."""

    @pytest.mark.asyncio
    async def test_resend_code_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test successful resend of verification code."""
        # Register a user
        await client.post(
            "/auth/signup",
            json={
                "name": "Resend User",
                "email": "resend@example.com",
                "password": "SecurePass123",
            },
        )

        # Get the initial code
        result = await db_session.execute(
            select(User).where(User.email == "resend@example.com")
        )
        user = result.scalar_one()
        initial_code = user.verification_token

        # Resend code
        response = await client.post(
            "/auth/resend-code",
            json={"email": "resend@example.com"},
        )

        assert response.status_code == 200
        assert "resent" in response.json()["message"].lower()

        # Check that code has changed (usually good practice to implement rotation)
        # Assuming our implementation will generate a new code
        db_session.expire_all()
        result = await db_session.execute(
            select(User).where(User.email == "resend@example.com")
        )
        user = result.scalar_one()
        new_code = user.verification_token

        assert new_code != initial_code
        assert len(new_code) == 6

    @pytest.mark.asyncio
    async def test_resend_code_user_not_found(self, client: AsyncClient):
        """Test resend with non-existent email returns 404."""
        response = await client.post(
            "/auth/resend-code",
            json={"email": "nonexistent@example.com"},
        )

        assert response.status_code == 404
        assert response.status_code == 404
        data = response.json()
        error_code = (
            data["detail"]["code"]
            if isinstance(data["detail"], dict)
            else data["detail"]
        )
        assert "USER_NOT_FOUND" == error_code or "not found" in str(error_code).lower()

    @pytest.mark.asyncio
    async def test_resend_code_already_verified(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test resend for already verified user returns 400."""
        # Register and verify user
        await client.post(
            "/auth/signup",
            json={
                "name": "Verified Resend",
                "email": "verified_resend@example.com",
                "password": "SecurePass123",
            },
        )

        # Determine code
        result = await db_session.execute(
            select(User).where(User.email == "verified_resend@example.com")
        )
        user = result.scalar_one()
        code = user.verification_token

        # Verify
        await client.post(
            "/auth/verify-code",
            json={"email": "verified_resend@example.com", "code": code},
        )

        # Try to resend
        response = await client.post(
            "/auth/resend-code",
            json={"email": "verified_resend@example.com"},
        )

        assert response.status_code == 400
        data = response.json()
        error_code = (
            data["detail"]["code"]
            if isinstance(data["detail"], dict)
            else data["detail"]
        )
        assert (
            "EMAIL_ALREADY_VERIFIED" == error_code
            or "already verified" in str(error_code).lower()
        )

    @pytest.mark.asyncio
    async def test_resend_code_invalid_email(self, client: AsyncClient):
        """Test resend with invalid email format returns 422."""
        response = await client.post(
            "/auth/resend-code",
            json={"email": "invalid-email"},
        )

        assert response.status_code == 422
