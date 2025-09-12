from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Tuple
from pathlib import Path
from dataclasses import dataclass


class PathConfig(BaseModel):
    """Configuration for path overrides"""
    media_path: Path
    db_path: Path


class BaseConfig(BaseSettings):
    """Base configuration with common settings"""
    TELEGRAM_API_ID: int = 0
    TELEGRAM_API_HASH: str = ""
    TELEGRAM_PHONE: str = ""
    TELEGRAM_DB_KEY: str = ""
    TWITTER_AUTHTOKEN: str = ""
    TWITTER_CSRFTOKEN: str = ""
    ENV: str = ""
    MAX_RETRY_ATTEMPTS: int = 5
    RETRY_BASE_DELAY: float = 2.0
    MAX_CONCURRENT_TASKS: int = 2
    SLOW_MODE: bool = False
    SLOW_MODE_DELAY: Tuple[float, float] = (5.0, 10.0)
    DEFAULT_FETCH_LIMIT: int | None = 100
    MESSAGE_STRATEGY: str = "unread"
    WRITE_MESSAGE_LINKS: bool = False


class Settings(BaseConfig):
    TWITTER_AUTHTOKEN: str = ""
    TWITTER_CSRFTOKEN: str = ""
    TAGGER_URL: str = ""
    SESSION_FILE: str = "user"

    # Paths
    MEDIA_PATH: Path = Path("./static/media/")
    ORPHAN_PATH: Path = Path("./recyclebin/orphan/")
    DB_PATH: Path = Path("./teledeck.db")
    UPDATE_PATH: Path = Path("./data/update_info")
    EXPORT_PATH: Path = Path("./exports")

    def with_path_override(self, paths: PathConfig) -> "Settings":
        """Create a new Settings instance with overridden values"""
        return Settings(
            **{
                **self.model_dump(),
                "MEDIA_PATH": paths.media_path,
                "DB_PATH": paths.db_path,
            }
        )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


class ExportConfig(PathConfig):
    """Configuration for export commands"""
    channel_id: Optional[int] = None
    channel_name: Optional[str] = None
    message_limit: Optional[int] = None

    @classmethod
    def custom(
        cls, cfg: Settings, export_path: Optional[Path], channel_name: Optional[str], channel_id: Optional[int]
    ):
        """Create an export configuration with custom paths"""
        base_path = export_path or (cfg.EXPORT_PATH / str(channel_name))
        return cls(
            media_path=base_path / "media",
            db_path=base_path / "teledeck_export.db",
            channel_id=channel_id,
            channel_name=channel_name
        )

def create_export_location(channel_name: str, export_path: Path, cfg: Settings):
    """ Create a new Settings instance with path overrides for export commands """
    export_cfg = ExportConfig.custom(cfg, export_path, channel_name, None)
    export_path.mkdir(parents=True, exist_ok=True)
    export_cfg.media_path.mkdir(parents=True, exist_ok=True)
    return cfg.with_path_override(export_cfg)


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
            slow_mode_delay=cfg.SLOW_MODE_DELAY,
        )


@dataclass
class ProcessingConfig(PathConfig):
    """Configuration for media processing"""
    orphan_path: Path
    write_message_links: bool = False
    max_file_size: int = 1_000_000_000  # 1GB default

    @classmethod
    def from_config(cls, cfg: Settings):
        return cls(
            media_path=cfg.MEDIA_PATH,
            db_path=cfg.DB_PATH,
            orphan_path=cfg.ORPHAN_PATH,
            write_message_links=cfg.WRITE_MESSAGE_LINKS,
        )


@dataclass
class StrategyConfig:
    """Configuration for message fetching strategies"""

    strategy: str
    limit: Optional[int]

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

# Example usage for other component configs
@dataclass
class DatabaseConfig:
    """Configuration for database operations"""
    db_path: Path
    must_create: bool = False

    @classmethod
    def from_config(cls, cfg: Settings | ExportConfig):
        if isinstance(cfg, Settings):
            return cls(db_path=cfg.DB_PATH)
        return cls(db_path=cfg.db_path)


@dataclass
class UpdaterConfig:
    """Configuration for the updater behavior"""
    message_strategy: str = "unread"  # Default to unread for updates
    message_limit: Optional[int] = None  # None means no limit
    mark_read: bool = True  # Whether to mark messages as read after processing
    description: str = "Processing messages"