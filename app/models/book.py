import uuid as uuid_lib
from datetime import datetime

from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid_lib.uuid4, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    publisher = Column(String(255), nullable=False)
    publish_date = Column(Date, nullable=False)
    pages = Column(Integer, nullable=False)
    language = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Foreign key to User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationship to User
    owner = relationship("User", back_populates="books")

    # Relationship to Reviews
    reviews = relationship("Review", back_populates="book", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Book(id={self.id}, uuid={self.uuid}, title={self.title})"
