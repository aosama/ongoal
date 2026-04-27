"""Ollama LLM provider — supports local and cloud models via local Ollama proxy.

Cloud models (e.g. gemma4:31b-cloud, qwen3.5:cloud) are auto-detected by the
model name suffix and routed through Ollama's cloud service.
"""

import json
import os
import asyncio
import logging
from typing import AsyncGenerator, Dict, List

import httpx

from backend.providers import LLMProvider, retry_with_backoff

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):

    def __init__(self):
        from backend.providers import DEFAULT_MAX_RETRIES, DEFAULT_RETRY_DELAY_MS
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud")
        self._is_cloud = self.model.endswith(":cloud") or self.model.endswith("-cloud")
        self.max_retries = int(os.getenv("OLLAMA_MAX_RETRIES", str(DEFAULT_MAX_RETRIES)))
        self.retry_delay_ms = int(os.getenv("OLLAMA_RETRY_DELAY_MS", str(DEFAULT_RETRY_DELAY_MS)))

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=120.0)

    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        async def _call():
            async with self._get_client() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_predict": max_tokens},
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data.get("response", "").strip()
                if not content and "thinking" in data:
                    content = data["thinking"].strip()
                return content

        return await retry_with_backoff(
            _call, max_retries=self.max_retries, initial_delay_ms=self.retry_delay_ms,
            label=f"Ollama generate({self.model})",
        )

    async def generate_stream(
        self, messages: List[Dict[str, str]], max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        from backend.providers import is_retryable_status

        async def _stream():
            async with self._get_client() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": True,
                        "options": {"num_predict": max_tokens},
                    },
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                            msg = chunk.get("message", {})
                            content = msg.get("content", "")
                            if content:
                                yield content
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
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
                    "Ollama stream(%s) failed with %s (attempt %d/%d), retrying in %.1fs",
                    self.model, exc.response.status_code, attempt + 1, self.max_retries, delay,
                )
                await asyncio.sleep(delay)
            except httpx.ConnectError as exc:
                last_exception = exc
                delay = (self.retry_delay_ms / 1000) * (2 ** attempt)
                logger.warning(
                    "Ollama stream(%s) connection error (attempt %d/%d), retrying in %.1fs",
                    self.model, attempt + 1, self.max_retries, delay,
                )
                await asyncio.sleep(delay)
        raise last_exception

    def is_available(self) -> bool:
        return True

    def get_status(self) -> Dict[str, object]:
        mode = "cloud" if self._is_cloud else "local"
        return {
            "provider": f"Ollama ({mode})",
            "model": self.model,
            "base_url": self.base_url,
            "available": True,
            "cost": "cloud subscription" if self._is_cloud else "free",
        }