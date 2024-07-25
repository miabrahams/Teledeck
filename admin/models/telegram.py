from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint
from typing import Optional, List
from datetime import datetime

class User(SQLModel, table=True):
    __tablename__ = 'users'

    id: int = Field(primary_key=True)
    email: str = Field(nullable=False, unique=True)
    password: str = Field(nullable=False)
    sessions: List["Session"] = Relationship(back_populates="user")



class Session(SQLModel, table=True):
    __tablename__ = 'sessions'

    id: int = Field(primary_key=True)
    session_id: str = Field(nullable=False, unique=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)

    user: User = Relationship(back_populates="sessions")

class Channel(SQLModel, table=True):
    __tablename__ = "channels"

    id: int = Field(primary_key=True)
    title: str = Field(nullable=False)

class Source(SQLModel, table=True):
    __tablename__ = 'sources'

    id: int = Field(primary_key=True)
    name: str = Field(nullable=False, unique=True)
    media_items: List["MediaItem"] = Relationship(back_populates="source")

class MediaType(SQLModel, table=True):
    __tablename__ = 'media_types'

    id: int = Field(primary_key=True)
    type: str = Field(nullable=False, unique=True)
    media_items: List["MediaItem"] = Relationship(back_populates="media_type")

class MediaItemTag(SQLModel, table=True):
    __tablename__ = 'media_item_tags'

    media_item_id: str = Field(foreign_key="media_items.id", primary_key=True)
    tag_id: int = Field(foreign_key="tags.id", primary_key=True)
    weight: float = Field(nullable=False)


class MediaItem(SQLModel, table=True):
    __tablename__ = 'media_items'

    id: str = Field(primary_key=True)
    source_id: int = Field(foreign_key="sources.id", nullable=False)
    media_type_id: int = Field(foreign_key="media_types.id", nullable=False)
    file_name: str = Field(nullable=False)
    file_size: int = Field(nullable=False)
    created_at: datetime = Field(nullable=False)
    updated_at: datetime = Field(nullable=False)
    seen: bool = Field(nullable=False)
    favorite: bool = Field(default=False, nullable=False)
    user_deleted: bool = Field(default=False, nullable=False)

    source: Source = Relationship(back_populates="media_items")
    media_type: MediaType = Relationship(back_populates="media_items")
    telegram_metadata: Optional["TelegramMetadata"] = Relationship(back_populates="media_item")
    twitter_metadata: List["TwitterMetadata"] = Relationship(back_populates="media_item")
    tags: List["Tag"] = Relationship(back_populates="media_items", link_model=MediaItemTag)


class TelegramMetadata(SQLModel, table=True):
    __tablename__ = 'telegram_metadata'

    media_item_id: str = Field(foreign_key="media_items.id", primary_key=True)
    channel_id: int = Field(nullable=False)
    message_id: int = Field(nullable=False)
    file_id: int = Field(nullable=False)
    from_preview: int = Field(nullable=False)
    date: datetime = Field(nullable=False)
    text: str = Field(nullable=False)
    url: str = Field(nullable=False)

    media_item: MediaItem = Relationship(back_populates="telegram_metadata")

class TwitterMetadata(SQLModel, table=True):
    __tablename__ = 'twitter_metadata'

    media_item_id: str = Field(foreign_key="media_items.id", primary_key=True)
    tweet_id: str = Field(nullable=False)
    date: datetime = Field(nullable=False)
    text: str = Field(nullable=False)
    url: str = Field(nullable=False)

    media_item: MediaItem = Relationship(back_populates="twitter_metadata")

class Tag(SQLModel, table=True):
    __tablename__ = 'tags'

    id: int = Field(primary_key=True)
    name: str = Field(nullable=False, unique=True)
    media_items: List[MediaItem] = Relationship(back_populates="tags", link_model=MediaItemTag)



class PossibleDuplicate(SQLModel, table=True):
    __tablename__ = 'possible_duplicates'

    first: str = Field(foreign_key="media_items.id", primary_key=True)
    second: str = Field(foreign_key="media_items.id", primary_key=True)

    __table_args__ = (UniqueConstraint('first', 'second'),)