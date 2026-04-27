"""
TDD Tests for Backend Goal Merge Logic

Tests the three merge operations according to OnGoal white paper:
- Replace: New goal contradicts old goal -> replace old with new
- Combine: New goal similar to old goal -> merge them into combined goal
- Keep: Goal is unique -> keep it unchanged

All tests mock call_llm_json for deterministic, fast execution.
Following TDD: RED -> GREEN -> REFACTOR
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock
from backend.pipelines import merge_goals
from backend.models import Goal


REPLACE_MERGE_RESPONSE = {
    "operations": [
        {"updated_goal": "Use informal, casual language in the story", "operation": "replace", "goal_numbers": ["1", "1"]},
    ]
}

COMBINE_MERGE_RESPONSE = {
    "operations": [
        {"updated_goal": "Add more character development and protagonist background", "operation": "combine", "goal_numbers": ["1", "1"]},
    ]
}

KEEP_MERGE_RESPONSE = {
    "operations": [
        {"updated_goal": "Add dialogue between characters", "operation": "keep", "goal_numbers": ["1"]},
        {"updated_goal": "Include vivid imagery of the setting", "operation": "keep", "goal_numbers": ["2"]},
    ]
}

MIXED_MERGE_RESPONSE = {
    "operations": [
        {"updated_goal": "Use sophisticated, advanced vocabulary", "operation": "replace", "goal_numbers": ["1", "1"]},
        {"updated_goal": "Develop the story's main plot and conflict further", "operation": "combine", "goal_numbers": ["2", "2"]},
        {"updated_goal": "Include humor in the story", "operation": "keep", "goal_numbers": ["3"]},
        {"updated_goal": "Add emotional depth to characters", "operation": "keep", "goal_numbers": ["3"]},
    ]
}


@pytest.mark.backend
class TestGoalMergeOperations:

    @pytest.mark.asyncio
    async def test_should_replace_conflicting_goals(self):
        old_goals = [
            Goal(
                id="G0_old",
                text="Use formal language throughout the story",
                type="suggestion",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            )
        ]

        new_goals = [
            Goal(
                id="G0_new",
                text="Use informal, casual language in the story",
                type="suggestion",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            )
        ]

        with patch("backend.pipelines.goal_merge.call_llm_json", new_callable=AsyncMock, return_value=REPLACE_MERGE_RESPONSE):
            result = await merge_goals(old_goals, new_goals)

        assert len(result) == 1, f"Replace should resolve conflicting goals into 1, got {len(result)}"
        assert "informal" in result[0].text.lower() or "casual" in result[0].text.lower()
        assert "use formal language" not in result[0].text.lower()
        assert result[0].type == "suggestion"

    @pytest.mark.asyncio
    async def test_should_combine_similar_goals(self):
        old_goals = [
            Goal(
                id="G0_old",
                text="Add more character development",
                type="request",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            )
        ]

        new_goals = [
            Goal(
                id="G0_new",
                text="Develop the protagonist's background more",
                type="request",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            )
        ]

        with patch("backend.pipelines.goal_merge.call_llm_json", new_callable=AsyncMock, return_value=COMBINE_MERGE_RESPONSE):
            result = await merge_goals(old_goals, new_goals)

        assert len(result) >= 1
        all_text = " ".join(g.text.lower() for g in result)
        assert "character" in all_text or "protagonist" in all_text or "background" in all_text

    @pytest.mark.asyncio
    async def test_should_keep_unique_goals(self):
        old_goals = [
            Goal(
                id="G0_old",
                text="Add dialogue between characters",
                type="request",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            )
        ]

        new_goals = [
            Goal(
                id="G0_new",
                text="Include vivid imagery of the setting",
                type="suggestion",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            )
        ]

        with patch("backend.pipelines.goal_merge.call_llm_json", new_callable=AsyncMock, return_value=KEEP_MERGE_RESPONSE):
            result = await merge_goals(old_goals, new_goals)

        assert len(result) == 2
        all_text = " ".join([goal.text.lower() for goal in result])
        assert "dialogue" in all_text
        assert "imagery" in all_text

    @pytest.mark.asyncio
    async def test_should_handle_mixed_merge_operations(self):
        old_goals = [
            Goal(
                id="G0_old",
                text="Use simple vocabulary",
                type="suggestion",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G1_old",
                text="Add more plot development",
                type="request",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G2_old",
                text="Include humor in the story",
                type="suggestion",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            )
        ]

        new_goals = [
            Goal(
                id="G0_new",
                text="Use sophisticated, advanced vocabulary",
                type="suggestion",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G1_new",
                text="Develop the story's main conflict further",
                type="request",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G2_new",
                text="Add emotional depth to characters",
                type="request",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            )
        ]

        with patch("backend.pipelines.goal_merge.call_llm_json", new_callable=AsyncMock, return_value=MIXED_MERGE_RESPONSE):
            result = await merge_goals(old_goals, new_goals)

        assert len(result) >= 3

        all_text = " ".join([goal.text.lower() for goal in result])
        assert "sophisticated" in all_text or "advanced" in all_text, f"Expected sophisticated/advanced vocabulary goal: {all_text}"
        assert "plot" in all_text or "conflict" in all_text
        assert "humor" in all_text, f"Humor goal should be preserved: {all_text}"

    @pytest.mark.asyncio
    async def test_should_handle_empty_goal_lists(self):
        new_goals = [Goal(id="G0", text="Test goal", type="request", source_message_id="msg_1", created_at=datetime.now().isoformat())]
        result = await merge_goals([], new_goals)
        assert len(result) == 1
        assert result[0].text == "Test goal"

        old_goals = [Goal(id="G0", text="Test goal", type="request", source_message_id="msg_1", created_at=datetime.now().isoformat())]
        result = await merge_goals(old_goals, [])
        assert len(result) == 1
        assert result[0].text == "Test goal"

        result = await merge_goals([], [])
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_should_preserve_goal_types_during_merge(self):
        old_goals = [
            Goal(id="G0", text="What is the main theme?", type="question", source_message_id="msg_1", created_at=datetime.now().isoformat()),
            Goal(id="G1", text="Please add more detail", type="request", source_message_id="msg_1", created_at=datetime.now().isoformat())
        ]

        new_goals = [
            Goal(id="G0", text="What themes are you exploring?", type="question", source_message_id="msg_2", created_at=datetime.now().isoformat()),
            Goal(id="G1", text="You should consider adding imagery", type="suggestion", source_message_id="msg_2", created_at=datetime.now().isoformat())
        ]

        merge_response = {
            "operations": [
                {"updated_goal": "What is the main theme being explored?", "operation": "combine", "goal_numbers": ["1", "1"]},
                {"updated_goal": "Add more detail and imagery", "operation": "combine", "goal_numbers": ["2", "2"]},
            ]
        }

        with patch("backend.pipelines.goal_merge.call_llm_json", new_callable=AsyncMock, return_value=merge_response):
            result = await merge_goals(old_goals, new_goals)

        types_in_result = [goal.type for goal in result]
        assert "question" in types_in_result, f"Should preserve question type: {types_in_result}"
        assert "request" in types_in_result or "suggestion" in types_in_result, \
            f"Should preserve request or suggestion type: {types_in_result}"