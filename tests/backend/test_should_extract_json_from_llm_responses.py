"""Tests for robust LLM JSON extraction utility."""
import pytest


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
