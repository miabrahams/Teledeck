from lib.tl_client import get_context, get_target_channels, QueueItem, message_task_producer, message_task_consumer, MAX_CONCURRENT_TASKS
import asyncio

# PROBLEMS
# 1. How to handle media that is not a file (e.g. web previews)?
# 2. Check what happens to Twitter embeds
# 3. Paginate / search by date?
async def main():
    ctx = await get_context()


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


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
