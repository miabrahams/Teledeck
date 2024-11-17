import asyncio
from .config import QueueManagerConfig
from .Logger import RichLogger
from .types import QueueItem, TaskWrapper, ChannelGenerator, ChannelMessageRetriever


class QueueManager:
    logger: RichLogger
    queue: asyncio.Queue[QueueItem]
    config: QueueManagerConfig
    consumers: list[asyncio.Task[None]]

    def __init__(self, logger: RichLogger, cfg: QueueManagerConfig):
        self.logger = logger
        self.queue: asyncio.Queue[QueueItem] = asyncio.Queue()
        self.config = cfg
        self.consumers = []

    async def producer(self, channels: ChannelGenerator, fetcher: ChannelMessageRetriever) -> int:
        """Produce message processing tasks."""
        total_tasks = 0
        async for channel in channels:
            # get_channel_messages
            async for message in fetcher(channel):
                total_tasks += 1
                await self.queue.put((channel, message))
        return total_tasks

    async def consumer(self, callback: TaskWrapper) -> None:
        """Consume and run message processing tasks."""
        while True:
            try:
                channel, message = await self.queue.get()
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
            self.queue.task_done()

    def create_consumers(self, callback: TaskWrapper):
        """Start message processing consumers."""

        self.consumers = [asyncio.create_task(self.consumer(callback)) for _ in range(self.config.max_concurrent_tasks)]

    def wait(self):
        return self.queue.join()

    def finish(self):
        for c in self.consumers:
            c.cancel()
