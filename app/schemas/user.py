import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User roles for access control."""
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.USER  # Default role for new users


class UserCreateAdmin(UserBase):
    """Schema for admin creating users with any role."""
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.USER
    is_active: bool = True


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class UserUpdateAdmin(UserUpdate):
    """Schema for admin updating users - can change role."""
    role: Optional[UserRole] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class ShowUser(UserBase):
    uuid: uuid.UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Simplified book schema for user response (to avoid circular imports)
class BookInUser(BaseModel):
    uuid: uuid.UUID
    title: str
    author: str
    publisher: str

    model_config = {"from_attributes": True}


class UserWithBooks(ShowUser):
    books: List[BookInUser] = []

    model_config = {"from_attributes": True}


# Aliases for backward compatibility
UserOut = ShowUser
ShowUserWithBooks = UserWithBooks
