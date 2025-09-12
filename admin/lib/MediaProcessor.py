from pathlib import Path
from typing import Optional
from telethon.tl.custom.message import Message
from telethon.tl.custom.file import File
from telethon.tl.types import Channel, Document, WebPage

from .TLContext import TLContext
from .types import Downloadable, MediaItem, DownloadItem, MessageMediaWebPage
from .api import find_web_preview, get_message_link
from .exceptions import ErrorContext, MediaError, DownloadError
from .config import ProcessingConfig

# The complexity here I believe stems from combining Document vs MessageMediaDocument.
# Document will arise from inspecting a MessageMediaWebPage?

class MediaContext:
    def __init__(self, message: Message, channel: Channel):
        self.message = message
        self.channel = channel

    def error(self, operation, **kwargs):
        return ErrorContext.new(
            operation=operation,
            message_id=self.message.id,
            channel_id=self.channel.id,
            channel_title=self.channel.title,
            **kwargs
        )

# TODO: Use Protocol
class MediaProcessor:
    """Handles extraction and processing of media from Telegram messages"""

    def __init__(self, ctx:TLContext, cfg:ProcessingConfig):
        self.logger = ctx.logger
        self.db = ctx.db
        self.client = ctx.client
        self.config = cfg

    def log_message_info(self, mCtx: MediaContext, info: dict):
        self.logger.save_to_json({"message": mCtx.message.id, "channel": mCtx.channel.title, "info": info})

    async def process_message(self, message: Message, channel: Channel):
        return await self._process_message(MediaContext(message, channel))

    async def _process_message(self, mCtx: MediaContext):
        """Main entry point for processing media content"""

        try:
            # Handle forwarded content
            await self.log_forwards(mCtx)

            mText = mCtx.message.text
            if mText and len(mText) > 300:
                self.log_message_info(mCtx, {"long_message": mText})

            media_item = await self._extract_media(mCtx)
            if not media_item:
                return

            download_item = await self._download_media(mCtx, media_item)
            if download_item:
                self._save_media_item(mCtx, download_item)


        except Exception as e:
            self.logger.write(f"failed to process message {mCtx.message.id} in channel {mCtx.channel.title}: {e}")
            raise MediaError(f"Message processing failed: {str(e)}", mCtx.error("processing")) from e


    async def log_forwards(self, mCtx: MediaContext):
        """Add log entries for forwarded messages and extract channels"""

        forward = getattr(mCtx.message, "forward", None)
        if not forward or not forward.is_channel:
            return

        self.logger.write(f"Found forward: {mCtx.message.id}")
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


    async def _extract_media(self, mCtx: MediaContext) -> Optional[MediaItem]:
        """Extract media content from message"""

        preview = find_web_preview(mCtx.message)
        if preview:
            return preview

        if not isinstance(mCtx.message.file, File):
            self.logger.write(f"No media found: {mCtx.message.id}")
            return None


        file: File = mCtx.message.file
        file_id = file.media.id
        # Size check
        if getattr(file, "size", 0) > self.config.max_file_size:
            return await self._handle_large_file(mCtx, file.name, file_id)

        if file.sticker_set:
            self.logger.write(f"Skipping sticker: {file_id}")
            return None

        return MediaItem(file, file_id, False, file.mime_type)


    async def _handle_large_file(self, mCtx: MediaContext,
                                 file_name: Optional[str],
                                 file_id: int) -> None:
        if self.config.write_message_links:
            messageLink = await get_message_link(self.client, mCtx.channel, mCtx.message)
            if messageLink is not None:
                self.logger.write(messageLink.stringify())
                self.logger.add_data({"large file found": messageLink.link})
        self.logger.write(f"*****Skipping large file*****: {file_name} ~ id: {file_id}")



    async def _download_media(self, mCtx: MediaContext, item: MediaItem) -> Optional[DownloadItem]:
        """Download media content and prepare download item"""

        try:
            print(item.target)
            final_target = item.target
            if isinstance(item.target, Document):
                final_target = item.target
            elif isinstance(item.target, File):
                final_target = item.target.media
            elif isinstance(item.target, MessageMediaWebPage):
                self.logger.write("Web Page")
                self.logger.write(item.target.to_json())
                self.logger.write(item.target.media)
                final_target = item.target.media
            else:
                self.logger.write("Unknown target type")
                final_target = item.target.media

            if final_target is None:
                self.logger.write("No target found.")
                if isinstance(item.target, File):
                    self.logger.write("File:", item.target.name, item.target.mime_type)
                else:
                    self.logger.write(item.target.stringify())
                return None

            existing = self.db.find_existing_media(final_target)
            if existing:
                self.logger.write(f"Found existing file_id: {final_target.id}")
                self.logger.write(final_target.stringify())
                return None
            file_path = await self._download_file(final_target)

            if not file_path:
                self.logger.write(repr(final_target))
                raise DownloadError("Failed to download file", mCtx.error("download_media"))

            return self._create_download_item(mCtx, item, file_path)

        except Exception as e:
            # Print trace
            import traceback
            traceback.print_exc()
            self.logger.write(f"Download failed: {str(e)}")
            raise

    async def _download_file(self, downloadable: Downloadable) -> Optional[Path]:
        download_task = self.logger.progress.add_task("[cyan]Downloading", total=100)

        def progress_callback(current: int, total: int):
            self.logger.progress.update(download_task, completed=current, total=total)

        try:
            if isinstance(downloadable, MessageMediaWebPage) and isinstance(downloadable.webpage, WebPage):
                # TODO: Check webpage handling. Can we get Twitter embeds here?
                print("Found webpage: ", downloadable.webpage.url)
            result = await self.client.download_media(
                downloadable,  # type: ignore this function can handle other types
                str(self.config.media_path),
                progress_callback=progress_callback
            )
            if isinstance(result, str):
                return Path(result)

        finally:
            self.logger.progress.remove_task(download_task)


    def _create_download_item(self, mCtx: MediaContext, item: MediaItem, file_path: Path) -> DownloadItem:
        """Create download item from the downloaded file"""
        file_name = file_path.parts[-1]
        file_size = file_path.stat().st_size
        mime_type = item.mime_type or "unknown/unknown"
        media_type = self._determine_media_type(mCtx, mime_type)

        return DownloadItem(
            target=item.target,
            id=item.id,
            from_preview=item.from_preview,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            media_type=media_type
        )


    def _determine_media_type(self, mCtx: MediaContext, mime_type: str) -> str:
        mtype = mime_type.split("/")[0]
        if mtype in ("video", "image"):
            return mtype
        if mCtx.message.photo:
            return "photo"
        return "document"

    def _save_media_item(self, mCtx: MediaContext, item: DownloadItem):
        try:
            self.db.save_media_item(self.logger, item, mCtx.channel.id, mCtx.message)
        except Exception as e:
            self.logger.write(f"Database insertion failed: {e}")
            file_path = self.config.media_path / item.file_name
            file_path.rename(self.config.orphan_path / item.file_name)
            self.logger.write(f"Moved {item.file_name} to orphans directory.")
