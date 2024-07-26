from telethon import functions
from telethon.client.telegramclient import TelegramClient
from telethon.tl.custom.message import Message
from telethon.tl.custom.file import File
from telethon.tl.custom.forward import Forward
from telethon.tl.types import (
    Channel,
    InputChannel,
    PeerChannel,
    InputPeerChannel,
    Photo,
    Document,
    TypeMessageMedia,
    InputMessagesFilterUrl,
    InputMessagesFilterVideo,
)
from telethon.tl.types.messages import DialogFilters
from telethon.helpers import TotalList
from telethon.errors import FloodWaitError
from telethon.tl.types.messages import ChatFull as ChatFullMessage, WebPage
from tqdm import tqdm
from dotenv import load_dotenv
from typing import AsyncGenerator, Coroutine, List, Dict, Any, NoReturn, Optional, Tuple, cast, AsyncIterable
import os
import asyncio
import json
import uuid
from datetime import datetime
from sqlmodel import create_engine, Session, select
from models.telegram import MediaItem, MediaType, Channel as ChannelModel, TelegramMetadata

engine = create_engine("sqlite:///teledeck.db", pool_timeout=60)

load_dotenv()  # take environment variables from .env.
api_id = os.environ["TG_API_ID"]
api_hash = os.environ["TG_API_HASH"]
phone = os.environ["TG_PHONE"]
session_file = "user"

QueueItem = Tuple[Channel, Message]
MessageTaskQueue = asyncio.Queue[QueueItem]
Downloadable = Document | File

# Paths
MEDIA_PATH = "./static/media/"
DB_PATH = "./teledeck.db"
UPDATE_PATH = "./data/update_info"
NEST_TQDM = True
DEFAULT_FETCH_LIMIT = 65


class TLContext:
    tclient: TelegramClient
    counter_semaphore: asyncio.Semaphore
    total_tasks: int
    finished_tasks: int
    data: List[Any]

    def __init__(self, tclient: TelegramClient):
        self.tclient = tclient
        self.engine = create_engine(f"sqlite:///{DB_PATH}")
        self.counter_semaphore = asyncio.Semaphore(1)
        self.data = []
        self.finished_tasks = 0
        self.total_tasks = -1
        self.progress_bar: Optional[tqdm[NoReturn]] = None

    async def init_progress(self, total_tasks: int):
        async with self.counter_semaphore:
            print("Found tasks: ", total_tasks)
            self.total_tasks = total_tasks
            self.progress_bar = tqdm(total=total_tasks, desc="Progress", unit="tasks")
            self.progress_bar.update(self.finished_tasks)

    async def update_message(self, new_message: str):
        async with self.counter_semaphore:
            if not self.progress_bar:
                return
            self.progress_bar.set_description(new_message)

    async def update_progress(self):
        async with self.counter_semaphore:
            self.finished_tasks += 1
            if not self.progress_bar:
                return
            self.progress_bar.update(1)
            if self.finished_tasks == self.total_tasks:
                self.progress_bar.close()

    def add_data(self, datum: Any):
        self.data.append(datum)


# Flood prevention
MAX_CONCURRENT_TASKS = 5
DELAY = 0.1
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)


async def exponential_backoff(attempt: int):
    wait_time = 2**attempt
    print(f"Rate limit hit. Waiting for {wait_time} seconds before retrying.")
    await asyncio.sleep(10 * DELAY * wait_time)


async def process_with_backoff(callback: Coroutine[Any, Any, None], task_label: str) -> None:
    async with semaphore:
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                await asyncio.sleep(DELAY)
                await callback
                break
            except FloodWaitError:
                if attempt < max_attempts - 1:
                    await exponential_backoff(attempt)
                else:
                    print(f"Max attempts reached. Skipping: {task_label}")
                    return


class DownloadProgressBar(tqdm):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs, leave=False)

    def update_to(self, current: int, total: int):
        self.total = total
        self.update(current - self.n)


async def download_media(ctx: TLContext, downloadable: Downloadable) -> str | bytes | None:
    if NEST_TQDM:
        with DownloadProgressBar(unit="B", unit_scale=True, desc="Download") as pb:
            return await ctx.tclient.download_media(downloadable, MEDIA_PATH, progress_callback=pb.update_to)
    else:
        return await ctx.tclient.download_media(downloadable, MEDIA_PATH)


