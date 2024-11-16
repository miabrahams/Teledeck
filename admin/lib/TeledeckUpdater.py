from telethon.tl.custom.message import Message # type: ignore
from telethon.tl.types import Channel
import asyncio
from datetime import datetime
from .config import Settings, BackoffConfig, ProcessingConfig, QueueManagerConfig, StrategyConfig
from BackoffManager import BackoffManager
from QueueManager import QueueManager
from MessageFetcher import MessageFetcher
from TLContext import TLContext
from MediaProcessor import MediaProcessor
from ChannelManager import ChannelManager

class TeledeckUpdater:
    def __init__(self, cfg: Settings, ctx: TLContext):
        self.ctx = ctx
        self.logger = ctx.logger
        self.queue_manager = QueueManager(self.logger, QueueManagerConfig.from_config(cfg))
        self.cm = ChannelManager(ctx)
        self.backoff = BackoffManager(BackoffConfig.from_config(cfg))
        self.mf = MessageFetcher(ctx.client, ctx.db, StrategyConfig.from_config(cfg))
        self.processor = MediaProcessor(ctx, ProcessingConfig.from_config(cfg))

    async def process_message(self, message: Message, channel: Channel):
        await self.processor.process_message(message, channel)
        await message.mark_read()


    async def message_task_wrapper(self, message: Message, channel: Channel):
        try: # Process message
            cb = self.process_message(message, channel)
            await self.backoff.process_with_backoff(cb)
            await message.mark_read()
        except Exception as e:
            self.logger.write(f"Failed to process message: {message.id} in channel {channel.title}")
            self.logger.write(repr(e))
        await self.logger.update_progress()


    async def run_update(self):
        gather_messages = asyncio.create_task(
            self.queue_manager.producer(
                self.cm.get_target_channels(),
                self.mf.get_channel_messages
            ))

        def process_message(message: Message, channel: Channel):
            return self.message_task_wrapper(message, channel)
        self.queue_manager.create_consumers(process_message)

        num_tasks = await gather_messages
        self.logger.write("Tasks gathered: ", num_tasks)

        await self.logger.run(num_tasks, self.queue_manager.wait())

        self.queue_manager.finish()

        self.logger.write(f"Gathered tasks: {num_tasks}")
        self.logger.write(f"Finished tasks: {self.logger.progress.tasks[0].completed}")
        self.logger.write(f"Update complete: {datetime.now()}")
