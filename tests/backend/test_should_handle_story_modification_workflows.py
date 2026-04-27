"""
TDD Test for Story Follow-up Goals Backend Logic

Tests the scenario:
1. Initial complex message: storytelling elements + story creation with specific requirements
2. Follow-up message: "make the story shorter"
3. Verify that follow-up goals are properly captured and merged

Following TDD: RED -> GREEN -> REFACTOR
"""

import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock
from backend.pipelines import infer_goals, merge_goals
from backend.models import Goal


INITIAL_STORY_CLAUSES = {
    "clauses": [
        {"clause": "What are the key elements of effective storytelling?", "type": "question", "summary": "Explain storytelling elements"},
        {"clause": "Write a creative very SHORT story about space exploration for teenagers", "type": "request", "summary": "Create a short space story for teens"},
        {"clause": "The protagonist should be relatable and face realistic challenges", "type": "suggestion", "summary": "Make a relatable protagonist"},
        {"clause": "Add more humor and interactive elements to make it engaging", "type": "suggestion", "summary": "Include humor and interactivity"},
    ]
}

FOLLOWUP_SHORTER_CLAUSES = {
    "clauses": [
        {"clause": "Make the story shorter", "type": "request", "summary": "Reduce story length"},
    ]
}

HUMOR_CLAUSES = {
    "clauses": [
        {"clause": "Add more humor to make it funnier", "type": "suggestion", "summary": "Increase humor"},
    ]
}

SHORT_STORY_CLAUSES = {
    "clauses": [
        {"clause": "Write a short story about space exploration for teenagers", "type": "request", "summary": "Create short space story"},
    ]
}

MERGE_INITIAL_WITH_SHORTER = {
    "operations": [
        {"updated_goal": "What are the key elements of effective storytelling?", "operation": "keep", "goal_numbers": ["1"]},
        {"updated_goal": "Write a creative short story about space exploration for teenagers", "operation": "combine", "goal_numbers": ["2", "1"]},
        {"updated_goal": "The protagonist should be relatable and face realistic challenges", "operation": "keep", "goal_numbers": ["3"]},
        {"updated_goal": "Add more humor and interactive elements to make it engaging", "operation": "keep", "goal_numbers": ["4"]},
    ]
}

MERGE_AFTER_HUMOR = {
    "operations": [
        {"updated_goal": "What are the key elements of effective storytelling?", "operation": "keep", "goal_numbers": ["1"]},
        {"updated_goal": "Write a creative short story about space exploration for teenagers", "operation": "keep", "goal_numbers": ["2"]},
        {"updated_goal": "The protagonist should be relatable and face realistic challenges", "operation": "keep", "goal_numbers": ["3"]},
        {"updated_goal": "Add more humor and interactive elements to make it engaging and funnier", "operation": "combine", "goal_numbers": ["4", "1"]},
    ]
}

MERGE_ADDITIVE = {
    "operations": [
        {"updated_goal": "Write a creative short story about space exploration for teenagers", "operation": "keep", "goal_numbers": ["1"]},
        {"updated_goal": "Make the protagonist relatable and face realistic challenges", "operation": "keep", "goal_numbers": ["2"]},
        {"updated_goal": "Make the story shorter", "operation": "combine", "goal_numbers": ["1", "1"]},
    ]
}

MERGE_SHORTER_THEN_HUMOR = {
    "operations": [
        {"updated_goal": "Write a short story about space exploration for teenagers", "operation": "keep", "goal_numbers": ["1"]},
        {"updated_goal": "Make the story shorter", "operation": "combine", "goal_numbers": ["1", "1"]},
    ]
}

MERGE_FINAL_WITH_HUMOR = {
    "operations": [
        {"updated_goal": "Write a short story about space exploration for teenagers", "operation": "keep", "goal_numbers": ["1"]},
        {"updated_goal": "Make the story shorter", "operation": "keep", "goal_numbers": ["2"]},
        {"updated_goal": "Add more humor to make it funnier", "operation": "combine", "goal_numbers": ["1", "1"]},
    ]
}


def _make_infer_mock(responses):
    call_idx = 0
    responses_list = list(responses)

    async def mock_fn(prompt, max_tokens=1000, label=""):
        nonlocal call_idx
        if call_idx < len(responses_list):
            resp = responses_list[call_idx]
            call_idx += 1
            return resp
        return None

    return mock_fn


def _patch_infer_merge(infer_responses, merge_response):
    return (
        patch("backend.pipelines.goal_inference.call_llm_json", side_effect=_make_infer_mock(infer_responses)),
        patch("backend.pipelines.goal_merge.call_llm_json", new_callable=AsyncMock, return_value=merge_response),
    )


