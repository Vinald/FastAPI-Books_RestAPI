"""
Tests for Admin endpoints.
"""
import pytest
from httpx import AsyncClient

from app.models.user import User


class TestAdminCreateUser:
    """Tests for POST /admin/users"""

    @pytest.mark.asyncio
    async def test_admin_create_user_success(self, client: AsyncClient, admin_headers: dict):
        """Test admin can create user with any role."""
        response = await client.post(
            "/api/v1.0/admin/users",
            headers=admin_headers,
            json={
                "username": "newadminuser",
                "email": "newadmin@example.com",
                "first_name": "New",
                "last_name": "Admin",
                "password": "password123",
                "role": "moderator"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "moderator"

    @pytest.mark.asyncio
    async def test_admin_create_admin_user(self, client: AsyncClient, admin_headers: dict):
        """Test admin can create another admin."""
        response = await client.post(
            "/api/v1.0/admin/users",
            headers=admin_headers,
            json={
                "username": "anotheradmin",
                "email": "anotheradmin@example.com",
                "first_name": "Another",
                "last_name": "Admin",
                "password": "password123",
                "role": "admin"
            }
        )
        assert response.status_code == 201
        assert response.json()["role"] == "admin"

    @pytest.mark.asyncio
    async def test_non_admin_cannot_create_user(self, client: AsyncClient, auth_headers: dict):
        """Test regular user cannot use admin endpoint."""
        response = await client.post(
            "/api/v1.0/admin/users",
            headers=auth_headers,
            json={
                "username": "hacker",
                "email": "hacker@example.com",
                "first_name": "Hacker",
                "last_name": "User",
                "password": "password123",
                "role": "admin"
            }
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_create_duplicate_email(
            self, client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """Test admin cannot create user with existing email."""
        response = await client.post(
            "/api/v1.0/admin/users",
            headers=admin_headers,
            json={
                "username": "uniqueuser",
                "email": "test@example.com",  # Already exists
                "first_name": "Test",
                "last_name": "User",
                "password": "password123",
                "role": "user"
            }
        )
        assert response.status_code == 400


class TestAdminUpdateUser:
    """Tests for PATCH /admin/users/{user_uuid}"""

    @pytest.mark.asyncio
    async def test_admin_update_user(
            self, client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """Test admin can update any user."""
        response = await client.patch(
            f"/api/v1.0/admin/users/{test_user.uuid}",
            headers=admin_headers,
            json={"first_name": "AdminChanged"}
        )
        assert response.status_code == 200
        assert response.json()["first_name"] == "AdminChanged"

    @pytest.mark.asyncio
    async def test_admin_update_user_role(
            self, client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """Test admin can update user role."""
        response = await client.patch(
            f"/api/v1.0/admin/users/{test_user.uuid}",
            headers=admin_headers,
            json={"role": "moderator"}
        )
        assert response.status_code == 200
        assert response.json()["role"] == "moderator"

    @pytest.mark.asyncio
    async def test_non_admin_cannot_update(
            self, client: AsyncClient, auth_headers: dict, test_admin: User
    ):
        """Test regular user cannot use admin update endpoint."""
        response = await client.patch(
            f"/api/v1.0/admin/users/{test_admin.uuid}",
            headers=auth_headers,
            json={"first_name": "Hacked"}
        )
        assert response.status_code == 403


class TestAdminDeleteUser:
    """Tests for DELETE /admin/users/{user_uuid}"""

    @pytest.mark.asyncio
    async def test_admin_delete_user(
            self, client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """Test admin can delete any user."""
        response = await client.delete(
            f"/api/v1.0/admin/users/{test_user.uuid}",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_non_admin_cannot_delete(
            self, client: AsyncClient, auth_headers: dict, test_admin: User
    ):
        """Test regular user cannot use admin delete endpoint."""
        response = await client.delete(
            f"/api/v1.0/admin/users/{test_admin.uuid}",
            headers=auth_headers
        )
        assert response.status_code == 403


class TestAdminChangeRole:
    """Tests for PATCH /admin/users/{user_uuid}/role"""

    @pytest.mark.asyncio
    async def test_admin_change_role(
            self, client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """Test admin can change user role."""
        response = await client.patch(
            f"/api/v1.0/admin/users/{test_user.uuid}/role",
            headers=admin_headers,
            params={"new_role": "moderator"}
        )
        assert response.status_code == 200
        assert response.json()["role"] == "moderator"

    @pytest.mark.asyncio
    async def test_admin_promote_to_admin(
            self, client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """Test admin can promote user to admin."""
        response = await client.patch(
            f"/api/v1.0/admin/users/{test_user.uuid}/role",
            headers=admin_headers,
            params={"new_role": "admin"}
        )
        assert response.status_code == 200
        assert response.json()["role"] == "admin"

    @pytest.mark.asyncio
    async def test_non_admin_cannot_change_role(
            self, client: AsyncClient, auth_headers: dict, test_admin: User
    ):
        """Test regular user cannot change roles."""
        response = await client.patch(
            f"/api/v1.0/admin/users/{test_admin.uuid}/role",
            headers=auth_headers,
            params={"new_role": "user"}
        )
        assert response.status_code == 403


class TestAdminActivateUser:
    """Tests for PATCH /admin/users/{user_uuid}/activate"""

    @pytest.mark.asyncio
    async def test_admin_deactivate_user(
            self, client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """Test admin can deactivate user."""
        response = await client.patch(
            f"/api/v1.0/admin/users/{test_user.uuid}/activate",
            headers=admin_headers,
            params={"is_active": False}
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    @pytest.mark.asyncio
    async def test_admin_activate_user(
            self, client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """Test admin can activate user."""
        response = await client.patch(
            f"/api/v1.0/admin/users/{test_user.uuid}/activate",
            headers=admin_headers,
            params={"is_active": True}
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is True

    @pytest.mark.asyncio
    async def test_non_admin_cannot_activate(
            self, client: AsyncClient, auth_headers: dict, test_admin: User
    ):
        """Test regular user cannot activate/deactivate users."""
        response = await client.patch(
            f"/api/v1.0/admin/users/{test_admin.uuid}/activate",
            headers=auth_headers,
            params={"is_active": False}
        )
        assert response.status_code == 403
