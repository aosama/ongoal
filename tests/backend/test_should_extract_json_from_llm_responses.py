"""Tests for robust LLM JSON extraction utility."""
import pytest
from unittest.mock import patch, AsyncMock


class TestExtractJsonObject:
    def test_should_extract_plain_json(self):
        from backend.json_parser import extract_json_object
        text = '{"clauses": [{"clause": "Write a story"}]}'
        result = extract_json_object(text)
        assert result == {"clauses": [{"clause": "Write a story"}]}

    def test_should_extract_json_from_markdown_fence(self):
        from backend.json_parser import extract_json_object
        text = 'Here is the analysis:\n```json\n{"category": "confirm"}\n```\nHope this helps!'
        result = extract_json_object(text)
        assert result == {"category": "confirm"}

    def test_should_extract_balanced_json_with_nested_braces(self):
        from backend.json_parser import extract_json_object
        # String values contain curly braces (edge case)
        text = '{"message": "Use {formal} language"}'
        result = extract_json_object(text)
        assert result == {"message": "Use {formal} language"}

    def test_should_extract_outermost_json_ignoring_trailing_text(self):
        from backend.json_parser import extract_json_object
        text = '{"key": "value"} Now here is some extra explanation.'
        result = extract_json_object(text)
        assert result == {"key": "value"}

    def test_should_return_none_when_no_json_found(self):
        from backend.json_parser import extract_json_object
        result = extract_json_object("Just plain text with no JSON here.")
        assert result is None

    def test_should_handle_nested_json_arrays_and_objects(self):
        from backend.json_parser import extract_json_object
        text = '{"operations": [{"updated_goal": "g1", "goal_numbers": ["1"]}]}'
        result = extract_json_object(text)
        assert result == {"operations": [{"updated_goal": "g1", "goal_numbers": ["1"]}]}

    def test_should_strip_single_line_markdown_fence(self):
        from backend.json_parser import extract_json_object
        text = '```json\n{"status": "ok"}\n```'
        result = extract_json_object(text)
        assert result == {"status": "ok"}


class TestPipelineFunctionsWithFencedJson:
    """Verify pipeline functions still work when LLM returns markdown-fenced JSON."""

    @pytest.mark.asyncio
    async def test_should_infer_goals_when_llm_returns_markdown_fenced_json(self):
        from unittest.mock import patch
        from backend.pipelines.goal_inference import infer_goals
        fake_response = (
            'Here is the JSON:\n```json\n'
            '{"clauses": [{"clause": "Write a story", "type": "request", "summary": "Create one"}]}'
            '\n```\nHope this helps!'
        )
        with patch('backend.llm_provider.get_provider') as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.generate.return_value = fake_response
            mock_get_provider.return_value = mock_provider
            goals = await infer_goals("Write a story", "msg_0")
        assert len(goals) == 1
        assert goals[0].text == "Write a story"
        assert goals[0].type == "request"

    @pytest.mark.asyncio
    async def test_should_evaluate_goal_when_llm_returns_fenced_json(self):
        from unittest.mock import patch
        from backend.models import Goal
        from backend.pipelines.goal_evaluation import evaluate_goal
        fake = '```json\n{"category": "confirm", "explanation": "ok", "examples": ["yes"]}\n```'
        with patch('backend.llm_provider.get_provider') as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.generate.return_value = fake
            mock_get_provider.return_value = mock_provider
            result = await evaluate_goal(Goal(id="G0", text="x", type="request", source_message_id="m"), "y")
        assert result["category"] == "confirm"

    @pytest.mark.asyncio
    async def test_should_extract_keyphrases_when_llm_returns_fenced_json(self):
        from unittest.mock import patch
        from backend.pipelines.keyphrase_extraction import extract_keyphrases
        fake = '```json\n{"keyphrases": ["space", "travel"]}\n```'
        with patch('backend.llm_provider.get_provider') as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.generate.return_value = fake
            mock_get_provider.return_value = mock_provider
            result = await extract_keyphrases("Space travel is amazing.")
        assert result == ["space", "travel"]
