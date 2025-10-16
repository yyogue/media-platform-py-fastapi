from sqlalchemy import (  # type: ignore
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Enum,
)
from sqlalchemy.orm import relationship  # type: ignore
from datetime import datetime
from database import Base
import enum


class MediaType(enum.Enum):
    IMAGE = "image"
    VIDEO = "video"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Relationship
    posts = relationship("Post", back_populates="owner")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    media_url = Column(String, nullable=False)  # S3 URL
    media_type = Column(Enum(MediaType), nullable=False)
    file_size = Column(Integer)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    # Relationship
    owner = relationship("User", back_populates="posts")
