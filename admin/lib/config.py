from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml
from pydantic import BaseModel, ConfigDict, Field

CONFIG_DIR_ENV = "TELEDECK_CONFIG_DIR"
CONFIG_FILE_ENV = "TELEDECK_CONFIG_FILE"
DEFAULT_FILE = "default.yaml"
LOCAL_FILE = "local.yaml"
CONFIG_ROOT = "config"


# TODO: Remove legacy env

class DelayRange(BaseModel):
    min: float = Field(default=5.0, ge=0)
    max: float = Field(default=10.0, ge=0)

    model_config = ConfigDict(extra="forbid")


class BackoffSettings(BaseModel):
    max_attempts: int = 5
    base_delay_seconds: float = 2.0
    slow_mode: bool = False
    slow_mode_delay_seconds: DelayRange = DelayRange()

    model_config = ConfigDict(extra="forbid")


class QueueSettings(BaseModel):
    max_concurrent_tasks: int = 2

    model_config = ConfigDict(extra="forbid")


class FetchSettings(BaseModel):
    default_limit: Optional[int] = 100
    strategy: str = "unread"
    write_message_links: bool = False

    model_config = ConfigDict(extra="forbid")


class StorageSettings(BaseModel):
    max_file_size_bytes: int = 1024 * 1024 * 1024

    model_config = ConfigDict(extra="forbid")


class PathSettings(BaseModel):
    db_path: Path = Path("./teledeck.db")
    static_root: Path = Path("./static")
    media_root: Path = Path("./static/media")
    orphan_root: Path = Path("./recyclebin/orphan")
    recycle_root: Path = Path("./recyclebin")
    static_assets: Path = Path("./server/assets")
    update_state: Path = Path("./data/update_info")
    export_root: Path = Path("./exports")

    model_config = ConfigDict(extra="forbid")


class AppSettings(BaseModel):
    env: str = "development"
    http_port: int = 4000
    session_cookie_name: str = "session"

    model_config = ConfigDict(extra="forbid")


class TelegramSettings(BaseModel):
    api_id: int = 0
    api_hash: str = ""
    phone: str = ""
    db_key: str = ""
    session_file: str = "user"

    model_config = ConfigDict(extra="forbid")


class TwitterSettings(BaseModel):
    auth_token: str = ""
    csrf_token: str = ""

    model_config = ConfigDict(extra="forbid")


class TaggingSettings(BaseModel):
    grpc_host: str = "localhost"
    grpc_port: int = 8081
    default_cutoff: float = 0.35

    model_config = ConfigDict(extra="forbid")


