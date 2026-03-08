"""
GraphQL Types

Strawberry type definitions for GraphQL schema.
"""
from datetime import datetime, date
from typing import List, Optional

import strawberry


@strawberry.type
class UserType:
    """GraphQL User type"""
    id: int
    uuid: str
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


@strawberry.type
class BookType:
    """GraphQL Book type"""
    id: int
    uuid: str
    title: str
    author: str
    publisher: Optional[str]
    publish_date: Optional[date]
    pages: Optional[int]
    language: Optional[str]
    user_id: Optional[int]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class ReviewType:
    """GraphQL Review type"""
    id: int
    uuid: str
    content: str
    rating: int
    user_id: int
    book_id: int
    created_at: datetime
    updated_at: datetime
    reviewer: Optional[UserType] = None
    book: Optional[BookType] = None


@strawberry.type
class BookWithReviews:
    """Book with its reviews"""
    book: BookType
    reviews: List[ReviewType]
    average_rating: Optional[float]
    review_count: int


@strawberry.type
class UserWithBooks:
    """User with their books"""
    user: UserType
    books: List[BookType]
    book_count: int


@strawberry.type
class PaginatedBooks:
    """Paginated books response"""
    items: List[BookType]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


@strawberry.type
class PaginatedUsers:
    """Paginated users response"""
    items: List[UserType]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


@strawberry.type
class PaginatedReviews:
    """Paginated reviews response"""
    items: List[ReviewType]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


# Input types for mutations
@strawberry.input
class BookInput:
    """Input for creating a book"""
    title: str
    author: str
    publisher: Optional[str] = None
    publish_date: Optional[date] = None
    pages: Optional[int] = None
    language: Optional[str] = None


@strawberry.input
class BookUpdateInput:
    """Input for updating a book"""
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    publish_date: Optional[date] = None
    pages: Optional[int] = None
    language: Optional[str] = None


@strawberry.input
class ReviewInput:
    """Input for creating a review"""
    content: str
    rating: int


@strawberry.input
class ReviewUpdateInput:
    """Input for updating a review"""
    content: Optional[str] = None
    rating: Optional[int] = None


@strawberry.type
class MutationResult:
    """Generic mutation result"""
    success: bool
    message: str


@strawberry.type
class BookMutationResult:
    """Book mutation result"""
    success: bool
    message: str
    book: Optional[BookType] = None


@strawberry.type
class ReviewMutationResult:
    """Review mutation result"""
    success: bool
    message: str
    review: Optional[ReviewType] = None
