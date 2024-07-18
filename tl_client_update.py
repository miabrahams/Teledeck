from telethon import functions
from telethon.client.telegramclient import TelegramClient
from telethon.tl.types import Message, Channel, InputMessagesFilterDocument, InputMessagesFilterVideo, InputMessagesFilterPhotoVideo, InputMessagesFilterGif
from telethon.tl.types.messages import DialogFilters
from telethon.tl.custom.file import File
from telethon.errors import FloodWaitError
from tqdm import tqdm
from dotenv import load_dotenv
from typing import List, Dict, Any, Tuple
import os
import asyncio
import sqlite3
import json
import uuid
from datetime import datetime


load_dotenv()  # take environment variables from .env.
api_id = os.environ["TG_API_ID"]
api_hash = os.environ["TG_API_HASH"]
phone = os.environ["TG_PHONE"]
username = "Hex"


# Paths
MEDIA_PATH = "./static/media/"
DB_PATH = "./teledeck.db"
UPDATE_PATH  = './data/update_info'
NEST_TQDM = True
DEFAULT_FETCH_LIMIT = 200


class TLContext:
    conn: sqlite3.Connection
    tclient: TelegramClient
    progress_bar: tqdm
    counter_semaphore: asyncio.Semaphore
    total_tasks: int
    finished_tasks: int
    data: List[Any]
    data_semaphore: asyncio.Semaphore

    def __init__(self, tclient: TelegramClient, conn: sqlite3.Connection):
        self.tclient: TelegramClient = tclient
        self.conn: sqlite3.Connection = conn
        self.counter_semaphore = asyncio.Semaphore(1)
        self.data_semaphore = asyncio.Semaphore(1)
        self.data = []
        self.init_progress(50000)

    def init_progress(self, total_tasks: int):
        print("Found tasks: ", total_tasks)
        self.total_tasks = total_tasks
        self.finished_tasks = 0
        self.progress_bar = tqdm(total=total_tasks, desc="Progress", unit="tasks")

    async def update_message(self, new_message):
        async with self.counter_semaphore:
            self.progress_bar.set_description(new_message)

    async def update_progress(self):
        async with self.counter_semaphore:
            self.finished_tasks += 1
            self.progress_bar.update(1)
            if self.finished_tasks == self.total_tasks:
                self.progress_bar.close()

    async def add_data(self, datum):
        async with self.data_semaphore:
            self.data.append(datum)


# Flood prevention
MAX_CONCURRENT_TASKS = 1
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


async def download_media(ctx: TLContext, message: Message) -> str:
    if NEST_TQDM:
        with DownloadProgressBar(unit="B", unit_scale=True, desc="Download") as pb:
            return await ctx.tclient.download_media(
                message, MEDIA_PATH, progress_callback=pb.update_to
            )
    else:
        return await ctx.tclient.download_media(message, MEDIA_PATH)

