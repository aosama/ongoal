import pytest
from unittest.mock import patch, AsyncMock
from backend.models import Goal
from backend.pipelines.goal_evaluation import evaluate_goal


@pytest.mark.asyncio
async def test_should_evaluate_goal_from_new_module():
    fake_response = '{"category": "confirm", "explanation": "Addresses the goal", "examples": ["yes"]}'
    mock_provider = AsyncMock()
    mock_provider.generate.return_value = fake_response
    with patch('backend.llm_provider.get_provider', return_value=mock_provider):
        goal = Goal(id="G0", text="Write a story", type="request", source_message_id="msg_0")
        result = await evaluate_goal(goal, "Here is a story...")

    assert result["category"] == "confirm"
    assert result["goal_id"] == "G0"
