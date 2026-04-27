"""Ollama Cloud REST API provider — OpenAI-compatible endpoint at https://ollama.com/v1.

Calls Ollama's hosted API directly using a Bearer API key.
"""

import json
import os
import asyncio
import logging
from typing import AsyncGenerator, Dict, List

import httpx

from backend.providers import LLMProvider, retry_with_backoff, DEFAULT_MAX_RETRIES, DEFAULT_RETRY_DELAY_MS

logger = logging.getLogger(__name__)


class OllamaCloudApiProvider(LLMProvider):

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_CLOUD_BASE_URL", "https://ollama.com/v1").rstrip("/")
        self.api_key = os.getenv("OLLAMA_CLOUD_API_KEY", "")
        self.model = os.getenv("OLLAMA_CLOUD_MODEL", "gemma3:27b")
        self.max_retries = int(os.getenv("OLLAMA_MAX_RETRIES", str(DEFAULT_MAX_RETRIES)))
        self.retry_delay_ms = int(os.getenv("OLLAMA_RETRY_DELAY_MS", str(DEFAULT_RETRY_DELAY_MS)))

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=120.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        async def _call():
            async with self._get_client() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()

        return await retry_with_backoff(
            _call, max_retries=self.max_retries, initial_delay_ms=self.retry_delay_ms,
            label=f"OllamaCloud generate({self.model})",
        )

    async def generate_stream(
        self, messages: List[Dict[str, str]], max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        from backend.providers import is_retryable_status

        async def _stream():
            async with self._get_client() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "stream": True,
                    },
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        payload = line[6:].strip()
                        if payload == "[DONE]":
                            break
                        try:
                            chunk = json.loads(payload)
                            content = chunk["choices"][0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

        last_exception = None
        for attempt in range(self.max_retries):
            try:
                async for chunk in _stream():
                    yield chunk
                return
            except httpx.HTTPStatusError as exc:
                if not is_retryable_status(exc.response.status_code):
                    raise
                last_exception = exc
                delay = (self.retry_delay_ms / 1000) * (2 ** attempt)
                logger.warning(
                    "OllamaCloud stream(%s) failed with %s (attempt %d/%d), retrying in %.1fs",
                    self.model, exc.response.status_code, attempt + 1, self.max_retries, delay,
                )
                await asyncio.sleep(delay)
            except httpx.ConnectError as exc:
                last_exception = exc
                delay = (self.retry_delay_ms / 1000) * (2 ** attempt)
                logger.warning(
                    "OllamaCloud stream(%s) connection error (attempt %d/%d), retrying in %.1fs",
                    self.model, attempt + 1, self.max_retries, delay,
                )
                await asyncio.sleep(delay)
        raise last_exception

    def is_available(self) -> bool:
        return bool(self.api_key)

    def get_status(self) -> Dict[str, object]:
        return {
            "provider": "Ollama Cloud API",
            "model": self.model,
            "base_url": self.base_url,
            "available": bool(self.api_key),
            "cost": "cloud subscription",
        }