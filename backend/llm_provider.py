"""
LLM Provider registry and module-level convenience functions.

Provider classes live in backend/providers/. This module handles
instantiation, caching, and re-exports the public API that the rest
of the codebase depends on.

Configuration via .env:
  LLM_PROVIDER=ollama|ollama_cloud|openrouter|anthropic  (default: ollama_cloud)

  --- Ollama local/proxy (LLM_PROVIDER=ollama) ---
  OLLAMA_BASE_URL     Local Ollama daemon URL  (default: http://localhost:11434)
  OLLAMA_MODEL        Model name; :cloud/-cloud suffix routes through Ollama Cloud
  OLLAMA_MAX_RETRIES  Retry count (default: 3)
  OLLAMA_RETRY_DELAY_MS  Initial backoff in ms (default: 1000)

  --- Ollama Cloud REST API (LLM_PROVIDER=ollama_cloud) ---
  OLLAMA_CLOUD_BASE_URL  API base URL  (default: https://ollama.com/v1)
  OLLAMA_CLOUD_API_KEY   API key from https://ollama.com/settings/api-keys
  OLLAMA_CLOUD_MODEL     Model name (default: gemma3:27b)

  --- OpenRouter (LLM_PROVIDER=openrouter) ---
  OPENROUTER_API_KEY, OPENROUTER_MODEL

  --- Anthropic Claude (LLM_PROVIDER=anthropic) ---
  ANTHROPIC_API_KEY, ANTHROPIC_MODEL
"""

import logging
import os

from dotenv import load_dotenv

from backend.providers import LLMProvider
from backend.providers.ollama_provider import OllamaProvider
from backend.providers.ollama_cloud_provider import OllamaCloudApiProvider
from backend.providers.openrouter_provider import OpenRouterProvider
from backend.providers.anthropic_provider import AnthropicProvider

load_dotenv()

logger = logging.getLogger(__name__)

PROVIDERS = {
    "ollama": OllamaProvider,
    "ollama_cloud": OllamaCloudApiProvider,
    "openrouter": OpenRouterProvider,
    "anthropic": AnthropicProvider,
}

_active_provider: LLMProvider = None


def get_provider() -> LLMProvider:
    global _active_provider
    if _active_provider is None:
        provider_name = os.getenv("LLM_PROVIDER", "ollama_cloud").lower()
        if provider_name not in PROVIDERS:
            logger.warning(
                "Unknown LLM_PROVIDER '%s', falling back to 'ollama_cloud'", provider_name
            )
            provider_name = "ollama_cloud"
        _active_provider = PROVIDERS[provider_name]()
    return _active_provider


def reset_provider():
    global _active_provider
    _active_provider = None


def is_available() -> bool:
    return get_provider().is_available()


async def generate(prompt: str, max_tokens: int = 1000) -> str:
    return await get_provider().generate(prompt, max_tokens)


async def generate_stream(messages: list[dict[str, str]], max_tokens: int = 2000):
    async for chunk in get_provider().generate_stream(messages, max_tokens):
        yield chunk


def get_service_status() -> dict[str, object]:
    provider = get_provider()
    status = provider.get_status()
    status["configured_provider"] = os.getenv("LLM_PROVIDER", "ollama")
    return status