"""Goal Detection — Detect conversational anomalies and goal behavior patterns."""

import logging
from typing import List, Dict, Optional

from backend.models import Goal
from backend.llm_caller import call_llm_json

logger = logging.getLogger(__name__)


async def _detect_flag(prompt: str, bool_key: str, result_keys: dict[str, object], max_tokens: int = 600, label: str = "") -> Optional[Dict]:
    """Generic boolean-flag detection: call LLM, check a boolean key, return selected keys."""
    data = await call_llm_json(prompt, max_tokens=max_tokens, label=label)
    if data and data.get(bool_key, False):
        return {k: data.get(k, v) for k, v in result_keys.items()}
    return None


async def detect_forgetting(goals: List[Goal], assistant_response: str) -> List[Dict]:
    """Detect goals that may have been forgotten in the conversation (REQ-03-01-006)."""
    if not goals or not assistant_response:
        return []

    repeatedly_ignored = [
        g for g in goals
        if not g.completed and not g.locked and g.evaluation and g.evaluation.category == "ignore"
    ]
    if not repeatedly_ignored:
        return []

    goals_text = "\n".join([f"- {g.id}: {g.text} (ignored {1} time(s))" for g in repeatedly_ignored])

    prompt = f"""You are analyzing whether the following conversation goals have been forgotten by the assistant. A "forgotten" goal is one that has been consistently ignored across responses.

Goals that were ignored in the latest response:
{goals_text}

Assistant response: {assistant_response}

For each goal that you believe is genuinely being forgotten (not just naturally completed or irrelevant), provide a brief explanation and a suggestion for what the user could do. If none are truly forgotten, return an empty list.

Respond ONLY with valid JSON:

{{
  "forgotten_goals": [
    {{"goal_id": "<ID>", "reason": "<REASON>", "suggestion": "<SUGGESTION>"}}
  ]
}}"""

    data = await call_llm_json(prompt, max_tokens=800, label="Forgetting detection")
    return data.get("forgotten_goals", []) if data else []


async def detect_contradiction(goals: List[Goal]) -> List[Dict]:
    """Detect contradictions between active goals (REQ-03-01-003)."""
    active_goals = [g for g in goals if not g.completed]
    if len(active_goals) < 2:
        return []

    goals_text = "\n".join([f"- {g.id}: {g.text} (type: {g.type})" for g in active_goals])

    prompt = f"""You are analyzing whether any of the following conversation goals contradict each other. Two goals contradict if they cannot both be satisfied simultaneously or if pursuing one would undermine the other.

Goals:
{goals_text}

For each pair of goals that you believe genuinely contradict each other, provide the goal IDs, the nature of the contradiction, and a suggested resolution. If no goals contradict, return an empty list.

Respond ONLY with valid JSON:

{{
  "contradictions": [
    {{"goal_id_1": "<ID_1>", "goal_id_2": "<ID_2>", "reason": "<REASON>", "resolution": "<SUGGESTION>"}}
  ]
}}"""

    data = await call_llm_json(prompt, max_tokens=800, label="Contradiction detection")
    return data.get("contradictions", []) if data else []


async def detect_derailment(goals: List[Goal], assistant_response: str) -> Optional[Dict]:
    """Detect if the assistant response has derailed from all tracked goals (REQ-03-02)."""
    active_goals = [g for g in goals if not g.completed]
    if not active_goals or not assistant_response:
        return None

    goals_text = "\n".join([f"- {g.id}: {g.text}" for g in active_goals])

    prompt = f"""You are analyzing whether the assistant's response has derailed from the conversation goals. Derailment means the response has drifted away from addressing any of the active goals without substantively engaging with any of them.

Active goals:
{goals_text}

Assistant response: {assistant_response}

Determine: has the response derailed? If yes, explain how and suggest what the user could do. If no, return derailment: false.

Respond ONLY with valid JSON:

{{
  "derailment": <true|false>,
  "reason": "<REASON_IF_TRUE>",
  "suggestion": "<SUGGESTION_IF_TRUE>"
}}"""

    return await _detect_flag(
        prompt, "derailment",
        {"reason": "", "suggestion": ""},
        max_tokens=600, label="Derailment detection",
    )


