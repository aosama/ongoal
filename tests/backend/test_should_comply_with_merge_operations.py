"""
Test Goal Merge Operations Compliance with OnGoal Requirements

Verifies that the merge stage correctly implements the three operations:
1. Replace: New goal contradicts old goal -> replace old with new
2. Combine: New goal similar to old goal -> merge them into combined goal
3. Keep: Goal is unique -> keep it unchanged

All tests use mocked LLM responses for deterministic execution.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock
from backend.pipelines import infer_goals, merge_goals
from backend.models import Goal


REPLACE_MERGE_RESPONSE = {
    "operations": [
        {"updated_goal": "Write a very short, simple story with minimal details", "operation": "replace", "goal_numbers": ["1", "1"]},
        {"updated_goal": "Include complex character backstories", "operation": "keep", "goal_numbers": ["2"]},
    ]
}

COMBINE_MERGE_RESPONSE = {
    "operations": [
        {"updated_goal": "Add character development and protagonist background", "operation": "combine", "goal_numbers": ["1", "1"]},
        {"updated_goal": "Include dialogue between characters", "operation": "keep", "goal_numbers": ["2"]},
    ]
}

KEEP_MERGE_RESPONSE = {
    "operations": [
        {"updated_goal": "Add humor to make the story entertaining", "operation": "keep", "goal_numbers": ["1"]},
        {"updated_goal": "Set the story in a futuristic space station", "operation": "keep", "goal_numbers": ["2"]},
        {"updated_goal": "Include technical details about spaceship engines", "operation": "keep", "goal_numbers": ["1"]},
        {"updated_goal": "Add a romantic subplot between crew members", "operation": "keep", "goal_numbers": ["2"]},
    ]
}

MIXED_MERGE_RESPONSE = {
    "operations": [
        {"updated_goal": "Write a short, concise story about space exploration", "operation": "replace", "goal_numbers": ["1", "1"]},
        {"updated_goal": "Ensure the main character faces realistic challenges for teens", "operation": "combine", "goal_numbers": ["2", "2"]},
        {"updated_goal": "Add humor to keep it engaging", "operation": "keep", "goal_numbers": ["3"]},
        {"updated_goal": "Include technical accuracy about space travel", "operation": "keep", "goal_numbers": ["3"]},
    ]
}

INFER_INITIAL_STORY = {
    "clauses": [
        {"clause": "What are the key elements of effective storytelling?", "type": "question", "summary": "Explain storytelling elements"},
        {"clause": "Write a creative very SHORT story about space exploration for teenagers", "type": "request", "summary": "Short space story"},
        {"clause": "Make the protagonist relatable with realistic challenges", "type": "suggestion", "summary": "Relatable protagonist"},
        {"clause": "Add more humor and interactive elements", "type": "suggestion", "summary": "Humor and interactivity"},
    ]
}

INFER_FOLLOWUP_SHORTER = {
    "clauses": [
        {"clause": "Make the story shorter", "type": "request", "summary": "Reduce story length"},
    ]
}

USER_SCENARIO_MERGE = {
    "operations": [
        {"updated_goal": "What are the key elements of effective storytelling?", "operation": "keep", "goal_numbers": ["1"]},
        {"updated_goal": "Write a creative short story about space exploration for teenagers", "operation": "combine", "goal_numbers": ["2", "1"]},
        {"updated_goal": "Make the protagonist relatable with realistic challenges", "operation": "keep", "goal_numbers": ["3"]},
        {"updated_goal": "Add more humor and interactive elements", "operation": "keep", "goal_numbers": ["4"]},
    ]
}


@pytest.mark.integration
class TestMergeOperationsCompliance:

    @pytest.mark.asyncio
    async def test_should_replace_explicitly_contradicting_goals(self):
        old_goals = [
            Goal(
                id="G0_old",
                text="Write a long detailed story with many chapters",
                type="request",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G1_old",
                text="Include complex character backstories",
                type="suggestion",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            )
        ]

        new_goals = [
            Goal(
                id="G0_new",
                text="Write a very short, simple story with minimal details",
                type="request",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            )
        ]

        with patch("backend.pipelines.goal_merge.call_llm_json", new_callable=AsyncMock, return_value=REPLACE_MERGE_RESPONSE):
            merged_goals = await merge_goals(old_goals, new_goals)

        merged_texts = [g.text.lower() for g in merged_goals]

        assert any("short" in text for text in merged_texts), \
            f"Replace should favor new contradicting goal (short over long): {merged_texts}"

        assert len(merged_goals) <= len(old_goals) + len(new_goals), \
            "Replace should not just accumulate all goals"

    @pytest.mark.asyncio
    async def test_should_combine_similar_goals_correctly(self):
        old_goals = [
            Goal(
                id="G0_old",
                text="Add character development to the story",
                type="suggestion",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G1_old",
                text="Include dialogue between characters",
                type="request",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            )
        ]

        new_goals = [
            Goal(
                id="G0_new",
                text="Develop the protagonist's background and personality more",
                type="suggestion",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            )
        ]

        with patch("backend.pipelines.goal_merge.call_llm_json", new_callable=AsyncMock, return_value=COMBINE_MERGE_RESPONSE):
            merged_goals = await merge_goals(old_goals, new_goals)

        merged_texts = [g.text.lower() for g in merged_goals]

        assert any("character" in text or "protagonist" in text for text in merged_texts), \
            f"Combine should merge similar character concepts: {merged_texts}"

        assert any("dialogue" in text for text in merged_texts), \
            f"Keep should preserve dialogue goal: {merged_texts}"

    @pytest.mark.asyncio
    async def test_should_keep_unique_goals_unchanged(self):
        old_goals = [
            Goal(
                id="G0_old",
                text="Add humor to make the story entertaining",
                type="suggestion",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G1_old",
                text="Set the story in a futuristic space station",
                type="request",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            )
        ]

        new_goals = [
            Goal(
                id="G0_new",
                text="Include technical details about spaceship engines",
                type="suggestion",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G1_new",
                text="Add a romantic subplot between crew members",
                type="offer",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            )
        ]

        with patch("backend.pipelines.goal_merge.call_llm_json", new_callable=AsyncMock, return_value=KEEP_MERGE_RESPONSE):
            merged_goals = await merge_goals(old_goals, new_goals)

        merged_texts = [g.text.lower() for g in merged_goals]

        assert any("humor" in text for text in merged_texts), \
            f"Keep should preserve humor goal: {merged_texts}"

        assert any("space" in text for text in merged_texts), \
            f"Keep should preserve space station goal: {merged_texts}"

        assert any("spaceship" in text or "engine" in text or "technical" in text for text in merged_texts), \
            f"Keep should preserve spaceship goal: {merged_texts}"

        assert len(merged_goals) >= 3, f"Keep should preserve most unique concepts, got {len(merged_goals)}"

    @pytest.mark.asyncio
    async def test_should_handle_mixed_operations_scenario(self):
        old_goals = [
            Goal(
                id="G0_old",
                text="Write a long, detailed story about space exploration",
                type="request",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G1_old",
                text="Make the protagonist a relatable teenager",
                type="suggestion",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G2_old",
                text="Add humor to keep it engaging",
                type="suggestion",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            )
        ]

        new_goals = [
            Goal(
                id="G0_new",
                text="Make the story much shorter and concise",
                type="request",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G1_new",
                text="Ensure the main character faces realistic challenges for teens",
                type="suggestion",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G2_new",
                text="Include technical accuracy about space travel",
                type="request",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            )
        ]

        with patch("backend.pipelines.goal_merge.call_llm_json", new_callable=AsyncMock, return_value=MIXED_MERGE_RESPONSE):
            merged_goals = await merge_goals(old_goals, new_goals)

        merged_texts = [g.text.lower() for g in merged_goals]

        assert any("short" in text or "concise" in text for text in merged_texts), \
            f"Replace should produce short/concise concept: {merged_texts}"

        assert any("character" in text or "protagonist" in text for text in merged_texts), \
            f"Combine should merge protagonist concepts: {merged_texts}"

        assert any("humor" in text for text in merged_texts), \
            f"Keep should preserve humor goal: {merged_texts}"

        assert 3 <= len(merged_goals) <= 6, f"Mixed operations should produce reasonable count, got {len(merged_goals)}"

    @pytest.mark.asyncio
    async def test_should_handle_actual_story_scenario_from_user_example(self):
        initial_message = ("What are the key elements of effective storytelling? "
                         "Please write a creative very SHORT story about space exploration for teenagers. "
                         "I think the protagonist should be relatable and face realistic challenges. "
                         "You should consider adding more humor and interactive elements to make it engaging.")

        followup_message = "Please make the story shorter."

        call_count = 0

        async def mock_infer_llm(prompt, max_tokens=1000, label=""):
            nonlocal call_count
            call_count += 1
            return INFER_INITIAL_STORY if call_count == 1 else INFER_FOLLOWUP_SHORTER

        with patch("backend.pipelines.goal_inference.call_llm_json", side_effect=mock_infer_llm), \
             patch("backend.pipelines.goal_merge.call_llm_json", new_callable=AsyncMock, return_value=USER_SCENARIO_MERGE):

            initial_goals = await infer_goals(initial_message, "msg_1")
            followup_goals = await infer_goals(followup_message, "msg_2")
            merged_goals = await merge_goals(initial_goals, followup_goals)

        assert len(initial_goals) > 0, "Should infer initial goals"
        assert len(followup_goals) > 0, "Should infer follow-up goals"
        assert len(merged_goals) > 0, "Should have merged goals"

        merged_texts = [g.text.lower() for g in merged_goals]
        assert any("short" in text for text in merged_texts), \
            f"Shortened story concept should be preserved: {merged_texts}"

        assert any("story" in text for text in merged_texts), \
            f"Story concept should be preserved: {merged_texts}"