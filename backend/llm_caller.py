"""
Shared LLM JSON caller — Eliminates the repeated "call LLM → parse JSON" pattern.

Every pipeline module that calls the LLM and expects a JSON response can use
call_llm_json() instead of individually importing the provider, calling generate,
and running extract_json_object.
"""

import logging
from typing import Any, Optional

import backend.llm_provider as llm_provider
from backend.json_parser import extract_json_object

logger = logging.getLogger(__name__)


async def call_llm_json(prompt: str, max_tokens: int = 1000, label: str = "") -> Optional[Any]:
    """Call the configured LLM provider and return the parsed JSON object.

    Returns the parsed dict/list on success, or None on any failure
    (LLM error, JSON parse error, empty response).
    """
    try:
        response_text = await llm_provider.generate(prompt, max_tokens=max_tokens)
        return extract_json_object(response_text)
    except Exception as e:
        if label:
            logger.warning("%s failed: %s", label, e)
        return None