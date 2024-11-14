# db_manager.py
from datetime import datetime
import uuid
from sqlmodel import Session, select, Column, Integer
from typing import Optional, Tuple, List

from models.telegram import (
    Message, MediaItem, TelegramMetadata, MediaType,
    ChannelModel
)
from .models import MediaInfo

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