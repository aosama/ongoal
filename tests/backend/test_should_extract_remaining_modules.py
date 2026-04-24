import pytest
from unittest.mock import patch, AsyncMock

# Unified extraction test for Tasks 3-7


@pytest.mark.asyncio
async def test_should_stream_from_new_module():
    from backend.pipelines.llm_streaming import stream_llm_response
    mock_ws = AsyncMock()
    mock_mgr = AsyncMock()
    mock_mgr.send_message = AsyncMock(return_value=True)

    async def fake_stream(*args, **kwargs):
        yield "Hello "
        yield "world"

    with patch('backend.pipelines.llm_streaming.LLMService.generate_streaming_response', fake_stream):
        with patch('backend.pipelines.llm_streaming.LLMService.is_available', return_value=True):
            result = await stream_llm_response("Hi", mock_mgr, mock_ws, "msg_1", [])

    assert result == "Hello world"


@pytest.mark.asyncio
async def test_should_extract_keyphrases_from_new_module():
    from backend.pipelines.keyphrase_extraction import extract_keyphrases
    fake_response = '{"keyphrases": ["space", "exploration"]}'
    with patch('backend.pipelines.keyphrase_extraction.LLMService.generate_response', return_value=fake_response):
        result = await extract_keyphrases("Space exploration is amazing.")
    assert result == ["space", "exploration"]


def test_should_compute_goal_progress_from_new_module():
    from backend.models import Goal, Conversation
    from backend.pipelines.goal_progress import compute_goal_progress
    conv = Conversation(id="test")
    g = Goal(id="G0", text="Write a story", type="request", source_message_id="msg_0")
    conv.goals.append(g)
    result = compute_goal_progress(conv)
    assert len(result) == 1
    assert result[0]["goal_id"] == "G0"


@pytest.mark.asyncio
async def test_should_detect_forgetting_from_new_module():
    from backend.pipelines.goal_detection import detect_forgetting
    with patch('backend.pipelines.goal_detection.LLMService.generate_response', return_value='{"forgotten_goals": []}'):
        result = await detect_forgetting([], "response")
    assert result == []


@pytest.mark.asyncio
async def test_should_detect_contradiction_from_new_module():
    from backend.models import Goal
    from backend.pipelines.goal_detection import detect_contradiction
    with patch('backend.pipelines.goal_detection.LLMService.generate_response', return_value='{"contradictions": []}'):
        result = await detect_contradiction([Goal(id="G0", text="A", type="request", source_message_id="m")])
    assert result == []


@pytest.mark.asyncio
async def test_should_merge_goals_from_new_module():
    from datetime import datetime
    from backend.models import Goal
    from backend.pipelines.goal_merge import merge_goals
    fake_response = '{"operations": [{"updated_goal": "Write a good story", "operation": "combine", "goal_numbers": ["1", "1"]}]}'
    with patch('backend.pipelines.goal_merge.LLMService.generate_response', return_value=fake_response):
        old = [Goal(id="G0_old", text="Write a story", type="request", source_message_id="msg_0")]
        new = [Goal(id="G0_new", text="Write a good story", type="request", source_message_id="msg_1")]
        result = merge_goals(old, new, "msg_1")
        result = await result
    assert len(result) == 1
    assert "good" in result[0].text
