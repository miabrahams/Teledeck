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

##### Message filtering strategies

async def NoMessages() -> AsyncIterable[Message]:
    return
    yield

def get_all_messages(tclient: TelegramClient, entity: Entity, limit: int | None)-> AsyncIterable[Message]:
    if limit is None:
        return tclient.iter_messages(entity)
    return tclient.iter_messages(entity, limit)

def get_oldest_messages(tclient: TelegramClient, entity: Entity, limit: int | None):
    raise NotImplementedError("This strategy is not tested")
    """
    TODO: Test for correctness
    if limit is None:
        return tclient.iter_messages(entity, reverse=True)
    return tclient.iter_messages(entity, limit, reverse=True, add_offset=500)
    """


def get_urls(tclient: TelegramClient, entity: Entity, limit: int | None):
    if limit is None:
        return tclient.iter_messages(entity, filter=InputMessagesFilterUrl)
    return tclient.iter_messages(entity, limit, filter=InputMessagesFilterUrl)


def get_all_videos(tclient: TelegramClient, entity: Entity, limit: int | None):
    if limit is None:
        return tclient.iter_messages(entity, filter=InputMessagesFilterVideo)
    return tclient.iter_messages(entity, limit, filter=InputMessagesFilterVideo)


async def get_unread_messages(tclient: TelegramClient, channel: Channel) -> AsyncIterable[Message]:
    full: Any = await tclient(functions.channels.GetFullChannelRequest(cast(InputChannel, channel)))
    if not isinstance(full, ChatFullMessage):
        raise ValueError("Full channel cannot be retrieved")
    full_channel = full.full_chat
    unread_count = getattr(full_channel, "unread_count")
    if not isinstance(unread_count, int):
        raise ValueError("Unread count not available: ", full_channel.stringify())
    if unread_count > 0:
        print(f"Unread messages in {channel.title}: {unread_count}")
        return tclient.iter_messages(channel, limit=unread_count)
    else:
        return NoMessages()

def get_messages_since_db_update(tclient: TelegramClient, channel: Channel, last_seen_post: int | None, limit: int | None):
    if last_seen_post is None:
        return default_strategy(tclient, channel, limit)
    else:
        if limit is None:
            return tclient.iter_messages(channel, min_id=last_seen_post)
        return tclient.iter_messages(channel, limit, min_id=last_seen_post)

def get_earlier_unseen_messages(tclient: TelegramClient, channel: Channel, oldest_seen_post: int | None, limit: int | None):
    if oldest_seen_post is None:
        return default_strategy(tclient, channel, limit)
    else:
        if limit is None:
            return tclient.iter_messages(channel, offset_id=oldest_seen_post)
        return tclient.iter_messages(channel, limit, offset_id=oldest_seen_post)

default_strategy = get_all_messages