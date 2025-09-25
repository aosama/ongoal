"""
TDD Tests for Goal CRUD Operations
Tests the manual goal management functionality as per TDD requirements (memory-only)
"""
import pytest
from datetime import datetime
from backend.models import Goal, Conversation

class TestGoalCRUDOperations:
    """Test goal CRUD operations following TDD principles"""

    @pytest.fixture
    def sample_conversation(self):
        """Create a sample conversation for testing"""
        conversation_id = "test_conv_001"
        return Conversation(id=conversation_id)

    def test_should_create_goal_manually(self, sample_conversation):
        """
        GIVEN: A conversation exists
        WHEN: A goal is created manually via CRUD operation
        THEN: The goal should be added with correct attributes
        """
        # GIVEN
        conversation = sample_conversation

        # WHEN
        new_goal = Goal(
            id="G0_manual",
            text="Write a short story about dragons",
            type="request",
            source_message_id="msg_0",
            created_at=datetime.now().isoformat()
        )
        conversation.goals.append(new_goal)

        # THEN
        assert len(conversation.goals) == 1
        retrieved_goal = conversation.goals[0]
        assert retrieved_goal.id == "G0_manual"
        assert retrieved_goal.text == "Write a short story about dragons"
        assert retrieved_goal.type == "request"
        assert retrieved_goal.locked == False
        assert retrieved_goal.completed == False

    def test_should_update_goal_attributes(self, sample_conversation):
        """
        GIVEN: A goal exists in the conversation
        WHEN: Goal attributes are updated via CRUD operation
        THEN: The changes should be reflected in memory
        """
        # GIVEN
        conversation = sample_conversation
        original_goal = Goal(
            id="G1_manual",
            text="Original goal text",
            type="question",
            source_message_id="msg_1",
            created_at=datetime.now().isoformat()
        )
        conversation.goals.append(original_goal)

        # WHEN
        original_goal.text = "Updated goal text"
        original_goal.type = "request"
        original_goal.locked = True
        original_goal.completed = True
        original_goal.status = "confirmed"

        # THEN
        updated_goal = conversation.goals[0]
        assert updated_goal.text == "Updated goal text"
        assert updated_goal.type == "request"
        assert updated_goal.locked == True
        assert updated_goal.completed == True
        assert updated_goal.status == "confirmed"

    def test_should_delete_goal_from_conversation(self, sample_conversation):
        """
        GIVEN: Multiple goals exist in a conversation
        WHEN: One goal is deleted via CRUD operation
        THEN: Only the specified goal should be removed
        """
        # GIVEN
        conversation = sample_conversation
        goal1 = Goal(id="G1", text="Goal 1", type="request", source_message_id="msg_1", created_at=datetime.now().isoformat())
        goal2 = Goal(id="G2", text="Goal 2", type="question", source_message_id="msg_2", created_at=datetime.now().isoformat())

        conversation.goals.extend([goal1, goal2])

        # WHEN
        conversation.goals = [g for g in conversation.goals if g.id != "G1"]

        # THEN
        assert len(conversation.goals) == 1
        remaining_goal = conversation.goals[0]
        assert remaining_goal.id == "G2"
        assert remaining_goal.text == "Goal 2"

    def test_should_lock_goal_to_prevent_automatic_updates(self, sample_conversation):
        """
        GIVEN: A goal exists in unlocked state
        WHEN: Goal is locked via CRUD operation
        THEN: Goal should have locked=True status
        """
        # GIVEN
        conversation = sample_conversation
        goal = Goal(
            id="G_lockable",
            text="Goal to be locked",
            type="suggestion",
            locked=False,
            source_message_id="msg_1",
            created_at=datetime.now().isoformat()
        )
        conversation.goals.append(goal)

        # WHEN
        goal.locked = True

        # THEN
        locked_goal = conversation.goals[0]
        assert locked_goal.locked == True

    def test_should_unlock_goal_to_allow_automatic_updates(self, sample_conversation):
        """
        GIVEN: A goal exists in locked state
        WHEN: Goal is unlocked via CRUD operation
        THEN: Goal should have locked=False status
        """
        # GIVEN
        conversation = sample_conversation
        goal = Goal(
            id="G_unlockable",
            text="Goal to be unlocked",
            type="offer",
            locked=True,
            source_message_id="msg_1",
            created_at=datetime.now().isoformat()
        )
        conversation.goals.append(goal)

        # WHEN
        goal.locked = False

        # THEN
        unlocked_goal = conversation.goals[0]
        assert unlocked_goal.locked == False

    def test_should_preserve_goal_creation_timestamp(self, sample_conversation):
        """
        GIVEN: A goal with specific creation timestamp
        WHEN: Goal is added to conversation
        THEN: The creation timestamp should be preserved exactly
        """
        # GIVEN
        conversation = sample_conversation
        specific_timestamp = "2024-01-15T10:30:00.000Z"

        # WHEN
        goal = Goal(
            id="G_timestamped",
            text="Goal with timestamp",
            type="request",
            source_message_id="msg_1",
            created_at=specific_timestamp
        )
        conversation.goals.append(goal)

        # THEN
        retrieved_goal = conversation.goals[0]
        assert retrieved_goal.created_at == specific_timestamp

    def test_should_support_all_four_goal_types(self, sample_conversation):
        """
        GIVEN: The four defined goal types (question, request, offer, suggestion)
        WHEN: Goals of each type are created
        THEN: All types should be supported and preserved correctly
        """
        # GIVEN
        conversation = sample_conversation
        goal_types = ["question", "request", "offer", "suggestion"]

        # WHEN
        for i, goal_type in enumerate(goal_types):
            goal = Goal(
                id=f"G_{i}_{goal_type}",
                text=f"A {goal_type} goal",
                type=goal_type,
                source_message_id=f"msg_{i}",
                created_at=datetime.now().isoformat()
            )
            conversation.goals.append(goal)

        # THEN
        assert len(conversation.goals) == 4

        retrieved_types = [goal.type for goal in conversation.goals]
        for goal_type in goal_types:
            assert goal_type in retrieved_types