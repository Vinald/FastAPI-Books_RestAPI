import uuid as uuid_lib
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, PyEnum):
    """User roles for access control."""
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid_lib.uuid4, index=True)
    username = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    is_active = Column(Boolean, nullable=False, default=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship to Books
    books = relationship("Book", back_populates="owner", lazy="selectin")

    def __repr__(self) -> str:
        return f"User(id={self.id}, uuid={self.uuid}, username={self.username}, role={self.role})"

    def has_role(self, role: UserRole) -> bool:
        """Check if user has a specific role."""
        return self.role == role

    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN

    def is_moderator(self) -> bool:
        """Check if user is a moderator."""
        return self.role == UserRole.MODERATOR

    def is_at_least_moderator(self) -> bool:
        """Check if user is at least a moderator (moderator or admin)."""
        return self.role in (UserRole.ADMIN, UserRole.MODERATOR)
