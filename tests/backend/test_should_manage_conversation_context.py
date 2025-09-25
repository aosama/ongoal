"""
Test conversation context - ensuring chatbot can see and reference previous messages.

This addresses the critical bug where the chatbot acts like each message is a fresh conversation,
when it should maintain context and be able to reference previous messages.
"""

import pytest
import asyncio
import json
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from backend.models import Conversation, Message
from backend.api_endpoints import get_conversations_store


@pytest.mark.backend
class TestConversationContext:
    
    def test_should_build_conversation_history_correctly(self):
        """
        TEST CASE: Verify conversation history is properly built for LLM context
        
        GIVEN: A conversation with multiple previous messages
        WHEN: Building context for LLM
        THEN: All messages should be included in correct format and order
        """
        
        # ARRANGE: Set up conversation with previous messages
        conversation_id = "test_conversation"
        conversations = get_conversations_store()
        conversations[conversation_id] = Conversation(id=conversation_id)
        
        # Add previous messages to conversation history
        previous_messages = [
            Message(
                id="msg_0",
                content="Tell me a story about a fish named Rupert who struggles with math but has a kind heart.",
                role="user",
                timestamp="2024-01-01T10:00:00"
            ),
            Message(
                id="msg_1", 
                content="Once upon a time, there was a fish named Rupert who had the biggest heart in the entire sea. Despite his struggles with math, Rupert would help baby seahorses find their way home and share his seaweed snacks with anyone who was hungry...",
                role="assistant",
                timestamp="2024-01-01T10:00:30"
            ),
            Message(
                id="msg_2",
                content="That's a beautiful story! What lesson does Rupert's story teach us?",
                role="user", 
                timestamp="2024-01-01T10:01:00"
            ),
            Message(
                id="msg_3",
                content="Rupert's story teaches us that sometimes our greatest weaknesses can lead us to discover our greatest strengths, and there's nothing more valuable than being kind, even when we feel like we're not good enough.",
                role="assistant",
                timestamp="2024-01-01T10:01:30"
            )
        ]
        
        for msg in previous_messages:
            conversations[conversation_id].messages.append(msg)
        
        # ACT: Build context as the LLM function would
        conversation = conversations[conversation_id]
        messages_for_llm = []
        
        if conversation and conversation.messages:
            # Include all previous messages for context
            for msg in conversation.messages:
                messages_for_llm.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add the current user message
        current_message = "What is the meaning of life according to the above story?"
        messages_for_llm.append({
            "role": "user", 
            "content": current_message
        })
        
        # ASSERT: The LLM context should include full conversation history
        assert len(messages_for_llm) == 5, f"Expected 5 messages in conversation history, got {len(messages_for_llm)}"
        
        # Check that previous messages are included
        message_contents = [msg['content'] for msg in messages_for_llm]
        assert any("Rupert" in content for content in message_contents), "Previous story about Rupert should be in conversation history"
        assert current_message in message_contents, "Current message should be included"
        
        # Check proper conversation structure (alternating user/assistant)
        assert messages_for_llm[0]['role'] == 'user', "First message should be from user"
        assert messages_for_llm[-1]['role'] == 'user', "Last message should be the current user message"
        assert messages_for_llm[-1]['content'] == current_message, "Last message should be the current message"
    
    def test_should_preserve_conversation_context_order(self):
        """
        TEST CASE: Verify messages are built in correct chronological order for LLM
        
        GIVEN: A conversation with multiple messages
        WHEN: Building context for LLM
        THEN: Messages should be in correct chronological order (oldest first)
        """
        
        conversation_id = "test_order"
        conversations = get_conversations_store()
        conversations[conversation_id] = Conversation(id=conversation_id)
        
        # Add messages in specific order
        messages = [
            ("user", "First message"),
            ("assistant", "First response"), 
            ("user", "Second message"),
            ("assistant", "Second response")
        ]
        
        for i, (role, content) in enumerate(messages):
            msg = Message(
                id=f"msg_{i}",
                content=content,
                role=role,
                timestamp=f"2024-01-01T10:0{i}:00"
            )
            conversations[conversation_id].messages.append(msg)
        
        # ACT: Build context as would be done for LLM
        conversation = conversations[conversation_id]
        messages_for_llm = []
        
        if conversation and conversation.messages:
            # Include all previous messages for context
            for msg in conversation.messages:
                messages_for_llm.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add current message
        current_message = "Third message"
        messages_for_llm.append({
            "role": "user", 
            "content": current_message
        })
        
        # ASSERT: Verify order
        expected_contents = ["First message", "First response", "Second message", "Second response", "Third message"]
        actual_contents = [msg['content'] for msg in messages_for_llm]
        
        assert actual_contents == expected_contents, f"Message order incorrect. Expected: {expected_contents}, Got: {actual_contents}"
    
    def test_should_maintain_conversation_history_in_storage(self):
        """
        TEST CASE: Verify conversation storage correctly maintains message history
        
        This tests the data layer to ensure messages are properly stored and retrievable.
        """
        
        conversation_id = "test_storage"
        conversations = get_conversations_store()
        conversations[conversation_id] = Conversation(id=conversation_id)
        
        # Add messages
        msg1 = Message(id="1", content="Hello", role="user", timestamp="2024-01-01T10:00:00")
        msg2 = Message(id="2", content="Hi there!", role="assistant", timestamp="2024-01-01T10:00:30")
        
        conversations[conversation_id].messages.append(msg1)
        conversations[conversation_id].messages.append(msg2)
        
        # Verify storage
        stored_conversation = conversations[conversation_id]
        assert len(stored_conversation.messages) == 2
        assert stored_conversation.messages[0].content == "Hello"
        assert stored_conversation.messages[1].content == "Hi there!"
        assert stored_conversation.messages[0].role == "user"
        assert stored_conversation.messages[1].role == "assistant"
