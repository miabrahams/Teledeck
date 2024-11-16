from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from telethon.tl.custom.message import Message
from telethon.tl.custom.file import File
from telethon.tl.types import Channel, Document

from .TLContext import TLContext
from .types import Downloadable, MediaItem, DownloadItem
from .api import find_web_preview, get_message_link
from .exceptions import MediaProcessingError
from .config import Settings


@dataclass
class ProcessingConfig:
    """Configuration for media processing"""
    media_path: Path
    orphan_path: Path
    write_message_links: bool = False
    max_file_size: int = 1_000_000_000 # 1GB default

    @staticmethod
    def from_config(cfg: Settings) -> "ProcessingConfig":
        return ProcessingConfig(
            media_path=cfg.MEDIA_PATH,
            orphan_path=cfg.ORPHAN_PATH,
            write_message_links=cfg.WRITE_MESSAGE_LINKS
        )


class MediaProcessor:
    """Handles extraction and processing of media from Telegram messages"""

    def __init__(self, ctx:TLContext, config:ProcessingConfig):
        self.logger = ctx.logger
        self.db = ctx.db
        self.client = ctx.client
        self.config = config


    async def process_message(self, message: Message, channel: Channel):
        """Main entry point for processing media content"""

        try:
            # Handle forwarded content
            await self.process_forward(message)

            ## TODO: Check for long text messages and save them in the log. Could be fun

            media_item = await self._extract_media(message, channel)
            if not media_item:
                return

            download_item = await self._download_media(media_item, message)
            if download_item:
                self._save_media_item(download_item, channel, message)


        except Exception as e:
            self.logger.write(f"failed to process message {message.id} in channel {channel.title}: {e}")
            raise MediaProcessingError(f"Message processing failed: {str(e)}") from e


    async def process_forward(self, message: Message):
        """Process forwarded content"""

        forward = getattr(message, "forward", None)
        if not forward or not forward.is_channel:
            return

        self.logger.write(f"Found forward: {message.id}")
        try:
            fwd_channel = await self.client.get_entity(getattr(forward, "chat_id"))
            if not isinstance(fwd_channel, Channel):
                self.logger.write(f"*************Unexpected non-channel forward: {getattr(forward, 'chat_id')}")
                return

            self.db.add_channel_if_not_exists(
                self.logger,
                fwd_channel.id,
                fwd_channel.title
            )

        except Exception as e:
            self.logger.write(f"Failed to process forward: {str(e)}")


    async def _extract_media(self, message: Message, channel: Channel) -> Optional[MediaItem]:
        """Extract media content from message"""

        preview = find_web_preview(message)
        if preview:
            return preview

        if not isinstance(message.file, File):
            self.logger.write(f"No media found: {message.id}")
            return None


        file: File = message.file
        file_id = file.media.id
        # Size check
        if getattr(file, "size", 0) > self.config.max_file_size:
            return await self._handle_large_file(message, channel, file.name, file_id)

        if file.sticker_set:
            self.logger.write(f"Skipping sticker: {file_id}")
            return None

        return MediaItem(file, file_id, False, file.mime_type)


    async def _handle_large_file(self, message: Message, channel: Channel,
                                 file_name: Optional[str],
                                 file_id: int) -> None:
        if self.config.write_message_links:
            messageLink = await get_message_link(self.client, channel, message)
            if messageLink is not None:
                self.logger.write(messageLink.stringify())
                self.logger.add_data({"large file found": messageLink.link})
        self.logger.write(f"*****Skipping large file*****: {file_name} ~ id: {file_id}")



    async def _download_media(self, item: MediaItem, message: Message) -> Optional[DownloadItem]:
        """Download media content and prepare download item"""

        try:
            if isinstance(item.target, Document | File):
                file_path = await self._download_file(item.target)
            else:
                if getattr(item.target, "media", None) is None:
                    self.logger.write("No target found")
                    return None
                file_path = await self._download_file(item.target.media)

            if not file_path:
                self.logger.write(repr(item.target))
                raise MediaProcessingError(f"Failed to download file: {item.id}")

            return self._create_download_item(item, file_path, message)

        except Exception as e:
            self.logger.write(f"Download failed: {str(e)}")
            return None

    async def _download_file(self, downloadable: Downloadable) -> Optional[Path]:
        download_task = self.logger.progress.add_task("[cyan]Downloading", total=100)

        def progress_callback(current: int, total: int):
            self.logger.progress.update(download_task, completed=current, total=total)

        try:
            result = await self.client.download_media(
                # TODO: Check webpage handling
                downloadable,
                str(self.config.media_path),
                progress_callback=progress_callback
            )
            if isinstance(result, str):
                return Path(result)

        finally:
            self.logger.progress.remove_task(download_task)


    def _create_download_item(self, item: MediaItem, file_path: Path, message: Message) -> DownloadItem:
        """Create download item from the downloaded file"""
        file_name = file_path.parts[-1]
        file_size = file_path.stat().st_size
        mime_type = item.mime_type or "unknown/unknown"
        media_type = self._determine_media_type(mime_type, message)

        return DownloadItem(
            target=item.target,
            id=item.id,
            from_preview=item.from_preview,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            media_type=media_type
        )


    def _determine_media_type(self, mime_type: str, message: Message) -> str:
        mtype = mime_type.split("/")[0]
        if mtype in ("video", "image"):
            return mtype
        if message.photo:
            return "photo"
        return "document"

    def _save_media_item(self, item: DownloadItem, channel: Channel, message: Message):
        try:
            self.db.save_media_item(self.logger, item, channel.id, message)
        except Exception as e:
            self.logger.write(f"Database insertion failed: {e}")
            file_path = self.config.media_path / item.file_name
            file_path.rename(self.config.orphan_path / item.file_name)
            self.logger.write(f"Moved {item.file_name} to orphans directory.")
