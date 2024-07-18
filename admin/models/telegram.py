from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)

class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: Optional[str] = Field(default=None)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")

class Channel(SQLModel, table=True):
    __tablename__ = "channels"

    id: int = Field(primary_key=True)
    title: Optional[str] = Field(default=None)

class MediaItem(SQLModel, table=True):
    __tablename__ = "media_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    file_id: int = Field(unique=True)
    channel_id: int
    message_id: Optional[int] = Field(default=None)
    date: Optional[datetime] = Field(default=None)
    text: Optional[str] = Field(default=None)
    type: str
    file_name: Optional[str] = Field(default=None)
    file_size: Optional[int] = Field(default=None)
    url: Optional[str] = Field(default=None)
    path: Optional[str] = Field(default=None)
    seen: Optional[bool] = Field(default=None)
    favorite: bool = Field(default=False)
