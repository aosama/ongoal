"""
Simple WebSocket test to debug connection issues
This tests WebSocket functionality directly without browser complexity
"""

import asyncio
import json
import websockets
import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_should_connect_to_websocket_directly(backend_url):
    """Test direct WebSocket connection to backend"""
    
    try:
        # Connect to WebSocket endpoint
        ws_url = backend_url.replace("http://", "ws://").replace("https://", "wss://")
        uri = f"{ws_url}/ws"
        print(f"🔗 Attempting direct WebSocket connection to {uri}")

        # Backend URL fixture ensures backend is running
        # No additional health check needed
            
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Send a test message
            test_message = {
                "type": "user_message",
                "message": "What is the capital of France?"
            }
            
            await websocket.send(json.dumps(test_message))
            print(f"📤 Sent test message: {test_message}")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response)
                print(f"📨 Received response: {response_data}")
                
                # Check if goals were inferred
                if response_data.get("type") == "goals_inferred":
                    goals = response_data.get("goals", [])
                    print(f"🎯 Goals inferred: {len(goals)} goals")
                    for goal in goals:
                        print(f"  - {goal['type']}: {goal['text']}")
                    
                    assert len(goals) > 0, "Should have inferred at least one goal"
                    assert any(goal['type'] == 'question' for goal in goals), "Should have inferred a question goal"
                    
                else:
                    print(f"❌ Expected goals_inferred, got: {response_data.get('type')}")
                    
            except asyncio.TimeoutError:
                print("⏱️ Timeout waiting for WebSocket response")
                raise AssertionError("No response received from WebSocket")
                
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        raise
