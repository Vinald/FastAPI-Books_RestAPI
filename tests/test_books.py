"""
Tests for Book endpoints.
"""
import pytest
from httpx import AsyncClient

from app.models.book import Book


class TestGetAllBooks:
    """Tests for GET /books/"""

    @pytest.mark.asyncio
    async def test_get_all_books(self, client: AsyncClient, test_book: Book):
        """Test getting all books."""
        response = await client.get("/api/v1.0/books/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_all_books_empty(self, client: AsyncClient):
        """Test getting books when none exist."""
        response = await client.get("/api/v1.0/books/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestGetMyBooks:
    """Tests for GET /books/my-books"""

    @pytest.mark.asyncio
    async def test_get_my_books(self, client: AsyncClient, auth_headers: dict, test_book: Book):
        """Test getting current user's books."""
        response = await client.get("/api/v1.0/books/my-books", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["title"] == "Test Book"

    @pytest.mark.asyncio
    async def test_get_my_books_no_token(self, client: AsyncClient):
        """Test getting my books without token fails."""
        response = await client.get("/api/v1.0/books/my-books")
        assert response.status_code == 401


class TestGetBookByUUID:
    """Tests for GET /books/{book_uuid}"""

    @pytest.mark.asyncio
    async def test_get_book_by_uuid(self, client: AsyncClient, test_book: Book):
        """Test getting book by UUID."""
        response = await client.get(f"/api/v1.0/books/{test_book.uuid}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Book"
        assert data["author"] == "Test Author"

    @pytest.mark.asyncio
    async def test_get_book_not_found(self, client: AsyncClient):
        """Test getting nonexistent book returns 404."""
        import uuid
        fake_uuid = uuid.uuid4()
        response = await client.get(f"/api/v1.0/books/{fake_uuid}")
        assert response.status_code == 404


class TestCreateBook:
    """Tests for POST /books/"""

    @pytest.mark.asyncio
    async def test_create_book_success(self, client: AsyncClient, auth_headers: dict):
        """Test creating a book."""
        response = await client.post(
            "/api/v1.0/books/",
            headers=auth_headers,
            json={
                "title": "New Book",
                "author": "New Author",
                "publisher": "New Publisher",
                "publish_date": "2024-06-15",
                "pages": 250,
                "language": "English"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Book"
        assert data["author"] == "New Author"

    @pytest.mark.asyncio
    async def test_create_book_no_token(self, client: AsyncClient):
        """Test creating book without token fails."""
        response = await client.post(
            "/api/v1.0/books/",
            json={
                "title": "New Book",
                "author": "New Author",
                "publisher": "New Publisher",
                "publish_date": "2024-06-15",
                "pages": 250,
                "language": "English"
            }
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_book_missing_fields(self, client: AsyncClient, auth_headers: dict):
        """Test creating book with missing fields fails."""
        response = await client.post(
            "/api/v1.0/books/",
            headers=auth_headers,
            json={
                "title": "Incomplete Book"
                # Missing required fields
            }
        )
        assert response.status_code == 422


class TestUpdateBook:
    """Tests for PATCH /books/{book_uuid}"""

    @pytest.mark.asyncio
    async def test_update_own_book(self, client: AsyncClient, auth_headers: dict, test_book: Book):
        """Test updating own book."""
        response = await client.patch(
            f"/api/v1.0/books/{test_book.uuid}",
            headers=auth_headers,
            json={"title": "Updated Title"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_book_multiple_fields(
            self, client: AsyncClient, auth_headers: dict, test_book: Book
    ):
        """Test updating multiple book fields."""
        response = await client.patch(
            f"/api/v1.0/books/{test_book.uuid}",
            headers=auth_headers,
            json={
                "title": "New Title",
                "author": "New Author",
                "pages": 500
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["author"] == "New Author"
        assert data["pages"] == 500

    @pytest.mark.asyncio
    async def test_update_book_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test updating nonexistent book returns 404."""
        import uuid
        fake_uuid = uuid.uuid4()
        response = await client.patch(
            f"/api/v1.0/books/{fake_uuid}",
            headers=auth_headers,
            json={"title": "Ghost Book"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_book_no_token(self, client: AsyncClient, test_book: Book):
        """Test updating book without token fails."""
        response = await client.patch(
            f"/api/v1.0/books/{test_book.uuid}",
            json={"title": "No Auth"}
        )
        assert response.status_code == 401


class TestDeleteBook:
    """Tests for DELETE /books/{book_uuid}"""

    @pytest.mark.asyncio
    async def test_delete_own_book(self, client: AsyncClient, auth_headers: dict, test_book: Book):
        """Test deleting own book."""
        response = await client.delete(
            f"/api/v1.0/books/{test_book.uuid}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_delete_book_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test deleting nonexistent book returns 404."""
        import uuid
        fake_uuid = uuid.uuid4()
        response = await client.delete(
            f"/api/v1.0/books/{fake_uuid}",
            headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_book_no_token(self, client: AsyncClient, test_book: Book):
        """Test deleting book without token fails."""
        response = await client.delete(f"/api/v1.0/books/{test_book.uuid}")
        assert response.status_code == 401
