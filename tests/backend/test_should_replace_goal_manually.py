"""
Test manual goal replacement API (REQ-03-01-004 — user-initiated)
"""

import pytest


class TestManualGoalReplacement:
    """POST /api/conversations/{id}/goals/{goal_id}/replace"""

    def test_should_replace_existing_goal(self, backend_url, clean_state):
        """Manual replacement creates new goal, marks old as replaced."""
        import requests

        # Create a conversation with a goal
        requests.post(f"{backend_url}/api/conversations/test_conv/reset")
        requests.post(f"{backend_url}/api/conversations/test_conv/goals", json={
            "text": "Old goal text",
            "type": "request",
            "source_message_id": "msg_1"
        })

        # Replace it
        resp = requests.post(f"{backend_url}/api/conversations/test_conv/goals/G0_manual/replace", json={
            "new_text": "New replacement goal",
            "new_type": "suggestion"
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["old_goal"]["status"] == "replaced"
        assert data["new_goal"]["text"] == "New replacement goal"

    def test_should_return_404_for_missing_conversation(self, backend_url):
        import requests
        resp = requests.post(f"{backend_url}/api/conversations/missing/goals/G0/replace", json={"new_text": "x"})
        assert resp.status_code == 404

    def test_should_return_404_for_missing_goal(self, backend_url, clean_state):
        import requests
        requests.post(f"{backend_url}/api/conversations/test_conv/reset")
        resp = requests.post(f"{backend_url}/api/conversations/test_conv/goals/G99/replace", json={"new_text": "x"})
        assert resp.status_code == 404
