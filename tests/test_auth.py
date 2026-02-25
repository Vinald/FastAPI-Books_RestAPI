"""
Tests for Authentication endpoints.
"""
import pytest
from httpx import AsyncClient

from app.core.security import create_verification_token, create_password_reset_token
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
        assert "email" in response.json()["detail"].lower()
        assert "already exists" in response.json()["detail"].lower()

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
        assert "username" in response.json()["detail"].lower()
        assert "already exists" in response.json()["detail"].lower()

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
    async def test_login_unverified_email(self, client: AsyncClient, unverified_user: User):
        """Test login with unverified email fails."""
        response = await client.post(
            "/api/v1.0/auth/login",
            data={
                "username": "unverified@example.com",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 403
        assert "verify your email" in response.json()["detail"].lower()

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


class TestEmailVerification:
    """Tests for email verification endpoints."""

    @pytest.mark.asyncio
    async def test_verify_email_success(self, client: AsyncClient, unverified_user: User):
        """Test successful email verification."""
        # Create a valid verification token
        verification_token = create_verification_token(unverified_user.email)

        response = await client.post(
            "/api/v1.0/auth/verify-email",
            json={"token": verification_token}
        )
        assert response.status_code == 200
        assert "verified successfully" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, client: AsyncClient):
        """Test email verification with invalid token fails."""
        response = await client.post(
            "/api/v1.0/auth/verify-email",
            json={"token": "invalid-token"}
        )
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_verify_email_already_verified(self, client: AsyncClient, test_user: User):
        """Test email verification for already verified user fails."""
        # test_user is already verified
        verification_token = create_verification_token(test_user.email)

        response = await client.post(
            "/api/v1.0/auth/verify-email",
            json={"token": verification_token}
        )
        assert response.status_code == 400
        assert "already verified" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_verify_email_nonexistent_user(self, client: AsyncClient):
        """Test email verification for non-existent email fails."""
        verification_token = create_verification_token("nonexistent@example.com")

        response = await client.post(
            "/api/v1.0/auth/verify-email",
            json={"token": verification_token}
        )
        assert response.status_code == 404


class TestResendVerification:
    """Tests for POST /auth/resend-verification"""

    @pytest.mark.asyncio
    async def test_resend_verification_success(self, client: AsyncClient, unverified_user: User):
        """Test resend verification for unverified user."""
        response = await client.post(
            "/api/v1.0/auth/resend-verification",
            json={"email": unverified_user.email}
        )
        # Response should be 200 or 503 depending on email service availability
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            assert "sent" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_resend_verification_already_verified(self, client: AsyncClient, test_user: User):
        """Test resend verification for already verified user fails."""
        response = await client.post(
            "/api/v1.0/auth/resend-verification",
            json={"email": test_user.email}
        )
        assert response.status_code == 400
        assert "already verified" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_resend_verification_nonexistent_email(self, client: AsyncClient):
        """Test resend verification for non-existent email (returns success for security)."""
        response = await client.post(
            "/api/v1.0/auth/resend-verification",
            json={"email": "nonexistent@example.com"}
        )
        # Should return success to prevent email enumeration
        assert response.status_code == 200
        assert "sent" in response.json()["message"].lower()


class TestForgotPassword:
    """Tests for POST /auth/forgot-password"""

    @pytest.mark.asyncio
    async def test_forgot_password_success(self, client: AsyncClient, test_user: User):
        """Test forgot password request."""
        response = await client.post(
            "/api/v1.0/auth/forgot-password",
            json={"email": test_user.email}
        )
        # Response should be 200 or 503 depending on email service availability
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            assert "sent" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_email(self, client: AsyncClient):
        """Test forgot password for non-existent email (returns success for security)."""
        response = await client.post(
            "/api/v1.0/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )
        # Should return success to prevent email enumeration
        assert response.status_code == 200
        assert "sent" in response.json()["message"].lower()


class TestResetPassword:
    """Tests for POST /auth/reset-password"""

    @pytest.mark.asyncio
    async def test_reset_password_success(self, client: AsyncClient, test_user: User):
        """Test successful password reset."""
        reset_token = create_password_reset_token(test_user.email)

        response = await client.post(
            "/api/v1.0/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 200
        assert "reset successfully" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, client: AsyncClient):
        """Test password reset with invalid token fails."""
        response = await client.post(
            "/api/v1.0/auth/reset-password",
            json={
                "token": "invalid-token",
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_reset_password_short_password(self, client: AsyncClient, test_user: User):
        """Test password reset with short password fails."""
        reset_token = create_password_reset_token(test_user.email)

        response = await client.post(
            "/api/v1.0/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "short"  # Too short
            }
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_reset_password_nonexistent_user(self, client: AsyncClient):
        """Test password reset for non-existent user fails."""
        reset_token = create_password_reset_token("nonexistent@example.com")

        response = await client.post(
            "/api/v1.0/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_login_after_password_reset(self, client: AsyncClient, test_user: User):
        """Test that user can login with new password after reset."""
        reset_token = create_password_reset_token(test_user.email)
        new_password = "brandnewpassword123"

        # Reset password
        reset_response = await client.post(
            "/api/v1.0/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": new_password
            }
        )
        assert reset_response.status_code == 200

        # Login with new password
        login_response = await client.post(
            "/api/v1.0/auth/login",
            data={
                "username": test_user.email,
                "password": new_password
            }
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
