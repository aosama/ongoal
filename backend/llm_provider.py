"""
LLM Provider abstraction - Supports multiple LLM backends (Ollama, OpenRouter, Anthropic)

Configuration via .env:
  LLM_PROVIDER=ollama|openrouter|anthropic  (default: ollama)
  OLLAMA_BASE_URL, OLLAMA_MODEL              (for ollama — use :cloud or -cloud suffix for cloud models)
  OLLAMA_MAX_RETRIES                        (default: 3, retry transient failures)
  OLLAMA_RETRY_DELAY_MS                     (default: 1000, initial backoff delay in ms)
  ANTHROPIC_API_KEY, ANTHROPIC_MODEL         (for anthropic provider)
  OPENROUTER_API_KEY, OPENROUTER_MODEL       (for openrouter provider)

Cloud models (e.g. gemma4:31b-cloud, qwen3.5:cloud) are routed through your local
Ollama installation to Ollama's cloud servers. No separate API key needed —
just `ollama signin` once, then use :cloud model names.
"""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Retry defaults for transient failures (rate limits, server errors)
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY_MS = 1000


def _is_retryable_status(status_code: int) -> bool:
    """Return True for status codes that warrant a retry."""
    return status_code in (408, 429, 500, 502, 503, 504)


async def _retry_with_backoff(func, max_retries: int = DEFAULT_MAX_RETRIES,
                               initial_delay_ms: int = DEFAULT_RETRY_DELAY_MS,
                               label: str = "LLM call"):
    """Retry an async callable with exponential backoff on transient errors.

    Retries on httpx.HTTPStatusError with retryable status codes and on
    httpx.ConnectError. Other exceptions propagate immediately.
    """
    last_exception = None
    for attempt in range(max_retries):
        try:
            return await func()
        except httpx.HTTPStatusError as exc:
            if not _is_retryable_status(exc.response.status_code):
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
    # All retries exhausted — raise the last exception
    raise last_exception


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate a single response from the LLM"""

    @abstractmethod
    async def generate_stream(
        self, messages: List[Dict[str, str]], max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM"""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is properly configured and ready"""

    @abstractmethod
    def get_status(self) -> Dict[str, object]:
        """Return provider status information for /api/llm-status"""


class OllamaProvider(LLMProvider):
    """Ollama LLM provider — supports local and cloud models (:cloud/-cloud suffix) via local Ollama proxy

    Cloud models (e.g. gemma4:31b-cloud, qwen3.5:cloud) are auto-detected by the
    model name suffix and routed through Ollama's cloud service. Transient failures
    (rate limits, server errors) are retried with exponential backoff.
    """

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud")
        self._is_cloud = self.model.endswith(":cloud") or self.model.endswith("-cloud")
        self.max_retries = int(os.getenv("OLLAMA_MAX_RETRIES", str(DEFAULT_MAX_RETRIES)))
        self.retry_delay_ms = int(os.getenv("OLLAMA_RETRY_DELAY_MS", str(DEFAULT_RETRY_DELAY_MS)))

    def _get_client(self) -> httpx.AsyncClient:
        """Get a fresh async client — avoids event-loop-closed errors in tests"""
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
                # Fallback: some models return content in "thinking" when truncated
                if not content and "thinking" in data:
                    content = data["thinking"].strip()
                return content

        return await _retry_with_backoff(
            _call, max_retries=self.max_retries, initial_delay_ms=self.retry_delay_ms,
            label=f"Ollama generate({self.model})",
        )

    async def generate_stream(
        self, messages: List[Dict[str, str]], max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        # Streaming uses a single connection — retry on initial connect only,
        # then yield chunks. If the stream breaks mid-way, the caller sees a
        # shorter response, which the goal pipeline handles gracefully.
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
                            # Cloud "thinking" models emit thinking tokens before content
                            content = msg.get("content", "")
                            if content:
                                yield content
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

        # For streaming, we retry the initial connection only
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                async for chunk in _stream():
                    yield chunk
                return
            except httpx.HTTPStatusError as exc:
                if not _is_retryable_status(exc.response.status_code):
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
        return True  # Always attempt — will fail gracefully if Ollama not running

    def get_status(self) -> Dict[str, object]:
        mode = "cloud" if self._is_cloud else "local"
        return {
            "provider": f"Ollama ({mode})",
            "model": self.model,
            "base_url": self.base_url,
            "available": True,
            "cost": "cloud subscription" if self._is_cloud else "free",
        }


class OpenRouterProvider(LLMProvider):
    """OpenRouter LLM provider (supports free-tier models)"""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.model = os.getenv(
            "OPENROUTER_MODEL", "google/gemma-2-9b-it:free"
        )
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.AsyncClient(
            timeout=120.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/aosama/ongoal",
            },
        )

    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        response = await self.client.post(
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

    async def generate_stream(
        self, messages: List[Dict[str, str]], max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        async with self.client.stream(
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
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    def is_available(self) -> bool:
        return bool(self.api_key)

    def get_status(self) -> Dict[str, object]:
        return {
            "provider": "OpenRouter",
            "model": self.model,
            "available": bool(self.api_key),
            "cost": "free tier" if ":free" in self.model else "paid",
        }


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider (paid, requires API key)"""

    def __init__(self):
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.client = None
        if api_key:
            import anthropic

            self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        if not self.client:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    async def generate_stream(
        self, messages: List[Dict[str, str]], max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        if not self.client:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")
        stream = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text"):
                yield chunk.delta.text

    def is_available(self) -> bool:
        return self.client is not None

    def get_status(self) -> Dict[str, object]:
        return {
            "provider": "Anthropic Claude",
            "model": self.model,
            "available": self.client is not None,
            "cost": "paid",
        }


# Provider registry
PROVIDERS = {
    "ollama": OllamaProvider,
    "openrouter": OpenRouterProvider,
    "anthropic": AnthropicProvider,
}

# Cached provider instance — reused across calls
_active_provider: LLMProvider = None


def get_provider() -> LLMProvider:
    """Get the configured LLM provider instance (cached)"""
    global _active_provider
    if _active_provider is None:
        provider_name = os.getenv("LLM_PROVIDER", "ollama").lower()
        if provider_name not in PROVIDERS:
            logger.warning(
                "Unknown LLM_PROVIDER '%s', falling back to 'ollama'", provider_name
            )
            provider_name = "ollama"
        _active_provider = PROVIDERS[provider_name]()
    return _active_provider


def reset_provider():
    """Reset the cached provider — useful for testing or config changes"""
    global _active_provider
    _active_provider = None