async def detect_repetition(conversation_messages: List) -> Optional[Dict]:
    """Detect if the LLM is repeating content across recent responses (REQ-03-02-006)."""
    assistant_responses = [m for m in conversation_messages if m.role == "assistant"]
    if len(assistant_responses) < 2:
        return None

    recent = assistant_responses[-3:]
    responses_text = "\n\n---\n\n".join(
        f"Response {i+1}:\n{m.content}" for i, m in enumerate(recent)
    )

    prompt = f"""You are analyzing whether the following assistant responses contain significant repetition. Repetition means the assistant is producing substantially similar content, restating the same points, or providing redundant information across multiple responses.

{responses_text}

Determine: is there significant repetition? If yes, describe what is repeated and suggest what the user could do differently. If no, return repetition: false.

Respond ONLY with valid JSON:

{{
  "repetition": <true|false>,
  "repeated_content": "<WHAT_IS_REPEATED>",
  "suggestion": "<SUGGESTION_FOR_USER>"
}}"""

    return await _detect_flag(
        prompt, "repetition",
        {"repeated_content": "", "suggestion": ""},
        max_tokens=600, label="Repetition detection",
    )


async def detect_fixation(goals: List[Goal]) -> Optional[Dict]:
    """Detect if the LLM is fixating on a single goal while neglecting others (REQ-03-03-002)."""
    active_goals = [g for g in goals if not g.completed]
    if len(active_goals) < 2:
        return None

    confirmed_goals = [g for g in active_goals if g.status == "confirm"]
    ignored_goals = [g for g in active_goals if g.status == "ignore"]
    if not confirmed_goals or not ignored_goals:
        return None

    goals_summary = "\n".join(
        f"- {g.id}: {g.text} (status: {g.status or 'unevaluated'})" for g in active_goals
    )

    prompt = f"""You are analyzing whether the assistant shows goal fixation — excessively focusing on some goals while consistently neglecting others.

Current goals and their status:
{goals_summary}

Determine: is there significant fixation? A fixation pattern means one or a few goals are always confirmed while others are always ignored across multiple turns. If yes, describe the fixation and suggest what the user could do. If no, return fixation: false.

Respond ONLY with valid JSON:

{{
  "fixation": <true|false>,
  "fixated_goal_ids": ["<ID_1>"],
  "neglected_goal_ids": ["<ID_2>"],
  "reason": "<REASON>",
  "suggestion": "<SUGGESTION>"
}}"""

    return await _detect_flag(
        prompt, "fixation",
        {"fixated_goal_ids": [], "neglected_goal_ids": [], "reason": "", "suggestion": ""},
        max_tokens=600, label="Fixation detection",
    )


async def detect_breakdown(conversation_messages: List, goals: List[Goal]) -> Optional[Dict]:
    """Detect communication breakdown when user rephrases the same unmet goal (REQ-03-01-007)."""
    user_messages = [m for m in conversation_messages if m.role == "user"]
    if len(user_messages) < 2:
        return None

    ignored_goals = [g for g in goals if not g.completed and g.status == "ignore"]
    if not ignored_goals:
        return None

    recent_user = user_messages[-4:]
    user_texts = "\n".join(f"Message {i+1}: {m.content}" for i, m in enumerate(recent_user))
    ignored_text = "\n".join(f"- {g.id}: {g.text}" for g in ignored_goals)

    prompt = f"""You are analyzing whether there is a communication breakdown in this conversation. A breakdown occurs when the user repeatedly addresses the same goal but the assistant keeps ignoring or misunderstanding it.

Recent user messages:
{user_texts}

Goals that were ignored in the latest evaluation:
{ignored_text}

Determine: is there a communication breakdown? Look for the user rephrasing, restating, or re-asking about the same topic that keeps being ignored. If yes, explain the breakdown and suggest what the user could do. If no, return breakdown: false.

Respond ONLY with valid JSON:

{{
  "breakdown": <true|false>,
  "reason": "<REASON>",
  "repeated_goal_ids": ["<ID>"],
  "suggestion": "<SUGGESTION>"
}}"""

    return await _detect_flag(
        prompt, "breakdown",
        {"reason": "", "repeated_goal_ids": [], "suggestion": ""},
        max_tokens=600, label="Breakdown detection",
    )