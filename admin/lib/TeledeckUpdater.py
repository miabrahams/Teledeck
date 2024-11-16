from telethon.tl.custom.message import Message # type: ignore
from telethon.tl.types import Channel
import asyncio
from datetime import datetime
from .config import Settings
from .utils import BackoffConfig, process_with_backoff
from .QueueManager import QueueManager
from .MessageFetcher import MessageFetcher
from .DatabaseService import DatabaseService
from .types import ServiceRoutine
from .Logger import RichLogger
from .TLContext import TLContext
from .MediaProcessor import MediaProcessor, ProcessingConfig
from .ChannelManager import ChannelManager


async def with_context(cb: ServiceRoutine):
    cfg = Settings()
    db_service = DatabaseService(cfg.DB_PATH)
    logger = RichLogger(cfg.UPDATE_PATH)
    async with TLContext(cfg, logger, db_service) as ctx:
        await cb(cfg, ctx)


class TeledeckUpdater:
    def __init__(self, cfg: Settings, ctx: TLContext):
        self.cfg = cfg
        self.ctx = ctx
        self.logger = ctx.logger
        self.processor = MediaProcessor(ctx, ProcessingConfig.from_config(cfg))
        self.backoff_config = BackoffConfig(
                cfg.MAX_RETRY_ATTEMPTS,
                cfg.RETRY_BASE_DELAY,
                cfg.SLOW_MODE,
                cfg.SLOW_MODE_DELAY)

    async def process_message(self, message: Message, channel: Channel):
        await self.processor.process_message(message, channel)
        await message.mark_read()


    async def message_task_wrapper(self, message: Message, channel: Channel):
        try: # Process message
            cb = self.process_message(message, channel)
            await process_with_backoff(cb, self.backoff_config)
            await message.mark_read()
        except Exception as e:
            self.logger.write(f"Failed to process message: {message.id} in channel {channel.title}")
            self.logger.write(repr(e))
        await self.logger.update_progress()


    async def run_update(self):
        qm = QueueManager(self.logger, self.cfg.MAX_CONCURRENT_TASKS)
        cm = ChannelManager(self.ctx)

        mf = MessageFetcher(self.ctx.client, self.ctx.db, self.cfg)
        gather_messages = asyncio.create_task(
            qm.producer(
                cm.get_target_channels(),
                mf.get_channel_messages
            ))

        def process_message(message: Message, channel: Channel):
            return self.message_task_wrapper(message, channel)
        qm.create_consumers(process_message)

        num_tasks = await gather_messages
        self.logger.write("Tasks gathered: ", num_tasks)

        await self.logger.run(num_tasks, qm.wait())

        qm.finish()

        self.logger.write(f"Gathered tasks: {num_tasks}")
        self.logger.write(f"Finished tasks: {self.logger.progress.tasks[0].completed}")
        self.logger.write(f"Update complete: {datetime.now()}")
