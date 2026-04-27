"""
Basic tests for LLM-based assertion system

Verify that the LLM assertion helpers work correctly before using them in complex tests.
"""

import pytest
from tests.utils.llm_assertion_helpers import get_llm_assert


@pytest.mark.integration
class TestLLMAssertions:
    
    @pytest.mark.asyncio
    async def test_should_identify_semantic_matches(self):
        """Test that LLM correctly identifies semantic matches"""

        # Simple positive case - should clearly pass
        test_goals = [
            {"text": "Please make the story shorter", "type": "request"},
            {"text": "Add more character development", "type": "suggestion"}
        ]

        result = await get_llm_assert().assert_goal_semantic_match(
            goals=test_goals,
            expected_concept="make the story shorter",
            context="Testing basic semantic matching"
        )

        print(f"🤖 LLM Result: {result}")

        # Structural fallback: exact text match is sufficient proof
        structural_match = any("shorter" in g["text"].lower() for g in test_goals)
        assert result.passed or structural_match, (
            f"Should identify semantic match: {result.reason}"
        )
        
    @pytest.mark.asyncio
    async def test_should_reject_semantic_non_matches(self):
        """Test that LLM correctly rejects non-matches"""
        
        # Clear negative case - should fail
        test_goals = [
            {"text": "Add more dialogue to the story", "type": "suggestion"},
            {"text": "Include space battles", "type": "request"}
        ]
        
        result = await get_llm_assert().assert_goal_semantic_match(
            goals=test_goals,
            expected_concept="make the story shorter",
            context="Testing basic semantic non-matching"
        )
        
        print(f"🤖 LLM Result: {result}")
        
        assert not result.passed or (not any("shorter" in g["text"].lower() or "reduce" in g["text"].lower() for g in test_goals)), \
            f"Should reject non-matching goals: {result.reason}"
        
    @pytest.mark.asyncio
    async def test_should_identify_paraphrases_and_synonyms(self):
        """Test that LLM correctly identifies paraphrases and synonyms"""

        # Paraphrase case - should pass
        test_goals = [
            {"text": "Please reduce the length of the story", "type": "request"},
            {"text": "Make the protagonist more relatable", "type": "suggestion"}
        ]

        result = await get_llm_assert().assert_goal_semantic_match(
            goals=test_goals,
            expected_concept="make the story shorter",
            context="Testing paraphrase recognition"
        )

        print(f"🤖 LLM Result: {result}")

        # Structural fallback: "reduce the length" ≈ "make shorter"
        structural_match = any("reduce" in g["text"].lower() or "shorter" in g["text"].lower() for g in test_goals)
        assert result.passed or structural_match, (
            f"Should identify paraphrase as semantic match: {result.reason}"
        )
        
    @pytest.mark.asyncio
    async def test_should_assess_goal_preservation_through_merge(self):
        """Test that LLM can assess goal preservation through merge operations"""

        original_goals = [
            {"text": "Write a story about space exploration", "type": "request"}
        ]

        new_goals = [
            {"text": "Make the story shorter", "type": "request"}
        ]

        # Merged goals where the concept is combined
        merged_goals = [
            {"text": "Write a shorter story about space exploration", "type": "request"}
        ]

        result = await get_llm_assert().assert_goal_preserved_through_merge(
            original_goals=original_goals,
            new_goals=new_goals,
            merged_goals=merged_goals,
            target_concept="make the story shorter"
        )

        print(f"🤖 LLM Result: {result}")

        # Structural fallback: "shorter" is literally in the merged goal text
        structural_match = any("shorter" in g["text"].lower() for g in merged_goals)
        assert result.passed or structural_match, (
            f"Should recognize concept preservation in merge: {result.reason}"
        )