@pytest.mark.integration
class TestStoryFollowupGoals:

    @pytest.mark.asyncio
    async def test_should_infer_goals_from_initial_story_request(self):
        with patch("backend.pipelines.goal_inference.call_llm_json", new_callable=AsyncMock, return_value=INITIAL_STORY_CLAUSES):
            initial_message = (
                "What are the key elements of effective storytelling? "
                "Please write a creative very SHORT story about space exploration for teenagers. "
                "I think the protagonist should be relatable and face realistic challenges. "
                "You should consider adding more humor and interactive elements to make it engaging."
            )

            inferred_goals = await infer_goals(initial_message, "msg_1")

        assert len(inferred_goals) > 0, f"Should infer goals from complex message, got: {len(inferred_goals)}"

        goal_texts = [goal.text.lower() for goal in inferred_goals]

        assert any("storytelling" in text or "story" in text for text in goal_texts), \
            f"Should capture storytelling request: {goal_texts}"

        assert any("short" in text for text in goal_texts), \
            f"Should capture 'short' requirement: {goal_texts}"

        goal_types = [goal.type for goal in inferred_goals]
        assert len(set(goal_types)) > 0, f"Should have goal types: {goal_types}"

    @pytest.mark.asyncio
    async def test_should_infer_goals_from_followup_make_shorter_request(self):
        with patch("backend.pipelines.goal_inference.call_llm_json", new_callable=AsyncMock, return_value=FOLLOWUP_SHORTER_CLAUSES):
            followup_message = "Please make the story shorter."

            followup_goals = await infer_goals(followup_message, "msg_2")

        assert len(followup_goals) > 0, f"Should infer goals from 'make shorter' request, got: {len(followup_goals)}"

        goal_texts = [goal.text.lower() for goal in followup_goals]
        assert any("shorter" in text or "short" in text for text in goal_texts), \
            f"Should capture 'shorter/short' concept: {goal_texts}"

        goal_types = [goal.type for goal in followup_goals]
        assert any(t in goal_types for t in ("request", "suggestion", "offer")), \
            f"Make shorter should be request, suggestion, or offer, got: {goal_types}"

    @pytest.mark.asyncio
    async def test_should_handle_story_followup_merge_pipeline(self):
        infer_mock = _make_infer_mock([INITIAL_STORY_CLAUSES, FOLLOWUP_SHORTER_CLAUSES])

        with patch("backend.pipelines.goal_inference.call_llm_json", side_effect=infer_mock), \
             patch("backend.pipelines.goal_merge.call_llm_json", new_callable=AsyncMock, return_value=MERGE_INITIAL_WITH_SHORTER):

            initial_message = (
                "What are the key elements of effective storytelling? "
                "Please write a creative very SHORT story about space exploration for teenagers. "
                "I think the protagonist should be relatable and face realistic challenges. "
                "You should consider adding more humor and interactive elements to make it engaging."
            )
            followup_message = "Please make the story shorter."

            initial_goals = await infer_goals(initial_message, "msg_1")
            followup_goals = await infer_goals(followup_message, "msg_2")
            merged_goals = await merge_goals(initial_goals, followup_goals)

        assert len(merged_goals) > 0, "Should have merged goals"

        merged_texts = [goal.text.lower() for goal in merged_goals]

        assert any("short" in text for text in merged_texts), \
            f"Story shortening concept should be preserved: {merged_texts}"

        assert any("story" in text for text in merged_texts), \
            f"Story-related goals should be preserved: {merged_texts}"

        goal_ids = [goal.id for goal in merged_goals]
        assert len(set(goal_ids)) == len(goal_ids), f"Goal IDs should be unique: {goal_ids}"

    @pytest.mark.asyncio
    async def test_should_handle_story_modification_goals_as_additive(self):
        with patch("backend.pipelines.goal_merge.call_llm_json", new_callable=AsyncMock, return_value=MERGE_ADDITIVE):
            existing_goals = [
                Goal(
                    id="G0_story",
                    text="Write a creative short story about space exploration for teenagers",
                    type="request",
                    source_message_id="msg_1",
                    created_at=datetime.now().isoformat()
                ),
                Goal(
                    id="G1_relatable",
                    text="Make the protagonist relatable and face realistic challenges",
                    type="suggestion",
                    source_message_id="msg_1",
                    created_at=datetime.now().isoformat()
                )
            ]

            new_goals = [
                Goal(
                    id="G2_shorter",
                    text="Make the story shorter",
                    type="request",
                    source_message_id="msg_2",
                    created_at=datetime.now().isoformat()
                )
            ]

            result = await merge_goals(existing_goals, new_goals)

        assert len(result) >= 2, f"Should preserve multiple goals, got {len(result)}: {[g.text for g in result]}"

        result_texts = [goal.text.lower() for goal in result]

        assert any("story" in text for text in result_texts), \
            f"Should preserve story goal: {result_texts}"

        assert any("shorter" in text or "short" in text for text in result_texts), \
            f"Should include 'make shorter/short' goal: {result_texts}"

    @pytest.mark.asyncio
    async def test_should_accumulate_multiple_story_modifications(self):
        infer_mock = _make_infer_mock([SHORT_STORY_CLAUSES, FOLLOWUP_SHORTER_CLAUSES, HUMOR_CLAUSES])

        with patch("backend.pipelines.goal_inference.call_llm_json", side_effect=infer_mock), \
             patch("backend.pipelines.goal_merge.call_llm_json", new_callable=AsyncMock) as merge_mock:

            merge_mock.side_effect = [MERGE_SHORTER_THEN_HUMOR, MERGE_FINAL_WITH_HUMOR]

            initial_goals = await infer_goals(
                "Write a short story about space exploration for teenagers.", "msg_1"
            )

            shorter_goals = await infer_goals("Please make the story shorter.", "msg_2")
            merged_after_shorter = await merge_goals(initial_goals, shorter_goals)

            humor_goals = await infer_goals("Also add more humor to make it funnier.", "msg_3")
            final_merged = await merge_goals(merged_after_shorter, humor_goals)

        final_texts = [goal.text.lower() for goal in final_merged]

        assert any("story" in text for text in final_texts), \
            f"Should preserve story concept: {final_texts}"

        assert any("shorter" in text or "short" in text for text in final_texts), \
            f"Should preserve 'shorter/short' modification: {final_texts}"

        assert any("humor" in text or "funnier" in text for text in final_texts), \
            f"Should preserve humor modification: {final_texts}"

        assert len(final_merged) <= 6, f"Should merge reasonably, got {len(final_merged)} goals"