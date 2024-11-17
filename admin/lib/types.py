from typing import Optional, Tuple
from dataclasses import dataclass
from typing import Protocol, Callable, Coroutine, AsyncGenerator, AsyncIterable, Any
import asyncio
from telethon.tl.custom.message import Message # type: ignore
from telethon.tl.custom.file import File # type: ignore
from telethon.tl.types import ( # type: ignore
    Channel,
    Document,
    MessageMediaWebPage,
)

MessageQueueItem = Tuple[Channel, Message]
MessageTaskQueue = asyncio.Queue[MessageQueueItem]
DLMedia = MessageMediaWebPage | Document | File
Downloadable = DLMedia | Message

TaskWrapper = Callable[[Message, Channel], Coroutine[Any, Any, None]]
ChannelGenerator = AsyncGenerator[Channel, None]
MessageGenerator = AsyncGenerator[Message, None]
MessageIter = AsyncIterable[Message]
ChannelMessageRetriever = Callable[[Channel], MessageGenerator]

@dataclass
class MediaItem:
    target: DLMedia
    id: int
    from_preview: bool = False
    mime_type: Optional[str] = None

@dataclass
class DownloadItem:
    target: DLMedia
    id: int
    from_preview: bool
    mime_type: str
    media_type: str
    file_name: str
    file_size: int



class ProgressCallback(Protocol):
    def __call__(self, current: int, total: int) -> None: ...