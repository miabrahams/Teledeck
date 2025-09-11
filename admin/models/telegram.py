from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint
import sqlalchemy as sa
from typing import Optional, List
from datetime import datetime

class UserModel(SQLModel, table=True):
    __tablename__ = 'users' # pyright: ignore[reportAssignmentType]

    id: int = Field(primary_key=True)
    email: str = Field(nullable=False, sa_type=sa.TEXT)
    password: str = Field(nullable=False, sa_type=sa.TEXT)
    sessions: List["Session"] = Relationship(back_populates="user")



class Session(SQLModel, table=True):
    __tablename__ = 'sessions' # pyright: ignore[reportAssignmentType]

    id: int = Field(primary_key=True)
    session_id: str = Field(nullable=False, sa_type=sa.TEXT)
    user_id: int = Field(foreign_key="users.id", nullable=False)

    user: UserModel = Relationship(back_populates="sessions")

class ChannelModel(SQLModel, table=True):
    __tablename__ = "channels" # pyright: ignore[reportAssignmentType]

    id: int = Field(primary_key=True)
    title: str = Field(nullable=False, sa_type=sa.TEXT)
    check: bool = Field(nullable=False, default=False)

class Source(SQLModel, table=True):
    __tablename__ = 'sources' # pyright: ignore[reportAssignmentType]

    id: int = Field(primary_key=True, default=None)
    name: str = Field(nullable=False, unique=True)
    media_items: List["MediaItem"] = Relationship(back_populates="source")

class MediaType(SQLModel, table=True):
    __tablename__ = 'media_types' # pyright: ignore[reportAssignmentType]

    id: int = Field(primary_key=True, default=None)
    type: str = Field(nullable=False, unique=True)
    media_items: List["MediaItem"] = Relationship(back_populates="media_type")

class MediaItemTag(SQLModel, table=True):
    __tablename__ = 'media_item_tags' # pyright: ignore[reportAssignmentType]

    media_item_id: str = Field(foreign_key="media_items.id", primary_key=True)
    tag_id: int = Field(foreign_key="tags.id", primary_key=True, index=True)
    weight: float = Field(nullable=True, index=True)

class MediaItem(SQLModel, table=True):
    __tablename__ = 'media_items' # pyright: ignore[reportAssignmentType]

    id: str = Field(primary_key=True, max_length=36)
    source_id: int = Field(foreign_key="sources.id", nullable=False)
    media_type_id: int = Field(foreign_key="media_types.id", nullable=False)
    file_name: str = Field(nullable=False)
    file_size: int = Field(nullable=False, index=True)
    created_at: datetime = Field(nullable=False, index=True)
    updated_at: datetime = Field(nullable=False)
    seen: bool = Field(nullable=False, index=True)
    favorite: bool = Field(default=False, nullable=False, index=True)
    user_deleted: bool = Field(default=False, nullable=False, index=True)
    deleted_at: Optional[datetime] = Field(nullable=True, index=True)

    source: Source = Relationship(back_populates="media_items")
    media_type: MediaType = Relationship(back_populates="media_items")
    telegram_metadata: Optional["TelegramMetadata"] = Relationship(back_populates="media_item")
    twitter_metadata: List["TwitterMetadata"] = Relationship(back_populates="media_item")
    tags: List["Tag"] = Relationship(back_populates="media_items", link_model=MediaItemTag)


class TelegramMetadata(SQLModel, table=True):
    __tablename__ = 'telegram_metadata' # pyright: ignore[reportAssignmentType]

    media_item_id: str = Field(foreign_key="media_items.id", primary_key=True)
    channel_id: int = Field(foreign_key="channels.id", nullable=False)
    message_id: int = Field(nullable=False)
    file_id: int = Field(nullable=False)
    from_preview: int = Field(nullable=False)
    date: datetime = Field(nullable=False)
    text: str = Field(sa_type=sa.TEXT, nullable=False)
    url: str = Field(nullable=False)

    media_item: MediaItem = Relationship(back_populates="telegram_metadata")

class TwitterMetadata(SQLModel, table=True):
    __tablename__ = 'twitter_metadata' # pyright: ignore[reportAssignmentType]

    media_item_id: str = Field(foreign_key="media_items.id", primary_key=True)
    tweet_id: int = Field(nullable=False)
    date: datetime = Field(nullable=False)
    text: str = Field(sa_type=sa.TEXT, nullable=False)
    url: str = Field(nullable=False)
    username: str = Field(nullable=False)

    media_item: MediaItem = Relationship(back_populates="twitter_metadata")

class Tag(SQLModel, table=True):
    __tablename__ = 'tags' # pyright: ignore[reportAssignmentType]

    id: int = Field(default=None, primary_key=True)
    name: str = Field(nullable=False, unique=True)
    media_items: List[MediaItem] = Relationship(back_populates="tags", link_model=MediaItemTag)

class AestheticScore(SQLModel, table=True):
    __tablename__ = 'aesthetic_score' # pyright: ignore[reportAssignmentType]
    media_item_id: str = Field(
        foreign_key="media_items.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    score: float = Field(nullable=False)

class Thumbnail(SQLModel, table=True):
    __tablename__ = 'thumbnails' # pyright: ignore[reportAssignmentType]
    media_item_id: str = Field(
        foreign_key="media_items.id",
        primary_key=True,
    )
    filename: str = Field(nullable=False)

class MediaItemDuplicates(SQLModel, table=True):
    __tablename__ = 'media_item_duplicates' # pyright: ignore[reportAssignmentType]

    first: str = Field(foreign_key="media_items.id", primary_key=True)
    second: str = Field(foreign_key="media_items.id", primary_key=True)

    __table_args__ = (UniqueConstraint('first', 'second'),)