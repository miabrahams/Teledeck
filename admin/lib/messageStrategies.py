from sqlalchemy import Engine
from telethon import TelegramClient, functions # type: ignore
from telethon.tl.custom.message import Message # type: ignore
from telethon.tl.types import ( # type: ignore
    Channel,
    InputChannel,
    InputMessagesFilterUrl,
    InputMessagesFilterVideo,
)
from telethon.hints import Entity # type: ignore
from telethon.tl.types.messages import ChatFull as ChatFullMessage
from typing import Any, cast, AsyncIterable
from sqlmodel import Session, select, Column, Integer
from models.telegram import TelegramMetadata


##### Message filtering strategies

class TDContext:
    tclient: TelegramClient
    engine: Engine

async def NoMessages() -> AsyncIterable[Message]:
    return
    yield

def get_all_messages(ctx: TDContext, entity: Entity, limit: int)-> AsyncIterable[Message]:
    return ctx.tclient.iter_messages(entity, limit)


def get_oldest_messages(ctx: TDContext, entity: Entity, limit: int):
    # TODO: Check add_offset
    return ctx.tclient.iter_messages(entity, limit, reverse=True, add_offset=500)


def get_urls(ctx: TDContext, entity: Entity, limit: int):
    return ctx.tclient.iter_messages(entity, limit, filter=InputMessagesFilterUrl)


def get_all_videos(ctx: TDContext, entity: Entity, limit: int):
    return ctx.tclient.iter_messages(entity, limit, filter=InputMessagesFilterVideo)


async def get_unread_messages(ctx: TDContext, channel: Channel) -> AsyncIterable[Message]:
    full: Any = await ctx.tclient(functions.channels.GetFullChannelRequest(cast(InputChannel, channel)))
    if not isinstance(full, ChatFullMessage):
        raise ValueError("Full channel cannot be retrieved")
    full_channel = full.full_chat
    unread_count = getattr(full_channel, "unread_count")
    if not isinstance(unread_count, int):
        raise ValueError("Unread count not available: ", full_channel.stringify())
    if unread_count > 0:
        print(f"Unread messages in {channel.title}: {unread_count}")
        return ctx.tclient.iter_messages(channel, limit=unread_count)
    else:
        return NoMessages()


def get_messages_since_db_update(ctx: TDContext, channel: Channel, limit: int):
    with Session(ctx.engine) as session:
        query = (
            select(TelegramMetadata.message_id)
            .where(TelegramMetadata.channel_id == channel.id)
            .order_by(Column("message_id", Integer).desc())  # Find the last message_id
        )
        last_seen_post = session.exec(query).first()

    if last_seen_post:
        return ctx.tclient.iter_messages(channel, limit, min_id=last_seen_post)
    else:
        return get_all_messages(ctx, channel, limit)


def get_earlier_messages(ctx: TDContext, channel: Channel, limit: int):
    with Session(ctx.engine) as session:

        query = (
            select(TelegramMetadata.message_id)
            .where(TelegramMetadata.channel_id == channel.id)
            .order_by(Column("message_id", Integer))
        )
        oldest_seen_post = session.exec(query).first()

    if oldest_seen_post is not None:
        # TODO: is oldest_seen_post a List??
        return ctx.tclient.iter_messages(channel, limit, offset_id=oldest_seen_post)
    else:
        return get_all_messages(ctx, channel, limit)