def save_to_json(data):
    os.makedirs(UPDATE_PATH, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    unique_id = str(uuid.uuid4())[:4]
    filename = os.path.join(UPDATE_PATH, f"data_{timestamp}_{unique_id}.json")
    with open(filename, 'w') as f:
        json.dump(data, f)

    return filename

async def process_message(ctx: TLContext, message: Message, channel: Channel) -> None:
    # print(f"PROCESS_MESSAGE {message.id} - {channel.title}")
    if message.file:
        file: File = message.file
        file_id = file.media.id
        if file.size > 1_000_000_000:
            """
            messageLinkRequest = functions.channels.ExportMessageLinkRequest(channel, message.id)
            messageLink = await ctx.tclient(messageLinkRequest)
            print(messageLink.stringify())
            await ctx.add_data(messageLink.link)
            """
            print(f"*****Skipping large file*****: {file_id}")
            return
        if file.sticker_set is not None:
            print(f"Skipping sticker: {file_id}")
            return

        # Check if file_id already exists in database
        cursor = ctx.conn.cursor()
        cursor.execute(
            "SELECT file_id, message_id FROM media_items WHERE file_id = ?", (file_id,)
        )
        found = cursor.fetchone()
        if found:
            # If message_id is empty update it
            if not found[1]:
                # Update with channel ID and message ID
                cursor.execute(
                    """
                UPDATE media_items
                set channel_id = ?, message_id = ?
                where file_id = ?
                """,
                    (channel.id, message.id, file_id),
                )
                ctx.conn.commit()

            print(f"Skipping download for existing file_id: {file_id}")
            await message.mark_read()
            return

        file_path = await download_media(ctx, message)
        if file_path:
            file_name = os.path.basename(file_path)

            if message.video or file_name.lower().endswith(".mp4"):
                media_type = "video"
            elif message.gif:
                media_type = "gif"
            elif message.photo:
                media_type = "photo"
            elif message.document:
                mime_type = message.document.mime_type
                media_type = (
                    mime_type.split("/")[-1] if "image/" in mime_type else "document"
                )
            else:
                media_type = "unknown"

            cursor.execute(
                """
            INSERT OR REPLACE INTO media_items
            (file_id, date, channel_id, text, type, file_name, file_size, url, message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    file_id,
                    message.date,
                    channel.id,
                    message.text,
                    media_type,
                    file_name,
                    message.file.size,
                    f"/media/{file_name}",
                    message.id,
                ),
            )
            ctx.conn.commit()
    elif message.web_preview:
        print(f"Skipping web preview: {message.id}")
    else:
        print(f"No media found: {message.id}")


def get_messages(ctx: TLContext, channel: Channel, limit: int):
    return ctx.tclient.iter_messages(channel, limit)


def get_old_messages(ctx: TLContext, channel: Channel, limit: int):
    return ctx.tclient.iter_messages(channel, limit, reverse=True, add_offset=500)

def get_all_videos(ctx: TLContext, channel: Channel):
    return ctx.tclient.iter_messages(channel, filter=InputMessagesFilterVideo)

def get_new_messages(ctx: TLContext, channel: Channel, limit: int):
    cursor = ctx.conn.cursor()
    query = cursor.execute(
        """
        SELECT message_id FROM media_items
        WHERE media_items.channel_id == ?
        AND media_items.message_id IS NOT NULL
        ORDER BY message_id DESC
        """,
        (channel.id,),
    )
    last_seen_post = query.fetchone()

    if last_seen_post:
        return ctx.tclient.iter_messages(channel, limit, min_id=last_seen_post[0])
    else:
        return get_messages(ctx, channel, limit)


def get_earlier_messages(ctx: TLContext, channel: Channel, limit: int):
    cursor = ctx.conn.cursor()
    query = cursor.execute(
        """
        SELECT message_id FROM media_items
        WHERE media_items.channel_id == ?
        AND media_items.message_id IS NOT NULL
        ORDER BY message_id ASC
        """,
        (channel.id,),
    )
    oldest_seen_post = query.fetchone()
    if oldest_seen_post:
        return ctx.tclient.iter_messages(channel, limit, offset_id=oldest_seen_post[0])
    else:
        return get_messages(ctx, channel, limit)


async def get_channel_messages(
    ctx: TLContext, channel: Channel
) -> Tuple[Channel, List[Message]]:
    print(f"Processing channel: {channel.title}")

    # fetch_messages_task = get_messages(ctx, channel, DEFAULT_FETCH_LIMIT)
    # fetch_messages_task = get_old_messages(ctx, channel, DEFAULT_FETCH_LIMIT)
    # fetch_messages_task = get_new_messages(ctx, channel, DEFAULT_FETCH_LIMIT)
    # fetch_messages_task = get_earlier_messages(ctx, channel, DEFAULT_FETCH_LIMIT)
    fetch_messages_task = get_all_videos(ctx, channel)

    messages: List[Message] = []
    async for message in fetch_messages_task:
        messages.append(message)
    return channel, messages



async def message_task_wrapper(ctx: TLContext, message: Message, channel: Channel):
    message_label = f"{message.id} - {channel.title}"
    await process_with_backoff(process_message(ctx, message, channel), message_label)
    await message.mark_read()
    await ctx.update_progress()


async def get_target_channels(ctx: TLContext) -> List[Channel]:
    chat_folders: DialogFilters = await ctx.tclient(
        functions.messages.GetDialogFiltersRequest()
    )

    try:
        media_folder = next(
            (
                folder
                for folder in chat_folders.filters
                if hasattr(folder, "title") and folder.title == "MediaView"
            )
        )
    except StopIteration:
        raise NameError("MediaView folder not found.")

    target_channels: List[Channel] = await asyncio.gather(
        *[ctx.tclient.get_entity(peer) for peer in media_folder.include_peers]
    )
    # Keep only channels where channel.title is not in the database
    # cursor = conn.cursor()
    # cursor.execute('SELECT DISTINCT channel FROM media_items')
    # existing_channels = set(row[0] for row in cursor.fetchall())
    # target_channels = [channel for channel in target_channels if channel.title not in existing_channels]
    # target_channels = [channel for channel in target_channels if channel.title.find("Macro") > -1]

    print(f"{len(target_channels)} channels found")

    return target_channels


# PROBLEMS
# 1. How to handle media that is not a file (e.g. web previews)?
# 2. Check what happens to Twitter embeds
# 3. Paginate / search by date?
async def main():
    tclient = TelegramClient(username, api_id, api_hash)
    await tclient.connect()
    print("Telegram client connected!")
    conn = sqlite3.connect(DB_PATH)
    ctx = TLContext(tclient, conn)
    print("Database connected!")

    target_channels = await get_target_channels(ctx)
    print("Found channels:")
    print([channel.title for channel in target_channels])

    channel_tasklists = await asyncio.gather(
        *[get_channel_messages(ctx, channel) for channel in target_channels]
    )

    message_tasks = [
        message_task_wrapper(ctx, message, channel)
        for (channel, messageList) in channel_tasklists
        for message in messageList
    ]


    ctx.init_progress(len(message_tasks))
    await asyncio.gather(*message_tasks)

    print("Processing complete")
    print(f"Finished tasks: {ctx.finished_tasks}")
    if len(ctx.data) > 0:
        filename = save_to_json(ctx.data)
        print(f"Exported data to {filename}")
    conn.close()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
