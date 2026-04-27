"""OpenRouter LLM provider (supports free-tier models)."""

import json
import os
from typing import AsyncGenerator, Dict, List

import httpx

from backend.providers import LLMProvider


class OpenRouterProvider(LLMProvider):

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