from pydantic_settings import BaseSettings, SettingsConfigDict

from typing import Tuple
from dataclasses import dataclass
from pathlib import Path

class Settings(BaseSettings):
    TELEGRAM_API_ID: int = 0
    TELEGRAM_API_HASH: str = ""
    TELEGRAM_PHONE: str = ""
    TELEGRAM_DB_KEY: str = ""
    TWITTER_AUTHTOKEN: str = ""
    TWITTER_CSRFTOKEN: str = ""
    ENV: str = ""
    TAGGER_URL: str = ""
    SESSION_FILE: str = "user"
    MAX_RETRY_ATTEMPTS: int = 5
    RETRY_BASE_DELAY: float = 2.0
    MAX_CONCURRENT_TASKS: int = 1
    SLOW_MODE: bool = False
    SLOW_MODE_DELAY: Tuple[float, float] = (5.0, 10.0)
    MEDIA_PATH: Path = Path("./static/media/")
    ORPHAN_PATH: Path = Path("./recyclebin/orphan/")
    DB_PATH: Path = Path("./teledeck.db")
    UPDATE_PATH: Path = Path("./data/update_info")
    DEFAULT_FETCH_LIMIT: int = 65
    MESSAGE_STRATEGY: str = "unread"
    WRITE_MESSAGE_LINKS: bool = False

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


@dataclass
class BackoffConfig:
    max_attempts: int
    base_delay: float
    slow_mode: bool = False
    slow_mode_delay: Tuple[float, float] = (5.0, 10.0)

    @classmethod
    def from_config(cls, cfg: Settings):
        return cls(
            max_attempts=cfg.MAX_RETRY_ATTEMPTS,
            base_delay=cfg.RETRY_BASE_DELAY,
            slow_mode=cfg.SLOW_MODE,
            slow_mode_delay=cfg.SLOW_MODE_DELAY
        )


@dataclass
class ProcessingConfig:
    """Configuration for media processing"""
    media_path: Path
    orphan_path: Path
    write_message_links: bool = False
    max_file_size: int = 1_000_000_000 # 1GB default

    @classmethod
    def from_config(cls, cfg: Settings):
        return cls(
            media_path=cfg.MEDIA_PATH,
            orphan_path=cfg.ORPHAN_PATH,
            write_message_links=cfg.WRITE_MESSAGE_LINKS,
        )

@dataclass
class StrategyConfig:
    """Configuration for message fetching strategies"""
    strategy: str
    limit: int

    @classmethod
    def from_config(cls, cfg: Settings):
        return cls(
            strategy=cfg.MESSAGE_STRATEGY,
            limit=cfg.DEFAULT_FETCH_LIMIT,
        )

@dataclass
class QueueManagerConfig:
    """Configuration for queue manager"""
    max_concurrent_tasks: int

    @classmethod
    def from_config(cls, cfg: Settings):
        return cls(
            max_concurrent_tasks=cfg.MAX_CONCURRENT_TASKS,
        )

@dataclass
class TelethonConfig:
    api_id: int
    api_hash: str
    phone: str
    session_file: str

    @classmethod
    def from_config(cls, cfg: Settings):
        return cls(
            api_id=cfg.TELEGRAM_API_ID,
            api_hash=cfg.TELEGRAM_API_HASH,
            phone=cfg.TELEGRAM_PHONE,
            session_file=cfg.SESSION_FILE,
        )