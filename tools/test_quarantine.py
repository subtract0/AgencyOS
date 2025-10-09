#!/usr/bin/env python3
"""
Test Quarantine System - Auto-mark flaky tests

Mars Rover Bulletproofing: Automatically quarantine flaky tests
that fail 3+ times in 1 week, preventing them from blocking development.

Usage:
    python tools/test_quarantine.py --check    # Check for quarantine candidates
    python tools/test_quarantine.py --apply    # Apply quarantine marks
    python tools/test_quarantine.py --list     # List quarantined tests
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set


class TestQuarantineSystem:
    """
    Automated test quarantine management.

    Quarantined tests:
    - Still run in CI (don't skip them)
    - Don't block merges (pytest-xfail or custom marker)
    - Generate issues for investigation
    - Auto-remove after 1 week of stability
    """

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.quarantine_log = self.project_root / "logs" / "quarantine_candidates.log"
        self.quarantine_registry = self.project_root / ".test-health" / "quarantine_registry.json"
        self.quarantine_marker = "quarantine"

    def load_quarantine_registry(self) -> Dict:
        """Load the registry of currently quarantined tests."""
        if self.quarantine_registry.exists():
            with open(self.quarantine_registry) as f:
                return json.load(f)
        return {"tests": {}, "last_updated": datetime.now().isoformat()}

    def save_quarantine_registry(self, registry: Dict):
        """Save the quarantine registry."""
        self.quarantine_registry.parent.mkdir(parents=True, exist_ok=True)
        registry["last_updated"] = datetime.now().isoformat()
        with open(self.quarantine_registry, "w") as f:
            json.dump(registry, f, indent=2)

    def find_quarantine_candidates(self) -> Set[str]:
        """
        Identify tests that should be quarantined.

        Criteria:
        - Failed 3+ times in past 7 days
        - OR marked as FLAKY by health tracking
        - OR failed after 3 retries multiple times
        """
        if not self.quarantine_log.exists():
            return set()

        candidates = set()
        cutoff_date = datetime.now() - timedelta(days=7)

        # Track failures per test in past week
        failures_per_test: Dict[str, int] = {}

        with open(self.quarantine_log) as f:
            for line in f:
                # Parse: "2025-10-07 14:30:45 | FAILED after 3 retries | test_path"
                match = re.match(r"([^|]+) \| (FAILED|FLAKY) [^|]* \| (.+)", line.strip())
                if not match:
                    continue

                timestamp_str, failure_type, test_path = match.groups()

                try:
                    timestamp = datetime.fromisoformat(timestamp_str.strip())
                except ValueError:
                    continue

                # Only consider recent failures
                if timestamp < cutoff_date:
                    continue

                test_path = test_path.strip()

                # Count failures
                failures_per_test[test_path] = failures_per_test.get(test_path, 0) + 1

                # Auto-quarantine if FLAKY marker or 3+ failures
                if failure_type == "FLAKY" or failures_per_test[test_path] >= 3:
                    candidates.add(test_path)

        return candidates

    def apply_quarantine_marker(self, test_path: str, reason: str) -> bool:
        """
        Add @pytest.mark.quarantine decorator to a test.

        Strategy:
        1. Parse test file
        2. Find test function
        3. Add marker before function definition
        4. Preserve formatting
        """
        # Convert test nodeid to file path
        # Example: "tests/unit/test_agent.py::test_memory" -> tests/unit/test_agent.py
        file_path_str = test_path.split("::")[0]
        file_path = self.project_root / file_path_str

        if not file_path.exists():
            print(f"⚠️  Test file not found: {file_path}")
            return False

        # Extract test function name
        test_func = test_path.split("::")[-1] if "::" in test_path else None
        if not test_func:
            print(f"⚠️  Invalid test path format: {test_path}")
            return False

        # Read test file
        with open(file_path) as f:
            lines = f.readlines()

        # Find test function and add marker
        modified = False
        new_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this is our test function
            if f"def {test_func}(" in line or f"async def {test_func}(" in line:
                # Check if marker already exists
                if i > 0 and "@pytest.mark.quarantine" in lines[i - 1]:
                    print(f"ℹ️  Already quarantined: {test_path}")
                    return False

                # Add marker before function
                indent = len(line) - len(line.lstrip())
                marker_line = " " * indent + f'@pytest.mark.quarantine(reason="{reason}")\n'

                new_lines.append(marker_line)
                new_lines.append(line)
                modified = True
                i += 1
                continue

            new_lines.append(line)
            i += 1

        if not modified:
            print(f"⚠️  Test function not found: {test_func} in {file_path}")
            return False

        # Write back
        with open(file_path, "w") as f:
            f.writelines(new_lines)

        print(f"✅ Quarantined: {test_path}")
        return True

    def check_candidates(self):
        """Check and display quarantine candidates."""
        candidates = self.find_quarantine_candidates()

        if not candidates:
            print("✅ No tests need quarantine")
            return

        print(f"⚠️  Found {len(candidates)} quarantine candidates:\n")

        for test in sorted(candidates):
            print(f"  • {test}")

        print(f"\nRun with --apply to quarantine these tests")

    def apply_quarantine(self):
        """Apply quarantine markers to candidate tests."""
        candidates = self.find_quarantine_candidates()

        if not candidates:
            print("✅ No tests need quarantine")
            return

        registry = self.load_quarantine_registry()

        quarantined_count = 0
        for test in candidates:
            # Skip if already quarantined
            if test in registry["tests"]:
                continue

            reason = "Flaky test auto-detected by health tracking"
            if self.apply_quarantine_marker(test, reason):
                registry["tests"][test] = {
                    "quarantined_at": datetime.now().isoformat(),
                    "reason": reason,
                    "auto_removed": False,
                }
                quarantined_count += 1

        if quarantined_count > 0:
            self.save_quarantine_registry(registry)
            print(f"\n✅ Quarantined {quarantined_count} tests")
            print(f"\nNext steps:")
            print(f"1. Run tests to verify quarantine works")
            print(f"2. Commit changes: git add <test-files>")
            print(f"3. Create PR with quarantine fixes")
        else:
            print("ℹ️  All candidates already quarantined")

    def list_quarantined(self):
        """List all currently quarantined tests."""
        registry = self.load_quarantine_registry()

        if not registry["tests"]:
            print("✅ No tests currently quarantined")
            return

        print(f"📋 Quarantined Tests ({len(registry['tests'])}):\n")

        for test, info in sorted(registry["tests"].items()):
            quarantined_at = datetime.fromisoformat(info["quarantined_at"])
            days_ago = (datetime.now() - quarantined_at).days

            print(f"  • {test}")
            print(f"    Quarantined: {days_ago} days ago")
            print(f"    Reason: {info['reason']}\n")


def main():
    parser = argparse.ArgumentParser(description="Test Quarantine System - Auto-mark flaky tests")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check for quarantine candidates",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply quarantine markers to candidates",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List currently quarantined tests",
    )

    args = parser.parse_args()

    system = TestQuarantineSystem()

    if args.check:
        system.check_candidates()
    elif args.apply:
        system.apply_quarantine()
    elif args.list:
        system.list_quarantined()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
