from telethon import functions # type: ignore
from telethon.tl.custom.message import Message # type: ignore
from telethon.tl.custom.file import File # type: ignore
from telethon.tl.custom.forward import Forward # type: ignore
from telethon.tl.types import ( # type: ignore
    Channel,
    InputPeerChannel,
    PeerChannel,
    Document,
    DialogFilter,
)
from telethon.tl.types.messages import DialogFilters # type: ignore
from typing import AsyncGenerator, List, Any, Optional, cast
import pathlib
import asyncio
from datetime import datetime
from .config import Settings
from .utils import process_with_backoff
from .QueueManager import QueueManager
from .MessageFetcher import MessageFetcher
from .DatabaseService import DatabaseService
from .types import Downloadable, MediaItem, DownloadItem, ServiceRoutine
from .Logger import RichLogger
from .TLContext import TLContext
from .api import find_web_preview, get_message_link



## TODO: WHERE DID THIS GO
# # semaphore = asyncio.Semaphore(cfg.MAX_CONCURRENT_TASKS)

## TODO: REMOVE FROM GLOBAL
cfg = Settings()


async def download_media(ctx: TLContext, downloadable: Downloadable) -> Optional[pathlib.Path]:
    download_task = ctx.logger.progress.add_task("[cyan]Downloading", total=100)

    def progress_callback(current: int, total: int):
        ctx.logger.progress.update(download_task, completed=current, total=total)

    result = await ctx.client.download_media(downloadable, str(cfg.MEDIA_PATH), progress_callback=progress_callback)

    ctx.logger.progress.remove_task(download_task)

    if isinstance(result, str):
        return pathlib.Path(result)
    return None



async def extract_media(ctx: TLContext, message: Message, channel: Channel) -> MediaItem | None:
    preview = find_web_preview(message)
    if preview:
        return preview
    elif isinstance(message.file, File):
        file: File = message.file
        file_id = file.media.id
        if getattr(file, "size", 0) > 1_000_000_000:
            if cfg.WRITE_MESSAGE_LINKS:
                messageLink = await get_message_link(ctx.client, channel, message)
                if messageLink is not None:
                    ctx.logger.write(messageLink.stringify())
                    ctx.logger.add_data({"large file found": messageLink.link})
            ctx.logger.write(f"*****Skipping large file*****: {file_id}")
        elif file.sticker_set:
            ctx.logger.write(f"Skipping sticker: {file_id}")
        else:
            return MediaItem(file, file_id, False, file.mime_type)
    else:
        ctx.logger.write(f"No media found: {message.id}")
    return None

async def extract_forward(ctx: TLContext, message: Message) -> None:
    forward = getattr(message, "forward")
    if not isinstance(forward, Forward):
        return
    ctx.logger.write(f"Found forward: {message.id}")

    if forward.is_channel:
        # fwd_channel: Channel = await forward.get_input_chat()
        fwd_channel = await ctx.client.get_entity(getattr(forward, "chat_id"))
        if not isinstance(fwd_channel, Channel):
            ctx.logger.write(f"*************Unexpected non-channel forward: {getattr(forward, 'chat_id')}")
            return

    ctx.db.add_channel_if_not_exists(ctx.logger, fwd_channel.id, fwd_channel.title)


async def process_message(ctx: TLContext, message: Message, channel: Channel) -> None:

    await extract_forward(ctx, message)

    item = await extract_media(ctx, message, channel)
    if not item:
        return

    if isinstance(item.target, Document | File):
        file_path = await download_media(ctx, item.target)
    else:
        if item.target.media is None:
            ctx.logger.write("No target found")
            return
        file_path = await download_media(ctx, item.target.media)
    if not file_path:
        ctx.logger.write(repr(item.target))
        raise ValueError(f"Failed to download file: {item.id}")

    file_path = pathlib.Path(file_path)
    file_name = file_path.parts[-1]
    file_size = file_path.stat().st_size
    mime_type = item.mime_type

    if mime_type is None:
        ctx.logger.write("WARNING: No MIME info.")
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
        ctx.db.save_media_item(ctx.logger, dlItem, channel.id, message)
    except Exception as e:
        ctx.logger.write(f"Database insertion failed: {e}")
        file_path.rename(cfg.ORPHAN_PATH / file_name)
        ctx.logger.write(f"Moved {file_name} to orphans directory.")

    await message.mark_read()


