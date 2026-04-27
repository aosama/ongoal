"""
Test Goal Replacement for Outdated Goals (REQ-03-01-004)

Generated with Verbalised Sampling: prompt produced 5 diverse scenarios,
the 3 lowest-probability (tail-distribution) cases were selected for
maximum coverage breadth.
"""

import pytest
from backend.models import Goal, Conversation, Message
from backend.pipelines.goal_merge import replace_outdated_goals


class TestReplaceOutdatedGoals:
    """Automatic replacement of goals contradicted by newer goals."""

    @pytest.fixture
    def conversation(self):
        conv = Conversation(id="test_conv")
        conv.messages.append(Message(id="msg_1", content="First user message", role="user"))
        return conv

    @pytest.fixture
    def existing_goals(self):
        return [
            Goal(id="G0", text="Add more imagery to the story", type="request", source_message_id="msg_1"),
            Goal(id="G1", text="Keep the tone light and humorous", type="suggestion", source_message_id="msg_1"),
        ]

    @pytest.fixture
    def contradicting_goals(self):
        return [
            Goal(id="G2", text="Remove all images and keep text only", type="request", source_message_id="msg_2"),
        ]

    async def test_should_mark_existing_goal_as_replaced_when_new_goal_contradicts(self, conversation, existing_goals, contradicting_goals, monkeypatch):
        """Direct semantic contradiction triggers replacement status.

        Uses monkeypatch to avoid real LLM dependency (REQ-03-01-004).
        """
        async def fake_detect(goals):
            return [
                {"goal_id_1": "G0", "goal_id_2": "G2", "reason": "Contradicts", "resolution": "Replace"}
            ]

        monkeypatch.setattr("backend.pipelines.goal_merge.detect_contradiction", fake_detect)
        conversation.goals = existing_goals.copy()
        result = await replace_outdated_goals(conversation.goals, contradicting_goals, "msg_2", conversation)

        replaced = [g for g in existing_goals if g.status == "replaced"]
        assert len(replaced) == 1
        assert replaced[0].id == "G0"
        assert "G0" not in [g.id for g in result]

    async def test_should_add_replace_entry_to_goal_history(self, conversation, existing_goals, contradicting_goals, monkeypatch):
        """Replacement is tracked in goal_history with operation='replace'."""
        async def fake_detect(goals):
            return [
                {"goal_id_1": "G0", "goal_id_2": "G2", "reason": "Contradicts", "resolution": "Replace"}
            ]

        monkeypatch.setattr("backend.pipelines.goal_merge.detect_contradiction", fake_detect)
        conversation.goals = existing_goals.copy()
        await replace_outdated_goals(conversation.goals, contradicting_goals, "msg_2", conversation)

        replace_entries = [h for h in conversation.goal_history if h.operation == "replace"]
        assert len(replace_entries) == 1
        assert replace_entries[0].goal_id == "G0"
        assert "G2" in replace_entries[0].previous_goal_ids

    async def test_should_not_replace_when_no_contradiction(self, conversation, existing_goals, monkeypatch):
        """Non-contradictory new goals leave existing goals untouched."""
        async def fake_detect(goals):
            return []

        monkeypatch.setattr("backend.pipelines.goal_merge.detect_contradiction", fake_detect)
        new_goals = [Goal(id="G2", text="Add a table of contents", type="suggestion", source_message_id="msg_2")]
        conversation.goals = existing_goals.copy()
        result = await replace_outdated_goals(conversation.goals, new_goals, "msg_2", conversation)

        assert len(result) == 2
        assert all(g.status is None for g in result)
        assert len([h for h in conversation.goal_history if h.operation == "replace"]) == 0
