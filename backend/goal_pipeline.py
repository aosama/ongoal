"""
OnGoal Pipeline Functions - Goal inference, merging, evaluation, and keyphrase extraction

Implements the 4 LLM-powered pipeline stages defined in:
  - A.1: Goal Inference (infer_goals)
  - A.2: Goal Merging (merge_goals)
  - A.3: Goal Evaluation (evaluate_goal)
  - A.4: Keyphrase Extraction (extract_keyphrases)
"""

import json
import logging
import re
from typing import List, Dict
from datetime import datetime

from dotenv import load_dotenv

from backend.models import Goal, GoalEvaluation
from backend.llm_service import LLMService

load_dotenv()

logger = logging.getLogger(__name__)


async def infer_goals(message: str, message_id: str, existing_goals_count: int = 0) -> List[Goal]:
    """Extract goals from user message using exact prompt from OnGoal requirements (Appendix A.1)"""
    
    # EXACT PROMPT from OnGoal Requirements Appendix A.1
    inference_prompt = f"""You will be presented with human dialogue in a conversation with you, an assistant. Your task is to extract every clause verbatim from the document exactly as it appears.

List all clauses in the dialogue that are either a question, request, offer, or suggestion. Briefly summarize how to address the goal of the clause in ONE sentence.

Please respond ONLY with a valid JSON in the following format:

{{
  "clauses": [
    {{"clause": "<CLAUSE_1>", "type": "<TYPE_1>", "summary": "<SUMMARY_1>"}},
    {{"clause": "<CLAUSE_2>", "type": "<TYPE_2>", "summary": "<SUMMARY_2>"}}
  ]
}}

Human dialogue: {message}"""

    for attempt in range(2):
        try:
            response_text = await LLMService.generate_response(inference_prompt, max_tokens=1000)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_data = json.loads(json_match.group())
                clauses_data = response_data.get("clauses", [])
            else:
                clauses_data = []
            
            goals = []
            total_prior = existing_goals_count
            for clause_data in clauses_data:
                goal = Goal(
                    id=f"G{total_prior}",
                    text=clause_data["clause"],
                    type=clause_data["type"],
                    summary=clause_data.get("summary", ""),
                    source_message_id=message_id,
                    created_at=datetime.now().isoformat()
                )
                total_prior += 1
                goals.append(goal)
            
            return goals
        
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("Goal inference parse error (attempt %d): %s", attempt + 1, e)
            if attempt == 0:
                continue
            return []
        except Exception as e:
            logger.warning("Goal inference failed: %s", e)
            return []
    
    return []


async def merge_goals(old_goals: List[Goal], new_goals: List[Goal]) -> List[Goal]:
    """Merge old and new goals, respecting locked goals"""
    
    if not new_goals:
        return old_goals
    
    if not old_goals:
        return new_goals
    
    # Separate locked goals — they are excluded from merge
    locked_goals = [g for g in old_goals if g.locked]
    mergeable_old = [g for g in old_goals if not g.locked]
    
    # If no mergeable old goals, just combine locked + new
    if not mergeable_old:
        return locked_goals + new_goals
    
    
    # Prepare goal lists as numbered strings
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
        
        # Build merged goals with unique IDs
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
                source_message_id=source_goal.source_message_id,
                locked=False,
                completed=source_goal.completed,
                created_at=datetime.now().isoformat()
            )
            goal_counter += 1
            merged_goals.append(merged_goal)
        
        # Re-add locked goals to the result
        result = locked_goals + (merged_goals if merged_goals else mergeable_old + new_goals)
        return result
        
    except Exception as e:
        logger.warning("Goal merge failed: %s", e)
        return locked_goals + mergeable_old + new_goals


async def evaluate_goal(goal: Goal, assistant_response: str) -> Dict:
    """Evaluate how assistant response addresses a goal using prompt from OnGoal requirements (Appendix A.3)"""

    from backend.models import GoalEvaluation

    evaluation_prompt = f"""You will be presented with human dialogue and a response from you, an assistant. Your task is to evaluate the assistant response in terms of the following conversational goal: {goal.text}

Categorize how the assistant response addresses the goal in one of three categories. The categories are confirm, contradict, or ignore. Explain the relationship between the response and the goal in ONE sentence. Extract clauses verbatim from the response exactly as they appear as examples that show evidence to support your explanation.

Please respond ONLY with a valid JSON in the following format:

{{
  "category": "<CATEGORY>",
  "explanation": "<EXPLANATION>",
  "examples": ["<EXAMPLE_1>", "<EXAMPLE_2>"]
}}

Assistant response: {assistant_response}"""

    try:
        response_text = await LLMService.generate_response(evaluation_prompt, max_tokens=1000)

        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            evaluation_data = json.loads(json_match.group())
            evaluation = GoalEvaluation(
                goal_id=goal.id,
                category=evaluation_data.get("category", "ignore"),
                explanation=evaluation_data.get("explanation", ""),
                examples=evaluation_data.get("examples", []),
            )
            goal.evaluation = evaluation
            goal.status = evaluation.category
            return evaluation.model_dump()

        # Fallback when JSON parse fails
        fallback = GoalEvaluation(goal_id=goal.id, category="ignore",
                                  explanation="Unable to evaluate goal")
        goal.evaluation = fallback
        goal.status = "ignore"
        return fallback.model_dump()

    except Exception as e:
        logger.warning("Goal evaluation failed for %s: %s", goal.id, e)
        error_eval = GoalEvaluation(goal_id=goal.id, category="ignore",
                                     explanation="Unable to evaluate goal due to service error")
        goal.evaluation = error_eval
        goal.status = "ignore"
        return error_eval.model_dump()


async def stream_llm_response(message: str, connection_manager, websocket, message_id: str, conversation_messages: List):
    """Stream LLM response using Anthropic Claude"""
    
    # Check if LLM service is available
    if not LLMService.is_available():
        error_msg = "LLM service unavailable - API key not configured"
        await connection_manager.send_message({
            "type": "error",
            "message": error_msg
        }, websocket)
        return error_msg
    
    try:
        # Build conversation history for LLM context
        messages_for_llm = []
        
        if conversation_messages:
            # Include all previous messages for context
            for msg in conversation_messages:
                messages_for_llm.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add the current user message
        messages_for_llm.append({
            "role": "user", 
            "content": message
        })
        
        # Sending messages to LLM for context
        
        # Start streaming response using centralized service
        full_response = ""
        async for text_chunk in LLMService.generate_streaming_response(messages_for_llm, max_tokens=2000):
            full_response += text_chunk

            # Send chunk to frontend
            await connection_manager.send_message({
                "type": "llm_response_chunk",
                "text": text_chunk,
                "message_id": message_id
            }, websocket)
        
        # Send completion signal
        await connection_manager.send_message({
            "type": "llm_response_complete",
            "message_id": message_id,
            "full_text": full_response
        }, websocket)

        return full_response

    except Exception as e:
        # Error in LLM streaming - log and send user-friendly error
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


