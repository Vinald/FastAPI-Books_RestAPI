import uuid
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BookNotFoundException,
    OwnershipRequiredException,
    ValidationException
)
from app.models.book import Book
from app.models.user import User
from app.schemas.book import BookCreate, BookUpdate


class BookService:
    @staticmethod
    async def get_all_books(session: AsyncSession) -> List[Book]:
        statement = select(Book).order_by(desc(Book.created_at))
        result = await session.execute(statement)
        books = result.scalars().all()
        return list(books)

    @staticmethod
    async def get_user_books(user_id: int, session: AsyncSession) -> List[Book]:
        """Get all books owned by a specific user."""
        statement = select(Book).where(Book.user_id == user_id).order_by(desc(Book.created_at))
        result = await session.execute(statement)
        books = result.scalars().all()
        return list(books)

    @staticmethod
    async def get_book(book_uuid: uuid.UUID, session: AsyncSession) -> Optional[Book]:
        statement = select(Book).where(Book.uuid == book_uuid)
        result = await session.execute(statement)
        book = result.scalars().first()
        return book if book else None

    @staticmethod
    async def create_book(
            book_data: BookCreate,
            session: AsyncSession,
            user_id: Optional[int] = None
    ) -> Book:
        book_data_dict = book_data.model_dump()
        pd = book_data_dict.get("publish_date")

        if isinstance(pd, str):
            try:
                book_data_dict["publish_date"] = date.fromisoformat(pd)
            except ValueError:
                try:
                    book_data_dict["publish_date"] = datetime.fromisoformat(pd).date()
                except ValueError:
                    raise ValidationException(
                        "publish_date must be an ISO date or datetime string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
                    )
        elif isinstance(pd, datetime):
            book_data_dict["publish_date"] = pd.date()

        if user_id:
            book_data_dict["user_id"] = user_id

        new_book = Book(**book_data_dict)
        session.add(new_book)
        await session.commit()
        await session.refresh(new_book)
        return new_book

    async def update_book(
            self,
            book_uuid: uuid.UUID,
            update_data: BookUpdate,
            session: AsyncSession,
            current_user: Optional[User] = None
    ) -> Book:
        book_to_update = await self.get_book(book_uuid, session)

        if not book_to_update:
            raise BookNotFoundException(book_uuid)

        # Check ownership if user is authenticated
        if current_user and book_to_update.user_id:
            if book_to_update.user_id != current_user.id and current_user.role.value != "admin":
                raise OwnershipRequiredException("books")

        update_data_dict = update_data.model_dump(exclude_unset=True)

        pd = update_data_dict.get("publish_date")
        if pd is not None:
            if isinstance(pd, str):
                try:
                    update_data_dict["publish_date"] = date.fromisoformat(pd)
                except ValueError:
                    try:
                        update_data_dict["publish_date"] = datetime.fromisoformat(pd).date()
                    except ValueError:
                        raise ValidationException(
                            "publish_date must be an ISO date or datetime string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
                        )
            elif isinstance(pd, datetime):
                update_data_dict["publish_date"] = pd.date()

        for key, value in update_data_dict.items():
            setattr(book_to_update, key, value)
        session.add(book_to_update)
        await session.commit()
        await session.refresh(book_to_update)
        return book_to_update

    async def delete_book(
            self,
            book_uuid: uuid.UUID,
            session: AsyncSession,
            current_user: Optional[User] = None
    ):
        book_to_delete = await self.get_book(book_uuid, session)

        if not book_to_delete:
            raise BookNotFoundException(book_uuid)

        # Check ownership if user is authenticated
        if current_user and book_to_delete.user_id:
            if book_to_delete.user_id != current_user.id and current_user.role.value != "admin":
                raise OwnershipRequiredException("books")

        await session.delete(book_to_delete)
        await session.commit()
        return {"message": f"Book {book_uuid} deleted successfully"}
