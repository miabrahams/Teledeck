from telethon import hints
from typing import cast
from telethon.tl.custom.dialog import Dialog
from .config import Settings, UpdaterConfig
from .TLContext import TLContext
from .TeledeckUpdater import TeledeckUpdater
from .ChannelManager import ChannelManager
from .MediaProcessor import ProcessingConfig, MediaProcessor
from .channelStrategies import SingleChannelNameLookup, AllChannelsInFolder

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


async def channel_list_sync(channel_name: str, _: Settings, ctx: TLContext):
    cm = ChannelManager(ctx)
    target_channels = await cm.get_update_folder_channels(channel_name)
    cm.logger.write("Found channels:")
    titles = [f"{n}: {channel.title}" for n, channel in enumerate(target_channels)]
    cm.logger.write("\n".join(titles))
    cm.db.update_channel_list(target_channels)

async def run_update(cfg: Settings, ctx: TLContext):
    """Run normal update process"""
    updater = TeledeckUpdater(cfg, ctx)
    provider = AllChannelsInFolder()
    config = UpdaterConfig(
        message_strategy="unread",
        message_limit=cfg.DEFAULT_FETCH_LIMIT,
        description="Update"
    )
    await updater.process_channels(provider, config)

async def run_export(channel_name: str, message_limit: int | None, cfg: Settings, ctx: TLContext):
    """Export all messages from a channel"""
    updater = TeledeckUpdater(cfg, ctx)
    provider = SingleChannelNameLookup(channel_name)
    config = UpdaterConfig(
        message_strategy="all",
        message_limit=message_limit,
        mark_read=False,  # Don't mark as read during export
        description="Export"
    )
    await updater.process_channels(provider, config)