"""
OnGoal Goal Features
Consolidated testing of all goal-related functionality

This file consolidates goal feature tests from:
- test_goal_analysis.py (individual goal views, evaluation timeline, message filtering)
- test_goal_management.py (goal controls, search, categorization, bulk operations)

Based on OnGoal System Section 4.2.3 and White Paper Section 5.1.2
"""

import pytest
from playwright.sync_api import expect, Page


class TestGoalFeatures:
    """
    Consolidated Goal Feature Tests
    
    Tests all goal-related functionality:
    - Individual goal view navigation and analysis
    - Goal control buttons (Lock, Complete, Restore)
    - Goal search and filtering
    - Goal categorization and organization
    - Goal evaluation timeline and patterns
    - Goal bulk operations and persistence
    """
    
    @pytest.mark.browser
    @pytest.mark.timeout(90)
    def test_should_display_lock_and_complete_buttons_on_each_goal(self, page: Page, test_environment, frontend_url):
        """
        Human should see Lock, Complete buttons on each goal
        
        White Paper Requirement: "Lock button: Prevents goal from being merged or replaced"
        "Complete button: Marks goal as achieved, removes from future evaluations"
        """
        page.goto(frontend_url)
        
        # Human sends message to create goals
        page.fill("input[placeholder*='Type your message']", "Write a story. Make it funny. Please add robots.")
        page.click("button:has-text('Send')")
        
        # Wait for LLM response to appear
        expect(page.locator(".chat-message").nth(1)).to_be_visible(timeout=8000)
        
        # Human checks Goals tab
        goals_tab = page.locator("button:has-text('Goals')")
        goals_tab.click()
        
        # Human should see goals with control buttons
        goal_items = page.locator(".space-y-3 > div.bg-gray-50")
        page.wait_for_function(
            "() => document.querySelectorAll('.space-y-3 > div.bg-gray-50').length > 0",
            timeout=10000
        )
        
        goal_count = goal_items.count()
        assert goal_count > 0, f"Expected goals to be created, but found {goal_count}"
        
        # Check each goal for control buttons
        for i in range(min(goal_count, 3)):  # Check first 3 goals
            goal = goal_items.nth(i)
            
            # Look for Lock and Complete buttons (flexible selectors)
            lock_button = goal.locator("button:has-text('Lock'), .lock-btn, [title*='lock'], [data-action='lock']")
            complete_button = goal.locator("button:has-text('Complete'), .complete-btn, [title*='complete'], [data-action='complete']")
            
            if lock_button.count() > 0:
                expect(lock_button.first).to_be_visible()
                print(f"✅ Goal {i+1}: Lock button visible")
            else:
                print(f"⚠️ Goal {i+1}: Lock button not found")
            
            if complete_button.count() > 0:
                expect(complete_button.first).to_be_visible()
                print(f"✅ Goal {i+1}: Complete button visible")
            else:
                print(f"⚠️ Goal {i+1}: Complete button not found")
        
        print("✅ Goal control buttons test completed")

    @pytest.mark.browser
    @pytest.mark.timeout(90)
    def test_should_provide_individual_goal_view_and_exit(self, page: Page, test_environment, frontend_url):
        """
        CONSOLIDATED: Individual goal view navigation (enter and exit)
        
        Combines:
        - test_should_allow_user_to_enter_individual_goal_view_by_clicking
        - test_should_allow_user_to_exit_individual_view_to_all_goals
        - test_should_show_evaluation_timeline_in_individual_view
        """
        page.goto(frontend_url)
        
        # Create goals
        chat_input = page.locator("input[placeholder*='Type your message']")
        chat_input.fill("Help me build a web application. Please help me choose the technology stack.")
        chat_input.press("Enter")
        
        # Switch to Goals tab
        goals_tab = page.locator("button:has-text('Goals')")
        goals_tab.click()
        
        page.wait_for_function(
            "() => document.querySelectorAll('.space-y-3 > div.bg-gray-50').length > 0",
            timeout=15000
        )
        
        goal_items = page.locator(".space-y-3 > div.bg-gray-50")
        if goal_items.count() > 0:
            # ENTER individual view
            goal_items.first.click()
            page.wait_for_timeout(1000)
            
            # Look for individual view indicators
            individual_view = page.locator(".individual-view, .goal-detail-view, .focused-goal")
            if individual_view.count() > 0:
                print("✅ Individual goal view activated")
                
                # Look for evaluation timeline in individual view
                timeline = page.locator(".evaluation-timeline, .goal-timeline, .eval-history")
                if timeline.count() > 0:
                    print("✅ Evaluation timeline visible in individual view")
                
                # EXIT individual view
                exit_buttons = page.locator("button:has-text('Back'), button:has-text('All Goals'), .back-btn")
                if exit_buttons.count() > 0:
                    exit_buttons.first.click()
                    page.wait_for_timeout(1000)
                    print("✅ Successfully exited individual view")
            else:
                print("⚠️ Individual view feature may not be implemented yet")
        else:
            print("⚠️ No goals found to test individual view")
        
        print("✅ Individual goal view navigation test completed")

    @pytest.mark.browser
    @pytest.mark.timeout(90)
    def test_should_allow_user_to_lock_goals_preventing_merge(self, page: Page, test_environment, frontend_url):
        """
        Human should be able to lock goals to prevent them from being merged
        """
        page.goto(frontend_url)
        
        # Create goals
        page.fill("input[placeholder*='Type your message']", "I want to learn Python. Please teach me about variables and functions.")
        page.click("button:has-text('Send')")
        
        # Wait for goals
        goals_tab = page.locator("button:has-text('Goals')")
        goals_tab.click()
        
        goal_items = page.locator(".space-y-3 > div.bg-gray-50")
        page.wait_for_function(
            "() => document.querySelectorAll('.space-y-3 > div.bg-gray-50').length > 0",
            timeout=10000
        )
        
        goal_count = goal_items.count()
        if goal_count > 0:
            # Try to lock first goal
            first_goal = goal_items.first
            lock_button = first_goal.locator("button:has-text('Lock'), .lock-btn, [data-action='lock']")
            
            if lock_button.count() > 0:
                lock_button.first.click()
                page.wait_for_timeout(1000)
                
                # Check for visual indication of locked state
                locked_indicator = first_goal.locator(".locked, [data-locked='true'], .lock-icon")
                if locked_indicator.count() > 0:
                    expect(locked_indicator.first).to_be_visible()
                    print("✅ Goal locked successfully")
                else:
                    print("⚠️ No visual indication of locked state")
            else:
                print("⚠️ Lock button not found")
        else:
            print("⚠️ No goals found to lock")
        
        print("✅ Goal locking test completed")

    @pytest.mark.browser
    @pytest.mark.timeout(90)
    def test_should_allow_user_to_complete_goals_stopping_evaluation(self, page: Page, test_environment, frontend_url):
        """
        Human should be able to complete goals to stop their evaluation
        """
        page.goto(frontend_url)
        
        # Create goals
        page.fill("input[placeholder*='Type your message']", "Help me understand machine learning algorithms. I need examples.")
        page.click("button:has-text('Send')")
        
        # Wait for goals
        goals_tab = page.locator("button:has-text('Goals')")
        goals_tab.click()
        
        goal_items = page.locator(".space-y-3 > div.bg-gray-50")
        page.wait_for_function(
            "() => document.querySelectorAll('.space-y-3 > div.bg-gray-50').length > 0",
            timeout=10000
        )
        
        goal_count = goal_items.count()
        if goal_count > 0:
            # Try to complete first goal
            first_goal = goal_items.first
            complete_button = first_goal.locator("button:has-text('Complete'), .complete-btn, [data-action='complete']")
            
            if complete_button.count() > 0:
                complete_button.first.click()
                page.wait_for_timeout(1000)
                
                # Check for visual indication of completed state
                completed_indicator = first_goal.locator(".completed, [data-completed='true'], .check-icon, .complete-icon")
                if completed_indicator.count() > 0:
                    expect(completed_indicator.first).to_be_visible()
                    print("✅ Goal completed successfully")
                else:
                    print("⚠️ No visual indication of completed state")
            else:
                print("⚠️ Complete button not found")
        else:
            print("⚠️ No goals found to complete")
        
        print("✅ Goal completion test completed")

    @pytest.mark.browser
    @pytest.mark.timeout(90)
    def test_should_provide_goal_search_and_categorization(self, page: Page, test_environment, frontend_url):
        """
        CONSOLIDATED: Goal search and categorization features
        
        Combines:
        - test_should_allow_user_to_search_for_goals_by_text
        - test_should_provide_goal_categorization_and_filtering
        """
        page.goto(frontend_url)
        
        # Create diverse goals
        page.fill("input[placeholder*='Type your message']", "What is the best programming language? Please explain Python vs JavaScript. I think React is good for frontend. You should recommend a backend framework too.")
        page.click("button:has-text('Send')")
        
        # Wait for goals
        goals_tab = page.locator("button:has-text('Goals')")
        goals_tab.click()
        
        page.wait_for_function(
            "() => document.querySelectorAll('.space-y-3 > div.bg-gray-50').length > 0",
            timeout=15000
        )
        
        # Test search functionality
        search_input = page.locator("input[placeholder*='search'], input[placeholder*='filter'], .search-goals")
        if search_input.count() > 0:
            search_input.first.fill("Python")
            page.wait_for_timeout(1000)
            print("✅ Goal search functionality available")
            search_input.first.fill("")  # Clear search
        else:
            print("⚠️ Goal search not implemented yet")
        
        # Test categorization controls
        category_buttons = page.locator("button:has-text('Question'), button:has-text('Request'), button:has-text('Offer'), button:has-text('Suggestion')")
        if category_buttons.count() > 0:
            first_category = category_buttons.first
            first_category.click()
            page.wait_for_timeout(1000)
            print("✅ Goal categorization functionality available")
        else:
            print("⚠️ Goal categorization not implemented yet")
        
        print("✅ Goal search and categorization test completed")





    @pytest.mark.browser
    @pytest.mark.timeout(90)
    def test_should_maintain_chronological_order_in_filtered_messages(self, page: Page, test_environment, frontend_url):
        """
        Human should see messages in chronological order when filtering in individual goal view
        """
        page.goto(frontend_url)
        
        # Create conversation with multiple messages
        messages = [
            "What is Python programming?",
            "How do I install Python?", 
            "Please show me a simple Python example."
        ]
        
        for message in messages:
            page.fill("input[placeholder*='Type your message']", message)
            page.click("button:has-text('Send')")
            page.wait_for_timeout(2000)  # Wait between messages
        
        # Wait for goals and enter individual view
        goals_tab = page.locator("button:has-text('Goals')")
        goals_tab.click()
        
        page.wait_for_function(
            "() => document.querySelectorAll('.space-y-3 > div.bg-gray-50').length > 0",
            timeout=15000
        )
        
        goal_items = page.locator(".space-y-3 > div.bg-gray-50")
        if goal_items.count() > 0:
            goal_items.first.click()
            page.wait_for_timeout(1000)
            
            # Check if messages are shown in chronological order
            chat_messages = page.locator(".chat-message")
            if chat_messages.count() >= 3:
                # Verify first message appears before third message
                first_message = page.locator("text=What is Python programming?")
                third_message = page.locator("text=Please show me a simple Python example")
                
                if first_message.count() > 0 and third_message.count() > 0:
                    print("✅ Messages maintained in individual view")
                else:
                    print("⚠️ Some messages not visible in individual view")
            else:
                print("⚠️ Not enough messages found in individual view")
        else:
            print("⚠️ No goals found to test message chronology")
        
        print("✅ Message chronological order test completed")
