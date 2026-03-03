import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.helpers.security import hash_password, generate_refresh_token
from src.models.db_scheams.user import User


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful login with existing email."""
        # add user
        user = User(
            email="login@example.com",
            name="Login User",
            hashed_password=hash_password("SecurePass123"),
            is_verified=True,
            verification_token="123456",
        )
        db_session.add(user)
        await db_session.commit()
        # Login
        response = await client.post(
            "/auth/login",
            json={"email": "login@example.com", "password": "SecurePass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, client: AsyncClient):
        """Test login with invalid email format returns 422."""

        response = await client.post(
            "/auth/login",
            json={"email": "invalid-email", "password": "SecurePass123"},
        )
        data = response.json()
        assert data["detail"][0]["loc"] == ["body", "email"]
        assert "email address is not valid" in data["detail"][0]["msg"].lower()

    @pytest.mark.asyncio
    async def test_login_invalid_password(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test login with invalid password returns 401."""
        # add user
        user = User(
            email="login@example.com",
            name="Login User",
            hashed_password=hash_password("SecurePass123"),
            is_verified=True,
            verification_token="123456",
        )
        db_session.add(user)
        await db_session.commit()
        response = await client.post(
            "/auth/login",
            json={"email": "login@example.com", "password": "wrong-password"},
        )
        assert response.status_code == 401
        data = response.json()
        error_code = (
            data["detail"]["code"]
            if isinstance(data["detail"], dict)
            else data["detail"]
        )
        assert (
            "INVALID_CREDENTIALS" == error_code or "invalid" in str(error_code).lower()
        )

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, client: AsyncClient):
        """Test login with non-existent email returns 401."""

        response = await client.post(
            "/auth/login",
            json={"email": "nonexistent@example.com", "password": "SecurePass123"},
        )
        assert response.status_code == 401
        data = response.json()
        error_code = (
            data["detail"]["code"]
            if isinstance(data["detail"], dict)
            else data["detail"]
        )
        assert (
            "INVALID_CREDENTIALS" == error_code or "invalid" in str(error_code).lower()
        )

    @pytest.mark.asyncio
    async def test_login_without_email(self, client: AsyncClient):
        """Test login without email returns 422."""
        response = await client.post(
            "/auth/login",
            json={"password": "SecurePass123"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["detail"][0]["loc"] == ["body", "email"]
        assert "field required" in data["detail"][0]["msg"].lower()

    @pytest.mark.asyncio
    async def test_login_without_password(self, client: AsyncClient):
        """Test login without password returns 422."""
        response = await client.post(
            "/auth/login",
            json={
                "email": "login@example.com",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert data["detail"][0]["loc"] == ["body", "password"]
        assert "field required" in data["detail"][0]["msg"].lower()


class TestRefreshToken:
    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test successful access token refresh."""
        # Create user
        user = User(
            email="refresh@example.com",
            name="Refresh User",
            hashed_password=hash_password("SecurePass123"),
            is_verified=True,
            verification_token="123456",
        )
        db_session.add(user)
        await db_session.commit()

        # Login to get refresh token
        login_response = await client.post(
            "/auth/login",
            json={"email": "refresh@example.com", "password": "SecurePass123"},
        )
        refresh_token = login_response.cookies.get("refresh_token")
        assert refresh_token is not None

        # Refresh access token
        response = await client.post(
            "/auth/refresh", cookies={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify new refresh token is set in cookies
        assert "refresh_token" in response.cookies
        assert response.cookies["refresh_token"] != refresh_token

    @pytest.mark.asyncio
    async def test_refresh_token_missing(self, client: AsyncClient):
        """Test refresh without token returns 401."""
        response = await client.post("/auth/refresh")
        assert response.status_code == 401
        assert response.status_code == 401
        data = response.json()
        error_code = (
            data["detail"]["code"]
            if isinstance(data["detail"], dict)
            else data["detail"]
        )
        assert (
            "REFRESH_TOKEN_NOT_FOUND" == error_code
            or "token not found" in str(error_code).lower()
        )

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token returns 401."""
        response = await client.post(
            "/auth/refresh", cookies={"refresh_token": "invalid_token_string"}
        )
        assert response.status_code == 401
        # Expect generic 401 for invalid token
