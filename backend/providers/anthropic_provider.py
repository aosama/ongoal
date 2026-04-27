"""Anthropic Claude LLM provider (paid, requires API key)."""

import os
from typing import AsyncGenerator, Dict, List

from backend.providers import LLMProvider


class AnthropicProvider(LLMProvider):

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