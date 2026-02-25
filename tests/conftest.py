"""
Pytest configuration and fixtures for testing the FastAPI Books API.
"""
import asyncio
from datetime import date
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_session
from app.core.security import get_password_hash
from app.main import app
from app.models.book import Book
from app.models.user import User, UserRole

# Test database URL - using SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database session override."""

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password=get_password_hash("testpassword123"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True  # User must be verified to login
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    admin = User(
        username="adminuser",
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password=get_password_hash("adminpassword123"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True  # User must be verified to login
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def test_moderator(db_session: AsyncSession) -> User:
    """Create a test moderator user."""
    moderator = User(
        username="moduser",
        email="mod@example.com",
        first_name="Mod",
        last_name="User",
        password=get_password_hash("modpassword123"),
        role=UserRole.MODERATOR,
        is_active=True,
        is_verified=True  # User must be verified to login
    )
    db_session.add(moderator)
    await db_session.commit()
    await db_session.refresh(moderator)
    return moderator


@pytest_asyncio.fixture
async def unverified_user(db_session: AsyncSession) -> User:
    """Create an unverified test user for email verification tests."""
    user = User(
        username="unverifieduser",
        email="unverified@example.com",
        first_name="Unverified",
        last_name="User",
        password=get_password_hash("testpassword123"),
        role=UserRole.USER,
        is_active=True,
        is_verified=False  # User is not verified
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_book(db_session: AsyncSession, test_user: User) -> Book:
    """Create a test book."""
    book = Book(
        title="Test Book",
        author="Test Author",
        publisher="Test Publisher",
        publish_date=date(2024, 1, 15),
        pages=300,
        language="English",
        user_id=test_user.id
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)
    return book


@pytest_asyncio.fixture
async def user_token(client: AsyncClient, test_user: User) -> str:
    """Get authentication token for test user."""
    response = await client.post(
        "/api/v1.0/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpassword123"
        }
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, test_admin: User) -> str:
    """Get authentication token for admin user."""
    response = await client.post(
        "/api/v1.0/auth/login",
        data={
            "username": "admin@example.com",
            "password": "adminpassword123"
        }
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(user_token: str) -> dict:
    """Get authorization headers for test user."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest_asyncio.fixture
async def admin_headers(admin_token: str) -> dict:
    """Get authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}
