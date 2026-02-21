from datetime import datetime
import uuid as uuid_lib
from sqlalchemy import Column, String, Integer, Date, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
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

    def __repr__(self) -> str:
        return f"Book(id={self.id}, uuid={self.uuid}, title={self.title})"
