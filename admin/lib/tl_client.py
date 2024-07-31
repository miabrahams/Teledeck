from telethon import functions # type: ignore
from telethon.client.telegramclient import TelegramClient # type: ignore
from telethon.tl.custom.message import Message # type: ignore
from telethon.tl.custom.file import File # type: ignore
from telethon.tl.custom.forward import Forward # type: ignore
from telethon.tl.types import ( # type: ignore
    Channel,
    InputChannel,
    InputPeerChannel,
    Document,
    DialogFilter,
    TypeMessageMedia,
    InputMessagesFilterUrl,
    InputMessagesFilterVideo,
    ExportedMessageLink
)
from telethon.hints import Entity # type: ignore
from telethon.errors import FloodWaitError # type: ignore
from telethon.tl.types.messages import ChatFull as ChatFullMessage, WebPage, DialogFilters # type: ignore
from tqdm import tqdm
from dotenv import load_dotenv
from typing import AsyncGenerator, Coroutine, List, Any, NoReturn, Optional, Tuple, cast, AsyncIterable
from os import environ
import pathlib
import asyncio
import json
import uuid
from datetime import datetime
from sqlmodel import create_engine, Session, select, Column, Integer
from models.telegram import MediaItem, MediaType, Channel as ChannelModel, TelegramMetadata


load_dotenv()  # take environment variables from .env.
api_id = environ["TG_API_ID"]
api_hash = environ["TG_API_HASH"]
phone = environ["TG_PHONE"]
session_file = "user"

QueueItem = Tuple[Channel, Message]
MessageTaskQueue = asyncio.Queue[QueueItem]
Downloadable = Document | File

# Paths
MEDIA_PATH = pathlib.Path("./static/media/")
ORPHAN_PATH = pathlib.Path("./recyclebin/orphan/")
DB_PATH = pathlib.Path("./teledeck.db")
UPDATE_PATH = pathlib.Path("./data/update_info")
NEST_TQDM = True
DEFAULT_FETCH_LIMIT = 65

# TODO: Enable cleanup using `with` statement; __enter__ and __exit__
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

    def save_data(self):
        if len(self.data) > 0:
            filename = save_to_json(self.data)
            print(f"Exported data to {filename}")

async def get_context():
    tclient = TelegramClient(session_file, int(api_id), api_hash)
    await tclient.connect()
    ctx = TLContext(tclient)
    return ctx


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


class DownloadProgressBar(tqdm): # type: ignore
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs, leave=False) # type: ignore

    def update_to(self, current: int, total: int):
        self.total = total
        self.update(current - self.n)


# download_media accepts Message, Media or Document. (Jul 2024)
async def download_media(ctx: TLContext, downloadable: Message | TypeMessageMedia | Document) -> Optional[pathlib.Path]:
    if NEST_TQDM:
        with DownloadProgressBar(unit="B", unit_scale=True, desc="Download") as pb:
            result = await ctx.tclient.download_media(downloadable, str(MEDIA_PATH), progress_callback=pb.update_to)
    else:
        result = await ctx.tclient.download_media(downloadable, str(MEDIA_PATH))

    if isinstance(result, str):
        return pathlib.Path(result)
    return None


def save_to_json(data: Any):
    UPDATE_PATH.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    unique_id = str(uuid.uuid4())[:4]
    filename = UPDATE_PATH / f"data_{timestamp}_{unique_id}.json"

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    return filename


async def get_message_link(ctx: TLContext, channel: InputChannel, message: Message) -> Optional[ExportedMessageLink]:
    messageLinkRequest = functions.channels.ExportMessageLinkRequest(channel, message.id)
    result: Any = await ctx.tclient(messageLinkRequest)
    if isinstance(result, ExportedMessageLink):
        return result
    return None

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

