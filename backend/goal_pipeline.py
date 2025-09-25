"""
OnGoal Pipeline Functions - Goal inference, merging, and evaluation
"""
import json
import re
from typing import List, Dict
from datetime import datetime

from dotenv import load_dotenv

from backend.models import Goal
from backend.llm_service import LLMService

# Load environment variables from .env file
load_dotenv()


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

    try:
        # Use centralized LLM service
        response_text = await LLMService.generate_response(inference_prompt, max_tokens=1000)
        
        # Extract JSON from response (updated for new format)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_data = json.loads(json_match.group())
            clauses_data = response_data.get("clauses", [])
        else:
            clauses_data = []
        
        # Convert to Goal objects (updated for new JSON structure)
        goals = []
        for i, clause_data in enumerate(clauses_data):
            goal = Goal(
                id=f"G{existing_goals_count + i}",
                text=clause_data["clause"],  # Using "clause" field now
                type=clause_data["type"],
                source_message_id=message_id,
                created_at=datetime.now().isoformat()
            )
            goals.append(goal)
        
        return goals
        
    except Exception as e:
        # Error in goal inference - log error but continue
        print(f"Warning: Goal inference failed: {e}")
        return []


async def merge_goals(old_goals: List[Goal], new_goals: List[Goal]) -> List[Goal]:
    """Merge old and new goals using exact prompt from OnGoal requirements (Appendix A.2)"""
    
    if not new_goals:
        return old_goals
    
    if not old_goals:
        return new_goals
    
    
    # Prepare goal lists as numbered strings
    old_goals_str_list = "\n".join([f"{i+1}. {goal.text}" for i, goal in enumerate(old_goals)])
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
        # Use centralized LLM service
        response_text = await LLMService.generate_response(merge_prompt, max_tokens=1500)

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_data = json.loads(json_match.group())
            operations = response_data.get("operations", [])
        else:
            operations = []
        
        # Process merge operations to create final goal list
        merged_goals = []
        all_goals = old_goals + new_goals
        
        for operation in operations:
            updated_goal_text = operation["updated_goal"]
            operation_type = operation["operation"]
            goal_numbers = operation["goal_numbers"]
            
            # Find the appropriate source goal based on the operation
            source_goal = None
            if goal_numbers and len(goal_numbers) > 0:
                try:
                    # Parse goal number (format: "1", "2", etc.)
                    primary_goal_idx = int(goal_numbers[0]) - 1  # Convert to 0-based index
                    
                    if operation_type in ["combine", "replace"] and len(goal_numbers) > 1:
                        # For combine/replace, prefer the newer goal's type (second goal number)
                        secondary_goal_idx = int(goal_numbers[1]) - 1
                        if secondary_goal_idx < len(new_goals):
                            source_goal = new_goals[secondary_goal_idx]
                        elif primary_goal_idx < len(old_goals):
                            source_goal = old_goals[primary_goal_idx]
                    else:
                        # For keep operations, use the original goal
                        if primary_goal_idx < len(all_goals):
                            source_goal = all_goals[primary_goal_idx]
                        
                except (ValueError, IndexError):
                    # Fallback if parsing fails
                    source_goal = old_goals[0] if old_goals else new_goals[0]
            else:
                # Fallback for malformed operations
                source_goal = old_goals[0] if old_goals else new_goals[0]
            
            # If we still don't have a source goal, use the first available
            if not source_goal:
                source_goal = old_goals[0] if old_goals else new_goals[0]
            
            merged_goal = Goal(
                id=f"G{len(merged_goals)}_{operation_type}",
                text=updated_goal_text,
                type=source_goal.type,  # Now uses the correct source goal's type
                source_message_id=source_goal.source_message_id,
                created_at=datetime.now().isoformat()
            )
            merged_goals.append(merged_goal)
        
        return merged_goals if merged_goals else old_goals + new_goals
        
    except Exception as e:
        # Error in goal merging - log error and fallback
        print(f"Warning: Goal merge failed: {e}")
        # Fallback: return all goals without merging
        return old_goals + new_goals


async def evaluate_goal(goal: Goal, assistant_response: str) -> Dict:
    """Evaluate how assistant response addresses a goal using exact prompt from OnGoal requirements (Appendix A.3)"""
    
    # EXACT PROMPT from OnGoal Requirements Appendix A.3
    evaluation_prompt = f"""You will be presented with human dialogue and a response from you, an assistant. Your task is to evaluate the assistant response in terms of the following conversational goal: {goal.text}

Categorize how the assistant response addresses the goal in one of three categories. The categories are confirm, contradict, or ignore. Explain the relationship between the response and the goal in ONE sentence. Extract clauses verbatim from the response exactly as they appear as examples that show evidence to support your explanation.

Please respond ONLY with a valid JSON in the following format:

{{
  "category": "<CATEGORY_1>",
  "explanation": "<EXPLANATION_1>",
  "examples": ["<EXAMPLE_1>", "<EXAMPLE_2>"]
}}

Assistant response: {assistant_response}"""

    try:
        # Use centralized LLM service
        response_text = await LLMService.generate_response(evaluation_prompt, max_tokens=1000)
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            evaluation_data = json.loads(json_match.group())
            return {
                "goal_id": goal.id,
                "category": evaluation_data.get("category", "ignore"),
                "explanation": evaluation_data.get("explanation", ""),
                "examples": evaluation_data.get("examples", []),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "goal_id": goal.id,
                "category": "ignore",
                "explanation": "Unable to evaluate goal",
                "examples": [],
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        # Error in goal evaluation - log and return safe fallback
        print(f"Warning: Goal evaluation failed for {goal.id}: {e}")
        return {
            "goal_id": goal.id,
            "category": "ignore",
            "explanation": f"Unable to evaluate goal due to service error",
            "examples": [],
            "timestamp": datetime.now().isoformat()
        }


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
        print(f"Error in LLM streaming: {e}")
        error_msg = "Unable to generate response. Please check your API key configuration."
        await connection_manager.send_message({
            "type": "error",
            "message": error_msg
        }, websocket)
        return error_msg