async def message_task_wrapper(ctx: TLContext, message: Message, channel: Channel):
    try: # Process message
        cb = process_message(ctx, message, channel)
        await process_with_backoff(cb, cfg.MAX_RETRY_ATTEMPTS, cfg.RETRY_BASE_DELAY, cfg.SLOW_MODE, cfg.SLOW_MODE_DELAY)
        await message.mark_read()
    except Exception as e:
        ctx.logger.write(f"Failed to process message: {message.id} in channel {channel.title}")
        ctx.logger.write(repr(e))
    await ctx.logger.update_progress()


async def get_target_channels(ctx: TLContext) -> AsyncGenerator[Channel, None]:
    # TODO: Extract this filtering logic to a separate function
    # nameMatch = ChannelModel.title.like("%Khael%")
    channel_models = ctx.db.get_channels_to_check([])

    for channel_model in channel_models:
        try:
            inputPeerChannel = await ctx.client.get_input_entity(PeerChannel(channel_model.id))
            channel = await ctx.client.get_entity(inputPeerChannel)
            if not isinstance(channel, Channel):
                raise ValueError(f"Channel not found: {channel_model.id}. Got {channel}")
            yield channel
        except Exception as e:
            if isinstance(channel, Channel):
                err_msg = f"Failed to get channel: {channel_model.id} {channel.title}"
            else:
                err_msg = f"Failed to get channel: {channel_model.id}"
            ctx.logger.write(err_msg)
            ctx.logger.write(str(e))
            ctx.logger.add_data(err_msg)
            ctx.logger.add_data(str(e))


    # channelTasks = [ctx.client.get_entity() for channel_id in channel_ids]
    # target_channels = await asyncio.gather(*channelTasks)
    # ctx.logger.write(f"{len(target_channels)} channels found")
    # return cast(List[Channel], target_channels)


async def get_update_folder_channels(ctx: TLContext) -> List[Channel]:
    chat_folders: Any  = await ctx.client(functions.messages.GetDialogFiltersRequest())
    if not isinstance(chat_folders, DialogFilters):
        raise ValueError("Could not find folders")

    try:
        media_folder = next(
            (folder for folder in chat_folders.filters if isinstance(folder, DialogFilter) and folder.title == "MediaView")
        )
    except StopIteration:
        raise NameError("MediaView folder not found.")

    peer_channels = [peer for peer in media_folder.include_peers if isinstance(peer, InputPeerChannel)]

    target_channels = await asyncio.gather( *[ctx.client.get_entity(peer) for peer in peer_channels])
    ctx.logger.write(f"{len(target_channels)} channels found")

    return cast(List[Channel], target_channels)


async def channel_check_list_sync(cfg: Settings, ctx: TLContext):
    target_channels = await get_update_folder_channels(ctx)
    ctx.logger.write("Found channels:")
    titles = [f"{n}: {channel.title}" for n, channel in enumerate(target_channels)]
    ctx.logger.write("\n".join(titles))
    ctx.db.update_channel_list(target_channels)


async def with_context(cb: ServiceRoutine):
    cfg = Settings()
    db_service = DatabaseService(cfg.DB_PATH)
    logger = RichLogger(cfg.UPDATE_PATH)
    async with TLContext(cfg, logger, db_service) as ctx:
        await cb(cfg, ctx)


async def client_update(cfg: Settings, ctx: TLContext):
    qm = QueueManager(ctx.logger, cfg.MAX_CONCURRENT_TASKS)

    mf = MessageFetcher(ctx.client, ctx.db, cfg)
    gather_messages = asyncio.create_task(
        qm.producer(
            get_target_channels(ctx),
            mf.get_channel_messages
        ))


    def process_message(message: Message, channel: Channel):
        return message_task_wrapper(ctx, message, channel)
    qm.create_consumers(process_message)

    num_tasks = await gather_messages
    ctx.logger.write("Tasks gathered: ", num_tasks)

    await ctx.logger.run(num_tasks, qm.wait())

    qm.finish()

    ctx.logger.write(f"Gathered tasks: {num_tasks}")
    ctx.logger.write(f"Finished tasks: {ctx.logger.progress.tasks[0].completed}")
    ctx.logger.write(f"Update complete: {datetime.now()}")