async def extract_forward(ctx: TLContext, message: Message) -> None:
    forward = getattr(message, "forward")
    if not isinstance(forward, Forward):
        return
    print(f"Found forward: {message.id}")

    if forward.is_channel:
        # fwd_channel: Channel = await forward.get_input_chat()
        fwd_channel = await ctx.tclient.get_entity(getattr(forward, "chat_id"))
        if not isinstance(fwd_channel, Channel):
            print(f"*************Unexpected non-channel forward: {getattr(forward, 'chat_id')}")
            return

        with Session(ctx.engine) as session:
            if not session.exec(select(ChannelModel).where(ChannelModel.id == fwd_channel.id)).first():
                session.add(ChannelModel(id=fwd_channel.id, title=fwd_channel.title))
                session.commit()
                log_msg = {"Forwarded to channel" : fwd_channel.stringify()}
                print(log_msg)
                ctx.add_data(log_msg)



async def process_message(ctx: TLContext, message: Message, channel: Channel) -> None:

    await extract_forward(ctx, message)

    extracted = extract_media(ctx, message)
    if not extracted:
        return

    download_target, file_id, from_preview = extracted

    # Check for existing files
    with Session(ctx.engine) as session:
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


    if isinstance(download_target, Document):
        mime_type = download_target.mime_type
        file_path = await download_media(ctx, download_target)
    else:
        mime_type = download_target.mime_type
        file_path = await download_media(ctx, download_target.media)
    if not file_path:
        print(download_target)
        raise ValueError(f"Failed to download file: {file_id}")

    file_path = pathlib.Path(file_path)
    new_item_id = uuid.uuid4().hex
    file_name = file_path.parts[-1]
    file_size = file_path.stat().st_size

    if mime_type is None:
        print("WARNING: No MIME info.")
        mime_type = "unknown/unknown"

    [mtype, _] = mime_type.split("/")
    media_type = {"video": "video", "image": "image"}.get(mtype, None)

    if media_type is None:
        if message.photo:
            media_type = "photo"
        else:
            media_type = "document"
    print(f"mime_type: {mime_type}   -  Media type: {media_type}")

    try:
        with Session(ctx.engine) as session:
            media_type_query = session.exec(select(MediaType).where(MediaType.type == media_type)).first()
            if not media_type_query:
                raise ValueError(f"Media type not found: {media_type}")
            session.add(
                MediaItem(
                    id = new_item_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    source_id=1,
                    seen = False,
                    media_type_id=media_type_query.id,
                    file_size=file_size,
                    file_name=file_name,
                )
            )

            session.add(
                TelegramMetadata(
                    media_item_id = new_item_id,
                    file_id=file_id,
                    channel_id=channel.id,
                    date=getattr(message, "date", datetime.now()),
                    text=getattr(message, "text", ""),
                    url=f"/media/{file_name}",
                    message_id=message.id,
                    from_preview=from_preview,
                )
            )

            session.commit()
    except Exception as e:
        print(f"Database insertion failed: {e}")
        file_path.rename(ORPHAN_PATH / file_name)
        print(f"Moved {file_name} to orphans directory.")

    await message.mark_read()


async def message_task_wrapper(ctx: TLContext, message: Message, channel: Channel):
    message_label = f"{message.id} - {channel.title}"
    await process_with_backoff(process_message(ctx, message, channel), message_label)
    await message.mark_read()
    await ctx.update_progress()


##### Message filtering strategies


def get_messages(ctx: TLContext, entity: Entity, limit: int)-> AsyncIterable[Message]:
    return ctx.tclient.iter_messages(entity, limit)


def get_old_messages(ctx: TLContext, entity: Entity, limit: int):
    return ctx.tclient.iter_messages(entity, limit, reverse=True, add_offset=500)


def get_urls(ctx: TLContext, entity: Entity, limit: int):
    return ctx.tclient.iter_messages(entity, filter=InputMessagesFilterUrl)


def get_all_videos(ctx: TLContext, entity: Entity):
    return ctx.tclient.iter_messages(entity, filter=InputMessagesFilterVideo)


