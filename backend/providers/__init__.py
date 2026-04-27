"""
LLM Provider abstraction layer.

Exports the LLMProvider ABC, retry utilities, and all concrete provider classes.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List

import httpx

logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY_MS = 1000


def is_retryable_status(status_code: int) -> bool:
    return status_code in (408, 429, 500, 502, 503, 504)


async def retry_with_backoff(func, max_retries: int = DEFAULT_MAX_RETRIES,
                              initial_delay_ms: int = DEFAULT_RETRY_DELAY_MS,
                              label: str = "LLM call"):
    last_exception = None
    for attempt in range(max_retries):
        try:
            return await func()
        except httpx.HTTPStatusError as exc:
            if not is_retryable_status(exc.response.status_code):
                raise
            last_exception = exc
            delay = (initial_delay_ms / 1000) * (2 ** attempt)
            logger.warning(
                "%s failed with %s (attempt %d/%d), retrying in %.1fs",
                label, exc.response.status_code, attempt + 1, max_retries, delay,
            )
            await asyncio.sleep(delay)
        except httpx.ConnectError as exc:
            last_exception = exc
            delay = (initial_delay_ms / 1000) * (2 ** attempt)
            logger.warning(
                "%s connection error (attempt %d/%d), retrying in %.1fs",
                label, attempt + 1, max_retries, delay,
            )
            await asyncio.sleep(delay)
    raise last_exception


class LLMProvider(ABC):

    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        ...

    @abstractmethod
    async def generate_stream(
        self, messages: List[Dict[str, str]], max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...

    @abstractmethod
    def get_status(self) -> Dict[str, object]:
        ...