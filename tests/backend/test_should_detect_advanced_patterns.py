"""
OnGoal Advanced Detection Tests
Tests for repetition detection, fixation detection, goal progress, and goal completion (REQ-03-02-006, REQ-03-03-002, REQ-03-02-001, REQ-03-02-004)
"""

import pytest
from backend.models import Goal, GoalEvaluation, Message, Conversation
from backend.pipelines import compute_goal_progress, detect_repetition, detect_fixation, detect_breakdown


@pytest.mark.unit
class TestGoalProgressComputation:
    """Tests for compute_goal_progress (REQ-03-02-001, REQ-03-02-004)"""

    def test_should_return_empty_progress_for_empty_conversation(self):
        conv = Conversation(id="test")
        progress = compute_goal_progress(conv)
        assert progress == []

    def test_should_show_manual_completed_for_completed_goal(self):
        conv = Conversation(id="test")
        goal = Goal(id="G0", text="test goal", type="request", source_message_id="m0", completed=True)
        conv.goals.append(goal)
        progress = compute_goal_progress(conv)
        assert len(progress) == 1
        assert progress[0]["completion_status"] == "completed_manual"
        assert progress[0]["progress_pct"] == 100

    def test_should_show_likely_complete_for_confirmed_goal(self):
        conv = Conversation(id="test")
        goal = Goal(
            id="G0", text="test goal", type="request", source_message_id="m0",
            status="confirm",
            evaluation=GoalEvaluation(goal_id="G0", category="confirm", explanation="confirmed"),
        )
        conv.goals.append(goal)
        assistant_msg = Message(id="msg_1", content="response", role="assistant")
        assistant_msg.goals = [goal]
        conv.messages.append(assistant_msg)
        progress = compute_goal_progress(conv)
        assert len(progress) == 1
        assert progress[0]["confirm_count"] == 2
        assert progress[0]["completion_status"] == "likely_complete"

    def test_should_show_at_risk_for_ignored_goal(self):
        conv = Conversation(id="test")
        goal = Goal(
            id="G0", text="test goal", type="request", source_message_id="m0",
            status="ignore",
            evaluation=GoalEvaluation(goal_id="G0", category="ignore", explanation="ignored"),
        )
        conv.goals.append(goal)
        progress = compute_goal_progress(conv)
        assert len(progress) == 1
        assert progress[0]["ignore_count"] == 1
        assert progress[0]["completion_status"] == "at_risk"

    def test_should_show_contradicted_for_contradicted_goal(self):
        conv = Conversation(id="test")
        goal = Goal(
            id="G0", text="test goal", type="request", source_message_id="m0",
            status="contradict",
            evaluation=GoalEvaluation(goal_id="G0", category="contradict", explanation="contradicted"),
        )
        conv.goals.append(goal)
        progress = compute_goal_progress(conv)
        assert len(progress) == 1
        assert progress[0]["contradict_count"] == 1
        assert progress[0]["completion_status"] == "contradicted"

    def test_should_show_active_for_unevaluated_goal(self):
        conv = Conversation(id="test")
        goal = Goal(id="G0", text="test goal", type="request", source_message_id="m0")
        conv.goals.append(goal)
        progress = compute_goal_progress(conv)
        assert len(progress) == 1
        assert progress[0]["total_evaluations"] == 0
        assert progress[0]["completion_status"] == "active"

    def test_should_show_progressing_for_mixed_evaluations(self):
        conv = Conversation(id="test")
        goal = Goal(
            id="G0", text="test goal", type="request", source_message_id="m0",
            status="confirm",
            evaluation=GoalEvaluation(goal_id="G0", category="confirm", explanation="ok"),
        )
        conv.goals.append(goal)
        progress = compute_goal_progress(conv)
        assert progress[0]["progress_pct"] >= 60
        assert progress[0]["completion_status"] in ("likely_complete", "progressing")

    def test_should_count_evaluations_across_messages(self):
        conv = Conversation(id="test")
        goal = Goal(
            id="G0", text="test goal", type="request", source_message_id="m0",
            status="confirm",
            evaluation=GoalEvaluation(goal_id="G0", category="confirm", explanation="ok"),
        )
        conv.goals.append(goal)
        msg1 = Message(id="msg_1", content="response 1", role="assistant")
        msg1.goals = [Goal(
            id="G0", text="test goal", type="request", source_message_id="m0",
            evaluation=GoalEvaluation(goal_id="G0", category="confirm", explanation="ok"),
        )]
        msg2 = Message(id="msg_2", content="response 2", role="assistant")
        msg2.goals = [Goal(
            id="G0", text="test goal", type="request", source_message_id="m0",
            evaluation=GoalEvaluation(goal_id="G0", category="ignore", explanation="ignored"),
        )]
        conv.messages.extend([msg1, msg2])
        progress = compute_goal_progress(conv)
        assert progress[0]["confirm_count"] == 2
        assert progress[0]["ignore_count"] == 1


@pytest.mark.unit
class TestRepetitionDetectionSyntax:
    """Unit tests for detect_repetition input validation"""

    @pytest.mark.asyncio
    async def test_should_return_none_for_single_response(self):
        msgs = [Message(id="m1", content="hello", role="assistant")]
        result = await detect_repetition(msgs)
        assert result is None

    @pytest.mark.asyncio
    async def test_should_return_none_for_empty_messages(self):
        result = await detect_repetition([])
        assert result is None


@pytest.mark.unit
class TestFixationDetectionSyntax:
    """Unit tests for detect_fixation input validation"""

    @pytest.mark.asyncio
    async def test_should_return_none_for_single_goal(self):
        goals = [Goal(id="G0", text="only goal", type="request", source_message_id="m0")]
        result = await detect_fixation(goals)
        assert result is None

    @pytest.mark.asyncio
    async def test_should_return_none_for_no_ignored_goals(self):
        goals = [
            Goal(id="G0", text="goal 1", type="request", source_message_id="m0", status="confirm"),
            Goal(id="G1", text="goal 2", type="request", source_message_id="m0", status="confirm"),
        ]
        result = await detect_fixation(goals)
        assert result is None

    @pytest.mark.asyncio
    async def test_should_return_none_for_no_confirmed_goals(self):
        goals = [
            Goal(id="G0", text="goal 1", type="request", source_message_id="m0", status="ignore"),
            Goal(id="G1", text="goal 2", type="request", source_message_id="m0", status="ignore"),
        ]
        result = await detect_fixation(goals)
        assert result is None


@pytest.mark.unit
class TestBreakdownDetectionSyntax:
    """Unit tests for detect_breakdown input validation"""

    @pytest.mark.asyncio
    async def test_should_return_none_for_single_user_message(self):
        msgs = [Message(id="m1", content="hello", role="user")]
        goals = [Goal(id="G0", text="test", type="request", source_message_id="m0", status="ignore")]
        result = await detect_breakdown(msgs, goals)
        assert result is None

    @pytest.mark.asyncio
    async def test_should_return_none_for_no_ignored_goals(self):
        msgs = [
            Message(id="m1", content="hello", role="user"),
            Message(id="m2", content="again", role="user"),
        ]
        goals = [Goal(id="G0", text="test", type="request", source_message_id="m0", status="confirm")]
        result = await detect_breakdown(msgs, goals)
        assert result is None

    @pytest.mark.asyncio
    async def test_should_return_none_for_empty_messages(self):
        goals = [Goal(id="G0", text="test", type="request", source_message_id="m0", status="ignore")]
        result = await detect_breakdown([], goals)
        assert result is None