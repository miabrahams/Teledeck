from lib.tl_client import get_context, get_target_channels, QueueItem, message_task_producer, message_task_consumer, MAX_CONCURRENT_TASKS
from sqlmodel import Session, select
from models.telegram import Channel as ChannelModel
import asyncio

# PROBLEMS
# 1. How to handle media that is not a file (e.g. web previews)?
# 2. Check what happens to Twitter embeds
# 3. Paginate / search by date?
async def main(load_saved_tasks: bool=False, start_task: int=0):
    ctx = await get_context()

    target_channels = await get_target_channels(ctx)
    print("Found channels:")
    [print(f"{n}: {channel.title}") for n, channel in enumerate(target_channels)]
    with Session(ctx.engine) as session:
        for channel in target_channels:
            if session.exec(select(ChannelModel).where(ChannelModel.id == channel.id)).first():
                continue
            session.add(ChannelModel(id=channel.id, title=channel.title))
            session.commit()
        # print(channel.stringify)

    queue = asyncio.Queue[QueueItem]()
    # One producer is fine!
    gather_messages = asyncio.create_task(message_task_producer(ctx, target_channels, queue))

    """
    if False:
        if load_saved_tasks:
            channel_tasklists = pickle.load(open("data/channel_tasklists.pkl", "rb"))
        else:
            channel_tasklists = await gather_tasklists(ctx, target_channels)
        if start_task > 0:
            channel_tasklists = channel_tasklists[start_task:]
    """

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
    import sys

    n = len(sys.argv)
    if n == 1:
        load_saved_tasks = False
        start_task = 0
    elif n == 2:
        load_saved_tasks = True
        start_task = 0
    else:
        load_saved_tasks = True
        start_task = int(sys.argv[2])
    asyncio.get_event_loop().run_until_complete(main(load_saved_tasks, start_task))
