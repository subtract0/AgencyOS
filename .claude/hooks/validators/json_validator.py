#!/usr/bin/env python3
"""JSON Validator Hook.

Validates JSON files after edit/write operations.
Ensures valid JSON structure and optionally schema compliance.

Usage:
    python json_validator.py <file_path>

Exit codes:
    0 = Valid JSON
    1 = Invalid JSON (agent should fix)
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path


LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs" / "validators"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_result(file_path: str, passed: bool, issues: list[str]):
    """Log validation result."""
    log_file = LOG_DIR / "json_validator.log"
    with open(log_file, "a") as f:
        status = "PASS" if passed else "FAIL"
        f.write(f"\n[{datetime.now().isoformat()}] {status}: {file_path}\n")
        for issue in issues:
            f.write(f"  - {issue}\n")


def validate_json(file_path: str) -> tuple[bool, list[str]]:
    """Validate JSON file."""
    issues = []

    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Try to parse
        data = json.loads(content)

        # Check for common issues
        if isinstance(data, dict):
            # Check for empty required fields
            for key, value in data.items():
                if value is None and key in ("name", "id", "type"):
                    issues.append(f"Field '{key}' is null but likely required")

        return len(issues) == 0, issues

    except json.JSONDecodeError as e:
        issues.append(f"JSON parse error at line {e.lineno}, column {e.colno}: {e.msg}")
        return False, issues
    except Exception as e:
        issues.append(f"Error reading file: {e}")
        return False, issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python json_validator.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    if not file_path.endswith(".json"):
        print(f"Not a JSON file: {file_path}")
        sys.exit(0)

    passed, issues = validate_json(file_path)
    log_result(file_path, passed, issues)

    if issues:
        print(f"\n❌ JSON validation failed: {file_path}")
        print("\nResolve these issues:")
        for issue in issues:
            print(f"  - {issue}")
        print(f"\nFix the JSON in {file_path}")
        sys.exit(1)
    else:
        print(f"✅ JSON validation passed: {file_path}")
        sys.exit(0)


if __name__ == "__main__":
    main()
