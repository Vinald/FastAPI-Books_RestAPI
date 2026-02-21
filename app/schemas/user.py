from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional
import uuid


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


class UserOut(UserBase):
    model_config = {"from_attributes": True}
