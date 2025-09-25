"""
OnGoal API Infrastructure Tests
Tests server health, connectivity, and WebSocket functionality without browser

These tests verify core infrastructure components:
- Backend health endpoints
- Frontend server accessibility
- WebSocket connectivity
- API response validation
"""

import pytest
import requests
import asyncio
import websockets
import json
import time


@pytest.mark.backend
class TestAPIInfrastructure:
    """Infrastructure tests for OnGoal API and server connectivity"""

    def test_should_provide_healthy_backend_service(self, backend_url):
        """Test backend health endpoint returns healthy status"""
        response = requests.get(f"{backend_url}/api/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_should_provide_websocket_connectivity(self, backend_url):
        """Test WebSocket endpoint accepts connections"""
        websocket_url = backend_url.replace("http", "ws") + "/ws"
        try:
            async with websockets.connect(websocket_url) as websocket:
                # Send a test message
                test_message = {
                    "type": "user_message",
                    "message": "test connection",
                    "conversation_id": "test_ws_connection"
                }
                await websocket.send(json.dumps(test_message))

                # Wait for response with timeout
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response)

                # Verify we got a valid response
                assert "type" in response_data
        except Exception as e:
            if "Connection refused" in str(e) or "Connect call failed" in str(e):
                pytest.skip("Backend server not running - skipping WebSocket test")
            else:
                pytest.fail(f"WebSocket connection failed: {e}")

    def test_should_handle_api_error_responses_gracefully(self, backend_url):
        """Test API handles invalid requests gracefully"""
        # Test invalid endpoint
        response = requests.get(f"{backend_url}/api/nonexistent", timeout=5)
        assert response.status_code == 404
        
        # Test malformed request (if chat endpoint exists)
        try:
            response = requests.post(f"{backend_url}/api/chat", 
                                   json={"invalid": "data"}, 
                                   timeout=5)
            # Should return 4xx error, not crash
            assert 400 <= response.status_code < 500
        except requests.exceptions.RequestException:
            # If endpoint doesn't exist yet, that's also acceptable
            pass

    def test_should_provide_cors_headers_for_frontend(self, backend_url):
        """Test backend provides proper CORS headers for frontend communication"""
        # Test with GET request which should include CORS headers
        response = requests.get(f"{backend_url}/api/health", 
                               headers={"Origin": "http://localhost:8080"}, 
                               timeout=5)
        
        # Should return successful response with CORS headers
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
