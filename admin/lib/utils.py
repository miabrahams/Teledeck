# utils.py
from typing import Tuple
import asyncio
import random
from dataclasses import dataclass

from .exceptions import TelegramClientError

@dataclass
class BackoffConfig:
    max_attempts: int
    base_delay: float
    slow_mode: bool = False
    slow_mode_delay: Tuple[float, float] = (5.0, 10.0)

async def exponential_backoff(attempt: int, base_delay: float) -> None:
    wait_time = 2 ** attempt
    await asyncio.sleep(10 * base_delay * wait_time)

async def process_with_backoff(callback, config: BackoffConfig):
    for attempt in range(config.max_attempts):
        try:
            if config.slow_mode:
                await asyncio.sleep(random.uniform(*config.slow_mode_delay))
            else:
                await asyncio.sleep(config.base_delay)
            return await callback
        except Exception as e:
            if attempt < config.max_attempts - 1:
                await exponential_backoff(attempt, config.base_delay)
            else:
                raise TelegramClientError(f"Max attempts reached: {str(e)}")