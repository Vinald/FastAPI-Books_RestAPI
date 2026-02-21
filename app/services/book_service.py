from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.schemas.book import BookCreate, BookUpdate
from app.models.book import Book
from fastapi import HTTPException, status
from datetime import date, datetime
import uuid


class BookService:
    @staticmethod
    async def get_all_books(session: AsyncSession):
        statement = select(Book).order_by(desc(Book.created_at))
        result = await session.execute(statement)
        books = result.scalars().all()
        return books

    @staticmethod
    async def get_book(book_uuid: uuid.UUID, session: AsyncSession):
        statement = select(Book).where(Book.uuid == book_uuid)
        result = await session.execute(statement)
        book = result.scalars().first()
        return book if book else None

    @staticmethod
    async def create_book(book_data: BookCreate, session: AsyncSession):
        book_data_dict = book_data.model_dump()
        pd = book_data_dict.get("publish_date")

        if isinstance(pd, str):
            # Accept ISO date or ISO datetime strings
            try:
                book_data_dict["publish_date"] = date.fromisoformat(pd)
            except ValueError:
                try:
                    book_data_dict["publish_date"] = datetime.fromisoformat(pd).date()
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="publish_date must be an ISO date or datetime string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
                    )
        elif isinstance(pd, datetime):
            book_data_dict["publish_date"] = pd.date()
        # if already a date or missing, leave as is

        new_book = Book(**book_data_dict)
        session.add(new_book)
        await session.commit()
        await session.refresh(new_book)
        return new_book

    async def update_book(
        self, book_uuid: uuid.UUID, update_data: BookUpdate, session: AsyncSession
    ):
        book_to_update = await self.get_book(book_uuid, session)

        if not book_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book {book_uuid} not found",
            )

        update_data_dict = update_data.model_dump(exclude_unset=True)

        pd = update_data_dict.get("publish_date")
        if pd is not None:
            if isinstance(pd, str):
                try:
                    update_data_dict["publish_date"] = date.fromisoformat(pd)
                except ValueError:
                    try:
                        update_data_dict["publish_date"] = datetime.fromisoformat(
                            pd
                        ).date()
                    except ValueError:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="publish_date must be an ISO date or datetime string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
                        )
            elif isinstance(pd, datetime):
                update_data_dict["publish_date"] = pd.date()

        for key, value in update_data_dict.items():
            setattr(book_to_update, key, value)
        session.add(book_to_update)
        await session.commit()
        await session.refresh(book_to_update)
        return book_to_update

    async def delete_book(self, book_uuid: uuid.UUID, session: AsyncSession):
        book_to_delete = await self.get_book(book_uuid, session)

        if not book_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book {book_uuid} not found",
            )

        await session.delete(book_to_delete)
        await session.commit()
        return {"message": f"Book {book_uuid} deleted successfully"}
