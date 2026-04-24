"""
Browser tests for persistence and goal replacement features.

Covers:
- localStorage persistence across page reloads
- Manual goal replacement via "Replace" button
- Goal status badge display
"""

import pytest
from playwright.sync_api import expect, Page
import requests


API_BASE = "http://localhost:8000"


class TestConversationPersistence:
    """localStorage-based conversation persistence tests."""

    @pytest.mark.browser
    def test_should_prompt_restore_when_localstorage_has_data(self, page, test_environment, frontend_url):
        """
        After saving a message, a page reload should prompt for session restoration.
        """
        page.goto(frontend_url)

        # Send a message and wait for response
        page.fill("input[placeholder*='Type your message']", "Hello persistence test")
        page.click("button:has-text('Send')")
        page.wait_for_timeout(2500)

        # Reload the page
        page.goto(frontend_url)

        # Expect the restore toast to appear
        toast = page.locator(".alert-toast")
        expect(toast.first).to_be_visible(timeout=3000)
        expect(page.get_by_text("Restore previous session?")).to_be_visible()

    @pytest.mark.browser
    def test_should_restore_session_on_click_restore(self, page, test_environment, frontend_url):
        """
        Clicking "Restore" should bring back the previous conversation.
        """
        page.goto(frontend_url)

        page.fill("input[placeholder*='Type your message']", "Restore me please")
        page.click("button:has-text('Send')")
        page.wait_for_timeout(2500)

        page.goto(frontend_url)

        # Click Restore in the toast
        page.get_by_role("button", name="Restore").click()
        page.wait_for_timeout(1000)

        # The earlier message should be visible somewhere in the page
        expect(page.get_by_text("Restore me please")).to_be_visible(timeout=5000)

    @pytest.mark.browser
    def test_should_start_fresh_on_click_start_fresh(self, page, test_environment, frontend_url):
        """
        Clicking "Start Fresh" should clear the conversation.
        """
        page.goto(frontend_url)

        page.fill("input[placeholder*='Type your message']", "Forget me")
        page.click("button:has-text('Send')")
        page.wait_for_timeout(2500)

        page.goto(frontend_url)
        page.get_by_role("button", name="Start Fresh").click()
        page.wait_for_timeout(500)

        # Message should be gone
        expect(page.locator(".chat-messages").get_by_text("Forget me")).not_to_be_visible()


class TestGoalReplacement:
    """Manual goal replacement via REST API seeding (avoids LLM latency).

    Uses absolute URL with port 8000 since the frontend servers the API
    from a separate FastAPI backend, not the same origin.
    """

    @staticmethod
    def _create_goal(text="Learn French geography"):
        import time
        url = "http://localhost:8000/api/conversations/default/goals"
        for _ in range(10):
            try:
                r = requests.post(url, json={"text": text, "type": "request"}, timeout=5)
                if r.status_code < 300:
                    return r.json()
            except Exception:
                time.sleep(1)
        raise RuntimeError("Failed to seed goal")

    @staticmethod
    def _replace_goal(gid, new_text):
        url = f"http://localhost:8000/api/conversations/default/goals/{gid}/replace"
        requests.post(url, json={"new_text": new_text, "new_type": "request"}, timeout=5)

    @pytest.mark.browser
    def test_should_show_replace_button_on_goals(self, page, test_environment, frontend_url):
        """Goals that are not replaced should show a "Replace" button."""
        page.goto(frontend_url)
        self._create_goal()
        page.click("button:has-text('Goals')")
        page.wait_for_timeout(500)

        replace_count = page.locator("button").filter(has_text="Replace").count()
        assert replace_count > 0, "Expected at least one Replace button on goals"

    @pytest.mark.browser
    def test_should_replace_goal_on_click(self, page, test_environment, frontend_url):
        """Clicking Replace should mark the old goal as replaced via prompt."""
        page.goto(frontend_url)
        self._create_goal()
        page.click("button:has-text('Goals')")
        page.wait_for_timeout(500)

        new_text = "Learn about European capitals"
        page.on("dialog", lambda dialog: dialog.accept(new_text))

        page.locator("button").filter(has_text="Replace").first.click()
        page.wait_for_timeout(1500)

        expect(page.get_by_text("replaced").first).to_be_visible(timeout=3000)

    @pytest.mark.browser
    def test_should_apply_line_through_to_replaced_goal(self, page, test_environment, frontend_url):
        """Replaced goals should visually appear with strikethrough."""
        goal = self._create_goal("Plan a trip to Mars")
        gid = goal["goal"]["id"]
        self._replace_goal(gid, "Plan a trip to the Moon")

        page.goto(frontend_url)
        page.click("button:has-text('Goals')")
        page.wait_for_timeout(500)

        replaced = page.locator(".line-through.opacity-50")
        assert replaced.count() > 0, "Expected at least one replaced goal with strikethrough styling"
