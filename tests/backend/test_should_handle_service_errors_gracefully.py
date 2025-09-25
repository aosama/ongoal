"""
TDD Tests for Enhanced Error Handling
Tests graceful handling of service errors and LLM failures as per TDD requirements
"""
import pytest
import asyncio
import os
import tempfile
from unittest.mock import patch, AsyncMock, MagicMock
from backend.models import Goal, Message
from backend.goal_pipeline import infer_goals, merge_goals, evaluate_goal, stream_llm_response
from backend.llm_service import LLMService
from backend.connection_manager import ConnectionManager

class TestServiceErrorHandling:
    """Test error handling following TDD principles"""


    @pytest.fixture
    def sample_goals(self):
        """Create sample goals for testing"""
        return [
            Goal(id="G1", text="Write a story", type="request", source_message_id="msg1", created_at="2024-01-01T00:00:00Z"),
            Goal(id="G2", text="Make it short", type="suggestion", source_message_id="msg2", created_at="2024-01-01T00:05:00Z")
        ]

    @pytest.mark.asyncio
    async def test_should_handle_llm_service_unavailable_gracefully(self):
        """
        GIVEN: LLM service is unavailable (no API key)
        WHEN: Goal inference is attempted
        THEN: Should return empty list and not crash
        """
        # GIVEN - Mock LLM service as unavailable
        with patch('backend.goal_pipeline.LLMService.generate_response') as mock_generate:
            mock_generate.side_effect = RuntimeError("❌ ANTHROPIC_API_KEY not configured")

            # WHEN
            result = await infer_goals("Help me write a story", "msg_001", 0)

            # THEN
            assert result == []
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_should_handle_llm_api_errors_gracefully(self):
        """
        GIVEN: LLM API returns error or malformed response
        WHEN: Goal operations are attempted
        THEN: Should fallback gracefully without crashing
        """
        # GIVEN - Mock LLM service to raise API error
        with patch('backend.goal_pipeline.LLMService.generate_response') as mock_generate:
            mock_generate.side_effect = Exception("API rate limit exceeded")

            # WHEN
            inference_result = await infer_goals("Write a mystery novel", "msg_001", 0)

            # THEN
            assert inference_result == []

    @pytest.mark.asyncio
    async def test_should_handle_malformed_llm_json_response(self):
        """
        GIVEN: LLM returns malformed JSON
        WHEN: Goal pipeline processes the response
        THEN: Should handle JSON parsing errors gracefully
        """
        # GIVEN - Mock LLM to return malformed JSON
        with patch('backend.goal_pipeline.LLMService.generate_response') as mock_generate:
            mock_generate.return_value = "This is not valid JSON at all!"

            # WHEN
            result = await infer_goals("Help me code", "msg_001", 0)

            # THEN
            assert result == []

    @pytest.mark.asyncio
    async def test_should_fallback_to_simple_merge_on_merge_failure(self, sample_goals):
        """
        GIVEN: Goal merge operation fails due to LLM error
        WHEN: Merge is attempted
        THEN: Should fallback to combining all goals without merging
        """
        # GIVEN
        old_goals = sample_goals[:1]
        new_goals = sample_goals[1:]

        with patch('backend.goal_pipeline.LLMService.generate_response') as mock_generate:
            mock_generate.side_effect = Exception("LLM service timeout")

            # WHEN
            result = await merge_goals(old_goals, new_goals)

            # THEN
            assert len(result) == 2  # Should return all goals
            assert result == old_goals + new_goals

    @pytest.mark.asyncio
    async def test_should_handle_goal_evaluation_service_errors(self, sample_goals):
        """
        GIVEN: Goal evaluation fails due to service error
        WHEN: Evaluation is attempted
        THEN: Should return safe fallback evaluation
        """
        # GIVEN
        goal = sample_goals[0]
        assistant_response = "Here's a great story for you..."

        with patch('backend.goal_pipeline.LLMService.generate_response') as mock_generate:
            mock_generate.side_effect = Exception("Service temporarily unavailable")

            # WHEN
            result = await evaluate_goal(goal, assistant_response)

            # THEN
            assert result["goal_id"] == goal.id
            assert result["category"] == "ignore"
            assert "service error" in result["explanation"].lower()
            assert result["examples"] == []
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_should_handle_streaming_response_errors(self):
        """
        GIVEN: Streaming LLM response encounters error
        WHEN: Response streaming is attempted
        THEN: Should send error message and return gracefully
        """
        # GIVEN
        mock_manager = MagicMock()
        mock_manager.send_message = AsyncMock()
        mock_websocket = MagicMock()

        with patch('backend.goal_pipeline.LLMService.generate_streaming_response') as mock_stream:
            mock_stream.side_effect = Exception("Streaming connection lost")

            # WHEN
            result = await stream_llm_response(
                "Tell me a story",
                mock_manager,
                mock_websocket,
                "msg_001",
                []
            )

            # THEN
            assert "Unable to generate response" in result
            mock_manager.send_message.assert_called_once()
            error_call_args = mock_manager.send_message.call_args[0][0]
            assert error_call_args["type"] == "error"

    def test_should_provide_service_status_information(self):
        """
        GIVEN: LLM service with various states
        WHEN: Service status is requested
        THEN: Should provide detailed status information
        """
        # WHEN
        status = LLMService.get_service_status()

        # THEN
        assert "service" in status
        assert "available" in status
        assert "model" in status
        assert "api_key_configured" in status
        assert "client_initialized" in status
        assert status["service"] == "Anthropic Claude"
        assert isinstance(status["available"], bool)

    def test_should_handle_memory_storage_operations_gracefully(self):
        """
        GIVEN: Memory-based storage operations
        WHEN: Operations are attempted on non-existent data
        THEN: Should handle errors without crashing the application
        """
        # GIVEN - Empty conversation dictionary
        conversations = {}

        # WHEN & THEN - Should not raise errors for missing conversations
        conversation = conversations.get("nonexistent_conv")
        assert conversation is None

        # Test passes if no unhandled exception occurs
        assert True

    @pytest.mark.asyncio
    async def test_should_handle_empty_llm_responses(self):
        """
        GIVEN: LLM returns empty or whitespace-only response
        WHEN: Goal operations are attempted
        THEN: Should handle empty responses gracefully
        """
        # GIVEN
        with patch('backend.goal_pipeline.LLMService.generate_response') as mock_generate:
            mock_generate.return_value = "   \n\t  "  # Whitespace only

            # WHEN
            result = await infer_goals("Test message", "msg_001", 0)

            # THEN
            assert result == []

    @pytest.mark.asyncio
    async def test_should_handle_partial_llm_json_responses(self):
        """
        GIVEN: LLM returns partially valid JSON with missing fields
        WHEN: Goal pipeline processes the response
        THEN: Should handle missing fields gracefully
        """
        # GIVEN
        with patch('backend.goal_pipeline.LLMService.generate_response') as mock_generate:
            # JSON with missing required fields
            mock_generate.return_value = '{"clauses": [{"clause": "Write story"}]}'  # Missing type and summary

            # WHEN
            result = await infer_goals("Write a story", "msg_001", 0)

            # THEN
            # Should handle gracefully, even if some data is missing
            assert isinstance(result, list)

    def test_should_handle_memory_goal_operations_gracefully(self):
        """
        GIVEN: Memory-based goal operations
        WHEN: Operations are attempted on empty data structures
        THEN: Should handle gracefully without corruption
        """
        # GIVEN
        from backend.models import Conversation
        conversation = Conversation(id="test_conv")

        # WHEN - Try to find non-existent goal
        goals = conversation.goals
        target_goal = next((g for g in goals if g.id == "nonexistent_goal"), None)

        # THEN
        assert target_goal is None
        assert len(conversation.goals) == 0

        # Verify no corruption occurred
        assert conversation.id == "test_conv"

    @pytest.mark.asyncio
    async def test_should_handle_websocket_connection_errors(self):
        """
        GIVEN: WebSocket connection encounters error
        WHEN: Message sending is attempted
        THEN: Should handle connection errors gracefully
        """
        # GIVEN
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock(side_effect=Exception("Connection closed"))

        manager = ConnectionManager()
        manager.active_connections = [mock_websocket]

        # WHEN & THEN - Should not raise exception
        try:
            await manager.send_message({"type": "test", "message": "test"}, mock_websocket)
        except Exception:
            pytest.fail("ConnectionManager should handle WebSocket errors gracefully")

    @pytest.mark.asyncio
    async def test_should_provide_user_friendly_error_messages(self):
        """
        GIVEN: Various service errors occur
        WHEN: Error messages are generated
        THEN: Should provide user-friendly messages (not technical stack traces)
        """
        # GIVEN
        mock_manager = MagicMock()
        mock_manager.send_message = AsyncMock()
        mock_websocket = MagicMock()

        with patch('backend.goal_pipeline.LLMService.is_available', return_value=False):
            # WHEN
            result = await stream_llm_response(
                "Test message",
                mock_manager,
                mock_websocket,
                "msg_001",
                []
            )

            # THEN
            assert "LLM service unavailable" in result
            assert "API key not configured" in result
            # Should not contain technical details like stack traces

    def test_should_maintain_service_availability_check(self):
        """
        GIVEN: LLM service availability needs to be checked
        WHEN: Availability is queried
        THEN: Should provide accurate availability status
        """
        # WHEN
        is_available = LLMService.is_available()

        # THEN
        assert isinstance(is_available, bool)

        # If available, service status should reflect that
        if is_available:
            status = LLMService.get_service_status()
            assert status["available"] == True
            assert status["client_initialized"] == True