"""
Goal Evaluation Stage — Assess how assistant responses address tracked goals.

Implements Appendix A.3 of the OnGoal requirements.
"""

import json
import logging
from typing import Dict

from backend.models import Goal, GoalEvaluation
from backend.llm_service import LLMService

logger = logging.getLogger(__name__)


async def evaluate_goal(goal: Goal, assistant_response: str) -> Dict:
    """Evaluate how assistant response addresses a goal using prompt from OnGoal requirements (Appendix A.3)"""

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

        from backend.json_parser import extract_json_object
        evaluation_data = extract_json_object(response_text)
        if evaluation_data:
            evaluation = GoalEvaluation(
                goal_id=goal.id,
                category=evaluation_data.get("category", "ignore"),
                explanation=evaluation_data.get("explanation", ""),
                examples=evaluation_data.get("examples", []),
            )
            goal.evaluation = evaluation
            goal.status = evaluation.category
            return evaluation.model_dump()

        else:
            fallback = GoalEvaluation(
                goal_id=goal.id, category="ignore",
                explanation="Unable to evaluate goal",
            )
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
