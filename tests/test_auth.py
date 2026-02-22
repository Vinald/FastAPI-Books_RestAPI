"""
Tests for Authentication endpoints.
"""
import pytest
from httpx import AsyncClient

from app.models.user import User


class TestAuthRegister:
    """Tests for POST /auth/register"""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1.0/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "first_name": "New",
                "last_name": "User",
                "password": "newpassword123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"  # Default role
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with existing email fails."""
        response = await client.post(
            "/api/v1.0/auth/register",
            json={
                "username": "anotheruser",
                "email": "test@example.com",  # Already exists
                "first_name": "Another",
                "last_name": "User",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, test_user: User):
        """Test registration with existing username fails."""
        response = await client.post(
            "/api/v1.0/auth/register",
            json={
                "username": "testuser",  # Already exists
                "email": "another@example.com",
                "first_name": "Another",
                "last_name": "User",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with short password fails."""
        response = await client.post(
            "/api/v1.0/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "first_name": "New",
                "last_name": "User",
                "password": "short"  # Too short
            }
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        response = await client.post(
            "/api/v1.0/auth/register",
            json={
                "username": "newuser",
                "email": "not-an-email",
                "first_name": "New",
                "last_name": "User",
                "password": "password123"
            }
        )
        assert response.status_code == 422


class TestAuthLogin:
    """Tests for POST /auth/login"""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login."""
        response = await client.post(
            "/api/v1.0/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password fails."""
        response = await client.post(
            "/api/v1.0/auth/login",
            data={
                "username": "test@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user fails."""
        response = await client.post(
            "/api/v1.0/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 401


class TestAuthRefresh:
    """Tests for POST /auth/refresh"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, test_user: User):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = await client.post(
            "/api/v1.0/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Then refresh
        response = await client.post(
            "/api/v1.0/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token fails."""
        response = await client.post(
            "/api/v1.0/auth/refresh",
            json={"refresh_token": "invalid-token"}
        )
        assert response.status_code == 401


class TestAuthLogout:
    """Tests for POST /auth/logout"""

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient, auth_headers: dict):
        """Test successful logout."""
        response = await client.post(
            "/api/v1.0/auth/logout",
            headers=auth_headers
        )
        # May return 200 or 503 depending on Redis availability
        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_logout_no_token(self, client: AsyncClient):
        """Test logout without token fails."""
        response = await client.post("/api/v1.0/auth/logout")
        assert response.status_code == 401


class TestAuthLogoutAll:
    """Tests for POST /auth/logout-all"""

    @pytest.mark.asyncio
    async def test_logout_all_success(self, client: AsyncClient, auth_headers: dict):
        """Test successful logout from all devices."""
        response = await client.post(
            "/api/v1.0/auth/logout-all",
            headers=auth_headers
        )
        # May return 200 or 503 depending on Redis availability
        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_logout_all_no_token(self, client: AsyncClient):
        """Test logout-all without token fails."""
        response = await client.post("/api/v1.0/auth/logout-all")
        assert response.status_code == 401
