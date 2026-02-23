import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.review import (
    ReviewCreate,
    ReviewUpdate,
    ReviewWithReviewer,
    ReviewWithBook,
    ReviewFull
)
from app.services.review_service import ReviewService

review_router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
    responses={
        404: {"description": "Review not found"},
        500: {"description": "Internal server error"}
    }
)

review_service = ReviewService()


@review_router.get(
    "/",
    response_model=List[ReviewFull],
    status_code=status.HTTP_200_OK,
    summary="Get all reviews",
    description="Retrieve all reviews with reviewer and book information."
)
async def get_all_reviews(
        session: AsyncSession = Depends(get_session)
) -> List[ReviewFull]:
    """Get all reviews."""
    return await review_service.get_all_reviews(session)


@review_router.get(
    "/my-reviews",
    response_model=List[ReviewWithBook],
    status_code=status.HTTP_200_OK,
    summary="Get my reviews",
    description="Get all reviews written by the current user."
)
async def get_my_reviews(
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> List[ReviewWithBook]:
    """Get current user's reviews."""
    return await review_service.get_my_reviews(current_user, session)


@review_router.get(
    "/book/{book_uuid}",
    response_model=List[ReviewWithReviewer],
    status_code=status.HTTP_200_OK,
    summary="Get reviews for a book",
    description="Get all reviews for a specific book."
)
async def get_reviews_by_book(
        book_uuid: uuid.UUID,
        session: AsyncSession = Depends(get_session)
) -> List[ReviewWithReviewer]:
    """Get all reviews for a book."""
    return await review_service.get_reviews_by_book(book_uuid, session)


@review_router.get(
    "/book/{book_uuid}/stats",
    status_code=status.HTTP_200_OK,
    summary="Get book rating stats",
    description="Get average rating and total reviews for a book."
)
async def get_book_rating_stats(
        book_uuid: uuid.UUID,
        session: AsyncSession = Depends(get_session)
) -> dict:
    """Get average rating for a book."""
    return await review_service.get_book_average_rating(book_uuid, session)


@review_router.get(
    "/user/{user_uuid}",
    response_model=List[ReviewWithBook],
    status_code=status.HTTP_200_OK,
    summary="Get reviews by user",
    description="Get all reviews written by a specific user."
)
async def get_reviews_by_user(
        user_uuid: uuid.UUID,
        session: AsyncSession = Depends(get_session)
) -> List[ReviewWithBook]:
    """Get all reviews by a user."""
    return await review_service.get_reviews_by_user(user_uuid, session)


@review_router.get(
    "/{review_uuid}",
    response_model=ReviewFull,
    status_code=status.HTTP_200_OK,
    summary="Get review by UUID",
    description="Get a specific review by its UUID."
)
async def get_review(
        review_uuid: uuid.UUID,
        session: AsyncSession = Depends(get_session)
) -> ReviewFull:
    """Get a review by UUID."""
    review = await review_service.get_review_by_uuid(review_uuid, session)
    if not review:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review {review_uuid} not found"
        )
    return review


@review_router.post(
    "/book/{book_uuid}",
    response_model=ReviewFull,
    status_code=status.HTTP_201_CREATED,
    summary="Create a review",
    description="Create a new review for a book. Users can only review a book once."
)
async def create_review(
        book_uuid: uuid.UUID,
        review_data: ReviewCreate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> ReviewFull:
    """Create a new review for a book."""
    return await review_service.create_review(book_uuid, review_data, current_user, session)


@review_router.patch(
    "/{review_uuid}",
    response_model=ReviewFull,
    status_code=status.HTTP_200_OK,
    summary="Update a review",
    description="Update an existing review. Users can only update their own reviews."
)
async def update_review(
        review_uuid: uuid.UUID,
        review_data: ReviewUpdate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> ReviewFull:
    """Update a review."""
    return await review_service.update_review(review_uuid, review_data, current_user, session)


@review_router.delete(
    "/{review_uuid}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a review",
    description="Delete a review. Users can only delete their own reviews."
)
async def delete_review(
        review_uuid: uuid.UUID,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> MessageResponse:
    """Delete a review."""
    result = await review_service.delete_review(review_uuid, current_user, session)
    return MessageResponse(**result)
