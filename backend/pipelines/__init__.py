"""OnGoal Pipeline Stages — Import convenience.

Example:
    from backend.pipelines import infer_goals, evaluate_goal
"""

from backend.pipelines.goal_inference import infer_goals
from backend.pipelines.goal_merge import merge_goals, replace_outdated_goals
from backend.pipelines.goal_evaluation import evaluate_goal
from backend.pipelines.llm_streaming import stream_llm_response
from backend.pipelines.keyphrase_extraction import extract_keyphrases
from backend.pipelines.goal_detection import (
    detect_forgetting, detect_contradiction, detect_derailment,
    detect_repetition, detect_fixation, detect_breakdown,
)
from backend.pipelines.goal_progress import compute_goal_progress
