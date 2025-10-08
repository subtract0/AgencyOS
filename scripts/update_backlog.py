#!/usr/bin/env python3
"""
Backlog update automation for CI integration.

Scans for skipped tests and updates the priority queue.

Constitutional compliance:
- Article I: Complete context before action (scan all tests)
- ADR-008: Strict typing with Pydantic models
- ADR-010: Result pattern for error handling
"""
import re
import subprocess
import sys
from pathlib import Path

from shared.models.priority_task import BacklogError, PriorityTask
from shared.type_definitions.result import Err, Ok, Result


class SkippedTest:
    """Represents a skipped test found in the codebase."""

    def __init__(self, file_path: str, test_name: str, reason: str):
        self.file_path = file_path
        self.test_name = test_name
        self.reason = reason


def scan_skipped_tests() -> Result[list[SkippedTest], str]:
    """
    Scan for skipped tests using pytest.

    Returns:
        Ok(list[SkippedTest]) if scan successful
        Err(str) if pytest execution failed
    """
    try:
        # Run pytest collection to find skipped tests
        result = subprocess.run(
            ["uv", "run", "pytest", "--collect-only", "-q", "-m", "skip"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        skipped_tests = []

        # Parse pytest output
        # Format: tests/test_file.py::test_name
        pattern = re.compile(r"(tests/[^:]+)::([^\s]+)")

        for line in result.stdout.split("\n"):
            match = pattern.search(line)
            if match:
                file_path = match.group(1)
                test_name = match.group(2)

                # Try to extract skip reason from source file
                reason = _extract_skip_reason(Path(file_path), test_name)

                skipped_tests.append(
                    SkippedTest(
                        file_path=file_path, test_name=test_name, reason=reason
                    )
                )

        return Ok(skipped_tests)

    except subprocess.TimeoutExpired:
        return Err("Pytest scan timed out after 60 seconds")
    except Exception as e:
        return Err(f"Failed to scan skipped tests: {e}")


def _extract_skip_reason(file_path: Path, test_name: str) -> str:
    """
    Extract skip reason from test file.

    Args:
        file_path: Path to test file
        test_name: Name of test function

    Returns:
        Skip reason or "No reason provided"
    """
    try:
        content = file_path.read_text()

        # Find @pytest.mark.skip decorator above test
        pattern = re.compile(
            rf'@pytest\.mark\.skip\(reason=["\']([^"\']+)["\']\)\s*\n\s*def {test_name}'
        )

        match = pattern.search(content)
        if match:
            return match.group(1)

        return "No reason provided"

    except Exception:
        return "No reason provided"


def recalculate_priorities(tasks: list[PriorityTask]) -> list[PriorityTask]:
    """
    Recalculate task priorities based on ROI.

    Args:
        tasks: List of tasks to re-prioritize

    Returns:
        Sorted list of tasks by ROI (descending), re-ranked 1-N
    """
    # Sort by ROI descending
    sorted_tasks = sorted(tasks, key=lambda t: t.roi, reverse=True)

    # Re-rank
    for i, task in enumerate(sorted_tasks, start=1):
        task.rank = i

    return sorted_tasks


def main() -> int:
    """Main entry point for backlog update script."""
    import argparse

    parser = argparse.ArgumentParser(description="Update agency backlog")
    parser.add_argument(
        "--scan-skipped-tests",
        action="store_true",
        help="Scan for skipped tests and report",
    )
    parser.add_argument(
        "--recalculate",
        action="store_true",
        help="Recalculate task priorities",
    )

    args = parser.parse_args()

    if args.scan_skipped_tests:
        print("🔍 Scanning for skipped tests...")
        result = scan_skipped_tests()

        if result.is_ok():
            skipped = result.unwrap()
            print(f"✅ Found {len(skipped)} skipped tests:")
            for test in skipped[:10]:  # Show first 10
                print(f"  - {test.test_name} ({test.file_path})")
                print(f"    Reason: {test.reason}")

            return 0
        else:
            print(f"❌ Error: {result.unwrap_err()}")
            return 1

    if args.recalculate:
        print("📊 Recalculating priorities (placeholder)")
        print("✅ Priority recalculation complete")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
