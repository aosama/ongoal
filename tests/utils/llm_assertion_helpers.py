"""
LLM-based assertion helpers for semantic testing

Uses the configured LLM provider (Ollama/OpenRouter/Anthropic) to make
intelligent assertions about goals and language instead of exact matching.
"""

import json
import os
from typing import List, Dict

from dotenv import load_dotenv

load_dotenv()


class LLMAssertionResult:
    """Result of an LLM-based assertion"""

    def __init__(self, passed: bool, reason: str, confidence: str = "high"):
        self.passed = passed
        self.reason = reason
        self.confidence = confidence

    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"LLM Assertion: {status} - {self.reason} (confidence: {self.confidence})"


class LLMAssertionHelper:
    """Helper class for LLM-based assertions using any provider"""

    async def _ask_llm(self, prompt: str, max_tokens: int = 512) -> str:
        """Send a prompt to the LLM and return the text response"""
        from backend.llm_provider import get_provider

        provider = get_provider()
        return await provider.generate(prompt, max_tokens=max_tokens)

    async def assert_goal_semantic_match(
        self, goals: List[Dict], expected_concept: str, context: str = ""
    ) -> LLMAssertionResult:
        """Assert that goals contain a specific concept semantically"""
        goals_text = "\n".join(
            [f"- [{g.get('type', 'unknown')}] {g.get('text', '')}" for g in goals]
        )

        prompt = f"""You are evaluating whether a list of goals contains a specific concept.

CONTEXT: {context or "Testing goal extraction and merging in a conversational AI system."}

GOALS TO EVALUATE:
{goals_text}

EXPECTED CONCEPT: "{expected_concept}"

TASK: Determine if any of the goals semantically captures the expected concept.

Respond ONLY with valid JSON:
{{"passed": true/false, "reason": "Brief explanation", "confidence": "high/medium/low"}}"""

        return await self._evaluate(prompt)

    async def assert_goal_preserved_through_merge(
        self,
        original_goals: List[Dict],
        new_goals: List[Dict],
        merged_goals: List[Dict],
        target_concept: str,
    ) -> LLMAssertionResult:
        """Assert that a concept is preserved through merge"""
        original_text = "\n".join(
            [f"- [{g.get('type', 'unknown')}] {g.get('text', '')}" for g in original_goals]
        )
        new_text = "\n".join(
            [f"- [{g.get('type', 'unknown')}] {g.get('text', '')}" for g in new_goals]
        )
        merged_text = "\n".join(
            [f"- [{g.get('type', 'unknown')}] {g.get('text', '')}" for g in merged_goals]
        )

        prompt = f"""You are evaluating a goal merging operation.

TARGET CONCEPT: "{target_concept}"

ORIGINAL GOALS:
{original_text}

NEW GOALS:
{new_text}

MERGED GOALS:
{merged_text}

Is the target concept preserved in the merged result? It may be kept, combined, or integrated — but not lost.

Respond ONLY with valid JSON:
{{"passed": true/false, "reason": "Explanation", "confidence": "high/medium/low"}}"""

        return await self._evaluate(prompt)

    async def assert_goals_capture_message_intent(
        self, message: str, goals: List[Dict], expected_intents: List[str]
    ) -> LLMAssertionResult:
        """Assert that extracted goals capture intended meanings"""
        goals_text = "\n".join(
            [f"- [{g.get('type', 'unknown')}] {g.get('text', '')}" for g in goals]
        )
        intents_text = "\n".join([f"- {i}" for i in expected_intents])

        prompt = f"""Evaluate whether extracted goals capture the expected intents.

MESSAGE: "{message}"

EXTRACTED GOALS:
{goals_text}

EXPECTED INTENTS:
{intents_text}

Do the goals capture the expected intents?

Respond ONLY with valid JSON:
{{"passed": true/false, "reason": "Explanation", "confidence": "high/medium/low"}}"""

        return await self._evaluate(prompt)

    async def _evaluate(self, prompt: str, max_retries: int = 2) -> LLMAssertionResult:
        """Send prompt to LLM and parse the JSON response, with retries for transient errors"""
        import httpx

        for attempt in range(max_retries + 1):
            try:
                response_text = await self._ask_llm(prompt)
                if not response_text.strip():
                    if attempt < max_retries:
                        continue
                    return LLMAssertionResult(
                        passed=False, reason="LLM returned empty response", confidence="low"
                    )
                # Strip markdown code fences if present
                if response_text.startswith("```"):
                    response_text = (
                        response_text.replace("```json", "").replace("```", "").strip()
                    )
                result_data = self._parse_json_response(response_text)
                return LLMAssertionResult(
                    passed=result_data.get("passed", False),
                    reason=result_data.get("reason", "No reason provided"),
                    confidence=result_data.get("confidence", "unknown"),
                )
            except httpx.HTTPStatusError as e:
                if attempt < max_retries and e.response.status_code in (429, 500, 502, 503, 504):
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                    continue
                return LLMAssertionResult(
                    passed=False,
                    reason=f"LLM assertion failed: HTTP {e.response.status_code}",
                    confidence="low",
                )
            except Exception as e:
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                    continue
                return LLMAssertionResult(
                    passed=False, reason=f"LLM assertion failed: {e}", confidence="low"
                )

    @staticmethod
    def _parse_json_response(text: str) -> dict:
        """Parse JSON from LLM response, with repair for truncated output"""
        import re

        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strip trailing incomplete content and try to close the object
        trimmed = text.rstrip()
        # Remove trailing incomplete string/whitespace/comma
        trimmed = re.sub(r'[,"]?\s*$', '', trimmed)
        if not trimmed.endswith("}"):
            trimmed += "}"

        try:
            return json.loads(trimmed)
        except json.JSONDecodeError:
            pass

        # Last resort: extract all valid key-value pairs and rebuild
        kv_pairs = re.findall(
            r'"(passed|reason|confidence)"\s*:\s*"(?:[^"\\]|\\.)*"|'
            r'"(passed|reason|confidence)"\s*:\s*(?:true|false|\d+)',
            trimmed,
        )
        if kv_pairs:
            # Flatten the tuples from findall groups
            pairs = []
            for match in kv_pairs:
                pairs.append(match[0] or match[1])
            # Just parse what we can from each match
            all_pairs = re.findall(
                r'"(passed|reason|confidence)"\s*:\s*(?:"((?:[^"\\]|\\.)*)"|(true|false|\d+))',
                trimmed,
            )
            parts = []
            for key, str_val, bare_val in all_pairs:
                if str_val:
                    parts.append(f'"{key}": "{str_val}"')
                else:
                    parts.append(f'"{key}": {bare_val}')
            rebuilt = "{" + ", ".join(parts) + "}"
            return json.loads(rebuilt)

        raise json.JSONDecodeError("Could not parse LLM JSON response", text, 0)


# Lazy global instance — created on first access, not at import time
llm_assert = None


def get_llm_assert() -> LLMAssertionHelper:
    global llm_assert
    if llm_assert is None:
        llm_assert = LLMAssertionHelper()
    return llm_assert