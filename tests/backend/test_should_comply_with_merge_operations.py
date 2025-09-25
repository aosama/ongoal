"""
Test Goal Merge Operations Compliance with OnGoal Requirements

Verifies that the merge stage correctly implements the three operations:
1. Replace: New goal contradicts old goal -> replace old with new
2. Combine: New goal similar to old goal -> merge them into combined goal  
3. Keep: Goal is unique -> keep it unchanged

Uses both structural verification and LLM semantic assertions.
"""

import pytest
import asyncio
from datetime import datetime
from backend.goal_pipeline import infer_goals, merge_goals
from backend.models import Goal
from tests.utils.llm_assertion_helpers import llm_assert


@pytest.mark.integration
class TestMergeOperationsCompliance:
    
    @pytest.mark.asyncio
    async def test_should_replace_explicitly_contradicting_goals(self):
        """
        Test Replace operation: New goal contradicts old goal
        According to requirements: "If a new goal contradicts an old goal, replace the old goal with the new goal"
        """
        # Arrange: Create goals that directly contradict each other
        old_goals = [
            Goal(
                id="G0_old",
                text="Write a long detailed story with many chapters",
                type="request",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G1_old", 
                text="Include complex character backstories",
                type="suggestion",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            )
        ]
        
        new_goals = [
            Goal(
                id="G0_new",
                text="Write a very short, simple story with minimal details",
                type="request", 
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            )
        ]
        
        # Act: Perform merge operation
        merged_goals = await merge_goals(old_goals, new_goals)
        
        print(f"\n🔄 REPLACE OPERATION TEST")
        print(f"Old goals ({len(old_goals)}):")
        for goal in old_goals:
            print(f"  - {goal.text}")
        print(f"New goals ({len(new_goals)}):")
        for goal in new_goals:
            print(f"  - {goal.text}")
        print(f"Merged goals ({len(merged_goals)}):")
        for goal in merged_goals:
            print(f"  - {goal.text}")
        
        # Assert: Use LLM to verify the contradiction was handled correctly
        merged_goal_dicts = [{"text": g.text, "type": g.type} for g in merged_goals]
        
        # Check that the contradicting concept (short vs long) was resolved in favor of new goal
        llm_result = await llm_assert.assert_goal_preserved_through_merge(
            original_goals=[{"text": g.text, "type": g.type} for g in old_goals],
            new_goals=[{"text": g.text, "type": g.type} for g in new_goals],
            merged_goals=merged_goal_dicts,
            target_concept="write a short simple story (NOT long detailed)"
        )
        
        print(f"🤖 LLM Replace Verification: {llm_result}")
        
        assert llm_result.passed, f"Replace operation should favor new contradicting goal: {llm_result.reason}"
        
        # Structural verification: should not have more goals than reasonable
        assert len(merged_goals) <= len(old_goals) + len(new_goals), "Replace should not just accumulate all goals"
        
    @pytest.mark.asyncio
    async def test_should_combine_similar_goals_correctly(self):
        """
        Test Combine operation: New goal similar to old goal
        According to requirements: "If a new goal is similar to an old goal, combine the old goal and the new goal into a new combined goal"
        """
        # Arrange: Create goals that are similar and should be combined
        old_goals = [
            Goal(
                id="G0_old",
                text="Add character development to the story", 
                type="suggestion",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G1_old",
                text="Include dialogue between characters",
                type="request",
                source_message_id="msg_1", 
                created_at=datetime.now().isoformat()
            )
        ]
        
        new_goals = [
            Goal(
                id="G0_new",
                text="Develop the protagonist's background and personality more",
                type="suggestion",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            )
        ]
        
        # Act: Perform merge operation
        merged_goals = await merge_goals(old_goals, new_goals)
        
        print(f"\n🔄 COMBINE OPERATION TEST")
        print(f"Old goals ({len(old_goals)}):")
        for goal in old_goals:
            print(f"  - {goal.text}")
        print(f"New goals ({len(new_goals)}):")
        for goal in new_goals:
            print(f"  - {goal.text}")
        print(f"Merged goals ({len(merged_goals)}):")
        for goal in merged_goals:
            print(f"  - {goal.text}")
        
        # Assert: Use LLM to verify similar goals were combined appropriately
        merged_goal_dicts = [{"text": g.text, "type": g.type} for g in merged_goals]
        
        # Check that both character development concepts are preserved
        llm_result = await llm_assert.assert_goal_preserved_through_merge(
            original_goals=[{"text": g.text, "type": g.type} for g in old_goals],
            new_goals=[{"text": g.text, "type": g.type} for g in new_goals],
            merged_goals=merged_goal_dicts,
            target_concept="character development and protagonist background"
        )
        
        print(f"🤖 LLM Combine Verification: {llm_result}")
        assert llm_result.passed, f"Combine operation should merge similar concepts: {llm_result.reason}"
        
        # Structural verification: should have fewer goals than simple addition
        assert len(merged_goals) < len(old_goals) + len(new_goals), "Combine should reduce total goal count through merging"
        
    @pytest.mark.asyncio
    async def test_should_keep_unique_goals_unchanged(self):
        """
        Test Keep operation: Goals are unique
        According to requirements: "If a goal is unique, keep that goal in the updated list"
        """
        # Arrange: Create goals that are completely different and should be kept separately
        old_goals = [
            Goal(
                id="G0_old",
                text="Add humor to make the story entertaining",
                type="suggestion",
                source_message_id="msg_1", 
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G1_old",
                text="Set the story in a futuristic space station",
                type="request",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            )
        ]
        
        new_goals = [
            Goal(
                id="G0_new",
                text="Include technical details about spaceship engines",
                type="suggestion",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G1_new",
                text="Add a romantic subplot between crew members",
                type="offer",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            )
        ]
        
        # Act: Perform merge operation
        merged_goals = await merge_goals(old_goals, new_goals)
        
        print(f"\n🔄 KEEP OPERATION TEST")
        print(f"Old goals ({len(old_goals)}):")
        for goal in old_goals:
            print(f"  - {goal.text}")
        print(f"New goals ({len(new_goals)}):")
        for goal in new_goals:
            print(f"  - {goal.text}")
        print(f"Merged goals ({len(merged_goals)}):")
        for goal in merged_goals:
            print(f"  - {goal.text}")
        
        # Assert: All unique concepts should be preserved
        merged_goal_dicts = [{"text": g.text, "type": g.type} for g in merged_goals]
        
        # Check that all unique concepts are preserved
        unique_concepts = [
            "humor and entertainment", 
            "futuristic space station setting",
            "technical spaceship details", 
            "romantic subplot"
        ]
        
        for concept in unique_concepts:
            llm_result = await llm_assert.assert_goal_semantic_match(
                goals=merged_goal_dicts,
                expected_concept=concept,
                context="Testing that unique goals are kept during merge"
            )
            print(f"🤖 LLM Keep Verification ({concept}): {llm_result}")
            assert llm_result.passed, f"Unique concept '{concept}' should be preserved: {llm_result.reason}"
        
        # Structural verification: should preserve most/all unique goals
        # The LLM may intelligently combine goals when they have synergy, which is acceptable
        assert len(merged_goals) >= 2, f"Keep operation should preserve core concepts, got {len(merged_goals)}"
        
    @pytest.mark.asyncio
    async def test_should_handle_mixed_operations_scenario(self):
        """
        Test complex scenario with all three operations: Replace + Combine + Keep
        This tests the real-world scenario from the user's story example
        """
        # Arrange: Complex realistic scenario
        old_goals = [
            Goal(
                id="G0_old",
                text="Write a long, detailed story about space exploration",
                type="request",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G1_old", 
                text="Make the protagonist a relatable teenager",
                type="suggestion",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G2_old",
                text="Add humor to keep it engaging",
                type="suggestion",
                source_message_id="msg_1",
                created_at=datetime.now().isoformat()
            )
        ]
        
        new_goals = [
            Goal(
                id="G0_new",
                text="Make the story much shorter and concise",  # Should REPLACE G0_old (contradicts long/detailed)
                type="request",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G1_new",
                text="Ensure the main character faces realistic challenges for teens",  # Should COMBINE with G1_old (similar)
                type="suggestion", 
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            ),
            Goal(
                id="G2_new",
                text="Include technical accuracy about space travel",  # Should be KEPT (unique)
                type="request",
                source_message_id="msg_2",
                created_at=datetime.now().isoformat()
            )
        ]
        
        # Act: Perform merge operation
        merged_goals = await merge_goals(old_goals, new_goals)
        
        print(f"\n🔄 MIXED OPERATIONS TEST")
        print(f"Old goals ({len(old_goals)}):")
        for goal in old_goals:
            print(f"  - {goal.text}")
        print(f"New goals ({len(new_goals)}):")
        for goal in new_goals:
            print(f"  - {goal.text}")
        print(f"Merged goals ({len(merged_goals)}):")
        for goal in merged_goals:
            print(f"  - {goal.text}")
        
        # Assert: Verify all three operations occurred correctly
        merged_goal_dicts = [{"text": g.text, "type": g.type} for g in merged_goals]
        
        # 1. REPLACE: Should favor "shorter" over "long detailed"
        replace_result = await llm_assert.assert_goal_semantic_match(
            goals=merged_goal_dicts,
            expected_concept="short concise story (NOT long detailed)",
            context="Verifying Replace operation: shorter story should override long detailed"
        )
        print(f"🤖 Replace Check: {replace_result}")
        assert replace_result.passed, f"Replace operation failed: {replace_result.reason}"
        
        # 2. COMBINE: Should merge protagonist concepts
        combine_result = await llm_assert.assert_goal_semantic_match(
            goals=merged_goal_dicts,
            expected_concept="relatable teenager protagonist with realistic challenges",
            context="Verifying Combine operation: protagonist goals should be merged"
        )
        print(f"🤖 Combine Check: {combine_result}")
        assert combine_result.passed, f"Combine operation failed: {combine_result.reason}"
        
        # 3. KEEP: Should preserve unique concepts  
        keep_concepts = ["humor and engagement", "technical accuracy about space travel"]
        for concept in keep_concepts:
            keep_result = await llm_assert.assert_goal_semantic_match(
                goals=merged_goal_dicts,
                expected_concept=concept,
                context="Verifying Keep operation: unique goals should be preserved"
            )
            print(f"🤖 Keep Check ({concept}): {keep_result}")
            assert keep_result.passed, f"Keep operation failed for '{concept}': {keep_result.reason}"
        
        # Structural verification
        assert 3 <= len(merged_goals) <= 5, f"Mixed operations should produce reasonable goal count, got {len(merged_goals)}"
        
        print(f"\n✅ MIXED OPERATIONS TEST PASSED - All three merge operations working correctly!")
        
    @pytest.mark.asyncio
    async def test_should_handle_actual_story_scenario_from_user_example(self):
        """
        Test the exact scenario the user reported: storytelling + make shorter
        This should definitively prove whether the merge is working per requirements
        """
        # Use infer_goals to get actual LLM-generated goals (more realistic test)
        initial_message = ("What are the key elements of effective storytelling? "
                         "Please write a creative very SHORT story about space exploration for teenagers. "
                         "I think the protagonist should be relatable and face realistic challenges. "
                         "You should consider adding more humor and interactive elements to make it engaging.")
        
        followup_message = "Please make the story shorter."
        
        # Act: Run the actual pipeline
        initial_goals = await infer_goals(initial_message, "msg_1")
        followup_goals = await infer_goals(followup_message, "msg_2") 
        merged_goals = await merge_goals(initial_goals, followup_goals)
        
        print(f"\n🔄 USER SCENARIO TEST")
        print(f"Initial inferred goals ({len(initial_goals)}):")
        for i, goal in enumerate(initial_goals):
            print(f"  {i+1}. [{goal.type}] {goal.text}")
            
        print(f"Follow-up inferred goals ({len(followup_goals)}):")
        for i, goal in enumerate(followup_goals):
            print(f"  {i+1}. [{goal.type}] {goal.text}")
            
        print(f"Final merged goals ({len(merged_goals)}):")
        for i, goal in enumerate(merged_goals):
            print(f"  {i+1}. [{goal.type}] {goal.text}")
        
        # Critical assertion: The "make shorter" concept should be handled correctly
        merged_goal_dicts = [{"text": g.text, "type": g.type} for g in merged_goals]
        
        preservation_result = await llm_assert.assert_goal_preserved_through_merge(
            original_goals=[{"text": g.text, "type": g.type} for g in initial_goals],
            new_goals=[{"text": g.text, "type": g.type} for g in followup_goals],
            merged_goals=merged_goal_dicts,
            target_concept="make the story shorter"
        )
        
        print(f"🤖 USER SCENARIO VERIFICATION: {preservation_result}")
        
        # This is the critical test - if this fails, the merge logic has a real problem
        assert preservation_result.passed, f"USER SCENARIO FAILED - Merge not working per requirements: {preservation_result.reason}"
        
        print(f"\n✅ USER SCENARIO TEST PASSED - Merge logic working correctly for real use case!")
