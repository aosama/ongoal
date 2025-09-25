"""
Data Model Tests for OnGoal Goal System
Tests data models and utility functions without external dependencies
Note: Goal inference functionality is tested in integration tests without mocking
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from backend.models import Goal


@pytest.mark.unit
class TestGoalDataModels:
    """Tests for Goal data models and utility functions"""

    def test_should_validate_goal_model_correctly(self):
        """Test Goal model validation and default values"""
        goal = Goal(
            id="G1",
            text="Test goal description",
            type="question",
            source_message_id="msg_1",
            created_at="2025-09-19T10:00:00"
        )
        
        assert goal.id == "G1"
        assert goal.text == "Test goal description"
        assert goal.type == "question"
        assert goal.source_message_id == "msg_1"
        assert goal.created_at == "2025-09-19T10:00:00"
        assert goal.locked == False
        assert goal.completed == False
        assert goal.status is None
    
    def test_should_handle_goal_model_with_status(self):
        """Test Goal model with status set"""
        goal = Goal(
            id="G2",
            text="Write a function",
            type="request",
            status="confirmed",
            locked=True,
            completed=True,
            source_message_id="msg_2",
            created_at="2025-09-19T10:05:00"
        )
        
        assert goal.id == "G2"
        assert goal.type == "request"
        assert goal.status == "confirmed"
        assert goal.locked == True
        assert goal.completed == True
    
    def test_should_validate_all_goal_types(self):
        """Test that Goal model accepts all valid goal types"""
        valid_types = ["question", "request", "offer", "suggestion"]
        
        for goal_type in valid_types:
            goal = Goal(
                id=f"G_{goal_type}",
                text=f"Test {goal_type} goal",
                type=goal_type,
                source_message_id="msg_test",
                created_at="2025-09-19T10:00:00"
            )
            assert goal.type == goal_type
    
    def test_should_accept_all_valid_status_values(self):
        """Test that Goal model accepts all valid status values"""
        valid_statuses = ["confirmed", "contradicted", "ignored", None]
        
        for status in valid_statuses:
            goal = Goal(
                id="G_status_test",
                text="Test goal for status",
                type="question",
                status=status,
                source_message_id="msg_status_test",
                created_at="2025-09-19T10:00:00"
            )
            assert goal.status == status
    
    def test_should_serialize_goal_model_to_json(self):
        """Test that Goal model can be serialized to dict/JSON"""
        goal = Goal(
            id="G_serialize",
            text="Test serialization",
            type="request",
            status="confirmed",
            locked=True,
            completed=False,
            source_message_id="msg_serialize",
            created_at="2025-09-19T10:00:00"
        )
        
        # Test dict conversion
        goal_dict = goal.model_dump()
        assert goal_dict["id"] == "G_serialize"
        assert goal_dict["text"] == "Test serialization"
        assert goal_dict["type"] == "request"
        assert goal_dict["status"] == "confirmed"
        assert goal_dict["locked"] == True
        assert goal_dict["completed"] == False
        
        # Test JSON serialization
        goal_json = goal.model_dump_json()
        assert isinstance(goal_json, str)
        
        # Test JSON can be parsed back
        parsed_dict = json.loads(goal_json)
        assert parsed_dict["id"] == "G_serialize"
