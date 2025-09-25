"""
Backend Isolated Tests - Tests that don't require external APIs
Testing core data models and business logic without external dependencies
"""

import pytest
from datetime import datetime
from backend.models import Goal, Message, Conversation


@pytest.mark.unit
class TestBackendIsolated:
    """Tests that run without external dependencies"""
    
    def test_goal_model_creation(self):
        """Test Goal model can be created and validated"""
        goal = Goal(
            id="test_goal_1",
            text="Write a story about robots",
            type="request",
            source_message_id="msg_1",
            created_at=datetime.now().isoformat()
        )
        
        assert goal.id == "test_goal_1"
        assert goal.text == "Write a story about robots"
        assert goal.type == "request"
        assert goal.status is None
        assert goal.locked is False
        assert goal.completed is False
        
    def test_goal_model_with_status(self):
        """Test Goal model with status updates"""
        goal = Goal(
            id="test_goal_2",
            text="Explain quantum physics",
            type="question",
            status="confirmed",
            locked=True,
            completed=False,
            source_message_id="msg_2",
            created_at=datetime.now().isoformat()
        )
        
        assert goal.status == "confirmed"
        assert goal.locked is True
        assert goal.completed is False
        
    def test_message_model_creation(self):
        """Test Message model creation"""
        message = Message(
            id="msg_1",
            content="Hello, please help me write code",
            role="user",
            timestamp=datetime.now().isoformat()
        )
        
        assert message.id == "msg_1"
        assert message.content == "Hello, please help me write code"
        assert message.role == "user"
        assert len(message.goals) == 0
        
    def test_conversation_model_creation(self):
        """Test Conversation model creation"""
        conversation = Conversation(id="test_conv")
        
        assert conversation.id == "test_conv"
        assert len(conversation.messages) == 0
        assert len(conversation.goals) == 0
        assert conversation.pipeline_settings["infer"] is True
        assert conversation.pipeline_settings["merge"] is True
        assert conversation.pipeline_settings["evaluate"] is True
        
    def test_conversation_with_messages_and_goals(self):
        """Test Conversation with messages and goals"""
        # Create goals
        goal1 = Goal(
            id="g1",
            text="Write code",
            type="request",
            source_message_id="m1",
            created_at=datetime.now().isoformat()
        )
        
        goal2 = Goal(
            id="g2",
            text="Explain the code",
            type="question",
            source_message_id="m1",
            created_at=datetime.now().isoformat()
        )
        
        # Create message with goals
        message = Message(
            id="m1",
            content="Write and explain some Python code",
            role="user",
            timestamp=datetime.now().isoformat(),
            goals=[goal1, goal2]
        )
        
        # Create conversation
        conversation = Conversation(
            id="test_conv",
            messages=[message],
            goals=[goal1, goal2]
        )
        
        assert len(conversation.messages) == 1
        assert len(conversation.goals) == 2
        assert conversation.messages[0].content == "Write and explain some Python code"
        assert conversation.goals[0].text == "Write code"
        assert conversation.goals[1].text == "Explain the code"
        
    def test_goal_serialization(self):
        """Test Goal model serialization"""
        goal = Goal(
            id="ser_test",
            text="Serialize this goal",
            type="suggestion",
            status="ignored",
            source_message_id="msg_ser",
            created_at="2024-01-01T12:00:00"
        )
        
        goal_dict = goal.model_dump()
        
        expected_keys = {"id", "text", "type", "status", "locked", "completed", "source_message_id", "created_at"}
        assert set(goal_dict.keys()) == expected_keys
        assert goal_dict["id"] == "ser_test"
        assert goal_dict["text"] == "Serialize this goal"
        assert goal_dict["type"] == "suggestion"
        assert goal_dict["status"] == "ignored"
        
    def test_pipeline_settings_modification(self):
        """Test modifying pipeline settings"""
        conversation = Conversation(id="pipeline_test")
        
        # Disable merge stage
        conversation.pipeline_settings["merge"] = False
        assert conversation.pipeline_settings["merge"] is False
        assert conversation.pipeline_settings["infer"] is True
        assert conversation.pipeline_settings["evaluate"] is True
        
        # Disable all stages
        conversation.pipeline_settings = {
            "infer": False,
            "merge": False,
            "evaluate": False
        }
        
        assert all(not value for value in conversation.pipeline_settings.values())
