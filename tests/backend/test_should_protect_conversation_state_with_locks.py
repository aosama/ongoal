"""Tests for ConversationRepository with async locks."""
import pytest
import asyncio
from backend.repository import ConversationRepository


class TestConversationRepository:
    def test_should_store_and_retrieve_conversation(self):
        repo = ConversationRepository()
        conv = repo.create("test-1")
        assert conv.id == "test-1"
        assert repo.get("test-1") is conv

    def test_should_return_none_for_missing_conversation(self):
        repo = ConversationRepository()
        assert repo.get("nonexistent") is None

    def test_should_reset_conversation(self):
        repo = ConversationRepository()
        c = repo.create("test-2")
        c.messages.append("fake")
        repo.reset("test-2")
        assert repo.get("test-2").messages == []

    def test_should_delete_conversation(self):
        repo = ConversationRepository()
        repo.create("test-3")
        repo.delete("test-3")
        assert repo.get("test-3") is None

    def test_should_list_all_ids(self):
        repo = ConversationRepository()
        repo.create("a")
        repo.create("b")
        assert sorted(repo.all_ids()) == ["a", "b"]

    @pytest.mark.asyncio
    async def test_should_allow_concurrent_reads_on_different_conversations(self):
        repo = ConversationRepository()
        repo.create("a")
        repo.create("b")

        async def read(conv_id):
            return repo.get(conv_id)

        results = await asyncio.gather(read("a"), read("b"))
        assert results[0].id == "a"
        assert results[1].id == "b"

    @pytest.mark.asyncio
    async def test_should_lock_prevents_race_on_concurrent_mutations(self):
        import asyncio
        from backend.models import Goal

        repo = ConversationRepository()
        repo.create("race-test")

        async def append_goal(idx):
            async with repo.with_lock("race-test"):
                conv = repo.get("race-test")
                conv.goals.append(Goal(id=f"G{idx}", text=f"goal {idx}", type="request", source_message_id="m"))
                await asyncio.sleep(0.01)

        await asyncio.gather(*(append_goal(i) for i in range(10)))
        conv = repo.get("race-test")
        assert len(conv.goals) == 10
        ids = {g.id for g in conv.goals}
        assert ids == {f"G{i}" for i in range(10)}
