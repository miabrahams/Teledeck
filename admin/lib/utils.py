# utils.py
from typing import Tuple
import asyncio
import random

from .exceptions import TelegramClientError

async def exponential_backoff(attempt: int, base_delay: float) -> None:
    wait_time = 2 ** attempt
    await asyncio.sleep(10 * base_delay * wait_time)

async def process_with_backoff(callback, max_attempts: int, base_delay: float,
                             slow_mode: bool = False, slow_mode_delay: Tuple[float, float] = (5.0, 10.0)):
    for attempt in range(max_attempts):
        try:
            if slow_mode:
                await asyncio.sleep(random.uniform(*slow_mode_delay))
            else:
                await asyncio.sleep(base_delay)
            return await callback
        except Exception as e:
            if attempt < max_attempts - 1:
                await exponential_backoff(attempt, base_delay)
            else:
                raise TelegramClientError(f"Max attempts reached: {str(e)}")