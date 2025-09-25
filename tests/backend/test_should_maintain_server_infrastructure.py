"""
OnGoal Server Infrastructure Tests
Tests server health, connectivity, and infrastructure requirements

These tests verify that the backend and frontend servers are properly
running and accessible before other tests can execute.
"""

import pytest
import requests


@pytest.mark.backend
class TestServerInfrastructure:
    """Infrastructure tests for OnGoal server health and connectivity"""

    def test_should_provide_healthy_backend_endpoint(self, backend_url):
        """Test that backend health endpoint is accessible and returns healthy status"""
        response = requests.get(f"{backend_url}/api/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_should_provide_backend_root_endpoint(self, backend_url):
        """Test that backend root endpoint is accessible"""
        response = requests.get(backend_url, timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "OnGoal Backend API" in data["message"]
