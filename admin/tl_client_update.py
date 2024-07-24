from telethon import functions
from telethon.client.telegramclient import TelegramClient
from telethon.tl.types import (
    Message,
    Channel,
    Dialog,
    InputMessagesFilterUrl,
    InputMessagesFilterVideo,
)
from telethon.tl.types.messages import DialogFilters
from telethon.tl.custom.file import File
from telethon.helpers import TotalList
from telethon.errors import FloodWaitError
from tqdm import tqdm
from dotenv import load_dotenv
from typing import AsyncGenerator, List, Dict, Any, Optional, Tuple, cast
import os
import asyncio
import json
import uuid
from datetime import datetime
from sqlmodel import create_engine, Session, select
from sqlalchemy.engine.base import Engine
from models.telegram import MediaItem, Channel as ChannelModel

engine = create_engine("sqlite:///teledeck.db")

load_dotenv()  # take environment variables from .env.
api_id = os.environ["TG_API_ID"]
api_hash = os.environ["TG_API_HASH"]
phone = os.environ["TG_PHONE"]
session_file = "user"


# Paths
MEDIA_PATH = "./static/media/"
DB_PATH = "./teledeck.db"
UPDATE_PATH = "./data/update_info"
NEST_TQDM = True
DEFAULT_FETCH_LIMIT = 65


class TLContext:
    tclient: TelegramClient
    progress_bar: tqdm
    counter_semaphore: asyncio.Semaphore
    total_tasks: int
    finished_tasks: int
    data: List[Any]
    data_semaphore: asyncio.Semaphore

    def __init__(self, tclient: TelegramClient):
        self.tclient = tclient
        self.engine = create_engine(f"sqlite:///{DB_PATH}")
        self.counter_semaphore = asyncio.Semaphore(1)
        self.data_semaphore = asyncio.Semaphore(1)
        self.data = []
        self.finished_tasks = 0
        self.total_tasks = -1
        self.progress_bar: Optional[tqdm] = None

    async def init_progress(self, total_tasks: int):
        async with self.counter_semaphore:
            print("Found tasks: ", total_tasks)
            self.total_tasks = total_tasks
            self.progress_bar = tqdm(total=total_tasks, desc="Progress", unit="tasks")
            self.progress_bar.update(self.finished_tasks)

    async def update_message(self, new_message):
        async with self.counter_semaphore:
            self.progress_bar.set_description(new_message)

    async def update_progress(self):
        async with self.counter_semaphore:
            self.finished_tasks += 1
            if not self.progress_bar:
                return
            self.progress_bar.update(1)
            if self.finished_tasks == self.total_tasks:
                self.progress_bar.close()

    async def add_data(self, datum):
        async with self.data_semaphore:
            self.data.append(datum)


# Flood prevention
MAX_CONCURRENT_TASKS = 5
DELAY = 0.1
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)


async def exponential_backoff(attempt):
    wait_time = 2**attempt
    print(f"Rate limit hit. Waiting for {wait_time} seconds before retrying.")
    await asyncio.sleep(10 * DELAY * wait_time)


async def process_with_backoff(callback: asyncio.Task, task_label: str) -> None:
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, leave=False)

    def update_to(self, current, total):
        self.total = total
        self.update(current - self.n)


async def download_media(ctx: TLContext, messageOrMedia) -> str:
    if NEST_TQDM:
        with DownloadProgressBar(unit="B", unit_scale=True, desc="Download") as pb:
            return await ctx.tclient.download_media(messageOrMedia, MEDIA_PATH, progress_callback=pb.update_to)
    else:
        return await ctx.tclient.download_media(messageOrMedia, MEDIA_PATH)


