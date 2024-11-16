from .TLContext import TLContext
from telethon import hints
from telethon.tl.custom.dialog import Dialog
from typing import cast
from .config import Settings
from .tl_client import TeledeckClient
from .ChannelManager import ChannelManager
from .MediaProcessor import ProcessingConfig, MediaProcessor

async def save_forwards(chat_name: str, cfg: Settings, ctx: TLContext):
    mp = MediaProcessor(ctx, ProcessingConfig.from_config(cfg))
    entity: hints.EntityLike | None = None
    async for d in ctx.client.iter_dialogs():
        dialog = cast(Dialog, d)
        if dialog.name == chat_name:
            entity = dialog.entity
            break
    if not entity:
        print("Could not find chat.")
        return

    n = 0
    async for message in ctx.client.iter_messages(entity, limit=5000):
        try:
            await mp.process_forward(message)
        except Exception as e:
            print(e)
        n += 1
        print(n)


async def channel_check_list_sync(cfg: Settings, ctx: TLContext):
    cm = ChannelManager(ctx)
    target_channels = await cm.get_update_folder_channels()
    cm.logger.write("Found channels:")
    titles = [f"{n}: {channel.title}" for n, channel in enumerate(target_channels)]
    cm.logger.write("\n".join(titles))
    cm.db.update_channel_list(target_channels)

async def run_update(cfg: Settings, ctx: TLContext):
    client = TeledeckClient(cfg, ctx)
    await client.run_update()