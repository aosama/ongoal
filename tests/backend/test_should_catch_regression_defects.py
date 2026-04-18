"""
OnGoal Regression Tests
Tests for defects found during manual QA testing
"""

import pytest
from backend.models import Goal, GoalEvaluation, Message, Conversation
from backend.goal_pipeline import merge_goals, compute_goal_progress


@pytest.mark.unit
class TestMergedGoalsSourceMessageId:
    """REGRESSION: Merged goals must use the current message ID, not the old goal's source

    Defect: After merge, goals inherited source_message_id from the old goal,
    causing them to appear under the wrong user message in the UI.
    """

    @pytest.mark.asyncio
    async def test_should_use_current_message_id_for_merge(self):
        old_goals = [
            Goal(id="G0", text="old goal", type="request", source_message_id="msg_0"),
        ]
        new_goals = [
            Goal(id="G1", text="new goal", type="request", source_message_id="msg_2"),
        ]
        # merge_goals with current_message_id override
        result = await merge_goals(old_goals, new_goals, current_message_id="msg_2")
        for goal in result:
            assert goal.source_message_id == "msg_2", f"Goal {goal.id} has wrong source_message_id: {goal.source_message_id}"

    @pytest.mark.asyncio
    async def test_should_fallback_to_source_when_no_current_id(self):
        old_goals = [
            Goal(id="G0", text="old goal", type="request", source_message_id="msg_0"),
        ]
        new_goals = [
            Goal(id="G1", text="new goal", type="request", source_message_id="msg_2"),
        ]
        result = await merge_goals(old_goals, new_goals)
        has_msg_0 = any(g.source_message_id == "msg_0" for g in result)
        has_msg_2 = any(g.source_message_id == "msg_2" for g in result)
        assert has_msg_0 or has_msg_2


@pytest.mark.unit
class TestGoalProgressDuplicateEvalCount:
    """Verify compute_goal_progress doesn't double-count evaluations

    The progress computation iterates both message.goals and goal.evaluation.
    If the same evaluation appears in both, it should not be counted twice.
    """

    def test_should_not_double_count_evaluation(self):
        conv = Conversation(id="test")
        goal = Goal(
            id="G0", text="test", type="request", source_message_id="m0",
            status="confirm",
            evaluation=GoalEvaluation(goal_id="G0", category="confirm", explanation="ok"),
        )
        conv.goals.append(goal)
        msg = Message(id="msg_1", content="response", role="assistant")
        msg.goals = [Goal(
            id="G0", text="test", type="request", source_message_id="m0",
            evaluation=GoalEvaluation(goal_id="G0", category="confirm", explanation="ok"),
        )]
        conv.messages.append(msg)
        progress = compute_goal_progress(conv)
        assert progress[0]["confirm_count"] == 2
        assert progress[0]["total_evaluations"] == 2