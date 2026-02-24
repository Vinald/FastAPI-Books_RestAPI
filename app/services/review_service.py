import uuid
from typing import List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    BookNotFoundException,
    UserNotFoundException,
    ReviewNotFoundException,
    DuplicateReviewException,
    OwnershipRequiredException
)
from app.models.book import Book
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewUpdate


class ReviewService:
    @staticmethod
    async def get_all_reviews(session: AsyncSession) -> List[Review]:
        """Get all reviews."""
        statement = select(Review).options(
            selectinload(Review.reviewer),
            selectinload(Review.book)
        ).order_by(desc(Review.created_at))
        result = await session.execute(statement)
        return list(result.scalars().all())

    @staticmethod
    async def get_review_by_uuid(review_uuid: uuid.UUID, session: AsyncSession) -> Optional[Review]:
        """Get a review by UUID."""
        statement = select(Review).where(Review.uuid == review_uuid).options(
            selectinload(Review.reviewer),
            selectinload(Review.book)
        )
        result = await session.execute(statement)
        return result.scalars().first()

    @staticmethod
    async def get_reviews_by_book(book_uuid: uuid.UUID, session: AsyncSession) -> List[Review]:
        """Get all reviews for a specific book."""
        book_statement = select(Book).where(Book.uuid == book_uuid)
        book_result = await session.execute(book_statement)
        book = book_result.scalars().first()

        if not book:
            raise BookNotFoundException(book_uuid)

        statement = select(Review).where(Review.book_id == book.id).options(
            selectinload(Review.reviewer)
        ).order_by(desc(Review.created_at))
        result = await session.execute(statement)
        return list(result.scalars().all())

    @staticmethod
    async def get_reviews_by_user(user_uuid: uuid.UUID, session: AsyncSession) -> List[Review]:
        """Get all reviews by a specific user."""
        user_statement = select(User).where(User.uuid == user_uuid)
        user_result = await session.execute(user_statement)
        user = user_result.scalars().first()

        if not user:
            raise UserNotFoundException(user_uuid)

        statement = select(Review).where(Review.user_id == user.id).options(
            selectinload(Review.book)
        ).order_by(desc(Review.created_at))
        result = await session.execute(statement)
        return list(result.scalars().all())

    @staticmethod
    async def get_my_reviews(current_user: User, session: AsyncSession) -> List[Review]:
        """Get all reviews by the current user."""
        statement = select(Review).where(Review.user_id == current_user.id).options(
            selectinload(Review.book)
        ).order_by(desc(Review.created_at))
        result = await session.execute(statement)
        return list(result.scalars().all())

    @staticmethod
    async def create_review(
            book_uuid: uuid.UUID,
            review_data: ReviewCreate,
            current_user: User,
            session: AsyncSession
    ) -> Review:
        """Create a new review for a book."""
        book_statement = select(Book).where(Book.uuid == book_uuid)
        book_result = await session.execute(book_statement)
        book = book_result.scalars().first()

        if not book:
            raise BookNotFoundException(book_uuid)

        # Check if user already reviewed this book
        existing_review_statement = select(Review).where(
            Review.book_id == book.id,
            Review.user_id == current_user.id
        )
        existing_result = await session.execute(existing_review_statement)
        existing_review = existing_result.scalars().first()

        if existing_review:
            raise DuplicateReviewException()

        new_review = Review(
            content=review_data.content,
            rating=review_data.rating,
            user_id=current_user.id,
            book_id=book.id
        )

        session.add(new_review)
        await session.commit()
        await session.refresh(new_review)

        # Load relationships
        statement = select(Review).where(Review.id == new_review.id).options(
            selectinload(Review.reviewer),
            selectinload(Review.book)
        )
        result = await session.execute(statement)
        return result.scalars().first()

    async def update_review(
            self,
            review_uuid: uuid.UUID,
            review_data: ReviewUpdate,
            current_user: User,
            session: AsyncSession
    ) -> Review:
        """Update a review."""
        review = await self.get_review_by_uuid(review_uuid, session)

        if not review:
            raise ReviewNotFoundException(review_uuid)

        # Check if user owns this review or is admin
        if review.user_id != current_user.id and current_user.role.value != "admin":
            raise OwnershipRequiredException("reviews")

        update_data = review_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(review, key, value)

        session.add(review)
        await session.commit()
        await session.refresh(review)

        return review

    async def delete_review(
            self,
            review_uuid: uuid.UUID,
            current_user: User,
            session: AsyncSession
    ) -> dict:
        """Delete a review."""
        review = await self.get_review_by_uuid(review_uuid, session)

        if not review:
            raise ReviewNotFoundException(review_uuid)

        # Check if user owns this review or is admin
        if review.user_id != current_user.id and current_user.role.value != "admin":
            raise OwnershipRequiredException("reviews")

        await session.delete(review)
        await session.commit()

        return {"message": f"Review {review_uuid} deleted successfully"}

    @staticmethod
    async def get_book_average_rating(book_uuid: uuid.UUID, session: AsyncSession) -> dict:
        """Get average rating for a book."""
        book_statement = select(Book).where(Book.uuid == book_uuid)
        book_result = await session.execute(book_statement)
        book = book_result.scalars().first()

        if not book:
            raise BookNotFoundException(book_uuid)

        statement = select(Review).where(Review.book_id == book.id)
        result = await session.execute(statement)
        reviews = list(result.scalars().all())

        if not reviews:
            return {
                "book_uuid": str(book_uuid),
                "average_rating": None,
                "total_reviews": 0
            }

        total_rating = sum(r.rating for r in reviews)
        average = round(total_rating / len(reviews), 2)

        return {
            "book_uuid": str(book_uuid),
            "average_rating": average,
            "total_reviews": len(reviews)
        }
