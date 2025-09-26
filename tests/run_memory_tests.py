#!/usr/bin/env python3
"""
Simple test runner for Memory API tests.

Runs all memory-related tests and provides a summary report.
"""

import subprocess
import sys
from typing import Tuple, List


def run_test_file(test_file: str) -> Tuple[bool, str]:
    """Run a single test file and return results."""
    print(f"\n{'=' * 50}")
    print(f"Running {test_file}")
    print("=" * 50)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v"],
            capture_output=True,
            text=True,
            cwd="/Users/am/Code/Agency",
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0, result.stdout
    except Exception as e:
        print(f"Error running {test_file}: {e}")
        return False, str(e)


def main() -> int:
    """Run all memory tests and provide summary."""
    print("Memory API Test Runner")
    print("=====================")

    test_files = [
        "tests/test_memory_api.py",
        "tests/test_hooks_memory_logging.py",
        "tests/test_learning_consolidation.py",
    ]

    results = []
    total_passed = 0
    total_failed = 0

    for test_file in test_files:
        success, output = run_test_file(test_file)
        results.append((test_file, success, output))

        # Extract pass/fail counts from pytest output
        if "passed" in output:
            for line in output.split("\n"):
                if "passed" in line and (
                    "failed" in line or line.strip().endswith("passed")
                ):
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "passed" in part:
                            passed = (
                                int(parts[i - 1])
                                if i > 0 and parts[i - 1].isdigit()
                                else 0
                            )
                            total_passed += passed
                        if "failed" in part:
                            failed = (
                                int(parts[i - 1])
                                if i > 0 and parts[i - 1].isdigit()
                                else 0
                            )
                            total_failed += failed
                    break

    print(f"\n{'=' * 60}")
    print("SUMMARY REPORT")
    print("=" * 60)

    for test_file, success, _ in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_file:<40} {status}")

    print(f"\nTotal Tests: {total_passed + total_failed}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")

    if total_failed == 0:
        print("\n✅ All memory tests passed!")
        return 0
    else:
        print(f"\n❌ {total_failed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
