"""
OnGoal Goal Progress & Sentence Similarity API Tests
Tests for goal progress and sentence similarity REST endpoints (REQ-03-02-001, REQ-03-02-004, REQ-04-03-006/007)
"""

import pytest
import requests

CONVERSATION_ID = "test_progress"


@pytest.mark.backend
class TestGoalProgressAPI:

    def test_should_return_progress_for_new_conversation(self, backend_url):
        requests.post(f"{backend_url}/api/conversations/{CONVERSATION_ID}/reset", timeout=5)
        response = requests.get(f"{backend_url}/api/conversations/{CONVERSATION_ID}/goal-progress", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "progress" in data
        assert data["goal_count"] == 0

    def test_should_return_404_for_missing_conversation(self, backend_url):
        response = requests.get(f"{backend_url}/api/conversations/nonexistent_progress/goal-progress", timeout=5)
        assert response.status_code == 404

    def test_should_show_progress_after_goal_creation(self, backend_url):
        requests.post(f"{backend_url}/api/conversations/{CONVERSATION_ID}/reset", timeout=5)
        requests.post(
            f"{backend_url}/api/conversations/{CONVERSATION_ID}/goals",
            json={"text": "test goal", "type": "request", "source_message_id": "m0"},
            timeout=5,
        )
        response = requests.get(f"{backend_url}/api/conversations/{CONVERSATION_ID}/goal-progress", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["goal_count"] == 1
        assert data["progress"][0]["completion_status"] == "active"


@pytest.mark.backend
class TestSentenceSimilarityAPI:

    def test_should_return_empty_for_new_conversation(self, backend_url):
        requests.post(f"{backend_url}/api/conversations/{CONVERSATION_ID}/reset", timeout=5)
        response = requests.get(f"{backend_url}/api/conversations/{CONVERSATION_ID}/sentence-similarity", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["similar_sentences"] == []
        assert data["unique_sentences"] == []
        assert data["message_count"] == 0

    def test_should_return_404_for_missing_conversation(self, backend_url):
        response = requests.get(f"{backend_url}/api/conversations/nonexistent_sim/sentence-similarity", timeout=5)
        assert response.status_code == 404