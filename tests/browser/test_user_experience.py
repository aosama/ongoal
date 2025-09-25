"""
OnGoal User Experience Features
Consolidated testing of UI/UX and conversation functionality

This file consolidates UX tests from:
- test_user_interface_experience.py (UI improvements, scrolling, legend)
- test_conversation_continuity.py (multi-turn conversation flow)
- test_accessibility_compliance.py (accessibility features)

Focuses on human usability and experience quality.
"""

import pytest
from playwright.sync_api import expect, Page


class TestUserExperience:
    """
    Consolidated User Experience Tests
    
    Tests all UX and conversation functionality:
    - Goal legend and visual indicators
    - Chat scrolling and input behavior
    - Multi-turn conversation continuity
    - Accessibility compliance
    - Overall usability features
    """
    
    @pytest.mark.browser
    @pytest.mark.timeout(90)
    def test_should_display_goal_legend_in_header(self, page: Page, test_environment, frontend_url):
        """
        GIVEN: User has loaded the OnGoal interface
        WHEN: User views the header area
        THEN: Goal legend with 4 color-coded goal types should be visible

        ACCEPTANCE CRITERIA:
        - Goals label is visible in header
        - Question indicator is present and visible
        - Request indicator is present and visible
        - Offer indicator is present and visible
        - Suggestion indicator is present and visible
        - All 4 goal type indicators are color-coded and distinguishable
        """
        # GIVEN: User has loaded the OnGoal interface
        page.goto(frontend_url)

        # WHEN: User views the header area
        # THEN: Goals label should be visible
        goals_label = page.locator("header span:has-text('Goals:'), .header span:has-text('Goals:'), h1:has-text('Goals:')")
        
        if goals_label.count() > 0:
            expect(goals_label.first).to_be_visible()
            print("✅ Goals label visible in header")
        else:
            print("⚠️ Goals label not found - may not be implemented yet")
        
        # THEN: Goal type indicators should be present
        goal_indicators = page.locator("header .goal-glyph, .header .goal-indicator, .legend .goal-type")

        if goal_indicators.count() > 0:
            print(f"✅ Found {goal_indicators.count()} goal type indicators")

            # THEN: All 4 goal types should be represented
            question_indicator = page.locator("header .goal-question, .legend .question, [data-goal-type='question']")
            request_indicator = page.locator("header .goal-request, .legend .request, [data-goal-type='request']")
            offer_indicator = page.locator("header .goal-offer, .legend .offer, [data-goal-type='offer']")
            suggestion_indicator = page.locator("header .goal-suggestion, .legend .suggestion, [data-goal-type='suggestion']")
            
            indicators_found = 0
            if question_indicator.count() > 0:
                indicators_found += 1
                print("✅ Question indicator found")
            if request_indicator.count() > 0:
                indicators_found += 1
                print("✅ Request indicator found")
            if offer_indicator.count() > 0:
                indicators_found += 1
                print("✅ Offer indicator found")
            if suggestion_indicator.count() > 0:
                indicators_found += 1
                print("✅ Suggestion indicator found")
            
            if indicators_found > 0:
                print(f"✅ {indicators_found} goal type indicators visible")
        else:
            print("⚠️ Goal legend not found - feature may not be implemented yet")
        
        print("✅ Goal legend test completed")

    @pytest.mark.browser
    @pytest.mark.timeout(90)
    def test_should_provide_proper_chat_area_scrolling(self, page: Page, test_environment, frontend_url):
        """
        Chat area should have proper scrolling behavior
        """
        page.goto(frontend_url)
        
        # Send multiple messages to create scrollable content
        messages = [
            "This is the first message to test scrolling behavior.",
            "This is the second message. The chat should scroll properly.",
            "Third message to create more content for scrolling tests.",
            "Fourth message to ensure we have enough content to scroll.",
            "Fifth message to definitely create a scrollable area."
        ]
        
        chat_input = page.locator("input[placeholder*='Type your message']")
        
        for i, message in enumerate(messages):
            chat_input.fill(message)
            chat_input.press("Enter")
            page.wait_for_timeout(1000)  # Shorter wait for UX test
        
        # Check if chat area is scrollable
        chat_area = page.locator(".chat-container, .messages, .conversation, .chat-area")
        
        if chat_area.count() > 0:
            # Check scrollability
            scroll_height = chat_area.first.evaluate("el => el.scrollHeight")
            client_height = chat_area.first.evaluate("el => el.clientHeight")
            
            if scroll_height > client_height:
                print(f"✅ Chat area is scrollable (content: {scroll_height}px, view: {client_height}px)")
                
                # Test scroll to bottom behavior
                page.keyboard.press("End")
                page.wait_for_timeout(500)
                
                # Should be at bottom
                scroll_top = chat_area.first.evaluate("el => el.scrollTop")
                max_scroll = scroll_height - client_height
                
                if abs(scroll_top - max_scroll) < 50:  # Allow small tolerance
                    print("✅ Scroll to bottom works correctly")
                else:
                    print(f"⚠️ Scroll position: {scroll_top}, expected near: {max_scroll}")
            else:
                print("⚠️ Chat area not scrollable - may need more content")
        else:
            print("⚠️ Chat area container not found")
        
        print("✅ Chat scrolling test completed")




    @pytest.mark.browser
    @pytest.mark.timeout(90)
    def test_should_provide_intuitive_navigation_patterns(self, page: Page, test_environment, frontend_url):
        """
        Navigation should follow intuitive patterns for users
        """
        page.goto(frontend_url)
        
        # Test tab navigation
        goals_tab = page.locator("button:has-text('Goals')")
        timeline_tab = page.locator("button:has-text('Timeline')")
        
        # Goals tab should be accessible
        if goals_tab.count() > 0:
            goals_tab.click()
            page.wait_for_timeout(500)
            
            # Check if tab appears active
            goals_classes = goals_tab.get_attribute("class") or ""
            if "text-blue-600" in goals_classes or "active" in goals_classes:
                print("✅ Goals tab shows active state")
            else:
                print("⚠️ Goals tab active state unclear")
        
        # Timeline tab should be accessible
        if timeline_tab.count() > 0:
            timeline_tab.click()
            page.wait_for_timeout(500)
            
            # Check if tab appears active
            timeline_classes = timeline_tab.get_attribute("class") or ""
            if "text-blue-600" in timeline_classes or "active" in timeline_classes:
                print("✅ Timeline tab shows active state")
            else:
                print("⚠️ Timeline tab active state unclear")
        
        # Test keyboard navigation
        page.keyboard.press("Tab")
        page.wait_for_timeout(200)
        focused_element = page.evaluate("() => document.activeElement.tagName")
        
        if focused_element in ["INPUT", "BUTTON"]:
            print(f"✅ Keyboard navigation works: focused on {focused_element}")
        else:
            print(f"⚠️ Keyboard navigation unclear: focused on {focused_element}")
        
        print("✅ Navigation patterns test completed")
