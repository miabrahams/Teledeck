from telethon import functions # type: ignore
from telethon.client.telegramclient import TelegramClient # type: ignore
from telethon.tl.custom.message import Message # type: ignore
from telethon.tl.custom.file import File # type: ignore
from telethon.tl.custom.forward import Forward # type: ignore
from telethon.tl.types import ( # type: ignore
    Channel,
    InputChannel,
    InputPeerChannel,
    PeerChannel,
    Document,
    DialogFilter,
    ExportedMessageLink
)
from telethon.tl.types.messages import ChatFull as WebPage, DialogFilters # type: ignore
from typing import AsyncGenerator, List, Any, Optional, cast
import pathlib
import asyncio
from datetime import datetime
from sqlmodel import create_engine, Session, select
from sqlalchemy.engine import Engine
from models.telegram import ChannelModel
from .config import Settings
from .DataLogger import DataLogger
from .ConsoleLogger import RichConsoleLogger
from .utils import process_with_backoff
from .DatabaseService import DatabaseService
from . import messageStrategies as strat
from .types import QueueItem, MessageTaskQueue, Downloadable, MediaItem, DownloadItem



cfg = Settings()

semaphore = asyncio.Semaphore(cfg.MAX_CONCURRENT_TASKS)


# TODO: Enable cleanup using `with` statement; __enter__ and __exit__
# TODO: Remove async from console operations
class TLContext:
    tclient: TelegramClient
    data: List[Any]
    logger: DataLogger
    console: RichConsoleLogger
    db: DatabaseService
    engine: Engine

    def __init__(self, tclient: TelegramClient, engine: Engine):
        self.tclient = tclient
        self.engine = engine
        self.db = DatabaseService(engine)
        self.overall_task = None
        self.data = []
        self.logger = DataLogger(cfg.UPDATE_PATH)
        self.console = RichConsoleLogger()

    def write(self, *args, **kwargs) -> None:
        # TODO: Move to logger
        self.console.write(*args, **kwargs)

    def save_data(self) -> None:
        # TODO: Make this automatic
        self.logger.save_data()


async def get_context():
    tclient = TelegramClient(cfg.SESSION_FILE, int(cfg.TELEGRAM_API_ID), cfg.TELEGRAM_API_HASH)
    conn = tclient.connect()
    engine = create_engine(f"sqlite:///{cfg.DB_PATH}")
    await conn
    ctx = TLContext(tclient, engine)
    return ctx




async def download_media(ctx: TLContext, downloadable: Downloadable) -> Optional[pathlib.Path]:
    download_task = ctx.console.progress.add_task("[cyan]Downloading", total=100)

    def progress_callback(current: int, total: int):
        ctx.console.progress.update(download_task, completed=current, total=total)

    result = await ctx.tclient.download_media(downloadable, str(cfg.MEDIA_PATH), progress_callback=progress_callback)

    ctx.console.progress.remove_task(download_task)

    if isinstance(result, str):
        return pathlib.Path(result)
    return None




async def get_message_link(ctx: TLContext, channel: InputChannel, message: Message) -> Optional[ExportedMessageLink]:
    messageLinkRequest = functions.channels.ExportMessageLinkRequest(channel, message.id)
    result: Any = await ctx.tclient(messageLinkRequest)
    if isinstance(result, ExportedMessageLink):
        return result
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


async def extract_media(ctx: TLContext, message: Message) -> MediaItem | None:
    preview = find_web_preview(message)
    if preview:
        return preview
    elif isinstance(message.file, File):
        file: File = message.file
        file_id = file.media.id
        if getattr(file, "size", 0) > 1_000_000_000:
            """
            messageLink = get_message_link(ctx, channel, message)
            ctx.write(messageLink.stringify())
            ctx.add_data(messageLink.link)
            """
            ctx.write(f"*****Skipping large file*****: {file_id}")
        elif file.sticker_set:
            ctx.write(f"Skipping sticker: {file_id}")
        else:
            return MediaItem(file, file_id, False, file.mime_type)
    else:
        ctx.write(f"No media found: {message.id}")
    return None

async def extract_forward(ctx: TLContext, message: Message) -> None:
    forward = getattr(message, "forward")
    if not isinstance(forward, Forward):
        return
    ctx.write(f"Found forward: {message.id}")

    if forward.is_channel:
        # fwd_channel: Channel = await forward.get_input_chat()
        fwd_channel = await ctx.tclient.get_entity(getattr(forward, "chat_id"))
        if not isinstance(fwd_channel, Channel):
            ctx.write(f"*************Unexpected non-channel forward: {getattr(forward, 'chat_id')}")
            return

        with Session(ctx.engine) as session:
            if not session.exec(select(ChannelModel).where(ChannelModel.id == fwd_channel.id)).first():
                session.add(ChannelModel(id=fwd_channel.id, title=fwd_channel.title))
                session.commit()
                log_msg = {"Forwarded to channel" : fwd_channel.stringify()}
                ctx.write(repr(log_msg))
                ctx.logger.add_data(log_msg)



