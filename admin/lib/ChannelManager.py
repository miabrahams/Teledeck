import asyncio
from typing import AsyncGenerator, Optional, List, Any, cast
from telethon import functions as tlfunctions
from telethon.tl.types import (
    Channel,
    PeerChannel,
    InputPeerChannel,
    DialogFilter
)
from telethon.tl.types.messages import DialogFilters # type: ignore
from telethon.tl.custom import Dialog # type: ignore
from models.telegram import ChannelModel # Todo: move this to db operations
from .TLContext import TLContext


class ChannelManager:
    def __init__(self, ctx: TLContext):
        self.db = ctx.db
        self.client = ctx.client
        self.logger = ctx.logger

    async def get_target_channels(self, channel_filter: Optional[List[Any]] = None) -> AsyncGenerator[Channel, None]:
        channel_models = self.db.get_channels_to_check(channel_filter or [])

        for channel_model in channel_models:
            try:
                inputPeerChannel = await self.client.get_input_entity(PeerChannel(channel_model.id))
                channel = await self.client.get_entity(inputPeerChannel)
                if not isinstance(channel, Channel):
                    raise ValueError(f"Channel not found: {channel_model.id}. Got {channel}")
                yield channel
            except Exception as e:
                err_msg = f"Failed to get channel: {channel_model.id}"
                self.logger.write(err_msg)
                self.logger.write(str(e))
                self.logger.add_data(err_msg)
                self.logger.add_data(str(e))

    async def lookup_channel_by_name(self, name: str) -> Channel:
        """Look up a channel by fuzzy matching name"""
        lName = name.lower()
        try:
            async for dialog in self.client.iter_dialogs():
                if not isinstance(dialog, Dialog):
                    self.logger.write(f"Unexpected dialog type: {type(dialog)}")
                    continue
                if not isinstance(dialog.input_entity, InputPeerChannel):
                    continue
                if dialog.name.lower().find(lName) == -1:
                    continue

                channel = dialog.entity
                if not isinstance(channel, Channel):
                    raise ValueError(f"Unexpected channel type for channel {channel.stringify()}")
                self.logger.write(f"Found channel: {channel.title}")
                return channel

            raise ValueError(f"Failed to get channel matching: {name}")
        except Exception as e:
            self.logger.write(f"Error looking up channel: {str(e)}")
            raise e

    async def get_channel_by_name(self, name: str):
        nameMatch = ChannelModel.title.like(f"%{name}%")
        return self.get_target_channels([nameMatch])


    async def get_update_folder_channels(self, channel_name: str) -> List[Channel]:
        chat_folders: Any  = await self.client(tlfunctions.messages.GetDialogFiltersRequest())
        if not isinstance(chat_folders, DialogFilters):
            raise ValueError("Could not find folders")

        try:
            media_folder = next(
                (folder for folder in chat_folders.filters if isinstance(folder, DialogFilter) and folder.title == channel_name)
            )
        except StopIteration:
            raise NameError("folder not found: " + channel_name)

        peer_channels = [peer for peer in media_folder.include_peers if isinstance(peer, InputPeerChannel)]

        target_channels = await asyncio.gather( *[self.client.get_entity(peer) for peer in peer_channels])
        self.logger.write(f"{len(target_channels)} channels found")

        return cast(List[Channel], target_channels)
