"""
OnGoal Pipeline Functions — Compatibility re-export layer.

All functions have been extracted into focused modules under backend/pipelines/.
New code should import from backend.pipelines directly; this file is preserved
for backward compatibility.
"""

# Compatibility re-exports
from backend.pipelines.goal_inference import infer_goals
from backend.pipelines.goal_evaluation import evaluate_goal
from backend.pipelines.llm_streaming import stream_llm_response
from backend.pipelines.keyphrase_extraction import extract_keyphrases
from backend.pipelines.goal_merge import merge_goals, replace_outdated_goals
from backend.pipelines.goal_detection import (
    detect_forgetting, detect_contradiction, detect_derailment,
    detect_repetition, detect_fixation, detect_breakdown,
)
from backend.pipelines.goal_progress import compute_goal_progress

# Backward compatibility: tests patch backend.goal_pipeline.LLMService
from backend.llm_service import LLMService  # noqa: F401
