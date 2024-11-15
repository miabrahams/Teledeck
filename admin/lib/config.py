from pydantic_settings import BaseSettings, SettingsConfigDict

import pathlib
from typing import Tuple

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
    MEDIA_PATH: pathlib.Path = pathlib.Path("./static/media/")
    ORPHAN_PATH: pathlib.Path = pathlib.Path("./recyclebin/orphan/")
    DB_PATH: pathlib.Path = pathlib.Path("./teledeck.db")
    UPDATE_PATH: pathlib.Path = pathlib.Path("./data/update_info")
    DEFAULT_FETCH_LIMIT: int = 65
    MESSAGE_STRATEGY: str = "unread"
    WRITE_MESSAGE_LINKS: bool = False

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