async def get_unread_messages(ctx: TLContext, channel: Channel) -> AsyncIterable[Message]:
    full: Any = await ctx.tclient(functions.channels.GetFullChannelRequest(cast(InputChannel, channel)))
    if not isinstance(full, ChatFullMessage):
        raise ValueError("Full channel cannot be retrieved")
    full_channel = full.full_chat
    unread_count = getattr(full_channel, "unread_count")
    if not isinstance(unread_count, int):
        raise ValueError("Unread count not available: ", full_channel.stringify())
    return ctx.tclient.iter_messages(channel, limit=unread_count)


def get_new_messages(ctx: TLContext, channel: Channel, limit: int):
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
        return get_messages(ctx, channel, limit)


def get_earlier_messages(ctx: TLContext, channel: Channel, limit: int):
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
        return get_messages(ctx, channel, limit)


async def get_target_channels(ctx: TLContext) -> AsyncGenerator[Channel, None]:
    with Session(ctx.engine) as session:
        channel_ids = session.exec(select(ChannelModel).where(ChannelModel.check == True)).all()


    for channel_id in channel_ids:
        input_id = await ctx.tclient.get_input_entity(channel_id.id)
        channel = await ctx.tclient.get_entity(input_id)
        if not isinstance(channel, Channel):
            raise ValueError(f"Channel not found: {channel_id.id}. Got {channel}")
        yield channel


    # channelTasks = [ctx.tclient.get_entity() for channel_id in channel_ids]
    # target_channels = await asyncio.gather(*channelTasks)
    # print(f"{len(target_channels)} channels found")
    # return cast(List[Channel], target_channels)


async def get_update_folder_channels(ctx: TLContext) -> List[Channel]:
    chat_folders: Any  = await ctx.tclient(functions.messages.GetDialogFiltersRequest())
    if not isinstance(chat_folders, DialogFilters):
        raise ValueError("Could not find folders")

    try:
        media_folder = next(
            (folder for folder in chat_folders.filters if isinstance(folder, DialogFilter) and folder.title == "MediaView")
        )
    except StopIteration:
        raise NameError("MediaView folder not found.")

    peer_channels = [peer for peer in media_folder.include_peers if isinstance(peer, InputPeerChannel)]

    target_channels = await asyncio.gather( *[ctx.tclient.get_entity(peer) for peer in peer_channels])
    print(f"{len(target_channels)} channels found")

    return cast(List[Channel], target_channels)


async def channel_check_list_sync(ctx: TLContext):
    target_channels = await get_update_folder_channels(ctx)
    print("Found channels:")
    [print(f"{n}: {channel.title}") for n, channel in enumerate(target_channels)]
    with Session(ctx.engine) as session:
        for channel in session.exec(select(ChannelModel)).all():
            channel.check = False
        session.commit()

    with Session(ctx.engine) as session:
        for channel in target_channels:
            existingChannel = session.get(ChannelModel, {"id": channel.id})
            if existingChannel:
                existingChannel.check = True
                session.commit()
            else:
                session.add(ChannelModel(id=channel.id, title=channel.title, check=True))
                session.commit()



async def message_task_producer(ctx: TLContext, channels: AsyncGenerator[Channel, None], queue: MessageTaskQueue) -> int:
    total_tasks = 0
    async for channel in channels:
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


async def client_update(ctx: TLContext):
    queue = asyncio.Queue[QueueItem]()

    gather_messages = asyncio.create_task(message_task_producer(ctx, get_target_channels(ctx), queue))

    consumers = [asyncio.create_task(message_task_consumer(ctx, queue)) for _ in range(MAX_CONCURRENT_TASKS)]

    num_tasks = await gather_messages
    print("******** Done producing*********")
    await ctx.init_progress(num_tasks)

    await queue.join()
    for c in consumers:
        c.cancel()

    print("Processing complete")
    print(f"Finished tasks: {ctx.finished_tasks}")
    ctx.save_data()
