from datetime import datetime
from .config import Settings, BackoffConfig, ProcessingConfig, QueueManagerConfig, StrategyConfig, UpdaterConfig
from .BackoffManager import BackoffManager
from .QueueManager import QueueManager
from .MessageFetcher import MessageFetcher
from .TLContext import TLContext
from .MediaProcessor import MediaProcessor
from .ChannelManager import ChannelManager
from .channelStrategies import ChannelProvider

class TeledeckUpdater:
    def __init__(self, cfg: Settings, ctx: TLContext):
        self.ctx = ctx
        self.logger = ctx.logger
        self.queue_manager = QueueManager(self.logger, QueueManagerConfig.from_config(cfg))
        self.cm = ChannelManager(ctx)
        self.backoff = BackoffManager(BackoffConfig.from_config(cfg))
        self.processor = MediaProcessor(ctx, ProcessingConfig.from_config(cfg))

    async def process_channels(self,
                             channel_provider: ChannelProvider,
                             updater_config: UpdaterConfig):
        """Process channels using the provided configuration"""
        await self.logger.run(100, self._process_channels(channel_provider, updater_config))


    async def _process_channels(self, channel_provider: ChannelProvider, updater_config: UpdaterConfig):
        self.processor.validate_paths()

        gather_channels = self.queue_manager.queueChannels(
            channel_provider.get_channels(self.cm))

        # Set up message gathering

        # Configure message fetcher with specified strategy
        mf = MessageFetcher(self.ctx.client, self.ctx.db, StrategyConfig(
            strategy=updater_config.message_strategy,
            limit=updater_config.message_limit
        ))

        gather_messages = self.queue_manager.processChannelQueue(
            mf.get_channel_messages
        )

        numChannels = await gather_channels
        self.logger.setNumChannels(numChannels)

        # Configure message processor
        async def process_message(message, channel):
            await self.backoff.process_with_backoff(
                lambda: self.processor.process_message(message, channel)
            )
            if updater_config.mark_read:
                await message.mark_read()
            self.logger.finish_message()


        self.queue_manager.create_consumers(process_message)

        # Run processing
        num_tasks = await gather_messages
        self.logger.setNumMessages(num_tasks)
        self.logger.write(f"Found {num_tasks} messages to process")

        # Logger is broken!! Need to think about what we're actually doing here.
        await self.queue_manager.wait()

        self.queue_manager.finish()
        self.logger.write(
            f"{updater_config.description} complete - \n"
            f"Gathered tasks: {num_tasks}\n"
            f"Finished tasks: {self.logger.progress.tasks[0].completed}\n"
            f"processed {self.logger.progress.tasks[0].completed} messages\n"
            f"Update complete: {datetime.now()}\n"
        )
