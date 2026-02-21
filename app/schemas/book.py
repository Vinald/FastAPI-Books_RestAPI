from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional
import uuid


class BookBase(BaseModel):
    uuid: uuid.UUID
    title: str
    author: str
    publisher: str
    publish_date: date
    pages: int
    language: str
    created_at: datetime
    updated_at: datetime


class BookCreate(BaseModel):
    title: str
    author: str
    publisher: str
    publish_date: date
    pages: int
    language: str


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    publish_date: Optional[date] = None
    pages: Optional[int] = None
    language: Optional[str] = None


class BookOut(BookBase):
    model_config = {"from_attributes": True}
