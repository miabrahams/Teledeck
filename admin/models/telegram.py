from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int = Field(default=None, primary_key=True)
    email: str = Field(default=None)
    password: str = Field(default=None)

class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: int = Field(default=None, primary_key=True)
    session_id: str = Field(default=None)
    user_id: int = Field(default=None, foreign_key="users.id")

class Channel(SQLModel, table=True):
    __tablename__ = "channels"

    id: int = Field(primary_key=True)
    title: str = Field(default=None)

class MediaItem(SQLModel, table=True):
    __tablename__ = "media_items"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    file_id: int = Field(unique=True, nullable=False)
    channel_id: int = Field(nullable=False)
    message_id: int = Field(nullable=False)
    date: datetime = Field(nullable=False)
    text: str = Field(nullable=False, default="")
    type: str = Field(nullable=False)
    file_name: str = Field(nullable=False)
    file_size: int = Field(nullable=False)
    url: str = Field(default=None)
    seen: bool = Field(default=False, nullable=False)
    favorite: bool = Field(nullable=False, default=False)
    user_deleted: bool = Field(default=False, nullable=False)
