import pytest


def test_should_import_goal_inference_from_pipelines():
    from backend.pipelines.goal_inference import infer_goals
    assert callable(infer_goals)
