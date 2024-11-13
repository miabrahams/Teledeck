from pydantic_settings import BaseSettings, SettingsConfigDict

import pathlib
from typing import Tuple


"""
load_dotenv()  # take environment variables from .env.
api_id = environ["TG_API_ID"]
api_hash = environ["TG_API_HASH"]
phone = environ["TG_PHONE"]
session_file = "user"

QueueItem = Tuple[Channel, Message]
MessageTaskQueue = asyncio.Queue[QueueItem]
Downloadable = Document | File

# Paths
MEDIA_PATH = pathlib.Path("./static/media/")
ORPHAN_PATH = pathlib.Path("./recyclebin/orphan/")
DB_PATH = pathlib.Path("./teledeck.db")
UPDATE_PATH = pathlib.Path("./data/update_info")
NEST_TQDM = True
DEFAULT_FETCH_LIMIT = 65

# Flood prevention
MAX_CONCURRENT_TASKS = 5
DELAY = 0.1


# For SLOW_MODE
SLOW_MODE = True
ADDITIONAL_DELAY = [5, 10]
if SLOW_MODE:
    MAX_CONCURRENT_TASKS = 1
"""


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

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

