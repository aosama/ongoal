#!/usr/bin/env python3
"""
OnGoal Unified Test Runner
Replaces all shell script runners with a single, efficient test execution system
"""

import subprocess
import sys
import argparse
import json
import time
from datetime import datetime
from pathlib import Path


class OnGoalTestRunner:
    """Unified test runner for all OnGoal test types"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_python = str(self.project_root / ".venv/bin/python")

    def run_unit_tests(self, verbose=True):
        """Run pure unit tests (no server dependencies)"""
        print("🧪 Running Unit Tests")
        print("=" * 40)

        cmd = [
            self.venv_python, "-m", "pytest",
            "tests/",
            "-m", "unit",
            "--tb=short"
        ]

        if verbose:
            cmd.append("-v")

        return self._execute_tests(cmd, "Unit Tests")

    def run_backend_tests(self, verbose=True):
        """Run backend API tests (backend server only)"""
        print("🔧 Running Backend Tests")
        print("=" * 40)

        cmd = [
            self.venv_python, "-m", "pytest",
            "tests/backend/",
            "-m", "not browser",
            "-n", "auto", "--dist=loadscope",
            "--tb=short"
        ]

        if verbose:
            cmd.append("-v")

        return self._execute_tests(cmd, "Backend Tests")

    def run_browser_tests(self, verbose=True, visible=False):
        """Run browser automation tests (both servers)"""
        print("🌐 Running Browser Tests")
        print("=" * 40)

        cmd = [
            self.venv_python, "-m", "pytest",
            "tests/browser/",
            "-m", "browser",
            "--tb=short"
        ]

        if verbose:
            cmd.append("-v")

        if visible:
            cmd.append("--visible")

        return self._execute_tests(cmd, "Browser Tests")

    def run_integration_tests(self, verbose=True):
        """Run integration tests"""
        print("🔗 Running Integration Tests")
        print("=" * 40)

        cmd = [
            self.venv_python, "-m", "pytest",
            "tests/",
            "-m", "integration",
            "-n", "auto", "--dist=loadscope",
            "--tb=short"
        ]

        if verbose:
            cmd.append("-v")

        return self._execute_tests(cmd, "Integration Tests")

    def run_regression_suite(self, verbose=True, visible=False):
        """Optimized regression: fast tests in parallel, slow/LLM tests in serial"""
        print("🎯 RUNNING OPTIMIZED REGRESSION SUITE")
        print("=" * 50)

        # Phase 1: Fast tests in parallel with xdist
        print("\n🚀 Phase 1: Fast tests (parallel)")
        print("-" * 40)
        fast_cmd = [
            self.venv_python, "-m", "pytest",
            "tests/backend/",
            "-m", "not slow",
            "--tb=short",
            "-n", "auto", "--dist=loadscope"
        ]
        if verbose:
            fast_cmd.append("-v")
        fast_ok = self._execute_tests(fast_cmd, "Fast Tests")

        # Phase 2: Check if slow tests exist
        slow_result = subprocess.run(
            [self.venv_python, "-m", "pytest", "--collect-only", "tests/backend/", "-m", "slow", "-q"],
            capture_output=True, text=True
        )
        if "collected 0 items" in slow_result.stdout or slow_result.returncode != 0:
            print("\n📋 No slow tests found — regression complete")
            self._print_regression_summary({"Fast Tests": fast_ok}, fast_ok)
            return fast_ok

        # Phase 3: Slow tests in serial (with real LLM calls)
        print("\n🐌 Phase 2: Slow tests (serial — real LLM calls)")
        print("-" * 40)
        slow_cmd = [
            self.venv_python, "-m", "pytest",
            "tests/backend/",
            "-m", "slow",
            "--tb=short",
            "-n", "1"
        ]
        if verbose:
            slow_cmd.append("-v")
        slow_ok = self._execute_tests(slow_cmd, "Slow Tests")

        overall = fast_ok and slow_ok
        self._print_regression_summary(
            {"Fast Tests": fast_ok, "Slow Tests": slow_ok}, overall
        )
        return overall

    def run_quick_smoke_tests(self, verbose=True):
        """Run quick smoke tests for rapid feedback"""
        print("💨 Running Quick Smoke Tests")
        print("=" * 40)

        cmd = [
            self.venv_python, "-m", "pytest",
            "tests/backend/test_backend_isolated.py",
            "tests/backend/test_api_infrastructure.py",
            "--tb=short"
        ]

        if verbose:
            cmd.append("-v")

        return self._execute_tests(cmd, "Smoke Tests")

    def _execute_tests(self, cmd, test_type):
        """Execute pytest command and return success status"""
        print(f"🚀 Command: {' '.join(cmd)}")
        print()

        start_time = time.time()

        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            duration = time.time() - start_time
            success = result.returncode == 0

            print(f"\n⏱️  {test_type} completed in {duration:.2f} seconds")
            return success

        except Exception as e:
            print(f"❌ Failed to execute {test_type}: {e}")
            return False

    def _print_regression_summary(self, results, overall_success):
        """Print regression test summary"""
        print("\n" + "=" * 50)
        print("📊 REGRESSION TEST SUMMARY")
        print("=" * 50)

        passed = sum(1 for success in results.values() if success)
        total = len(results)

        for category, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status}: {category}")

        print(f"\nResult: {passed}/{total} test categories passed")

        if overall_success:
            print("🎉 ALL REGRESSION TESTS PASSED!")
            print("✅ OnGoal system is working correctly")
        else:
            print("🚨 REGRESSION DETECTED!")
            print("🔍 Check test output above for details")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="OnGoal Unified Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Categories:
  unit      - Pure unit tests (fastest, no servers)
  backend   - Backend API tests (backend server only)
  browser   - Browser automation tests (both servers)
  integration - Cross-component integration tests
  regression - Complete test suite (all categories)
  smoke     - Quick smoke tests for rapid feedback

Examples:
  python test_runner.py unit           # Fast unit tests only
  python test_runner.py backend        # Backend API tests
  python test_runner.py browser        # Browser tests (headless)
  python test_runner.py browser --visible  # Browser tests (visible)
  python test_runner.py regression     # Full regression suite
  python test_runner.py smoke          # Quick smoke tests
        """
    )

    parser.add_argument(
        "category",
        choices=["unit", "backend", "browser", "integration", "regression", "smoke"],
        help="Test category to run"
    )

    parser.add_argument(
        "--visible", action="store_true",
        help="Run browser tests in visible mode (non-headless)"
    )

    parser.add_argument(
        "--quiet", action="store_true",
        help="Reduce output verbosity"
    )

    args = parser.parse_args()

    runner = OnGoalTestRunner()
    verbose = not args.quiet

    # Route to appropriate test function
    test_functions = {
        "unit": lambda: runner.run_unit_tests(verbose),
        "backend": lambda: runner.run_backend_tests(verbose),
        "browser": lambda: runner.run_browser_tests(verbose, args.visible),
        "integration": lambda: runner.run_integration_tests(verbose),
        "regression": lambda: runner.run_regression_suite(verbose, args.visible),
        "smoke": lambda: runner.run_quick_smoke_tests(verbose)
    }

    success = test_functions[args.category]()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()