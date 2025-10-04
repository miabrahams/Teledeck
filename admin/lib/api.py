from telethon import functions
from telethon.client.telegramclient import TelegramClient
from telethon.tl.custom.message import Message
from telethon.tl.types import (
    InputChannel,
    Channel,
    ExportedMessageLink,
    Document,
    WebPage,
)
from typing import Any, Optional


from .types import MediaItem


async def get_message_link(tclient: TelegramClient, channel: Channel, message: Message) -> Optional[ExportedMessageLink]:
    if channel.access_hash is None:
        return None
    ic = InputChannel(channel.id, channel.access_hash)
    messageLinkRequest = functions.channels.ExportMessageLinkRequest(ic, message.id)
    result: Any = await tclient(messageLinkRequest)
    if isinstance(result, ExportedMessageLink):
        return result
    print("Failed to get message link.", result)
    return None

def find_web_preview(message: Message) -> MediaItem | None:
    if not getattr(message, "web_preview", None):
        return None
    page = message.web_preview
    if not isinstance(page, WebPage):
        return None
    if not isinstance(page.document, Document):
        return None
    if page.document.mime_type == "video/mp4":
        download_target = page.document
        return MediaItem(download_target, download_target.id, True)  # has mime_type
    return None
