"""
OnGoal Pipeline Functions - Goal inference, merging, evaluation, and keyphrase extraction

Implements the 4 LLM-powered pipeline stages defined in:
  - A.1: Goal Inference (infer_goals)
  - A.2: Goal Merging (merge_goals)
  - A.3: Goal Evaluation (evaluate_goal)
  - A.4: Keyphrase Extraction (extract_keyphrases)
"""

# Compatibility re-exports (new code should import from backend.pipelines directly)
from backend.pipelines.goal_inference import infer_goals
from backend.pipelines.goal_evaluation import evaluate_goal

import json
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime

from dotenv import load_dotenv

from backend.models import Goal, GoalEvaluation
from backend.llm_service import LLMService

load_dotenv()

logger = logging.getLogger(__name__)


# infer_goals was extracted to backend/pipelines/goal_inference.py


async def replace_outdated_goals(existing_goals: List[Goal], new_goals: List[Goal], current_message_id: str, conversation) -> List[Goal]:
    """Detect and mark outdated goals that are contradicted by new goals.

    Uses existing detect_contradiction() to find pairs, then marks the older
    goal as replaced. Adds a GoalHistoryEntry tracking the replacement.
    Returns the filtered existing_goals with replaced goals removed.
    """
    from backend.models import GoalHistoryEntry

    combined = existing_goals + new_goals
    contradictions = await detect_contradiction(combined)
    if not contradictions:
        return existing_goals

    replaced_ids = set()
    for c in contradictions:
        gid1 = c.get("goal_id_1")
        gid2 = c.get("goal_id_2")
        reason = c.get("reason", "Contradicts newer goal")

        # Determine which goal is older (from existing_goals vs new_goals)
        goal1 = next((g for g in combined if g.id == gid1), None)
        goal2 = next((g for g in combined if g.id == gid2), None)
        if not goal1 or not goal2:
            continue

        # Mark the one from existing_goals as replaced
        old_goal = goal1 if goal1 in existing_goals and goal2 in new_goals else (
            goal2 if goal2 in existing_goals and goal1 in new_goals else None
        )
        new_goal = goal2 if old_goal is goal1 else (goal1 if old_goal is goal2 else None)
        if not old_goal or not new_goal:
            continue

        old_goal.status = "replaced"
        replaced_ids.add(old_goal.id)

        # Track in conversation history
        entry = GoalHistoryEntry(
            turn=len([m for m in conversation.messages if m.role == "user"]),
            operation="replace",
            goal_id=old_goal.id,
            goal_text=old_goal.text,
            goal_type=old_goal.type,
            previous_goal_ids=[new_goal.id],
            previous_goal_texts=[new_goal.text],
        )
        conversation.goal_history.append(entry)

    return [g for g in existing_goals if g.id not in replaced_ids]


