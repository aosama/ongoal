"""
Goal Inference Stage — Extract goals from natural language user messages.

Implements Appendix A.1 of the OnGoal requirements.
"""

import json
import logging
from datetime import datetime
from typing import List

from backend.models import Goal
from backend.llm_service import LLMService

logger = logging.getLogger(__name__)


async def infer_goals(message: str, message_id: str, existing_goals_count: int = 0) -> List[Goal]:
    """Extract goals from user message using exact prompt from OnGoal requirements (Appendix A.1)"""
    
    # Input validation: reject empty/whitespace-only messages
    if not message or not message.strip():
        raise ValueError("Message cannot be empty")
    
    # Input validation: enforce maximum message length (safety guard)
    MAX_MESSAGE_LENGTH = 4000
    if len(message) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"Message too long (max {MAX_MESSAGE_LENGTH} chars)")
    
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

            from backend.json_parser import extract_json_object
            response_data = extract_json_object(response_text)
            clauses_data = response_data.get("clauses", []) if response_data else []
            
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