class Settings(BaseModel):
    app: AppSettings = AppSettings()
    paths: PathSettings = PathSettings()
    storage: StorageSettings = StorageSettings()
    telegram: TelegramSettings = TelegramSettings()
    backoff: BackoffSettings = BackoffSettings()
    queue: QueueSettings = QueueSettings()
    fetch: FetchSettings = FetchSettings()
    twitter: TwitterSettings = TwitterSettings()
    tagging: TaggingSettings = TaggingSettings()

    model_config = ConfigDict(extra="forbid")

    def __init__(self, **data: Any) -> None:
        if not data:
            data = self.load_data()
        super().__init__(**data)

    # --- Convenience properties mirroring legacy attribute names ---
    @property
    def ENV(self) -> str:
        return self.app.env

    @property
    def PORT(self) -> int:
        return self.app.http_port

    @property
    def SESSION_COOKIE_NAME(self) -> str:
        return self.app.session_cookie_name

    @property
    def DB_PATH(self) -> Path:
        return self.paths.db_path

    @property
    def MEDIA_PATH(self) -> Path:
        return self.paths.media_root

    @property
    def ORPHAN_PATH(self) -> Path:
        return self.paths.orphan_root

    @property
    def EXPORT_PATH(self) -> Path:
        return self.paths.export_root

    @property
    def UPDATE_PATH(self) -> Path:
        return self.paths.update_state

    @property
    def MAX_RETRY_ATTEMPTS(self) -> int:
        return self.backoff.max_attempts

    @property
    def RETRY_BASE_DELAY(self) -> float:
        return self.backoff.base_delay_seconds

    @property
    def SLOW_MODE(self) -> bool:
        return self.backoff.slow_mode

    @property
    def SLOW_MODE_DELAY(self) -> Tuple[float, float]:
        rng = self.backoff.slow_mode_delay_seconds
        return rng.min, rng.max

    @property
    def DEFAULT_FETCH_LIMIT(self) -> Optional[int]:
        return self.fetch.default_limit

    @property
    def MESSAGE_STRATEGY(self) -> str:
        return self.fetch.strategy

    @property
    def WRITE_MESSAGE_LINKS(self) -> bool:
        return self.fetch.write_message_links

    @property
    def MAX_CONCURRENT_TASKS(self) -> int:
        return self.queue.max_concurrent_tasks

    @property
    def TELEGRAM_API_ID(self) -> int:
        return self.telegram.api_id

    @property
    def TELEGRAM_API_HASH(self) -> str:
        return self.telegram.api_hash

    @property
    def TELEGRAM_PHONE(self) -> str:
        return self.telegram.phone

    @property
    def TELEGRAM_DB_KEY(self) -> str:
        return self.telegram.db_key

    @property
    def SESSION_FILE(self) -> str:
        return self.telegram.session_file

    @property
    def TWITTER_AUTHTOKEN(self) -> str:
        return self.twitter.auth_token

    @property
    def TWITTER_CSRFTOKEN(self) -> str:
        return self.twitter.csrf_token

    @property
    def TAGGER_URL(self) -> str:
        return self.tagging.grpc_host

    @property
    def TAGGER_PORT(self) -> int:
        return self.tagging.grpc_port

    @classmethod
    def load_data(cls) -> Dict[str, Any]:
        sources: Dict[str, Any] = {}
        config_file = os.getenv(CONFIG_FILE_ENV)

        if config_file:
            path = Path(config_file)
            if not path.exists():
                raise FileNotFoundError(f"Config file not found: {config_file}")
            sources = _load_yaml(path)
        else:
            config_dir = cls._resolve_config_dir()
            default_path = config_dir / DEFAULT_FILE
            local_path = config_dir / LOCAL_FILE
            sources = _load_yaml(default_path)
            if local_path.exists():
                sources = _merge_dicts(sources, _load_yaml(local_path))

        sources = _apply_legacy_env_overrides(sources)
        sources = _apply_env_overrides(sources)
        return sources

    @staticmethod
    def _resolve_config_dir() -> Path:
        if custom := os.getenv(CONFIG_DIR_ENV):
            return Path(custom)

        cwd = Path.cwd()
        candidates = [
            cwd / CONFIG_ROOT,
            cwd.parent / CONFIG_ROOT,
            cwd.parent.parent / CONFIG_ROOT,
        ]
        for candidate in candidates:
            if candidate.is_dir():
                return candidate
        raise FileNotFoundError("Unable to locate config directory; set TELEDECK_CONFIG_DIR")

    def with_path_override(self, paths: "PathConfig") -> "Settings":
        data = self.model_copy(deep=True)
        data.paths.media_root = paths.media_path
        data.paths.db_path = paths.db_path
        return data


class PathConfig(BaseModel):
    media_path: Path
    db_path: Path

    model_config = ConfigDict(extra="forbid")


class ExportConfig(PathConfig):
    channel_id: Optional[int] = None
    channel_name: Optional[str] = None
    message_limit: Optional[int] = None

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def custom(
        cls,
        cfg: Settings,
        export_path: Optional[Path],
        channel_name: Optional[str],
        channel_id: Optional[int],
    ) -> "ExportConfig":
        base_path = export_path or (cfg.EXPORT_PATH / str(channel_name))
        return cls(
            media_path=base_path / "media",
            db_path=base_path / "teledeck_export.db",
            channel_id=channel_id,
            channel_name=channel_name,
        )


def create_export_location(channel_name: str, export_path: Optional[Path], cfg: Settings) -> Settings:
    export_cfg = ExportConfig.custom(cfg, export_path, channel_name, None)
    base_dir = export_cfg.media_path.parent
    base_dir.mkdir(parents=True, exist_ok=True)
    export_cfg.media_path.mkdir(parents=True, exist_ok=True)
    return cfg.with_path_override(export_cfg)


@dataclass
class BackoffConfig:
    max_attempts: int
    base_delay: float
    slow_mode: bool = False
    slow_mode_delay: Tuple[float, float] = (5.0, 10.0)

    @classmethod
    def from_config(cls, cfg: Settings) -> "BackoffConfig":
        return cls(
            max_attempts=cfg.backoff.max_attempts,
            base_delay=cfg.backoff.base_delay_seconds,
            slow_mode=cfg.backoff.slow_mode,
            slow_mode_delay=(
                cfg.backoff.slow_mode_delay_seconds.min,
                cfg.backoff.slow_mode_delay_seconds.max,
            ),
        )


class ProcessingConfig(PathConfig):
    orphan_path: Path
    write_message_links: bool = False
    max_file_size: int = 1024 * 1024 * 1024

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_config(cls, cfg: Settings) -> "ProcessingConfig":
        return cls(
            media_path=cfg.MEDIA_PATH,
            db_path=cfg.DB_PATH,
            orphan_path=cfg.ORPHAN_PATH,
            write_message_links=cfg.WRITE_MESSAGE_LINKS,
            max_file_size=cfg.storage.max_file_size_bytes,
        )