async def merge_goals(old_goals: List[Goal], new_goals: List[Goal], current_message_id: str = "", conversation=None) -> List[Goal]:
    """Merge old and new goals, respecting locked goals"""
    
    if not new_goals:
        return old_goals

    if not old_goals:
        return new_goals

    locked_goals = [g for g in old_goals if g.locked]
    mergeable_old = [g for g in old_goals if not g.locked]

    if not mergeable_old:
        return locked_goals + new_goals

    old_goals_str_list = "\n".join([f"{i+1}. {goal.text}" for i, goal in enumerate(mergeable_old)])
    new_goals_str_list = "\n".join([f"{i+1}. {goal.text}" for i, goal in enumerate(new_goals)])
    
    # ENHANCED PROMPT - Based on OnGoal Requirements Appendix A.2 with semantic contradiction awareness
    merge_prompt = f"""You have one set of old numbered bullet point goals:
{old_goals_str_list}

You have another set of new numbered bullet point goals:
{new_goals_str_list}

Merge the two lists of bullet point goals into a single updated list of goals. Use the following three operations as rules to perform the merge:

* Replace: If a new goal contradicts an old goal (either directly or semantically), replace the old goal with the new goal. Consider semantic contradictions like "short simple story" vs "complex detailed elements". List the number of the old goal, then the number of the new goal.
* Combine: If a new goal is similar to an old goal and they can work together without contradiction, combine the old goal and the new goal into a new combined goal. List the number of the old goal, then the number of the new goal.
* Keep: If a goal is unique and does not conflict with the overall intent of new goals, keep that goal in the updated list. List the original number of the goal.

CRITICAL REQUIREMENTS:
1. EVERY goal from both lists must be handled by exactly one operation
2. Unique goals that don't contradict the new goals MUST be preserved via Keep or Combine operations
3. Consider the overall intent and semantic compatibility
4. If old goals conflict with the spirit/intent of new goals, favor the newer goals through Replace operations

EXAMPLE: If old goals contain "Include humor" and new goals don't mention humor, the humor goal should be kept or combined with a compatible new goal, not ignored.

Please respond ONLY with a valid JSON in the following format:

{{
  "operations": [
    {{
      "updated_goal": "<GOAL_1>",
      "operation": "<OPERATION_1>",
      "goal_numbers": ["<GOAL_NUMBER_1>", "<GOAL_NUMBER_2>"]
    }},
    {{
      "updated_goal": "<GOAL_2>",
      "operation": "<OPERATION_2>",
      "goal_numbers": ["<GOAL_NUMBER_1>", "<GOAL_NUMBER_2>"]
    }}
  ]
}}"""

    try:
        response_text = await LLMService.generate_response(merge_prompt, max_tokens=1500)

        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        operations = json.loads(json_match.group()).get("operations", []) if json_match else []

        merged_goals = []
        all_mergeable = mergeable_old + new_goals
        goal_counter = 0
        
        for operation in operations:
            updated_goal_text = operation["updated_goal"]
            operation_type = operation["operation"]
            goal_numbers = operation.get("goal_numbers", [])
            
            source_goal = None
            if goal_numbers:
                try:
                    primary_idx = int(goal_numbers[0]) - 1
                    if operation_type in ["combine", "replace"] and len(goal_numbers) > 1:
                        secondary_idx = int(goal_numbers[1]) - 1
                        source_goal = new_goals[secondary_idx] if secondary_idx < len(new_goals) else (
                            mergeable_old[primary_idx] if primary_idx < len(mergeable_old) else None
                        )
                    else:
                        source_goal = all_mergeable[primary_idx] if primary_idx < len(all_mergeable) else None
                except (ValueError, IndexError):
                    pass
            
            if not source_goal:
                source_goal = mergeable_old[0] if mergeable_old else new_goals[0]
            
            merged_goal = Goal(
                id=f"G{goal_counter}",
                text=updated_goal_text,
                type=source_goal.type,
                source_message_id=current_message_id or source_goal.source_message_id,
                locked=False,
                completed=source_goal.completed,
                created_at=datetime.now().isoformat()
            )
            goal_counter += 1
            merged_goals.append(merged_goal)

        result = locked_goals + (merged_goals if merged_goals else mergeable_old + new_goals)
        # Ensure current_message_id is applied even when the LLM returns
        # an empty operations list or produces no merged_goals
        if current_message_id:
            for goal in result:
                goal.source_message_id = current_message_id
        return result
        
    except Exception as e:
        logger.warning("Goal merge failed: %s", e)
        # Fallback: on LLM failure, still override source_message_id for new goals when current_message_id is provided
        if current_message_id:
            for g in mergeable_old:
                g.source_message_id = current_message_id
            for g in new_goals:
                g.source_message_id = current_message_id
        return locked_goals + mergeable_old + new_goals


# evaluate_goal was extracted to backend/pipelines/goal_evaluation.py