async def process_message(ctx: TLContext, message: Message, channel: Channel) -> None:

    await extract_forward(ctx, message)

    item = await extract_media(ctx, message)
    if not item:
        return

    if isinstance(item.target, Document | File):
        file_path = await download_media(ctx, item.target)
    else:
        if item.target.media is None:
            ctx.write("No target found")
            return
        file_path = await download_media(ctx, item.target.media)
    if not file_path:
        ctx.write(repr(item.target))
        raise ValueError(f"Failed to download file: {item.id}")

    file_path = pathlib.Path(file_path)
    file_name = file_path.parts[-1]
    file_size = file_path.stat().st_size
    mime_type = item.mime_type

    if mime_type is None:
        ctx.write("WARNING: No MIME info.")
        mime_type = "unknown/unknown"

    [mtype, _] = mime_type.split("/")
    media_type = {"video": "video", "image": "image"}.get(mtype, None)

    if media_type is None:
        if message.photo:
            media_type = "photo"
        else:
            media_type = "document"

    dlItem = DownloadItem(
        **item.__dict__, file_name=file_name, file_size=file_size, mime_type=mime_type, media_type=media_type
    )

    try:
        ctx.db.save_media_item(ctx.console, dlItem, channel.id, message)
    except Exception as e:
        ctx.write(f"Database insertion failed: {e}")
        file_path.rename(cfg.ORPHAN_PATH / file_name)
        ctx.write(f"Moved {file_name} to orphans directory.")

    await message.mark_read()


async def message_task_wrapper(ctx: TLContext, message: Message, channel: Channel):
    try: # Process message
        cb = process_message(ctx, message, channel)
        await process_with_backoff(cb, cfg.MAX_RETRY_ATTEMPTS, cfg.RETRY_BASE_DELAY, cfg.SLOW_MODE, cfg.SLOW_MODE_DELAY)
        await message.mark_read()
    except Exception as e:
        ctx.write(f"Failed to process message: {message.id} in channel {channel.title}")
        ctx.write(repr(e))
    await ctx.console.update_progress()


async def get_target_channels(ctx: TLContext) -> AsyncGenerator[Channel, None]:
    with Session(ctx.engine) as session:
        # XXX: Extract this filtering logic to a separate function
        channel_ids = session.exec(select(ChannelModel).where(ChannelModel.check == 1).where(ChannelModel.title.like("%Khael%"))).all()

    for channel_id in channel_ids:
        try:
            input_id = await ctx.tclient.get_input_entity(PeerChannel(channel_id.id))
            channel = await ctx.tclient.get_entity(input_id)
            if not isinstance(channel, Channel):
                raise ValueError(f"Channel not found: {channel_id.id}. Got {channel}")
            yield channel
        except Exception as e:
            if isinstance(channel, Channel):
                err_msg = f"Failed to get channel: {channel_id.id} {channel.title}"
            else:
                err_msg = f"Failed to get channel: {channel_id.id}"
            ctx.write(err_msg)
            ctx.write(str(e))
            ctx.logger.add_data(err_msg)
            ctx.logger.add_data(str(e))


    # channelTasks = [ctx.tclient.get_entity() for channel_id in channel_ids]
    # target_channels = await asyncio.gather(*channelTasks)
    # ctx.write(f"{len(target_channels)} channels found")
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
    ctx.write(f"{len(target_channels)} channels found")

    return cast(List[Channel], target_channels)


async def channel_check_list_sync(ctx: TLContext):
    target_channels = await get_update_folder_channels(ctx)
    ctx.write("Found channels:")
    titles = [f"{n}: {channel.title}" for n, channel in enumerate(target_channels)]
    ctx.write("\n".join(titles))
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
            ctx.write("******Failed to process message: \n" + str(e))
            ctx.write("\n".join(map(str, [channel.title, message.id, getattr(message, "text", ""), type(message.media)])))
            ctx.write(traceback.format_exc())
            # link = await get_message_link(ctx, channel, message)
            # print("Message link: ", link.stringify())
        queue.task_done()


async def get_channel_messages(context: TLContext, channel: Channel) -> AsyncGenerator[Message, None]:
    """Get messages from a channel based on strategy."""
    context.write(f"Processing channel: {channel.title}")
    limit = cfg.DEFAULT_FETCH_LIMIT
    tclient = context.tclient

    match cfg.MESSAGE_STRATEGY:
        case "all":
            strategy = strat.get_all_messages(tclient, channel, limit)
        case "db":
            last_seen_post = context.db.get_last_seen_post(channel.id)
            strategy = strat.get_messages_since_db_update(tclient, channel, last_seen_post, limit)
        case "oldest":
            strategy = strat.get_oldest_messages(tclient, channel, limit)
        case "before":
            before_id = context.db.get_last_seen_post(channel.id)
            strategy = strat.get_earlier_unseen_messages(tclient, channel, before_id, limit)
        case "urls":
            strategy = strat.get_urls(tclient, channel, limit)
        case "videos":
            strategy = strat.get_all_videos(tclient, channel, limit)
        case "unread":
            strategy = await strat.get_unread_messages(tclient, channel)

    async for message in strategy:
        yield message


async def client_update(ctx: TLContext):
    queue = asyncio.Queue[QueueItem]()

    gather_messages = asyncio.create_task(message_task_producer(ctx, get_target_channels(ctx), queue))

    consumers = [asyncio.create_task(message_task_consumer(ctx, queue)) for _ in range(cfg.MAX_CONCURRENT_TASKS)]

    num_tasks = await gather_messages
    ctx.write("Tasks gathered: ", num_tasks)

    await ctx.console.run(num_tasks, queue.join())

    for c in consumers:
        c.cancel()

    ctx.write(f"Gathered tasks: {num_tasks}")
    ctx.write(f"Finished tasks: {ctx.console.progress.tasks[0].completed}")
    ctx.write(f"Update complete: {datetime.now()}")
