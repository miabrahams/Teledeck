# db_manager.py
from datetime import datetime
import uuid
from sqlmodel import Session, select, Column, Integer
from typing import Optional, Tuple, List

from .ConsoleLogger import RichConsoleLogger
from models.telegram import (
    Message, MediaItem, TelegramMetadata, MediaType,
    ChannelModel
)
from .types import DownloadItem

class DatabaseService:
    def __init__(self, engine):
        self.engine = engine

    def get_last_seen_post(self, channel_id: int) -> int | None:
        with Session(self.engine) as session:
            query = (
                select(TelegramMetadata.message_id)
                .where(TelegramMetadata.channel_id == channel_id)
                .order_by(Column("message_id", Integer).desc())  # Find the last message_id
            )
            return session.exec(query).first()

    def get_earliest_seen_post(self, channel_id: int) -> int | None:
        with Session(self.engine) as session:
            query = (
                select(TelegramMetadata.message_id)
                .where(TelegramMetadata.channel_id == channel_id)
                .order_by(Column("message_id", Integer))
            )
            return session.exec(query).first()

    def save_media_item(self,
                       console: RichConsoleLogger,
                       item: DownloadItem,
                       channel_id: int,
                       message: Message) -> None:
        with Session(self.engine) as session:
            # First check if media already exists
            existing = self._get_existing_media(session, item)
            if existing:
                console.write(f"Found existing file_id: {item.id}")
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
                file_name=item.file_name
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