async def stream_llm_response(message: str, connection_manager, websocket, message_id: str, conversation_messages: List):
    """Stream LLM response using the configured provider"""
    if not LLMService.is_available():
        error_msg = "LLM service unavailable - API key not configured"
        await connection_manager.send_message({
            "type": "error",
            "message": error_msg
        }, websocket)
        return error_msg

    try:
        messages_for_llm = []

        if conversation_messages:
            for msg in conversation_messages:
                messages_for_llm.append({
                    "role": msg.role,
                    "content": msg.content
                })

        messages_for_llm.append({
            "role": "user",
            "content": message
        })

        full_response = ""
        async for text_chunk in LLMService.generate_streaming_response(messages_for_llm, max_tokens=2000):
            full_response += text_chunk

            send_ok = await connection_manager.send_message({
                "type": "llm_response_chunk",
                "text": text_chunk,
                "message_id": message_id
            }, websocket)

            # Stop burning tokens if the client disconnected mid-stream
            if not send_ok:
                logger.info("WebSocket disconnected mid-stream (message %s) — stopping LLM", message_id)
                return full_response

        await connection_manager.send_message({
            "type": "llm_response_complete",
            "message_id": message_id,
            "full_text": full_response
        }, websocket)

        return full_response

    except Exception as e:
        logger.error("LLM streaming error: %s", e)
        error_msg = "Unable to generate response. Please check your API key configuration."
        await connection_manager.send_message({
            "type": "error",
            "message": error_msg
        }, websocket)
        return error_msg


async def extract_keyphrases(assistant_response: str) -> List[str]:
    """Extract salient keyphrases from an assistant response (REQ-09-04-001–005).

    Uses the keyphrase extraction prompt from OnGoal Requirements Appendix A.4.
    Returns a list of verbatim phrases capturing the most salient topics.
    """

    keyphrase_prompt = f"""You will be presented with an assistant response. Extract the most salient keyphrases from the response exactly as they appear verbatim. Focus on phrases that capture key topics and themes.

Respond ONLY with a valid JSON in the following format:

{{
  "keyphrases": ["<KEYPHRASE_1>", "<KEYPHRASE_2>"]
}}

Assistant response: {assistant_response}"""

    try:
        response_text = await LLMService.generate_response(keyphrase_prompt, max_tokens=500)

        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("keyphrases", [])

        logger.warning("Keyphrase extraction: no JSON found in response")
        return []

    except Exception as e:
        logger.warning("Keyphrase extraction failed: %s", e)
        return []