def save_to_json(data: Any):
    os.makedirs(UPDATE_PATH, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    unique_id = str(uuid.uuid4())[:4]
    filename = os.path.join(UPDATE_PATH, f"data_{timestamp}_{unique_id}.json")
    with open(filename, "w") as f:
        json.dump(data, f)

    return filename


async def get_message_link(ctx: TLContext, channel: InputChannel, message: Message) -> str:
    messageLinkRequest = functions.channels.ExportMessageLinkRequest(channel, message.id)
    return await ctx.tclient(messageLinkRequest)

def find_web_preview(message: Message) -> (Tuple[Document, int, int] | None):

    if not getattr(message, "web_preview", None):
        return None
    page = message.web_preview
    if not isinstance(page, WebPage):
        return None
    if not isinstance(page.document, Document):
        return None
    if page.document.mime_type == "video/mp4":
        print("Found embedded video")
        download_target = page.document
        return download_target, download_target.id, 1  # has mime_type
    return None


def extract_media(ctx: TLContext, message: Message) -> Tuple[Downloadable, int, int] | None:
    preview = find_web_preview(message)
    if preview:
        return preview
    elif isinstance(message.file, File):
        file: File = message.file
        file_id = file.media.id
        if getattr(file, "size", 0) > 1_000_000_000:
            """
            messageLink = get_message_link(ctx, channel, message)
            print(messageLink.stringify())
            ctx.add_data(messageLink.link)
            """
            print(f"*****Skipping large file*****: {file_id}")
        elif file.sticker_set:
            print(f"Skipping sticker: {file_id}")
        else:
            return file, file_id, 0
    else:
        print(f"No media found: {message.id}")
    return None

async def extract_forwards(ctx: TLContext, forward: Forward) -> None:
    if forward.is_channel:
        # fwd_channel: Channel = await forward.get_input_chat()
        fwd_channel = await ctx.tclient.get_entity(forward.chat_id)
        if not isinstance(fwd_channel, Channel):
            print(f"*************Unexpected non-channel forward: {forward.chat_id}")
            return

        with Session(ctx.engine) as session:
            if not session.exec(select(ChannelModel).where(ChannelModel.id == fwd_channel.id)).first():
                session.add(ChannelModel(id=fwd_channel.id, title=fwd_channel.title))
                session.commit()
                log_msg = {"Forwarded to channel" : fwd_channel.stringify()}
                print(log_msg)
                ctx.add_data(log_msg)



async def process_message(ctx: TLContext, message: Message, channel: Channel) -> None:

    if getattr(message, "forward", None):
        print(f"Found forward: {message.id}")
        await extract_forwards(ctx, message.forward)

    extracted = extract_media(ctx, message)
    if not extracted:
        return

    download_target, file_id, from_preview = extracted

    # Check for existing files
    with Session(engine) as session:
        query = select(MediaItem, TelegramMetadata).where(MediaItem.id == TelegramMetadata.media_item_id).where(TelegramMetadata.file_id == file_id).where(TelegramMetadata.from_preview == from_preview)
        existingResult: Optional[Tuple[MediaItem, TelegramMetadata]] = session.exec(query).first()

    if existingResult is not None:
        (mediaItem, telegramMetadata) = existingResult
        fileSize = getattr(message.file, "size", None)
        if mediaItem.file_size != fileSize:
            print(message.stringify())
            print(mediaItem.file_name)
            raise AssertionError(f"File size mismatch: {mediaItem.file_size} vs {fileSize}")
        # Update legacy entries
        if not telegramMetadata.message_id:
            telegramMetadata.message_id = message.id
            telegramMetadata.channel_id = channel.id
            session.commit()
        print(f"Skipping download for existing file_id: {file_id}")
        return

    mime_type = download_target.mime_type
    if not mime_type:
        print(download_target.stringify())
        raise ValueError("No MIME info.")
    if isinstance(download_target, Document):
        file_path = await download_media(ctx, download_target)
    else:
        file_path = await download_media(ctx, download_target.media)
    if not file_path:
        print(download_target)
        raise ValueError(f"Failed to download file: {file_id}")
    file_name: str = os.path.basename(str(file_path))
    filestat = os.stat(file_path)
    file_size = filestat.st_size


    [mtype, _] = mime_type.split("/")

    match mtype:
        case "video":
            media_type = "video"
        case "image":
            media_type = "image"
        case _:
            media_type = None

    if media_type is None:
        if message.photo:
            media_type = "photo"
        else:
            media_type = "document"
            raise ValueError(f"Unknown media type: {mime_type}")

    with Session(engine) as session:
        media_type_id = session.exec(select(MediaType).where(MediaType.type == media_type)).first().id

    print(f"Media type: {media_type} media_type_id: {media_type_id}")
    new_item_id = uuid.uuid4()
    with Session(engine) as session:
        session.add(
            MediaItem(
                id = new_item_id.hex,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                source_id=1,
                seen = False,
                media_type_id=media_type_id,
                file_size=file_size,
                file_name=file_name,
            )
        )

        session.add(
            TelegramMetadata(
                media_item_id = new_item_id.hex,
                file_id=file_id,
                channel_id=channel.id,
                date=message.date,
                text=message.text,
                url=f"/media/{file_name}",
                message_id=message.id,
                from_preview=from_preview,
            )
        )

        session.commit()
        # await message.mark_read()


async def message_task_wrapper(ctx: TLContext, message: Message, channel: Channel):
    message_label = f"{message.id} - {channel.title}"
    await process_with_backoff(process_message(ctx, message, channel), message_label)
    await message.mark_read()
    await ctx.update_progress()


##### Message filtering strategies


def get_messages(ctx: TLContext, channel: Channel, limit: int):
    return ctx.tclient.iter_messages(channel, limit)


def get_old_messages(ctx: TLContext, channel: Channel, limit: int):
    return ctx.tclient.iter_messages(channel, limit, reverse=True, add_offset=500)


def get_urls(ctx: TLContext, channel: Channel, limit: int):
    return ctx.tclient.iter_messages(channel, filter=InputMessagesFilterUrl)


def get_all_videos(ctx: TLContext, channel: Channel):
    return ctx.tclient.iter_messages(channel, filter=InputMessagesFilterVideo)


async def get_unread_messages(ctx: TLContext, channel: Channel) -> AsyncIterable[Message]:
    full: Any = await ctx.tclient(functions.channels.GetFullChannelRequest(channel))
    if not isinstance(full, ChatFullMessage):
        raise ValueError("Full channel cannot be retrieved")
    full_channel = full.full_chat
    if not isinstance(full_channel.unread_count, int):
        raise ValueError("Unread count not available: ", full_channel.stringify())
    return ctx.tclient.iter_messages(channel, limit=full_channel.unread_count)


def get_new_messages(ctx: TLContext, channel: Channel, limit: int):
    with Session(engine) as session:
        query = (
            select(TelegramMetadata.message_id)
            .where(TelegramMetadata.channel_id == channel.id)
            .order_by(TelegramMetadata.message_id.desc())  # Find the last message_id
        )
        last_seen_post = session.exec(query).first()

    if last_seen_post:
        return ctx.tclient.iter_messages(channel, limit, min_id=last_seen_post)
    else:
        return get_messages(ctx, channel, limit)


def get_earlier_messages(ctx: TLContext, channel: Channel, limit: int):
    with Session(engine) as session:

        query = (
            select(TelegramMetadata.message_id)
            .where(TelegramMetadata.channel_id == channel.id)
            .order_by(TelegramMetadata.message_id)
        )
        oldest_seen_post = session.exec(query).first()

    if oldest_seen_post is not None:
        # TODO: is oldest_seen_post a List??
        return ctx.tclient.iter_messages(channel, limit, offset_id=oldest_seen_post)
    else:
        return get_messages(ctx, channel, limit)


async def get_target_channels(ctx: TLContext) -> List[Channel]:
    chat_folders = await ctx.tclient(functions.messages.GetDialogFiltersRequest())
    if not isinstance(chat_folders, DialogFilters):
        raise ValueError("Could not find folders")

    try:
        media_folder = next(
            (folder for folder in chat_folders.filters if getattr(folder, "title", "") == "MediaView")
        )
    except StopIteration:
        raise NameError("MediaView folder not found.")

    target_channels = await asyncio.gather(
        *[ctx.tclient.get_entity(peer) for peer in media_folder.include_peers if isinstance(peer, InputPeerChannel)]
    )
    print(f"{len(target_channels)} channels found")

    return target_channels


async def message_task_producer(ctx: TLContext, channels: List[Channel], queue: MessageTaskQueue) -> int:
    total_tasks = 0
    for channel in channels:
        async for message in get_channel_messages(ctx, channel):
            total_tasks += 1
            await queue.put((channel, message))
    return total_tasks


async def message_task_consumer(ctx: TLContext, queue: MessageTaskQueue):
    while True:
        (channel, message) = await queue.get()
        try:
            await message_task_wrapper(ctx, message, channel)
        except Exception as e:
            import traceback
            print("******Failed to process message: ", e)
            print(channel.title, message.id, getattr(message, "text", ""), type(message.media))
            print(traceback.format_exc())
            # link = await get_message_link(ctx, channel, message)
            # print("Message link: ", link.stringify())
        queue.task_done()

async def get_channel_messages(ctx: TLContext, channel: Channel) -> AsyncGenerator[Message, None]:
    print(f"Processing channel: {channel.title}")

    # fetch_messages_task = get_messages(ctx, channel, DEFAULT_FETCH_LIMIT)
    # fetch_messages_task = get_old_messages(ctx, channel, DEFAULT_FETCH_LIMIT)
    # fetch_messages_task = get_new_messages(ctx, channel, DEFAULT_FETCH_LIMIT)
    # fetch_messages_task = get_earlier_messages(ctx, channel, DEFAULT_FETCH_LIMIT)
    # fetch_messages_task = get_all_videos(ctx, channel)
    # fetch_messages_task = get_urls(ctx, channel, DEFAULT_FETCH_LIMIT)

    fetch_messages_task = await get_unread_messages(ctx, channel)

    async for message in fetch_messages_task:
        yield message


# PROBLEMS
# 1. How to handle media that is not a file (e.g. web previews)?
# 2. Check what happens to Twitter embeds
# 3. Paginate / search by date?
async def main(load_saved_tasks: bool=False, start_task: int=0):
    tclient = TelegramClient(session_file, int(api_id), api_hash)
    await tclient.connect()
    print("Telegram client connected!")
    ctx = TLContext(tclient)
    print("Database connected!")

    target_channels = await get_target_channels(ctx)
    print("Found channels:")
    [print(f"{n}: {channel.title}") for n, channel in enumerate(target_channels)]
    with Session(engine) as session:
        for channel in target_channels:
            if session.exec(select(ChannelModel).where(ChannelModel.id == channel.id)).first():
                continue
            session.add(ChannelModel(id=channel.id, title=channel.title))
            session.commit()
        # print(channel.stringify)

    queue = asyncio.Queue[QueueItem]()
    # One producer is fine!
    gather_messages = asyncio.create_task(message_task_producer(ctx, target_channels, queue))

    """
    if False:
        if load_saved_tasks:
            channel_tasklists = pickle.load(open("data/channel_tasklists.pkl", "rb"))
        else:
            channel_tasklists = await gather_tasklists(ctx, target_channels)
        if start_task > 0:
            channel_tasklists = channel_tasklists[start_task:]
    """

    consumers = [asyncio.create_task(message_task_consumer(ctx, queue)) for _ in range(MAX_CONCURRENT_TASKS)]

    num_tasks = await gather_messages
    print("******** Done producing*********")
    await ctx.init_progress(num_tasks)

    await queue.join()
    for c in consumers:
        c.cancel()

    print("Processing complete")
    print(f"Finished tasks: {ctx.finished_tasks}")
    if len(ctx.data) > 0:
        filename = save_to_json(ctx.data)
        print(f"Exported data to {filename}")


if __name__ == "__main__":
    import sys

    n = len(sys.argv)
    if n == 1:
        load_saved_tasks = False
        start_task = 0
    elif n == 2:
        load_saved_tasks = True
        start_task = 0
    else:
        load_saved_tasks = True
        start_task = int(sys.argv[2])
    asyncio.get_event_loop().run_until_complete(main(load_saved_tasks, start_task))

