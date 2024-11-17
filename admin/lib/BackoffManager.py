# utils.py
import asyncio
import random
from .config import BackoffConfig

from .exceptions import RateLimitError

class BackoffManager:
    def __init__(self, cfg: BackoffConfig):
        self.config = cfg

    async def exponential_backoff(self, attempt: int, base_delay: float) -> None:
        wait_time = 2 ** attempt
        await asyncio.sleep(10 * base_delay * wait_time)

    async def process_with_backoff(self, callback):
        for attempt in range(self.config.max_attempts):
            try:
                if self.config.slow_mode:
                    await asyncio.sleep(random.uniform(*self.config.slow_mode_delay))
                else:
                    await asyncio.sleep(self.config.base_delay)
                return await callback
            except Exception as e:
                if attempt < self.config.max_attempts - 1:
                    await self.exponential_backoff(attempt, self.config.base_delay)
                else:
                    raise RateLimitError("Max attempts reached", 1337) from e