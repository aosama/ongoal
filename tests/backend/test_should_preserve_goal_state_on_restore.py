import pytest
import asyncio
from datetime import datetime
from backend.models import Conversation, Goal, GoalHistoryEntry
from backend.api_endpoints import restore_goal_from_history, conversation_repository


class TestRestoreGoalFromHistory:
    def test_should_preserve_created_at_from_history_entry(self):
        conversation_id = "test-restore-unit"
        now = "2025-04-17T10:00:00"

        # Create conversation with a history entry
        conversation = Conversation(id=conversation_id)
        entry = GoalHistoryEntry(
            turn=1,
            operation="infer",
            goal_id="g1",
            goal_text="test goal",
            goal_type="question",
            timestamp=now,
        )
        conversation.goal_history.append(entry)
        conversation_repository.create(conversation_id)
        conversation_repository._store[conversation_id] = conversation

        # Call restore endpoint directly
        result = asyncio.run(restore_goal_from_history(conversation_id, 0))

        # Verify restored goal uses history timestamp
        restored = next(g for g in conversation.goals if g.id == "g1")
        assert restored.created_at == now, f"Expected created_at={now}, got {restored.created_at}"

    def test_should_default_locked_to_false_for_restored_goal(self):
        conversation_id = "test-restore-locked"

        conversation = Conversation(id=conversation_id)
        entry = GoalHistoryEntry(
            turn=1,
            operation="infer",
            goal_id="g1",
            goal_text="test goal",
            goal_type="question",
            timestamp=datetime.now().isoformat(),
        )
        conversation.goal_history.append(entry)
        conversation_repository.create(conversation_id)
        conversation_repository._store[conversation_id] = conversation

        asyncio.run(restore_goal_from_history(conversation_id, 0))

        restored = next(g for g in conversation.goals if g.id == "g1")
        assert restored.locked == False

    def test_should_update_existing_goal_when_restored(self):
        conversation_id = "test-restore-update"

        conversation = Conversation(id=conversation_id)
        original_goal = Goal(
            id="g1",
            text="original text",
            type="request",
            source_message_id="msg_1",
            created_at="2025-01-01T00:00:00",
            locked=False,
        )
        conversation.goals.append(original_goal)

        entry = GoalHistoryEntry(
            turn=2,
            operation="replace",
            goal_id="g1",
            goal_text="restored text",
            goal_type="question",
            timestamp="2025-06-01T12:00:00",
        )
        conversation.goal_history.append(entry)
        conversation_repository.create(conversation_id)
        conversation_repository._store[conversation_id] = conversation

        asyncio.run(restore_goal_from_history(conversation_id, 0))

        existing = conversation.get_goal_by_id("g1")
        assert existing.text == "restored text"
        assert existing.type == "question"
        # created_at should be preserved from history entry when updating
        assert existing.created_at == entry.timestamp
