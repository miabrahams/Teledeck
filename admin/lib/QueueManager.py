import asyncio
from .config import QueueManagerConfig
from .Logger import RichLogger
from .types import MessageQueueItem, TaskWrapper, ChannelGenerator, ChannelMessageRetriever
from telethon.tl.types import Channel


class QueueManager:
    logger: RichLogger
    channelQueue: asyncio.Queue[Channel]
    messageQueue: asyncio.Queue[MessageQueueItem]
    config: QueueManagerConfig
    consumers: list[asyncio.Task[None]]

    def __init__(self, logger: RichLogger, cfg: QueueManagerConfig):
        self.logger = logger
        self.channelQueue: asyncio.Queue[Channel] = asyncio.Queue()
        self.messageQueue: asyncio.Queue[MessageQueueItem] = asyncio.Queue()
        self.config = cfg
        self.consumers = []

    async def queueChannels(self, channels: ChannelGenerator) -> int:
        total_channels = 0
        async for channel in channels:
            total_channels += 1
            await self.channelQueue.put(channel)
        return total_channels


    async def processChannelQueue(self, fetcher: ChannelMessageRetriever) -> int:
        """Produce message processing tasks."""
        # Consume from queue
        total_tasks = 0
        await asyncio.sleep(1.0)
        while True:
            try:
                channel = self.channelQueue.get_nowait()
                async for message in fetcher(channel):
                    total_tasks += 1
                    await self.messageQueue.put((channel, message))
                self.logger.finish_channel()
            except asyncio.QueueEmpty:
                break
        return total_tasks

    async def messageConsumer(self, callback: TaskWrapper) -> None:
        """Consume and run message processing tasks."""
        while True:
            try:
                channel, message = await self.messageQueue.get()
                await callback(message, channel)
            except Exception as e:
                import traceback

                # TODO: add proper exception handling
                self.logger.write("******Failed to process message: \n" + str(e))
                self.logger.write(
                    "\n".join(map(str, [channel.title, message.id, getattr(message, "text", ""), type(message.media)]))
                )
                self.logger.write(traceback.format_exc())
                # link = await get_message_link(ctx, channel, message)
                # print("Message link: ", link.stringify())
                self.logger.add_data({"error": f"Failed to process message: {str(e)}"})
            finally:
                self.messageQueue.task_done()

    def create_consumers(self, callback: TaskWrapper):
        """Start message processing consumers."""

        self.consumers = [asyncio.create_task(self.messageConsumer(callback)) for _ in range(self.config.max_concurrent_tasks)]

    def wait(self):
        return self.messageQueue.join()

    def finish(self):
        for c in self.consumers:
            c.cancel()
