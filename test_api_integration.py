#!/usr/bin/env python
"""
Test API integration for agents that make real API calls.

This script runs the skipped tests that require actual API calls.
Run this separately from the main test suite to avoid hanging during CI/CD.
"""

import subprocess
import sys
import time


def run_api_tests():
    """Run all API integration tests."""
    print("=" * 60)
    print("Running API Integration Tests")
    print("=" * 60)
    print("\nNote: These tests make real API calls and may incur costs.")
    print("They are normally skipped in the main test suite.\n")

    tests_to_run = [
        # Test planner agent API calls
        "tests/test_planner_agent.py::test_planner_asks_clarifying_questions_vague_auth",
        "tests/test_planner_agent.py::test_planner_asks_clarifying_questions_file_format",
        "tests/test_planner_agent.py::test_planner_with_clear_requirements",
        "tests/test_planner_agent.py::test_planner_fibonacci_simple",
        "tests/test_planner_agent.py::test_planner_fibonacci_interactive",
    ]

    # Remove skip markers temporarily
    print("Removing skip markers from tests...")
    cmd = [
        "python", "-m", "pytest",
        "--override-ini", "markers=",  # Override markers
        "-p", "no:warnings",  # Disable warnings
        "-v",  # Verbose output
        "--tb=short",  # Short traceback
    ] + tests_to_run

    print(f"Running command: {' '.join(cmd)}\n")

    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False, text=True)
    elapsed_time = time.time() - start_time

    print(f"\n{'=' * 60}")
    print(f"Tests completed in {elapsed_time:.2f} seconds")
    print(f"Exit code: {result.returncode}")

    return result.returncode


if __name__ == "__main__":
    exit_code = run_api_tests()
    sys.exit(exit_code)