"""
Conversation Repository — Centralized, thread-safe in-memory storage.

Provides atomic operations for conversation state with async locks
per conversation ID, eliminating race conditions in concurrent
WebSocket + REST access.
"""

import asyncio
from typing import Dict, Optional

from backend.models import Conversation


class ConversationRepository:
    """Thread-safe in-memory conversation store.

    Each conversation ID has its own asyncio.Lock, allowing concurrent
    access to *different* conversations while serializing access to
    the *same* conversation.
    """

    def __init__(self):
        self._store: Dict[str, Conversation] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, conversation_id: str) -> asyncio.Lock:
        """Return (and create if absent) the lock for a specific conversation."""
        lock = self._locks.get(conversation_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[conversation_id] = lock
        return lock

    def create(self, conversation_id: str) -> Conversation:
        """Create a new empty conversation and return it."""
        conversation = Conversation(id=conversation_id)
        self._store[conversation_id] = conversation
        return conversation

    def get(self, conversation_id: str) -> Optional[Conversation]:
        """Get existing conversation or None."""
        return self._store.get(conversation_id)

    def get_or_create(self, conversation_id: str) -> Conversation:
        """Get or create a conversation."""
        conversation = self._store.get(conversation_id)
        if conversation is None:
            conversation = self.create(conversation_id)
        return conversation

    def reset(self, conversation_id: str) -> Conversation:
        """Reset conversation to empty state, preserving the ID."""
        conversation = Conversation(id=conversation_id)
        self._store[conversation_id] = conversation
        # Clean up orphan lock if any
        self._locks.pop(conversation_id, None)
        return conversation

    def delete(self, conversation_id: str) -> bool:
        """Remove conversation and its lock. Returns True if existed."""
        existed = conversation_id in self._store
        self._store.pop(conversation_id, None)
        self._locks.pop(conversation_id, None)
        return existed

    def all_ids(self) -> list[str]:
        """Return list of all stored conversation IDs."""
        return list(self._store.keys())

    def with_lock(self, conversation_id: str):
        """Return the asyncio.Lock for a conversation.

        Usage:
            async with repo.with_lock("default"):
                conv = repo.get_or_create("default")
                conv.goals.append(new_goal)
        """
        return self._get_lock(conversation_id)
