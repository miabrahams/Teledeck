import asyncio
from typing import AsyncGenerator, List, Any, cast
from telethon.tl.types import (
    Channel,
    PeerChannel,
    InputPeerChannel,
    DialogFilter
)
from telethon.tl.types.messages import DialogFilters # type: ignore
from .TLContext import TLContext
from telethon import functions as tlfunctions





class ChannelManager:
    def __init__(self, ctx: TLContext):
        self.db = self.db
        self.client = self.client
        self.logger = self.logger

    async def get_target_channels(self) -> AsyncGenerator[Channel, None]:
        # TODO: Extract this filtering logic to a separate function
        # nameMatch = ChannelModel.title.like("%Khael%")
        channel_models = self.db.get_channels_to_check([])

        for channel_model in channel_models:
            try:
                inputPeerChannel = await self.client.get_input_entity(PeerChannel(channel_model.id))
                channel = await self.client.get_entity(inputPeerChannel)
                if not isinstance(channel, Channel):
                    raise ValueError(f"Channel not found: {channel_model.id}. Got {channel}")
                yield channel
            except Exception as e:
                if isinstance(channel, Channel):
                    err_msg = f"Failed to get channel: {channel_model.id} {channel.title}"
                else:
                    err_msg = f"Failed to get channel: {channel_model.id}"
                self.logger.write(err_msg)
                self.logger.write(str(e))
                self.logger.add_data(err_msg)
                self.logger.add_data(str(e))


    async def get_update_folder_channels(self) -> List[Channel]:
        chat_folders: Any  = await self.client(tlfunctions.messages.GetDialogFiltersRequest())
        if not isinstance(chat_folders, DialogFilters):
            raise ValueError("Could not find folders")

        try:
            media_folder = next(
                (folder for folder in chat_folders.filters if isinstance(folder, DialogFilter) and folder.title == "MediaView")
            )
        except StopIteration:
            raise NameError("MediaView folder not found.")

        peer_channels = [peer for peer in media_folder.include_peers if isinstance(peer, InputPeerChannel)]

        target_channels = await asyncio.gather( *[self.client.get_entity(peer) for peer in peer_channels])
        self.logger.write(f"{len(target_channels)} channels found")

        return cast(List[Channel], target_channels)

