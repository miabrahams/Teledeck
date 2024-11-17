from typing import Callable, Coroutine, Any
from telethon.client.telegramclient import TelegramClient # type: ignore
from typing import Optional
from dataclasses import dataclass
from .config import Settings, TelethonConfig, DatabaseConfig
from .Logger import RichLogger
from .DatabaseService import DatabaseService

@dataclass
class TLContext:
    config: Settings
    logger: RichLogger
    db: DatabaseService
    client: TelegramClient

ServiceRoutine = Callable[[Settings, TLContext], Coroutine[Any, Any, None]]

async def with_context(cfg: Settings, cb: ServiceRoutine):
    db_service = DatabaseService(DatabaseConfig.from_config(cfg))
    logger = RichLogger(cfg.UPDATE_PATH)
    async with TLContextProvider(cfg, logger, db_service) as ctx:
        return await cb(cfg, ctx)

class TLContextProvider:
    def __init__(self, settings: Settings, logger: RichLogger, db: DatabaseService):
        self.settings = settings
        self.config =  TelethonConfig.from_config(settings)
        self.logger = logger
        self.db = db
        self._client: Optional[TelegramClient] = None

    async def __aenter__(self):
        self._client = TelegramClient(self.config.session_file, self.config.api_id, self.config.api_hash)
        await self._client.connect()
        return TLContext(self.settings, self.logger, self.db, self.client)

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
