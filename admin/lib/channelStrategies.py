from typing import AsyncGenerator, List, Protocol
from telethon.tl.types import Channel
from .ChannelManager import ChannelManager


class ChannelProvider(Protocol):
    """Protocol for providing channels to process"""
    def get_channels(self, cm: ChannelManager) -> AsyncGenerator[Channel, None]:
        ...

class SingleChannelNameLookup(ChannelProvider):
    """Provides a single channel for export"""
    def __init__(self, channel_name: str):
        self.channel_name = channel_name

    async def get_channels(self, cm: ChannelManager) -> AsyncGenerator[Channel, None]:
        channel = await cm.lookup_channel_by_name(self.channel_name)
        if not channel:
            raise ValueError(f"Channel not found: {self.channel_name}")
        yield channel

class AllChannelsInFolder(ChannelProvider):
    """Provides channels from the update folder"""
    async def get_channels(self, cm: ChannelManager) -> AsyncGenerator[Channel, None]:
        async for channel in cm.get_target_channels():
            yield channel

class ChannelListProvider(ChannelProvider):
    """Provides a pre-computed list of channels"""
    def __init__(self, channels: List[Channel]):
        self.channels = channels

    async def get_channels(self, _: ChannelManager) -> AsyncGenerator[Channel, None]:
        for channel in self.channels:
            yield channel