@dataclass
class StrategyConfig:
    strategy: str
    limit: Optional[int]

    @classmethod
    def from_config(cls, cfg: Settings) -> "StrategyConfig":
        return cls(
            strategy=cfg.MESSAGE_STRATEGY,
            limit=cfg.DEFAULT_FETCH_LIMIT,
        )


@dataclass
class QueueManagerConfig:
    max_concurrent_tasks: int

    @classmethod
    def from_config(cls, cfg: Settings) -> "QueueManagerConfig":
        return cls(max_concurrent_tasks=cfg.MAX_CONCURRENT_TASKS)


@dataclass
class TelethonConfig:
    api_id: int
    api_hash: str
    phone: str
    session_file: str

    @classmethod
    def from_config(cls, cfg: Settings) -> "TelethonConfig":
        return cls(
            api_id=cfg.TELEGRAM_API_ID,
            api_hash=cfg.TELEGRAM_API_HASH,
            phone=cfg.TELEGRAM_PHONE,
            session_file=cfg.SESSION_FILE,
        )


@dataclass
class DatabaseConfig:
    db_path: Path
    must_create: bool = False

    @classmethod
    def from_config(cls, cfg: Settings | ExportConfig) -> "DatabaseConfig":
        if isinstance(cfg, Settings):
            return cls(db_path=cfg.DB_PATH)
        return cls(db_path=cfg.db_path)


@dataclass
class UpdaterConfig:
    message_strategy: str = "unread"
    message_limit: Optional[int] = None
    mark_read: bool = True
    description: str = "Processing messages"


# --- internal helpers ----------------------------------------------------

def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
        if not isinstance(data, dict):
            raise TypeError(f"Expected mapping in config file {path}")
        return data


def _merge_dicts(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(base)
    for key, value in overlay.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def _apply_env_overrides(data: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(data)
    valid_roots = {
        "app",
        "paths",
        "storage",
        "telegram",
        "backoff",
        "queue",
        "fetch",
        "twitter",
        "tagging",
    }
    for env_name, value in os.environ.items():
        if "__" not in env_name:
            continue
        key_path = env_name.lower().split("__")
        if key_path[0] not in valid_roots:
            continue
        merged = _set_nested_value(merged, key_path, value)
    return merged


def _apply_legacy_env_overrides(data: Dict[str, Any]) -> Dict[str, Any]:
    legacy_map = {
        "ENV": ("app", "env"),
        "PORT": ("app", "http_port"),
        "SESSION_COOKIE_NAME": ("app", "session_cookie_name"),
        "DATABASE_NAME": ("paths", "db_path"),
        "DB_PATH": ("paths", "db_path"),
        "STATIC_DIR": ("paths", "static_assets"),
        "MEDIA_DIR": ("paths", "static_root"),
        "MEDIA_PATH": ("paths", "media_root"),
        "RECYCLE_DIR": ("paths", "recycle_root"),
        "ORPHAN_PATH": ("paths", "orphan_root"),
        "TAGGER_URL": ("tagging", "grpc_host"),
        "TAGGER_PORT": ("tagging", "grpc_port"),
        "TELEGRAM_API_ID": ("telegram", "api_id"),
        "TELEGRAM_API_HASH": ("telegram", "api_hash"),
        "TELEGRAM_PHONE": ("telegram", "phone"),
        "TELEGRAM_DB_KEY": ("telegram", "db_key"),
        "SESSION_FILE": ("telegram", "session_file"),
        "TWITTER_AUTHTOKEN": ("twitter", "auth_token"),
        "TWITTER_CSRFTOKEN": ("twitter", "csrf_token"),
    }
    merged = dict(data)
    for env_name, key_path in legacy_map.items():
        value = os.getenv(env_name)
        if value is None:
            continue
        merged = _set_nested_value(merged, key_path, value)
    return merged


def _set_nested_value(data: Dict[str, Any], path: Tuple[str, ...] | list[str], value: Any) -> Dict[str, Any]:
    if isinstance(path, tuple):
        keys = list(path)
    else:
        keys = path

    target = dict(data)
    current = target
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = _coerce_value(value, current.get(keys[-1]))
    return target


def _coerce_value(value: Any, existing: Any) -> Any:
    if existing is None:
        return value
    if isinstance(existing, bool):
        return str(value).lower() in {"true", "1", "yes", "on"}
    if isinstance(existing, int):
        try:
            return int(value)
        except ValueError:
            return existing
    if isinstance(existing, float):
        try:
            return float(value)
        except ValueError:
            return existing
    if isinstance(existing, Path):
        return Path(str(value))
    if isinstance(existing, dict):
        # If we somehow pass a dict, merge recursively
        if isinstance(value, dict):
            return _merge_dicts(existing, value)
        return existing
    return value
