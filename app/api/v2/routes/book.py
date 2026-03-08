"""
V2 Book Routes with Pagination and Advanced Features

Enhanced book endpoints with:
- Pagination support
- Advanced filtering
- Search functionality
- Sorting options
"""
import uuid
from typing import Optional

from fastapi import APIRouter, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.exceptions import BookNotFoundException
from app.core.responses import PUBLIC_RESPONSES, AUTH_RESPONSES, CREATE_RESPONSES
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.book import BookCreate, BookOut, BookUpdate
from app.schemas.pagination import PaginatedResponse
from app.services.book_service import BookService

book_router = APIRouter(tags=["Books"], prefix="/books")

book_service = BookService()


@book_router.get(
    "/",
    response_model=PaginatedResponse[BookOut],
    status_code=status.HTTP_200_OK,
    summary="Get all books (paginated)",
    description="Retrieve all books with pagination, search, and sorting support.",
    responses={500: PUBLIC_RESPONSES[500]}
)
async def get_books(
        session: AsyncSession = Depends(get_session),
        page: int = Query(default=1, ge=1, description="Page number"),
        page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
        search: Optional[str] = Query(default=None, description="Search in title and author"),
        sort_by: Optional[str] = Query(default="created_at", description="Sort by field"),
        sort_order: str = Query(default="desc", pattern="^(asc|desc)$", description="Sort direction")
) -> PaginatedResponse[BookOut]:
    """Get all books with pagination"""
    books, total = await book_service.get_all_books_paginated(
        session=session,
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return PaginatedResponse.create(
        items=books,
        total=total,
        page=page,
        page_size=page_size
    )


@book_router.get(
    "/my-books",
    response_model=PaginatedResponse[BookOut],
    status_code=status.HTTP_200_OK,
    summary="Get my books (paginated)",
    description="Get all books owned by the current authenticated user with pagination.",
    responses=AUTH_RESPONSES
)
async def get_my_books(
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user),
        page: int = Query(default=1, ge=1, description="Page number"),
        page_size: int = Query(default=10, ge=1, le=100, description="Items per page")
) -> PaginatedResponse[BookOut]:
    """Get all books owned by the current user with pagination"""
    books, total = await book_service.get_user_books_paginated(
        user_id=current_user.id,
        session=session,
        page=page,
        page_size=page_size
    )
    return PaginatedResponse.create(
        items=books,
        total=total,
        page=page,
        page_size=page_size
    )


@book_router.get(
    "/{book_uuid}",
    response_model=BookOut,
    status_code=status.HTTP_200_OK,
    summary="Get book by UUID",
    description="Get a single book by its UUID.",
    responses=PUBLIC_RESPONSES
)
async def get_book(book_uuid: uuid.UUID, session: AsyncSession = Depends(get_session)) -> BookOut:
    """Get a single book by UUID"""
    book = await book_service.get_book(book_uuid, session)
    if not book:
        raise BookNotFoundException(book_uuid)
    return book


@book_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=BookOut,
    summary="Create a book",
    description="Create a new book. The book will be associated with the authenticated user.",
    responses=CREATE_RESPONSES
)
async def create_book(
        book: BookCreate,
        session: AsyncSession = Depends(get_session),
        current_user: Optional[User] = Depends(get_current_active_user)
) -> BookOut:
    """Create a new book (associated with authenticated user)"""
    new_book = await book_service.create_book(book, session, user_id=current_user.id if current_user else None)
    return new_book


@book_router.patch(
    "/{book_uuid}",
    response_model=BookOut,
    status_code=status.HTTP_200_OK,
    summary="Update a book",
    description="Update a book by UUID. Only the owner or admin can update.",
    responses=AUTH_RESPONSES
)
async def update_book(
        book_uuid: uuid.UUID,
        book_update_data: BookUpdate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> BookOut:
    """Update a book by UUID (only owner can update)"""
    updated_book = await book_service.update_book(book_uuid, book_update_data, session, current_user)
    return updated_book


@book_router.delete(
    "/{book_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book",
    description="Delete a book by UUID. Only the owner or admin can delete.",
    responses=AUTH_RESPONSES
)
async def delete_book(
        book_uuid: uuid.UUID,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> None:
    """Delete a book by UUID (only owner can delete)"""
    await book_service.delete_book(book_uuid, session, current_user)
