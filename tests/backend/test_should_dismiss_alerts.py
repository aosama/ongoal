"""
OnGoal Alert API Tests
Tests alert CRUD endpoints and alert display pipeline (REQ-03-01-006, REQ-03-01-003, REQ-03-03-006)
"""

import pytest
import requests

CONVERSATION_ID = "test_alerts"


@pytest.mark.backend
class TestAlertAPI:
    """Tests for alert REST endpoints"""

    def test_should_return_empty_alerts_for_new_conversation(self, backend_url):
        requests.post(f"{backend_url}/api/conversations/{CONVERSATION_ID}/reset", timeout=5)
        response = requests.get(f"{backend_url}/api/conversations/{CONVERSATION_ID}/alerts", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["alerts"] == []

    def test_should_clear_all_alerts(self, backend_url):
        requests.post(f"{backend_url}/api/conversations/{CONVERSATION_ID}/reset", timeout=5)
        response = requests.delete(f"{backend_url}/api/conversations/{CONVERSATION_ID}/alerts", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_should_dismiss_single_alert_by_index(self, backend_url):
        requests.post(f"{backend_url}/api/conversations/{CONVERSATION_ID}/reset", timeout=5)
        requests.post(
            f"{backend_url}/api/conversations/{CONVERSATION_ID}/goals",
            json={"text": "Test goal", "type": "request", "source_message_id": "msg_0"},
            timeout=5,
        )
        inject_url = f"{backend_url}/api/conversations/{CONVERSATION_ID}/alerts/_inject"
        requests.post(inject_url, json={
            "alert_type": "forgetting",
            "severity": "warning",
            "goal_ids": ["G0"],
            "message": "Goal forgotten",
        }, timeout=5)
        response = requests.delete(f"{backend_url}/api/conversations/{CONVERSATION_ID}/alerts/0", timeout=5)
        assert response.status_code == 200
        response2 = requests.get(f"{backend_url}/api/conversations/{CONVERSATION_ID}/alerts", timeout=5)
        assert response2.json()["count"] == 0

    def test_should_reject_invalid_alert_index(self, backend_url):
        requests.post(f"{backend_url}/api/conversations/{CONVERSATION_ID}/reset", timeout=5)
        response = requests.delete(f"{backend_url}/api/conversations/{CONVERSATION_ID}/alerts/99", timeout=5)
        assert response.status_code == 404

    def test_should_include_alerts_in_conversation_state(self, backend_url):
        requests.post(f"{backend_url}/api/conversations/{CONVERSATION_ID}/reset", timeout=5)
        response = requests.get(f"{backend_url}/api/conversations/{CONVERSATION_ID}", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    def test_should_404_on_alerts_for_missing_conversation(self, backend_url):
        response = requests.get(f"{backend_url}/api/conversations/nonexistent/alerts", timeout=5)
        assert response.status_code == 404