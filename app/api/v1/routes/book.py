from fastapi import APIRouter, status, Depends, HTTPException
from app.schemas.book import BookCreate, BookOut, BookUpdate
from typing import List
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.book_service import BookService
import uuid

book_router = APIRouter(tags=["Books"], prefix="/books")

book_service = BookService()


@book_router.get("/", response_model=List[BookOut], status_code=status.HTTP_200_OK)
async def get_books(session: AsyncSession = Depends(get_db)) -> List[BookOut]:
    """Get all books"""
    books = await book_service.get_all_books(session)
    return books


@book_router.get("/{book_uuid}", response_model=BookOut, status_code=status.HTTP_200_OK)
async def get_book(
    book_uuid: uuid.UUID, session: AsyncSession = Depends(get_db)
) -> BookOut:
    """Get a single book by UUID"""
    book = await book_service.get_book(book_uuid, session)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Book {book_uuid} not found"
        )
    return book


@book_router.post("/", status_code=status.HTTP_201_CREATED, response_model=BookOut)
async def create_book(
    book: BookCreate, session: AsyncSession = Depends(get_db)
) -> BookOut:
    """Create a new book"""
    new_book = await book_service.create_book(book, session)
    return new_book


@book_router.patch(
    "/{book_uuid}", response_model=BookOut, status_code=status.HTTP_200_OK
)
async def update_book(
    book_uuid: uuid.UUID,
    book_update_data: BookUpdate,
    session: AsyncSession = Depends(get_db),
) -> BookOut:
    """Update a book by UUID"""
    updated_book = await book_service.update_book(book_uuid, book_update_data, session)
    return updated_book


@book_router.delete("/{book_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_uuid: uuid.UUID, session: AsyncSession = Depends(get_db)
) -> None:
    """Delete a book by UUID"""
    await book_service.delete_book(book_uuid, session)
