"""
OnGoal Test Configuration - Simplified and Efficient
Single session-scoped server with proper test isolation
"""

import pytest
import asyncio
import subprocess
import time
import requests
from pathlib import Path
import os
import signal


class BackendTestServer:
    """Manages a single backend server for all tests"""

    def __init__(self):
        self.backend_process = None
        self.backend_url = "http://localhost:8000"
        self.project_root = Path(__file__).parent.parent

    def start(self):
        """Start backend server once per test session"""
        try:
            self.cleanup_existing_processes()

            # Load environment variables
            from dotenv import load_dotenv
            load_dotenv()

            # Start backend server
            print("🚀 Starting OnGoal backend server for tests...")
            backend_cmd = [
                str(self.project_root / ".venv/bin/python"),
                "-m", "uvicorn",
                "backend.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--log-level", "warning"  # Reduce noise
            ]

            self.backend_process = subprocess.Popen(
                backend_cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy()
            )

            # Wait for server to be ready
            self.wait_for_health()
            print("✅ Backend server ready for tests")

        except Exception as e:
            self.cleanup()
            raise Exception(f"Failed to start test backend: {e}")

    def cleanup_existing_processes(self):
        """Kill any existing processes on port 8000"""
        try:
            result = subprocess.run(
                ["lsof", "-ti", ":8000"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    subprocess.run(["kill", "-9", pid], check=False)
                time.sleep(2)
        except FileNotFoundError:
            # lsof not available, try pkill
            subprocess.run(["pkill", "-9", "-f", "uvicorn.*backend.main"], check=False)
            time.sleep(2)

    def wait_for_health(self):
        """Wait for backend to respond to health checks"""
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.backend_url}/api/health", timeout=2)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                pass

            # Check if process died
            if self.backend_process.poll() is not None:
                stdout, stderr = self.backend_process.communicate()
                raise Exception(f"Backend crashed: {stderr.decode()}")

            time.sleep(1)

        raise Exception("Backend failed to start within 30 seconds")

    def reset_state(self):
        """Reset application state between tests"""
        try:
            # Reset conversation state
            requests.post(f"{self.backend_url}/api/conversations/default/reset", timeout=5)
        except Exception:
            pass  # Ignore reset failures

    def cleanup(self):
        """Stop the backend server"""
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                self.backend_process.wait()
        print("🧹 Backend server stopped")


class FrontendTestServer:
    """Manages frontend server for browser tests only"""

    def __init__(self):
        self.frontend_process = None
        self.frontend_port = None
        self.frontend_url = None  # Will be set after finding an available port
        self.project_root = Path(__file__).parent.parent

    def find_available_port(self, start_port=8080):
        """Find an available port starting from start_port"""
        import socket
        for port in range(start_port, start_port + 10):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        raise Exception("No available ports found")

    def start(self):
        """Start frontend server for browser tests"""
        try:
            # Find an available port
            if not self.frontend_port:
                self.frontend_port = self.find_available_port(8080)
                self.frontend_url = f"http://localhost:{self.frontend_port}"

            print(f"🌐 Starting frontend server on port {self.frontend_port}...")

            # Create a modified frontend script that uses our port
            frontend_env = os.environ.copy()
            frontend_env['FRONTEND_PORT'] = str(self.frontend_port)

            self.frontend_process = subprocess.Popen(
                [str(self.project_root / ".venv/bin/python"), "-c", f"""
import sys
import os
sys.path.insert(0, '{str(self.project_root)}')
from run_frontend import main
import http.server
import socketserver
from pathlib import Path

# Override port
PORT = {self.frontend_port}
HOST = "localhost"

# Change to frontend directory
frontend_dir = Path('{str(self.project_root)}') / "frontend"
os.chdir(frontend_dir)

class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

with socketserver.TCPServer((HOST, PORT), NoCacheHTTPRequestHandler) as httpd:
    httpd.serve_forever()
"""],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=frontend_env
            )

            self.wait_for_ready()
            print(f"✅ Frontend server ready on port {self.frontend_port}")

        except Exception as e:
            self.cleanup()
            raise Exception(f"Failed to start frontend: {e}")

    def cleanup_existing_processes(self):
        """Kill any existing frontend processes"""
        # Kill any python processes running frontend
        subprocess.run(["pkill", "-9", "-f", "NoCacheHTTPRequestHandler"], check=False)
        subprocess.run(["pkill", "-9", "-f", "run_frontend"], check=False)
        time.sleep(1)

    def wait_for_ready(self):
        """Wait for frontend to be ready"""
        max_attempts = 20
        for attempt in range(max_attempts):
            try:
                response = requests.get(self.frontend_url, timeout=2)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                pass

            if self.frontend_process.poll() is not None:
                stdout, stderr = self.frontend_process.communicate()
                error_output = stdout.decode() if stdout else "No output"
                raise Exception(f"Frontend crashed: {error_output}")

            time.sleep(1)

        raise Exception("Frontend failed to start within 20 seconds")

    def cleanup(self):
        """Stop the frontend server"""
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
                self.frontend_process.wait()


# Global server instances
_backend_server = None
_frontend_server = None


@pytest.fixture(scope="session", autouse=True)
def backend_server():
    """Single backend server for all tests"""
    global _backend_server
    _backend_server = BackendTestServer()
    _backend_server.start()
    yield _backend_server
    _backend_server.cleanup()


@pytest.fixture(scope="session")
def frontend_server():
    """Frontend server for browser tests"""
    global _frontend_server
    if _frontend_server is None:
        _frontend_server = FrontendTestServer()
        _frontend_server.start()
    yield _frontend_server
    # Don't cleanup here - let the process handle it


@pytest.fixture(autouse=True)
def clean_state():
    """Reset application state before each test"""
    if _backend_server:
        _backend_server.reset_state()
    yield


@pytest.fixture
def backend_url():
    """Backend server URL"""
    return "http://localhost:8000"


@pytest.fixture
def frontend_url(frontend_server):
    """Frontend server URL"""
    return frontend_server.frontend_url


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--visible", action="store_true", default=False,
        help="Run browser tests in visible mode"
    )


@pytest.fixture(scope="session")
def browser_context_args():
    """Configure browser context for testing"""
    return {
        "viewport": {"width": 1400, "height": 900},
        "ignore_https_errors": True,
        "record_video_dir": None,  # Disable for performance
        "record_har_path": None,   # Disable for performance
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(request):
    """Configure browser launch arguments"""
    visible_mode = request.config.getoption("--visible", default=False)

    if visible_mode:
        return {
            "headless": False,
            "slow_mo": 1000,
            "devtools": False,
            "timeout": 30000,
        }
    else:
        return {
            "headless": True,
            "slow_mo": 0,
            "devtools": False,
            "timeout": 30000,
        }


@pytest.fixture
def page(browser, frontend_server, frontend_url, clean_state):
    """Browser page fixture with clean state - depends on frontend_server"""
    page = browser.new_page()
    page.set_viewport_size({"width": 1400, "height": 900})
    page.set_default_timeout(15000)
    page.set_default_navigation_timeout(20000)

    yield page
    page.close()

@pytest.fixture
def test_environment(frontend_server, backend_server):
    """Test environment fixture that ensures both servers are running"""
    return {
        "frontend_server": frontend_server,
        "backend_server": backend_server,
        "frontend_url": frontend_server.frontend_url,
        "backend_url": "http://localhost:8000"
    }