def save_to_json(data):
    os.makedirs(UPDATE_PATH, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    unique_id = str(uuid.uuid4())[:4]
    filename = os.path.join(UPDATE_PATH, f"data_{timestamp}_{unique_id}.json")
    with open(filename, "w") as f:
        json.dump(data, f)

    return filename


async def get_message_link(ctx: TLContext, channel: Channel, message: Message):
    messageLinkRequest = functions.channels.ExportMessageLinkRequest(channel, message.id)
    return await ctx.tclient(messageLinkRequest)


def extract_media(ctx: TLContext, message: Message):
    if message.web_preview and message.web_preview.document and message.web_preview.document.mime_type == "video/mp4":
        print("Found embedded video")
        download_target = message.media.webpage.document
        file_id = -1 * download_target.id  # TODO: Fix hack

        return download_target, file_id  # has mime_type

    elif message.file:
        file: File = message.file
        file_id = file.media.id
        if file.size > 1_000_000_000:
            """
            messageLink = get_message_link(ctx, channel, message)
            print(messageLink.stringify())
            await ctx.add_data(messageLink.link)
            """
            print(f"*****Skipping large file*****: {file_id}")
            return None, None
        if file.sticker_set is not None:
            print(f"Skipping sticker: {file_id}")
            return None, None
        return file, file_id

    elif message.web_preview:
        print(f"Skipping web preview: {message.id}")
        return None, None
    else:
        print(f"No media found: {message.id}")
        return None, None


async def process_message(ctx: TLContext, message: Message, channel: Channel) -> None:
    download_target, file_id = extract_media(ctx, message)
    if file_id is None:
        return

    # Check for existing files
    with Session(engine) as session:
        query = select(MediaItem).where(MediaItem.file_id == file_id)
        found = session.exec(query).first()
        if found:
            if found.file_size != message.file.size:
                print(message.stringify())
                print(found.file_name)
                raise AssertionError(f"File size mismatch: {found.file_size} vs {message.file.size}")
            # Update legacy entries
            if not found.message_id:
                found.message_id = message.id
                found.channel_id = channel.id
                session.commit()
            print(f"Skipping download for existing file_id: {file_id}")
            return

    # TODO: Handle different media types better
    if isinstance(download_target, File):
        file_path = await download_media(ctx, message)
    else:
        file_path = await download_media(ctx, download_target)
    file_name = os.path.basename(file_path)

    mime_type = download_target.mime_type if hasattr(download_target, "mime_type") else "/"
    [mtype, subtype] = mime_type.split("/")

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
        session.add(
            MediaItem(
                file_id=file_id,
                channel_id=channel.id,
                date=message.date,
                text=message.text,
                type=media_type,
                file_name=file_name,
                file_size=message.file.size,
                url=f"/media/{file_name}",
                message_id=message.id,
            )
        )
        session.commit()
        await message.mark_read()


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


def get_urls(ctx: TLContext, channel: Channel, limit):
    return ctx.tclient.iter_messages(channel, filter=InputMessagesFilterUrl)


def get_all_videos(ctx: TLContext, channel: Channel):
    return ctx.tclient.iter_messages(channel, filter=InputMessagesFilterVideo)


async def get_unread_messages(ctx: TLContext, channel: Channel):
    full = await ctx.tclient(functions.channels.GetFullChannelRequest(channel))
    full_channel = full.full_chat
    return ctx.tclient.iter_messages(channel, limit=full_channel.unread_count)


def get_new_messages(ctx: TLContext, channel: Channel, limit: int):
    with Session(engine) as session:
        query = (
            select(MediaItem.message_id)
            .where(MediaItem.channel_id == channel.id)
            .where(MediaItem.message_id is not None)
            .order_by(MediaItem.message_id.desc())  # Find the last message_id
        )
        last_seen_post = session.exec(query).first()

    if last_seen_post:
        return ctx.tclient.iter_messages(channel, limit, min_id=last_seen_post)
    else:
        return get_messages(ctx, channel, limit)


def get_earlier_messages(ctx: TLContext, channel: Channel, limit: int):
    with Session(engine) as session:
        query = (
            select(MediaItem.message_id)
            .where(MediaItem.channel_id == channel.id)
            .where(MediaItem.message_id is not None)
            .order_by(MediaItem.message_id)
        )
        oldest_seen_post = session.exec(query).first()

    if oldest_seen_post:
        return ctx.tclient.iter_messages(channel, limit, offset_id=oldest_seen_post[0])
    else:
        return get_messages(ctx, channel, limit)


async def get_target_channels(ctx: TLContext) -> List[Channel]:
    chat_folders: DialogFilters = await ctx.tclient(functions.messages.GetDialogFiltersRequest())

    try:
        media_folder = next(
            (folder for folder in chat_folders.filters if hasattr(folder, "title") and folder.title == "MediaView")
        )
    except StopIteration:
        raise NameError("MediaView folder not found.")

    target_channels: List[Channel] = await asyncio.gather(
        *[ctx.tclient.get_entity(peer) for peer in media_folder.include_peers]
    )
    print(f"{len(target_channels)} channels found")

    return target_channels


async def message_task_producer(ctx: TLContext, channels: List[Channel], queue: asyncio.Queue) -> int:
    total_tasks = 0
    for channel in channels:
        async for message in get_channel_messages(ctx, channel):
            total_tasks += 1
            await queue.put((channel, message))
    return total_tasks


async def message_task_consumer(ctx: TLContext, queue: asyncio.Queue):
    while True:
        task = await queue.get()
        channel = cast(Channel, task[0])
        message = cast(Message, task[1])
        try:
            await message_task_wrapper(ctx, message, channel)
        except Exception as e:
            import traceback
            print("******Failed to process message: ", e)
            print(message.stringify())
            print(traceback.format_exc())
            link = await get_message_link(ctx, channel, message)
            print("Message link: ", link.stringify())
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
async def main(load_saved_tasks=False, start_task=0):
    tclient = TelegramClient(session_file, api_id, api_hash)
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

    queue = asyncio.Queue()
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
    elif n == 3:
        load_saved_tasks = True
        start_task = int(sys.argv[2])
    asyncio.get_event_loop().run_until_complete(main(load_saved_tasks, start_task))

