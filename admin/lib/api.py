from telethon import functions # type: ignore
from telethon.client.telegramclient import TelegramClient # type: ignore
from telethon.tl.custom.message import Message # type: ignore
from telethon.tl.types import ( # type: ignore
    InputChannel,
    Channel,
    ExportedMessageLink
)
from typing import Any, Optional


from telethon.tl.types import ( # type: ignore
    Document,
)
from telethon.tl.types.messages import ChatFull as WebPage # type: ignore

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
