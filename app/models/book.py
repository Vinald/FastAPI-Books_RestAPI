from datetime import datetime, date
import uuid
from sqlalchemy import Column, String, Integer, Date, DateTime
from sqlalchemy.dialects.mysql import CHAR
from app.core.database import Base


class Book(Base):
    __tablename__ = "books"

    uid = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    publisher = Column(String(255), nullable=False)
    publish_date = Column(Date, nullable=False)
    pages = Column(Integer, nullable=False)
    language = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self) -> str:
        return f"Book(uid={self.uid}, title={self.title}, author={self.author})"
