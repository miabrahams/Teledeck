from typing import Optional, Tuple
from dataclasses import dataclass
from typing import Protocol
import asyncio
from telethon.tl.custom.message import Message # type: ignore
from telethon.tl.custom.file import File # type: ignore
from telethon.tl.types import ( # type: ignore
    Channel,
    Document,
    TypeMessageMedia,
)

QueueItem = Tuple[Channel, Message]
MessageTaskQueue = asyncio.Queue[QueueItem]
# Downloadable = Document | File
Downloadable = Message | TypeMessageMedia | Document | File


@dataclass
class DownloadItem:
    target: Downloadable
    id: int
    from_preview: bool = False
    mime_type: str = ""


class ProgressCallback(Protocol):
    def __call__(self, current: int, total: int) -> None: ...