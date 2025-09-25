#!/usr/bin/env python3
"""
OnGoal Backend Runner
Development server script for the OnGoal backend
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def main():
    """Run the OnGoal backend server"""
    
    # Check for .env file
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("⚠️  No .env file found!")
        print("📝 Please copy env.example to .env and configure your API keys")
        print(f"   cp {Path(__file__).parent / 'env.example'} {env_file}")
        return 1
    
    print("🚀 Starting OnGoal Backend Server...")
    print("📍 Backend API: http://localhost:8000")
    print("🔌 WebSocket: ws://localhost:8000/ws")
    print("📖 API Docs: http://localhost:8000/docs")
    print("❤️  Health Check: http://localhost:8000/api/health")
    print()
    
    try:
        # Import and run the FastAPI app
        from main import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=[str(backend_dir)],
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
