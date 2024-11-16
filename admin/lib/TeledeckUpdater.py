import asyncio
from datetime import datetime
from telethon.tl.custom.message import Message # type: ignore
from telethon.tl.types import Channel
from .config import Settings, BackoffConfig, ProcessingConfig, QueueManagerConfig, StrategyConfig, UpdaterConfig
from BackoffManager import BackoffManager
from QueueManager import QueueManager
from MessageFetcher import MessageFetcher
from TLContext import TLContext
from MediaProcessor import MediaProcessor
from ChannelManager import ChannelManager
from channelStrategies import ChannelProvider

class TeledeckUpdater:
    def __init__(self, cfg: Settings, ctx: TLContext):
        self.ctx = ctx
        self.logger = ctx.logger
        self.queue_manager = QueueManager(self.logger, QueueManagerConfig.from_config(cfg))
        self.cm = ChannelManager(ctx)
        self.backoff = BackoffManager(BackoffConfig.from_config(cfg))
        self.processor = MediaProcessor(ctx, ProcessingConfig.from_config(cfg))

    async def message_task_wrapper(self, cb, message: Message, channel: Channel):
        try:
            await self.backoff.process_with_backoff(cb)
        except Exception as e:
            self.logger.write(f"Failed to process message: {message.id} in channel {channel.title}")
            self.logger.write(repr(e))
        await self.logger.update_progress()

    async def process_channels(self,
                             channel_provider: ChannelProvider,
                             updater_config: UpdaterConfig):
        """Process channels using the provided configuration"""

        # Configure message fetcher with specified strategy
        mf = MessageFetcher(self.ctx.client, self.ctx.db, StrategyConfig(
            strategy=updater_config.message_strategy,
            limit=updater_config.message_limit or 0
        ))

        # Set up message gathering
        gather_messages = self.queue_manager.producer(
            channel_provider.get_channels(self.cm),
            mf.get_channel_messages
        )

        # Configure message processor
        async def process_message(message, channel):
            await self.processor.process_message(message, channel)
            if updater_config.mark_read:
                await message.mark_read()
            await self.logger.update_progress()

        self.queue_manager.create_consumers(process_message)

        # Run processing
        num_tasks = await gather_messages
        self.logger.write(f"Found {num_tasks} messages to process")

        await self.logger.run(num_tasks, self.queue_manager.wait())

        self.queue_manager.finish()
        self.logger.write(
            f"{updater_config.description} complete - \n"
            f"Gathered tasks: {num_tasks}\n"
            f"Finished tasks: {self.logger.progress.tasks[0].completed}\n"
            f"processed {self.logger.progress.tasks[0].completed} messages\n"
            f"Update complete: {datetime.now()}\n"
        )
