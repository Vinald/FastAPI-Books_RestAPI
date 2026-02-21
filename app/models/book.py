from datetime import datetime
import uuid
from sqlalchemy import Column, String, Integer, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Book(Base):
    __tablename__ = "books"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    publisher = Column(String(255), nullable=False)
    publish_date = Column(Date, nullable=False)
    pages = Column(Integer, nullable=False)
    language = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self) -> str:
        return f"Book(uuid={self.uuid}, title={self.title}, author={self.author})"
