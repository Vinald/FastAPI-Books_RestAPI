from pydantic import BaseModel
import uuid
from datetime import datetime, date


class BookBase(BaseModel):
    uid: uuid.UUID
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
    title: str
    author: str
    publisher: str
    pages: int
    language: str


class BookOut(BookBase):
    model_config = {"from_attributes": True}
    
