import uuid
from typing import List, Optional

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.book import BookCreate, BookOut, BookUpdate
from app.services.book_service import BookService

book_router = APIRouter(tags=["Books"], prefix="/books")

book_service = BookService()


@book_router.get("/", response_model=List[BookOut], status_code=status.HTTP_200_OK)
async def get_books(session: AsyncSession = Depends(get_session)) -> List[BookOut]:
    """Get all books"""
    books = await book_service.get_all_books(session)
    return books


@book_router.get("/my-books", response_model=List[BookOut], status_code=status.HTTP_200_OK)
async def get_my_books(
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> List[BookOut]:
    """Get all books owned by the current user"""
    books = await book_service.get_user_books(current_user.id, session)
    return books


@book_router.get("/{book_uuid}", response_model=BookOut, status_code=status.HTTP_200_OK)
async def get_book(book_uuid: uuid.UUID, session: AsyncSession = Depends(get_session)) -> BookOut:
    """Get a single book by UUID"""
    book = await book_service.get_book(book_uuid, session)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Book {book_uuid} not found"
        )
    return book


@book_router.post("/", status_code=status.HTTP_201_CREATED, response_model=BookOut)
async def create_book(
        book: BookCreate,
        session: AsyncSession = Depends(get_session),
        current_user: Optional[User] = Depends(get_current_active_user)
) -> BookOut:
    """Create a new book (associated with authenticated user)"""
    new_book = await book_service.create_book(book, session, user_id=current_user.id if current_user else None)
    return new_book


@book_router.patch("/{book_uuid}", response_model=BookOut, status_code=status.HTTP_200_OK)
async def update_book(
        book_uuid: uuid.UUID,
        book_update_data: BookUpdate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> BookOut:
    """Update a book by UUID (only owner can update)"""
    updated_book = await book_service.update_book(book_uuid, book_update_data, session, current_user)
    return updated_book


@book_router.delete("/{book_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
        book_uuid: uuid.UUID,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> None:
    """Delete a book by UUID (only owner can delete)"""
    await book_service.delete_book(book_uuid, session, current_user)
