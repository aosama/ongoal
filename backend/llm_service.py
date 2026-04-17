"""
Centralized LLM service for OnGoal
Delegates to the configured LLM provider (Ollama, OpenRouter, or Anthropic)
"""

import logging
import os
from typing import List, Dict, Any, AsyncGenerator

from dotenv import load_dotenv

from backend.llm_provider import get_provider, LLMProvider

load_dotenv()

logger = logging.getLogger(__name__)


class LLMService:
    """Centralized service for all LLM operations in OnGoal"""

    @staticmethod
    def _get_provider() -> LLMProvider:
        return get_provider()

    @staticmethod
    async def generate_response(
        prompt: str,
        max_tokens: int = 1000,
        model: str = None
    ) -> str:
        """Generate a single response from the LLM"""
        provider = LLMService._get_provider()
        if not provider.is_available():
            raise RuntimeError(
                "LLM provider not configured. Please set up your LLM provider "
                "(Ollama, OpenRouter, or Anthropic) in the .env file."
            )
        return await provider.generate(prompt, max_tokens)

    @staticmethod
    async def generate_streaming_response(
        messages: List[Dict[str, str]],
        max_tokens: int = 2000,
        model: str = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM"""
        provider = LLMService._get_provider()
        if not provider.is_available():
            raise RuntimeError(
                "LLM provider not configured. Please set up your LLM provider "
                "(Ollama, OpenRouter, or Anthropic) in the .env file."
            )
        async for chunk in provider.generate_stream(messages, max_tokens):
            yield chunk

    @staticmethod
    def is_available() -> bool:
        """Check if LLM service is available"""
        return LLMService._get_provider().is_available()

    @staticmethod
    def get_service_status() -> Dict[str, Any]:
        """Get detailed service status information"""
        provider = LLMService._get_provider()
        status = provider.get_status()
        status["configured_provider"] = os.getenv("LLM_PROVIDER", "ollama")
        return status