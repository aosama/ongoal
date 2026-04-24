"""
Robust JSON extraction from LLM responses.

Handles markdown code fences, nested braces, trailing text, and partial JSON.
"""

import json
import re
from typing import Any, Optional


# Private helper — not part of public API
def _strip_markdown_fences(text: str) -> str:
    """Remove markdown ```json ... ``` fences if present."""
    pattern = r'^\s*```(?:json)?\s*\n(.*?)\n?\s*```\s*$'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1)
    return text


# Private helper — not part of public API
def _find_balanced_braces(text: str) -> Optional[str]:
    """Locate the outermost balanced `{ ... }` pair using brace counting.

    Returns the substring from the first `{` to its matching `}`,
    or None if no balanced pair is found.
    """
    depth = 0
    start = -1
    for idx, char in enumerate(text):
        if char == '{':
            if depth == 0:
                start = idx
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0 and start != -1:
                return text[start:idx + 1]
    return None


def extract_json_object(text: str) -> Optional[Any]:
    """Extract the first valid JSON object from *any* LLM response string.

    Strategy:
        1. Strip markdown code fences.
        2. Use brace counting to find the outermost balanced `{...}` pair.
        3. Attempt json.loads — on success return the parsed object.
        4. Fall back to regex search for the first `{`.
        5. Return None if nothing works.
    """
    if not text:
        return None

    # Step 1: remove markdown fences
    stripped = _strip_markdown_fences(text)

    # Step 2: brace counting for balanced outer braces
    balanced = _find_balanced_braces(stripped)
    if balanced is not None:
        try:
            return json.loads(balanced)
        except json.JSONDecodeError:
            pass

    # Step 3: fallback regex search (first `{` to last `}`)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None
