import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    rating: int = Field(..., ge=1, le=5)


class ReviewCreate(ReviewBase):
    """Schema for creating a review."""
    pass


class ReviewUpdate(BaseModel):
    """Schema for updating a review."""
    content: Optional[str] = Field(None, min_length=1, max_length=1000)
    rating: Optional[int] = Field(None, ge=1, le=5)


class ReviewerInfo(BaseModel):
    """Minimal user info for review display."""
    uuid: uuid.UUID
    username: str
    first_name: str
    last_name: str

    model_config = {"from_attributes": True}


class BookInfo(BaseModel):
    """Minimal book info for review display."""
    uuid: uuid.UUID
    title: str
    author: str

    model_config = {"from_attributes": True}


class ReviewOut(ReviewBase):
    """Schema for review output."""
    id: int
    uuid: uuid.UUID
    user_id: int
    book_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewWithReviewer(ReviewOut):
    """Review with reviewer information."""
    reviewer: ReviewerInfo

    model_config = {"from_attributes": True}


class ReviewWithBook(ReviewOut):
    """Review with book information."""
    book: BookInfo

    model_config = {"from_attributes": True}


class ReviewFull(ReviewOut):
    """Full review with both reviewer and book info."""
    reviewer: ReviewerInfo
    book: BookInfo

    model_config = {"from_attributes": True}
