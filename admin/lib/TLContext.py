from telethon.client.telegramclient import TelegramClient # type: ignore
from typing import Optional
from .config import Settings
from .Logger import RichLogger
from .DatabaseService import DatabaseService

class TLContext:
    def __init__(self, config: Settings, logger: RichLogger, db: DatabaseService):
        self.config = config
        self.logger = logger
        self.db = db
        self.session_file = config.SESSION_FILE
        self.api_id = int(config.TELEGRAM_API_ID)
        self.api_hash = config.TELEGRAM_API_HASH
        self._client: Optional[TelegramClient] = None

    async def __aenter__(self):
        self._client = TelegramClient(self.session_file, self.api_id, self.api_hash)
        await self._client.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.add_data({"Exception":
                {
                    "exc_val": exc_val,
                    "exc_tb": exc_tb,
                    "exc_type": exc_type
                }
            })
        if self._client:
            self._client.disconnect()
        self.logger.save_data()

    @property
    def client(self) -> TelegramClient:
        if not self._client:
            raise RuntimeError("Client not initialized - use async with block")
        return self._client
