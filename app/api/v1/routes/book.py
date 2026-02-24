import uuid
from typing import List, Optional

from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.exceptions import BookNotFoundException
from app.core.responses import PUBLIC_RESPONSES, AUTH_RESPONSES, CREATE_RESPONSES
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.book import BookCreate, BookOut, BookUpdate
from app.services.book_service import BookService

book_router = APIRouter(tags=["Books"], prefix="/books")

book_service = BookService()


@book_router.get(
    "/",
    response_model=List[BookOut],
    status_code=status.HTTP_200_OK,
    summary="Get all books",
    description="Retrieve all books in the system.",
    responses={500: PUBLIC_RESPONSES[500]}
)
async def get_books(session: AsyncSession = Depends(get_session)) -> List[BookOut]:
    """Get all books"""
    books = await book_service.get_all_books(session)
    return books


@book_router.get(
    "/my-books",
    response_model=List[BookOut],
    status_code=status.HTTP_200_OK,
    summary="Get my books",
    description="Get all books owned by the current authenticated user.",
    responses=AUTH_RESPONSES
)
async def get_my_books(
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> List[BookOut]:
    """Get all books owned by the current user"""
    books = await book_service.get_user_books(current_user.id, session)
    return books


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
