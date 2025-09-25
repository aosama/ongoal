#!/usr/bin/env python3
"""
OnGoal Frontend Server
Simple HTTP server for serving the Vue.js frontend during development
"""

import os
import sys
import http.server
import socketserver
from pathlib import Path

def main():
    """Run the OnGoal frontend development server"""
    
    # Change to frontend directory
    frontend_dir = Path(__file__).parent / "frontend"
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        return 1
    
    os.chdir(frontend_dir)
    
    # Server configuration
    PORT = 8080
    HOST = "localhost"
    
    print("🎨 Starting OnGoal Frontend Server...")
    print(f"📍 Frontend URL: http://{HOST}:{PORT}")
    print("💡 Make sure the backend is running on http://localhost:8000")
    print("🔄 The page will auto-reload when you make changes")
    print()
    
    try:
        # Create a simple HTTP server
        class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def end_headers(self):
                # Disable caching for development
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                super().end_headers()
            
            def log_message(self, format, *args):
                # Custom log format
                print(f"📡 {self.address_string()} - {format % args}")
        
        with socketserver.TCPServer((HOST, PORT), NoCacheHTTPRequestHandler) as httpd:
            print(f"✅ Frontend server running at http://{HOST}:{PORT}")
            print("Press Ctrl+C to stop")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped by user")
        return 0
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use!")
            print("Please close any other applications using this port or choose a different port")
        else:
            print(f"❌ Failed to start frontend server: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