async def detect_forgetting(goals: List[Goal], assistant_response: str) -> List[Dict]:
    """Detect goals that may have been forgotten in the conversation (REQ-03-01-006).

    A goal is considered "forgotten" if it has been repeatedly ignored across
    multiple assistant responses. Returns a list of alert dicts.
    """
    if not goals or not assistant_response:
        return []

    active_goals = [g for g in goals if not g.completed and not g.locked]
    repeatedly_ignored = [
        g for g in active_goals
        if g.evaluation and g.evaluation.category == "ignore"
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

    try:
        response_text = await LLMService.generate_response(prompt, max_tokens=800)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("forgotten_goals", [])
        return []
    except Exception as e:
        logger.warning("Forgetting detection failed: %s", e)
        return []


async def detect_contradiction(goals: List[Goal]) -> List[Dict]:
    """Detect contradictions between active goals (REQ-03-01-003).

    Returns pairs of goals that contradict each other with explanation.
    """
    if len(goals) < 2:
        return []

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

    try:
        response_text = await LLMService.generate_response(prompt, max_tokens=800)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("contradictions", [])
        return []
    except Exception as e:
        logger.warning("Contradiction detection failed: %s", e)
        return []


async def detect_breakdown(conversation_messages: List, goals: List[Goal]) -> Optional[Dict]:
    """Detect communication breakdown when user rephrases the same unmet goal (REQ-03-01-007).

    A breakdown occurs when the user sends multiple messages addressing the
    same goal that the assistant keeps ignoring or misunderstanding.
    """
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

    try:
        response_text = await LLMService.generate_response(prompt, max_tokens=600)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            if data.get("breakdown", False):
                return {
                    "reason": data.get("reason", ""),
                    "repeated_goal_ids": data.get("repeated_goal_ids", []),
                    "suggestion": data.get("suggestion", ""),
                }
        return None
    except Exception as e:
        logger.warning("Breakdown detection failed: %s", e)
        return None


async def detect_repetition(conversation_messages: List) -> Optional[Dict]:
    """Detect if the LLM is repeating content across recent responses (REQ-03-02-006).

    Compares the last N assistant responses. If significant repetition is
    found, returns an alert dict with details.
    """
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

    try:
        response_text = await LLMService.generate_response(prompt, max_tokens=600)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            if data.get("repetition", False):
                return {
                    "repeated_content": data.get("repeated_content", ""),
                    "suggestion": data.get("suggestion", ""),
                }
        return None
    except Exception as e:
        logger.warning("Repetition detection failed: %s", e)
        return None


async def detect_fixation(goals: List[Goal]) -> Optional[Dict]:
    """Detect if the LLM is fixating on a single goal while neglecting others (REQ-03-03-002).

    Fixation means one goal is repeatedly confirmed while others are
    consistently ignored, suggesting unbalanced attention.
    """
    active_goals = [g for g in goals if not g.completed]
    if len(active_goals) < 2:
        return None

    confirmed_goals = [g for g in active_goals if g.status == "confirm"]
    ignored_goals = [g for g in active_goals if g.status == "ignore"]

    if not confirmed_goals or not ignored_goals:
        return None

    goals_summary = "\n".join(
        f"- {g.id}: {g.text} (status: {g.status or 'unevaluated'})"
        for g in active_goals
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

    try:
        response_text = await LLMService.generate_response(prompt, max_tokens=600)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            if data.get("fixation", False):
                return {
                    "fixated_goal_ids": data.get("fixated_goal_ids", []),
                    "neglected_goal_ids": data.get("neglected_goal_ids", []),
                    "reason": data.get("reason", ""),
                    "suggestion": data.get("suggestion", ""),
                }
        return None
    except Exception as e:
        logger.warning("Fixation detection failed: %s", e)
        return None


def compute_goal_progress(conversation) -> List[Dict]:
    """Compute goal progress tracking across all messages (REQ-03-02-001, REQ-03-02-004).

    For each active goal, counts confirm/ignore/contradict across all
    evaluations and derives a progress summary with completion status.
    """
    progress = []
    for goal in conversation.goals:
        if goal.completed:
            progress.append({
                "goal_id": goal.id,
                "goal_text": goal.text,
                "confirm_count": 0,
                "ignore_count": 0,
                "contradict_count": 0,
                "total_evaluations": 0,
                "progress_pct": 100,
                "completion_status": "completed_manual",
            })
            continue

        confirm_count = 0
        ignore_count = 0
        contradict_count = 0

        for msg in conversation.messages:
            if msg.role == "assistant" and msg.goals:
                for msg_goal in msg.goals:
                    if msg_goal.id == goal.id and msg_goal.evaluation:
                        cat = msg_goal.evaluation.category
                        if cat == "confirm":
                            confirm_count += 1
                        elif cat == "ignore":
                            ignore_count += 1
                        elif cat == "contradict":
                            contradict_count += 1

        if goal.evaluation:
            current = goal.evaluation.category
            if current == "confirm":
                confirm_count += 1
            elif current == "ignore":
                ignore_count += 1
            elif current == "contradict":
                contradict_count += 1

        total = confirm_count + ignore_count + contradict_count
        if total == 0:
            pct = 0
        else:
            pct = int((confirm_count / total) * 100)

        if confirm_count >= 2 and ignore_count == 0 and contradict_count == 0:
            completion_status = "likely_complete"
        elif confirm_count >= 1 and pct >= 60:
            completion_status = "progressing"
        elif ignore_count > confirm_count:
            completion_status = "at_risk"
        elif contradict_count > 0:
            completion_status = "contradicted"
        else:
            completion_status = "active"

        progress.append({
            "goal_id": goal.id,
            "goal_text": goal.text,
            "confirm_count": confirm_count,
            "ignore_count": ignore_count,
            "contradict_count": contradict_count,
            "total_evaluations": total,
            "progress_pct": pct,
            "completion_status": completion_status,
        })
    return progress


async def detect_derailment(goals: List[Goal], assistant_response: str) -> Optional[Dict]:
    """Detect if the assistant response has derailed from all tracked goals (REQ-03-02).

    Derailment means the response has drifted away from all active goals
    without addressing any of them substantively.
    """
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

    try:
        response_text = await LLMService.generate_response(prompt, max_tokens=600)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            if data.get("derailment", False):
                return {
                    "reason": data.get("reason", ""),
                    "suggestion": data.get("suggestion", ""),
                }
        return None
    except Exception as e:
        logger.warning("Derailment detection failed: %s", e)
        return None


