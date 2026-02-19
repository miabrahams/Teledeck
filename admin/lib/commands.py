import re
from telethon import hints
from typing import cast
from telethon.tl.custom.dialog import Dialog
from .config import Settings, UpdaterConfig
from .TLContext import TLContext
from .TeledeckUpdater import TeledeckUpdater
from .ChannelManager import ChannelManager
from .MediaProcessor import ProcessingConfig, MediaProcessor
from .channelStrategies import SingleChannelNameLookup, ChannelListProvider

async def login(_: Settings, ctx: TLContext):
    ctx.client.start()
    me = await ctx.client.get_me()
    print(me.stringify())
    await ctx.client.send_message(me, 'Hello, myself!')

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
    fetch_limit = cfg.DEFAULT_FETCH_LIMIT or 1000
    async for message in ctx.client.iter_messages(entity, limit=fetch_limit):
        try:
            await mp.log_forwards(message)
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

async def run_update(channel_pattern: str | None, confirm_update: bool, cfg: Settings, ctx: TLContext):
    """Run normal update process"""
    cm = ChannelManager(ctx)
    channels = [channel async for channel in cm.get_target_channels()]

    if channel_pattern:
        try:
            pattern = re.compile(channel_pattern, re.IGNORECASE)
        except re.error as e:
            cm.logger.write(f"Invalid --channel-pattern regex: {e}")
            return
        channels = [channel for channel in channels if pattern.search(channel.title)]

    if channel_pattern or confirm_update:
        cm.logger.write("Matched channels:")
        if channels:
            titles = [f"{n}: {channel.title}" for n, channel in enumerate(channels)]
            cm.logger.write("\n".join(titles))
        else:
            cm.logger.write("(none)")

    if not channels:
        cm.logger.write("No channels matched; update skipped.")
        return

    if confirm_update:
        response = input(f"Proceed with update for {len(channels)} channel(s)? [y/N]: ").strip().lower()
        if response not in ("y", "yes"):
            cm.logger.write("Update cancelled.")
            return

    updater = TeledeckUpdater(cfg, ctx)
    provider = ChannelListProvider(channels)
    config = UpdaterConfig(
        message_strategy="unread", # all, unread
        message_limit=cfg.DEFAULT_FETCH_LIMIT,
        description="Update",
        mark_read=True,
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
