import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    uuid: uuid.UUID
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = False


class ShowUser(UserBase):
    model_config = {"from_attributes": True}


class ShowUserWithBooks:
    pass
