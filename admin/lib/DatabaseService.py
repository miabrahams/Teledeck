# db_manager.py
from datetime import datetime
import uuid
from sqlmodel import Session, select, Column, Integer, SQLModel
from typing import Optional, Tuple, List, Any
from telethon.types import (
    Channel,
    Document
)
from telethon.tl.custom.message import Message
from .config import DatabaseConfig

from .Logger import RichLogger
from models.telegram import (
    MediaItem, TelegramMetadata, MediaType,
    ChannelModel, Source
)
from .types import DownloadItem
from sqlmodel import create_engine

class DatabaseService:
    def __init__(self, config: DatabaseConfig):
        needs_init = not config.db_path.exists()
        self.engine = create_engine(f"sqlite:///{config.db_path}")
        if needs_init:
            self._init_db()

    def get_last_seen_post(self, channel_id: int) -> int | None:
        with Session(self.engine) as session:
            query = (
                select(TelegramMetadata.message_id)
                .where(TelegramMetadata.channel_id == channel_id)
                .order_by(Column("message_id", Integer).desc())  # Find the last message_id
            )
            return session.exec(query).first()

    def _init_db(self):
        SQLModel.metadata.create_all(self.engine)

        with Session(self.engine) as session:
            session.add_all([Source(name=name) for name in ["telegram", "twitter", "furaffinity", "deviantart", "e621"]])
            session.add_all([MediaType(type=type) for type in ["photo", "video", "jpeg", "webp", "gif", "png", "document", "image"]])
            session.commit()

    def get_earliest_seen_post(self, channel_id: int) -> int | None:
        with Session(self.engine) as session:
            query = (
                select(TelegramMetadata.message_id)
                .where(TelegramMetadata.channel_id == channel_id)
                .order_by(Column("message_id", Integer))
            )
            return session.exec(query).first()

    def save_media_item(self,
                       logger: RichLogger,
                       item: DownloadItem,
                       channel_id: int,
                       message: Message) -> None:
        with Session(self.engine) as session:
            # First check if media already exists
            existing = self._get_existing_media(session, item)
            if existing:
                logger.write(f"Found existing file_id: {item.id}")
                self._update_existing_media(session, existing, item, channel_id, message)
                # TODO: add more detail
                return

            # Create new media item
            media_type = self._get_or_raise_media_type(session, item.media_type)
            new_item_id = uuid.uuid4().hex

            media_item = MediaItem(
                id=new_item_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                source_id=1,  # TODO: Make this configurable
                seen=False,
                media_type_id=media_type.id,
                file_size=item.file_size or 0,
                file_name=item.file_name,
                deleted_at=None,
            )

            telegram_metadata = TelegramMetadata(
                media_item_id=new_item_id,
                file_id=item.id,
                channel_id=channel_id,
                date=getattr(message, "date", datetime.now()),
                text=getattr(message, "text", ""),
                url=f"/media/{item.file_name}",
                message_id=message.id,
                from_preview=int(item.from_preview),
            )

            session.add(media_item)
            session.add(telegram_metadata)
            session.commit()

    def _get_existing_media(self,
                          session: Session,
                          download_item: DownloadItem) -> Optional[Tuple[MediaItem, TelegramMetadata]]:
        return session.exec(
            select(MediaItem, TelegramMetadata)
            .where(MediaItem.id == TelegramMetadata.media_item_id)
            .where(TelegramMetadata.file_id == download_item.id)
            .where(TelegramMetadata.from_preview == int(download_item.from_preview))
        ).first()


    ## External callers
    def find_existing_media(self,
                          download_item: Document) -> Optional[Tuple[MediaItem, TelegramMetadata]]:
        with Session(self.engine) as session:
            return session.exec(
                select(MediaItem, TelegramMetadata)
                .where(MediaItem.id == TelegramMetadata.media_item_id)
                .where(TelegramMetadata.file_id == download_item.id)
            ).first()



    def get_media_type(self, type_name: str) -> Optional[MediaType]:
        with Session(self.engine) as session:
            return session.exec(
                select(MediaType).where(MediaType.type == type_name)
            ).first()


    def _update_existing_media(self,
                             session: Session,
                             existing: Tuple[MediaItem, TelegramMetadata],
                             item: DownloadItem,
                             channel_id: int,
                             message: Message) -> None:

        (mediaItem, telegramMetadata) = existing
        fileSize = getattr(message.file, "size", None)
        if mediaItem.file_size != fileSize:
            raise AssertionError(f"File size mismatch: {mediaItem.file_size} vs {fileSize}")
        # Update legacy entries
        if not telegramMetadata.message_id:
            telegramMetadata.message_id = item.id
            telegramMetadata.channel_id = channel_id
            session.commit()
        return

    def _get_or_raise_media_type(self, session: Session, type_name: str) -> MediaType:
        media_type = session.exec(
            select(MediaType).where(MediaType.type == type_name)
        ).first()
        if not media_type:
            raise ValueError(f"Media type not found: {type_name}")
        return media_type


    def get_channels_to_check(self, conds: list[Any]) -> List[ChannelModel]:
        # Get list of channel IDs to check.
        with Session(self.engine) as session:
            statement = select(ChannelModel).where(ChannelModel.check == 1)
            for cond in conds:
                statement = statement.where(cond)
            return [
                channel for channel in
                session.exec(statement).all()
            ]

    def add_channel_if_not_exists(self, logger: RichLogger, channel_id: int, channel_title: str) -> None:
        # Add a channel to the database if it doesn't exist.
        # TODO: Add error handling
        with Session(self.engine) as session:
            if not session.exec(
                select(ChannelModel).where(ChannelModel.id == channel_id)
            ).first():
                newChannel = ChannelModel(id=channel_id, title=channel_title)
                session.add(newChannel)
                session.commit()
                log_msg = {"Forwarded to channel": channel_title}
                logger.write(repr(log_msg))
                logger.add_data(log_msg)

    def update_channel_list(self, target_channels: List[Channel]):
        with Session(self.engine) as session:
            for channel in session.exec(select(ChannelModel)).all():
                channel.check = False
            session.commit()

        with Session(self.engine) as session:
            for channel in target_channels:
                existingChannel = session.get(ChannelModel, channel.id)
                if existingChannel:
                    existingChannel.check = True
                    session.commit()
                else:
                    session.add(ChannelModel(id=channel.id, title=channel.title, check=True))
                    session.commit()
