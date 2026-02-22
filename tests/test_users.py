"""
Tests for User endpoints.
"""
import pytest
from httpx import AsyncClient

from app.models.user import User


class TestGetCurrentUser:
    """Tests for GET /users/me"""

    @pytest.mark.asyncio
    async def test_get_me_success(self, client: AsyncClient, auth_headers: dict, test_user: User):
        """Test getting current user profile."""
        response = await client.get("/api/v1.0/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "books" in data

    @pytest.mark.asyncio
    async def test_get_me_no_token(self, client: AsyncClient):
        """Test getting current user without token fails."""
        response = await client.get("/api/v1.0/users/me")
        assert response.status_code == 401


class TestGetAllUsers:
    """Tests for GET /users/"""

    @pytest.mark.asyncio
    async def test_get_all_users(self, client: AsyncClient, test_user: User):
        """Test getting all users."""
        response = await client.get("/api/v1.0/users/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestGetUserByUUID:
    """Tests for GET /users/{user_uuid}"""

    @pytest.mark.asyncio
    async def test_get_user_by_uuid_success(self, client: AsyncClient, test_user: User):
        """Test getting user by UUID."""
        response = await client.get(f"/api/v1.0/users/{test_user.uuid}")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_user_by_uuid_not_found(self, client: AsyncClient):
        """Test getting nonexistent user returns 404."""
        import uuid
        fake_uuid = uuid.uuid4()
        response = await client.get(f"/api/v1.0/users/{fake_uuid}")
        assert response.status_code == 404


class TestGetUserByEmail:
    """Tests for GET /users/email/{email}"""

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, client: AsyncClient, test_user: User):
        """Test getting user by email."""
        response = await client.get("/api/v1.0/users/email/test@example.com")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, client: AsyncClient):
        """Test getting nonexistent email returns 404."""
        response = await client.get("/api/v1.0/users/email/nonexistent@example.com")
        assert response.status_code == 404


class TestUpdateUser:
    """Tests for PATCH /users/{user_uuid}"""

    @pytest.mark.asyncio
    async def test_update_own_profile(self, client: AsyncClient, auth_headers: dict, test_user: User):
        """Test updating own profile."""
        response = await client.patch(
            f"/api/v1.0/users/{test_user.uuid}",
            headers=auth_headers,
            json={"first_name": "Updated"}
        )
        assert response.status_code == 200
        assert response.json()["first_name"] == "Updated"

    @pytest.mark.asyncio
    async def test_update_other_user_forbidden(
            self, client: AsyncClient, auth_headers: dict, test_admin: User
    ):
        """Test updating another user's profile is forbidden for regular users."""
        response = await client.patch(
            f"/api/v1.0/users/{test_admin.uuid}",
            headers=auth_headers,
            json={"first_name": "Hacked"}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_update_any_user(
            self, client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """Test admin can update any user."""
        response = await client.patch(
            f"/api/v1.0/users/{test_user.uuid}",
            headers=admin_headers,
            json={"first_name": "AdminUpdated"}
        )
        assert response.status_code == 200
        assert response.json()["first_name"] == "AdminUpdated"

    @pytest.mark.asyncio
    async def test_update_no_token(self, client: AsyncClient, test_user: User):
        """Test updating without token fails."""
        response = await client.patch(
            f"/api/v1.0/users/{test_user.uuid}",
            json={"first_name": "NoToken"}
        )
        assert response.status_code == 401


class TestDeleteUser:
    """Tests for DELETE /users/{user_uuid}"""

    @pytest.mark.asyncio
    async def test_delete_own_account(self, client: AsyncClient, test_user: User):
        """Test deleting own account."""
        # Login first
        login_response = await client.post(
            "/api/v1.0/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete(
            f"/api/v1.0/users/{test_user.uuid}",
            headers=headers
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_delete_other_user_forbidden(
            self, client: AsyncClient, auth_headers: dict, test_admin: User
    ):
        """Test deleting another user is forbidden for regular users."""
        response = await client.delete(
            f"/api/v1.0/users/{test_admin.uuid}",
            headers=auth_headers
        )
        assert response.status_code == 403


class TestChangePassword:
    """Tests for POST /users/change-password"""

    @pytest.mark.asyncio
    async def test_change_password_success(self, client: AsyncClient, auth_headers: dict):
        """Test successful password change."""
        response = await client.post(
            "/api/v1.0/users/change-password",
            headers=auth_headers,
            json={
                "current_password": "testpassword123",
                "new_password": "newpassword456"
            }
        )
        assert response.status_code == 200
        assert "successfully" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, client: AsyncClient, auth_headers: dict):
        """Test password change with wrong current password fails."""
        response = await client.post(
            "/api/v1.0/users/change-password",
            headers=auth_headers,
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword456"
            }
        )
        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_change_password_no_token(self, client: AsyncClient):
        """Test password change without token fails."""
        response = await client.post(
            "/api/v1.0/users/change-password",
            json={
                "current_password": "testpassword123",
                "new_password": "newpassword456"
            }
        )
        assert response.status_code == 401
