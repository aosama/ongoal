"""
Basic tests for LLM-based assertion system

Verify that the LLM assertion helpers work correctly before using them in complex tests.
"""

import pytest
from tests.utils.llm_assertion_helpers import llm_assert


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
        
        result = await llm_assert.assert_goal_semantic_match(
            goals=test_goals,
            expected_concept="make the story shorter",
            context="Testing basic semantic matching"
        )
        
        print(f"🤖 LLM Result: {result}")
        
        # This should pass since there's an exact match
        assert result.passed, f"Should identify exact semantic match: {result.reason}"
        assert result.confidence in ["high", "medium", "low"], f"Should provide confidence level: {result.confidence}"
        
    @pytest.mark.asyncio
    async def test_should_reject_semantic_non_matches(self):
        """Test that LLM correctly rejects non-matches"""
        
        # Clear negative case - should fail
        test_goals = [
            {"text": "Add more dialogue to the story", "type": "suggestion"},
            {"text": "Include space battles", "type": "request"}
        ]
        
        result = await llm_assert.assert_goal_semantic_match(
            goals=test_goals,
            expected_concept="make the story shorter",
            context="Testing basic semantic non-matching"
        )
        
        print(f"🤖 LLM Result: {result}")
        
        # This should fail since there's no match
        assert not result.passed, f"Should reject non-matching goals: {result.reason}"
        
    @pytest.mark.asyncio
    async def test_should_identify_paraphrases_and_synonyms(self):
        """Test that LLM correctly identifies paraphrases and synonyms"""
        
        # Paraphrase case - should pass
        test_goals = [
            {"text": "Please reduce the length of the story", "type": "request"},
            {"text": "Make the protagonist more relatable", "type": "suggestion"}
        ]
        
        result = await llm_assert.assert_goal_semantic_match(
            goals=test_goals,
            expected_concept="make the story shorter",
            context="Testing paraphrase recognition"
        )
        
        print(f"🤖 LLM Result: {result}")
        
        # This should pass since "reduce the length" means "make shorter"
        assert result.passed, f"Should identify paraphrase as semantic match: {result.reason}"
        
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
        
        result = await llm_assert.assert_goal_preserved_through_merge(
            original_goals=original_goals,
            new_goals=new_goals,
            merged_goals=merged_goals,
            target_concept="make the story shorter"
        )
        
        print(f"🤖 LLM Result: {result}")
        
        # Should recognize that "shorter" was incorporated into the merged goal
        assert result.passed, f"Should recognize concept preservation in merge: {result.reason}"
