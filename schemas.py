from pydantic import (  # type: ignore
    BaseModel,
    EmailStr,
    Field,
)
from datetime import datetime
from typing import Optional
from models import MediaType


# User Schema
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_lentgth=7)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# Post Schema
class PostCreates(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None


class PostResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    media_url: str
    media_type: MediaType
    file_size: int
    owner_id: int
    owner_username: int
    created_at: datetime

    class Config:
        from_attributes = True
