"""
Goal Merge Stage — Merge new and existing goals using LLM-powered operations.

Implements Appendix A.2 of the OnGoal requirements.
"""

import json
import logging
from datetime import datetime
from typing import List, Dict

from backend.models import Goal
from backend.llm_service import LLMService
from backend.pipelines.goal_detection import detect_contradiction

logger = logging.getLogger(__name__)


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

        from backend.json_parser import extract_json_object
        operations_data = extract_json_object(response_text)
        operations = operations_data.get("operations", []) if operations_data else []

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
