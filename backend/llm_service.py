"""
Centralized LLM service for OnGoal
Eliminates code duplication and provides consistent LLM interaction patterns
"""

import os
import anthropic
from typing import List, Dict, Any, AsyncGenerator, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration - retrieve from environment variables
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL")
anthropic_client = None

# Initialize Anthropic client if API key is available
if os.getenv("ANTHROPIC_API_KEY"):
    anthropic_client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


class LLMService:
    """Centralized service for all LLM operations in OnGoal"""

    @staticmethod
    async def generate_response(
        prompt: str,
        max_tokens: int = 1000,
        model: str = ANTHROPIC_MODEL
    ) -> str:
        """
        Generate a single response from the LLM

        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens for response
            model: Model to use for generation

        Returns:
            The generated response text

        Raises:
            RuntimeError: If ANTHROPIC_API_KEY is not configured
        """
        if not anthropic_client:
            raise RuntimeError(
                "❌ ANTHROPIC_API_KEY not configured. OnGoal requires Claude API access. "
                "Please set your ANTHROPIC_API_KEY environment variable to use OnGoal."
            )

        response = await anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    @staticmethod
    async def generate_streaming_response(
        messages: List[Dict[str, str]],
        max_tokens: int = 2000,
        model: str = ANTHROPIC_MODEL
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from the LLM

        Args:
            messages: List of message dictionaries with role and content
            max_tokens: Maximum tokens for response
            model: Model to use for generation

        Yields:
            String chunks of the streaming response

        Raises:
            RuntimeError: If ANTHROPIC_API_KEY is not configured
        """
        if not anthropic_client:
            raise RuntimeError(
                "❌ ANTHROPIC_API_KEY not configured. OnGoal requires Claude API access. "
                "Please set your ANTHROPIC_API_KEY environment variable to use OnGoal."
            )

        stream = await anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            stream=True
        )

        async for chunk in stream:
            if chunk.type == "content_block_delta" and hasattr(chunk.delta, 'text'):
                yield chunk.delta.text

    @staticmethod
    def is_available() -> bool:
        """Check if LLM service is available (API key configured)"""
        return anthropic_client is not None

    @staticmethod
    def get_service_status() -> Dict[str, Any]:
        """Get detailed service status information"""
        return {
            "service": "Anthropic Claude",
            "available": anthropic_client is not None,
            "model": ANTHROPIC_MODEL,
            "api_key_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
            "client_initialized": anthropic_client is not None
        }