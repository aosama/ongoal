"""
TDD Test for Story Follow-up Goals Backend Logic

Tests the scenario:
1. Initial complex message: storytelling elements + story creation with specific requirements
2. Follow-up message: "make the story shorter" 
3. Verify that follow-up goals are properly captured and merged

Uses LLM-based semantic assertions instead of keyword matching for robust testing.

Following TDD: RED -> GREEN -> REFACTOR
"""

import pytest
import asyncio
from datetime import datetime
from backend.goal_pipeline import infer_goals, merge_goals
from backend.models import Goal
from tests.utils.llm_assertion_helpers import llm_assert


@pytest.mark.integration
class TestStoryFollowupGoals:
    
    @pytest.mark.asyncio
    async def test_should_infer_goals_from_initial_story_request(self):
        """
        RED: Test that initial complex story request is properly parsed into goals
        Expected: Should identify multiple goals from the complex request
        """
        # Arrange: The exact message from user scenario
        initial_message = ("What are the key elements of effective storytelling? "
                         "Please write a creative very SHORT story about space exploration for teenagers. "
                         "I think the protagonist should be relatable and face realistic challenges. "
                         "You should consider adding more humor and interactive elements to make it engaging.")
        
        # Act: Infer goals from the initial message
        inferred_goals = await infer_goals(initial_message, "msg_1")
        
        # Assert: Should extract multiple goals from this complex request
        assert len(inferred_goals) > 0, f"Should infer goals from complex message, got: {len(inferred_goals)}"
        
        # Convert to text for analysis
        goal_texts = [goal.text.lower() for goal in inferred_goals]
        all_goals_text = " ".join(goal_texts)
        
        print(f"Initial message inferred {len(inferred_goals)} goals:")
        for i, goal in enumerate(inferred_goals):
            print(f"  Goal {i+1}: [{goal.type}] {goal.text}")
        
        # Should capture key aspects of the request
        assert any("storytelling" in text or "story" in text for text in goal_texts), \
            f"Should capture storytelling request: {goal_texts}"
        
        # Should capture specific requirements (relatable protagonist, humor, etc.)
        assert any("short" in text for text in goal_texts), \
            f"Should capture 'short' requirement: {goal_texts}"
        
        # Should identify different goal types appropriately
        goal_types = [goal.type for goal in inferred_goals]
        assert len(set(goal_types)) > 0, f"Should have goal types: {goal_types}"
        
    @pytest.mark.asyncio
    async def test_should_infer_goals_from_followup_make_shorter_request(self):
        """
        RED: Test that follow-up "make shorter" request is properly inferred as a goal
        Expected: Should identify the modification request as a goal
        """
        # Arrange: Follow-up message asking to make story shorter
        followup_message = "Please make the story shorter."
        
        # Act: Infer goals from follow-up message
        followup_goals = await infer_goals(followup_message, "msg_2")
        
        # Assert: Should capture the "make shorter" goal
        assert len(followup_goals) > 0, f"Should infer goals from 'make shorter' request, got: {len(followup_goals)}"
        
        goal_texts = [goal.text.lower() for goal in followup_goals]
        all_goals_text = " ".join(goal_texts)
        
        print(f"Follow-up message inferred {len(followup_goals)} goals:")
        for i, goal in enumerate(followup_goals):
            print(f"  Goal {i+1}: [{goal.type}] {goal.text}")
        
        # Should capture the "shorter" concept using LLM semantic understanding
        goal_dicts = [{"text": goal.text, "type": goal.type} for goal in followup_goals]
        llm_result = await llm_assert.assert_goal_semantic_match(
            goals=goal_dicts,
            expected_concept="make the story shorter",
            context="Testing follow-up goal inference for story modification requests"
        )
        
        print(f"🤖 LLM Assertion: {llm_result}")
        assert llm_result.passed, f"LLM assertion failed: {llm_result.reason}"
        
        # Should be classified as appropriate goal type (likely "request")
        goal_types = [goal.type for goal in followup_goals]
        assert "request" in goal_types or "suggestion" in goal_types, \
            f"Make shorter should be request or suggestion, got: {goal_types}"
            
    @pytest.mark.asyncio
    async def test_should_handle_story_followup_merge_pipeline(self):
        """
        RED: Test complete pipeline - initial story request + follow-up make shorter
        Expected: Both goals should be properly handled through the merge pipeline
        """
        # Arrange: Simulate the two-message scenario
        initial_message = ("What are the key elements of effective storytelling? "
                         "Please write a creative very SHORT story about space exploration for teenagers. "
                         "I think the protagonist should be relatable and face realistic challenges. "
                         "You should consider adding more humor and interactive elements to make it engaging.")
        
        followup_message = "Please make the story shorter."
        
        # Act: Process both messages through the pipeline
        
        # Step 1: Infer goals from initial message (conversation starts empty)
        initial_goals = await infer_goals(initial_message, "msg_1")
        print(f"\n🎯 Step 1 - Initial goals ({len(initial_goals)}):")
        for goal in initial_goals:
            print(f"  [{goal.type}] {goal.text}")
        
        # Step 2: Infer goals from follow-up message
        followup_goals = await infer_goals(followup_message, "msg_2")
        print(f"\n🎯 Step 2 - Follow-up goals ({len(followup_goals)}):")
        for goal in followup_goals:
            print(f"  [{goal.type}] {goal.text}")
        
        # Step 3: Merge follow-up goals with existing goals
        merged_goals = await merge_goals(initial_goals, followup_goals)
        print(f"\n🎯 Step 3 - Merged goals ({len(merged_goals)}):")
        for goal in merged_goals:
            print(f"  [{goal.type}] {goal.text}")
        
        # Assert: Follow-up goal should be present in final merged results
        assert len(merged_goals) > 0, "Should have merged goals"
        
        merged_texts = [goal.text.lower() for goal in merged_goals]
        all_merged_text = " ".join(merged_texts)
        
        # Critical assertion: "make shorter" concept should be preserved using LLM semantic understanding
        goal_dicts = [{"text": goal.text, "type": goal.type} for goal in merged_goals]
        llm_result = await llm_assert.assert_goal_preserved_through_merge(
            original_goals=[{"text": g.text, "type": g.type} for g in initial_goals],
            new_goals=[{"text": g.text, "type": g.type} for g in followup_goals],
            merged_goals=goal_dicts,
            target_concept="make the story shorter"
        )
        
        print(f"🤖 LLM Assertion: {llm_result}")
        assert llm_result.passed, f"LLM assertion failed: {llm_result.reason}"
        
        # Should still have story-related goals
        assert any("story" in text for text in merged_texts), \
            f"Story-related goals should be preserved: {merged_texts}"
        
        # Verify goal IDs and structure
        goal_ids = [goal.id for goal in merged_goals]
        assert len(set(goal_ids)) == len(goal_ids), f"Goal IDs should be unique: {goal_ids}"
        
    @pytest.mark.asyncio
    async def test_should_handle_story_modification_goals_as_additive(self):
        """
        RED: Test that story modification requests add to rather than replace story goals
        Expected: "Make shorter" should be additional goal, not replacement
        """
        # Arrange: Create scenario where we have existing story goals and add modification
        existing_goals = [
            Goal(
                id="G0_story",
                text="Write a creative short story about space exploration for teenagers",
                type="request",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G1_relatable",
                text="Make the protagonist relatable and face realistic challenges",
                type="suggestion",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            )
        ]
        
        new_goals = [
            Goal(
                id="G2_shorter",
                text="Make the story shorter",
                type="request",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            )
        ]
        
        # Act: Merge the modification goal with existing story goals
        result = await merge_goals(existing_goals, new_goals)
        
        # Assert: Should combine/keep goals appropriately
        assert len(result) >= 2, f"Should preserve multiple goals, got {len(result)}: {[g.text for g in result]}"
        
        result_texts = [goal.text.lower() for goal in result]
        combined_text = " ".join(result_texts)
        
        # Should preserve original story concept
        assert any("story" in text for text in result_texts), \
            f"Should preserve story goal: {result_texts}"
        
        # Should include the modification request
        assert any("shorter" in text or "short" in text for text in result_texts), \
            f"Should include 'make shorter/short' goal: {result_texts}"
        
        print(f"✅ Merged {len(existing_goals)} existing + {len(new_goals)} new = {len(result)} final goals")
        for goal in result:
            print(f"  [{goal.type}] {goal.text}")
            
    @pytest.mark.asyncio
    async def test_should_accumulate_multiple_story_modifications(self):
        """
        RED: Test that multiple story modifications accumulate properly
        Expected: "Make shorter" + "Add more humor" should both be captured
        """
        # Arrange: Initial story request
        initial_goals = await infer_goals(
            "Write a short story about space exploration for teenagers.", "msg_1"
        )
        
        # First modification: make shorter
        shorter_goals = await infer_goals("Please make the story shorter.", "msg_2")
        merged_after_shorter = await merge_goals(initial_goals, shorter_goals)
        
        # Second modification: add humor
        humor_goals = await infer_goals("Also add more humor to make it funnier.", "msg_3")
        final_merged = await merge_goals(merged_after_shorter, humor_goals)
        
        # Assert: All modification requests should be captured
        final_texts = [goal.text.lower() for goal in final_merged]
        combined_text = " ".join(final_texts)
        
        print(f"Final goals after multiple modifications ({len(final_merged)}):")
        for goal in final_merged:
            print(f"  [{goal.type}] {goal.text}")
        
        # Should have story concept
        assert any("story" in text for text in final_texts), \
            f"Should preserve story concept: {final_texts}"
        
        # Should have shorter modification
        assert any("shorter" in text or "short" in text for text in final_texts), \
            f"Should preserve 'shorter/short' modification: {final_texts}"
        
        # Should have humor modification  
        assert any("humor" in text or "funnier" in text for text in final_texts), \
            f"Should preserve humor modification: {final_texts}"
        
        # Should have reasonable number of goals (not just accumulating endlessly)
        assert len(final_merged) <= 6, f"Should merge reasonably, got {len(final_merged)} goals"
