"""
GraphQL Resolvers

Query and mutation resolvers for GraphQL schema.
"""
import uuid as uuid_module
from typing import Optional

import strawberry
from strawberry.types import Info

from app.graphql.types import (
    UserType, BookType, ReviewType,
    BookWithReviews, PaginatedBooks, PaginatedUsers, PaginatedReviews,
    BookInput, BookUpdateInput, ReviewInput, MutationResult, BookMutationResult, ReviewMutationResult
)


def model_to_user_type(user) -> UserType:
    """Convert SQLAlchemy User model to GraphQL UserType."""
    return UserType(
        id=user.id,
        uuid=str(user.uuid),
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


def model_to_book_type(book) -> BookType:
    """Convert SQLAlchemy Book model to GraphQL BookType."""
    return BookType(
        id=book.id,
        uuid=str(book.uuid),
        title=book.title,
        author=book.author,
        publisher=book.publisher,
        publish_date=book.publish_date,
        pages=book.pages,
        language=book.language,
        user_id=book.user_id,
        created_at=book.created_at,
        updated_at=book.updated_at
    )


def model_to_review_type(review, include_relations: bool = False) -> ReviewType:
    """Convert SQLAlchemy Review model to GraphQL ReviewType."""
    reviewer = None
    book = None

    if include_relations:
        if hasattr(review, 'reviewer') and review.reviewer:
            reviewer = model_to_user_type(review.reviewer)
        if hasattr(review, 'book') and review.book:
            book = model_to_book_type(review.book)

    return ReviewType(
        id=review.id,
        uuid=str(review.uuid),
        content=review.content,
        rating=review.rating,
        user_id=review.user_id,
        book_id=review.book_id,
        created_at=review.created_at,
        updated_at=review.updated_at,
        reviewer=reviewer,
        book=book
    )


@strawberry.type
class Query:
    """GraphQL Query resolvers"""

    @strawberry.field
    async def books(
            self,
            info: Info,
            page: int = 1,
            page_size: int = 10,
            search: Optional[str] = None
    ) -> PaginatedBooks:
        """Get paginated list of books."""
        from app.services.book_service import BookService

        session = info.context["session"]
        book_service = BookService()

        books, total = await book_service.get_all_books_paginated(
            session=session,
            page=page,
            page_size=page_size,
            search=search
        )

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return PaginatedBooks(
            items=[model_to_book_type(b) for b in books],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )

    @strawberry.field
    async def book(self, info: Info, uuid: str) -> Optional[BookType]:
        """Get a single book by UUID."""
        from app.services.book_service import BookService

        session = info.context["session"]
        book_service = BookService()

        book = await book_service.get_book(uuid_module.UUID(uuid), session)

        if not book:
            return None

        return model_to_book_type(book)

    @strawberry.field
    async def book_with_reviews(self, info: Info, uuid: str) -> Optional[BookWithReviews]:
        """Get a book with its reviews."""
        from app.services.book_service import BookService
        from app.services.review_service import ReviewService

        session = info.context["session"]
        book_service = BookService()
        review_service = ReviewService()

        book = await book_service.get_book(uuid_module.UUID(uuid), session)

        if not book:
            return None

        reviews = await review_service.get_reviews_by_book(uuid_module.UUID(uuid), session)
        stats = await review_service.get_book_average_rating(uuid_module.UUID(uuid), session)

        return BookWithReviews(
            book=model_to_book_type(book),
            reviews=[model_to_review_type(r, include_relations=True) for r in reviews],
            average_rating=stats.get("average_rating"),
            review_count=stats.get("total_reviews", 0)
        )

    @strawberry.field
    async def users(
            self,
            info: Info,
            page: int = 1,
            page_size: int = 10,
            search: Optional[str] = None
    ) -> PaginatedUsers:
        """Get paginated list of users."""
        from app.services.user_services import UserService

        session = info.context["session"]
        user_service = UserService()

        users, total = await user_service.get_all_users_paginated(
            session=session,
            page=page,
            page_size=page_size,
            search=search
        )

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return PaginatedUsers(
            items=[model_to_user_type(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )

    @strawberry.field
    async def user(self, info: Info, uuid: str) -> Optional[UserType]:
        """Get a single user by UUID."""
        from app.services.user_services import UserService

        session = info.context["session"]
        user_service = UserService()

        user = await user_service.get_user_by_uuid(uuid_module.UUID(uuid), session)

        if not user:
            return None

        return model_to_user_type(user)

    @strawberry.field
    async def reviews(
            self,
            info: Info,
            page: int = 1,
            page_size: int = 10,
            book_uuid: Optional[str] = None
    ) -> PaginatedReviews:
        """Get paginated list of reviews."""
        from app.services.review_service import ReviewService

        session = info.context["session"]
        review_service = ReviewService()

        if book_uuid:
            reviews, total = await review_service.get_reviews_by_book_paginated(
                book_uuid=uuid_module.UUID(book_uuid),
                session=session,
                page=page,
                page_size=page_size
            )
        else:
            reviews, total = await review_service.get_all_reviews_paginated(
                session=session,
                page=page,
                page_size=page_size
            )

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return PaginatedReviews(
            items=[model_to_review_type(r, include_relations=True) for r in reviews],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )

    @strawberry.field
    async def me(self, info: Info) -> Optional[UserType]:
        """Get current authenticated user."""
        user = info.context.get("user")

        if not user:
            return None

        return model_to_user_type(user)


@strawberry.type
class Mutation:
    """GraphQL Mutation resolvers"""

    @strawberry.mutation
    async def create_book(self, info: Info, input: BookInput) -> BookMutationResult:
        """Create a new book."""
        from app.services.book_service import BookService
        from app.schemas.book import BookCreate

        user = info.context.get("user")
        if not user:
            return BookMutationResult(
                success=False,
                message="Authentication required",
                book=None
            )

        session = info.context["session"]
        book_service = BookService()

        try:
            book_data = BookCreate(
                title=input.title,
                author=input.author,
                publisher=input.publisher,
                publish_date=input.publish_date,
                pages=input.pages,
                language=input.language
            )

            new_book = await book_service.create_book(
                book_data=book_data,
                session=session,
                user_id=user.id
            )

            return BookMutationResult(
                success=True,
                message="Book created successfully",
                book=model_to_book_type(new_book)
            )

        except Exception as e:
            return BookMutationResult(
                success=False,
                message=str(e),
                book=None
            )

    @strawberry.mutation
    async def update_book(
            self,
            info: Info,
            uuid: str,
            input: BookUpdateInput
    ) -> BookMutationResult:
        """Update an existing book."""
        from app.services.book_service import BookService
        from app.schemas.book import BookUpdate

        user = info.context.get("user")
        if not user:
            return BookMutationResult(
                success=False,
                message="Authentication required",
                book=None
            )

        session = info.context["session"]
        book_service = BookService()

        try:
            update_data = BookUpdate(
                title=input.title,
                author=input.author,
                publisher=input.publisher,
                publish_date=input.publish_date,
                pages=input.pages,
                language=input.language
            )

            updated_book = await book_service.update_book(
                book_uuid=uuid_module.UUID(uuid),
                update_data=update_data,
                session=session,
                current_user=user
            )

            return BookMutationResult(
                success=True,
                message="Book updated successfully",
                book=model_to_book_type(updated_book)
            )

        except Exception as e:
            return BookMutationResult(
                success=False,
                message=str(e),
                book=None
            )

    @strawberry.mutation
    async def delete_book(self, info: Info, uuid: str) -> MutationResult:
        """Delete a book."""
        from app.services.book_service import BookService

        user = info.context.get("user")
        if not user:
            return MutationResult(
                success=False,
                message="Authentication required"
            )

        session = info.context["session"]
        book_service = BookService()

        try:
            await book_service.delete_book(
                book_uuid=uuid_module.UUID(uuid),
                session=session,
                current_user=user
            )

            return MutationResult(
                success=True,
                message="Book deleted successfully"
            )

        except Exception as e:
            return MutationResult(
                success=False,
                message=str(e)
            )

    @strawberry.mutation
    async def create_review(
            self,
            info: Info,
            book_uuid: str,
            input: ReviewInput
    ) -> ReviewMutationResult:
        """Create a new review for a book."""
        from app.services.review_service import ReviewService
        from app.schemas.review import ReviewCreate

        user = info.context.get("user")
        if not user:
            return ReviewMutationResult(
                success=False,
                message="Authentication required",
                review=None
            )

        session = info.context["session"]
        review_service = ReviewService()

        try:
            review_data = ReviewCreate(
                content=input.content,
                rating=input.rating
            )

            new_review = await review_service.create_review(
                book_uuid=uuid_module.UUID(book_uuid),
                review_data=review_data,
                current_user=user,
                session=session
            )

            return ReviewMutationResult(
                success=True,
                message="Review created successfully",
                review=model_to_review_type(new_review, include_relations=True)
            )

        except Exception as e:
            return ReviewMutationResult(
                success=False,
                message=str(e),
                review=None
            )


# Create the GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
