#!/usr/bin/env python3
"""TypeScript/JavaScript Validator Hook.

Validates TS/JS/TSX/JSX files after edit/write operations.
Uses basic AST checks and optional tsc for full validation.

Usage:
    python typescript_validator.py <file_path>

Exit codes:
    0 = Validation passed
    1 = Errors found (agent should fix)
"""

import subprocess
import sys
import os
import re
from datetime import datetime
from pathlib import Path


LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs" / "validators"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_result(file_path: str, passed: bool, issues: list[str]):
    """Log validation result."""
    log_file = LOG_DIR / "typescript_validator.log"
    with open(log_file, "a") as f:
        status = "PASS" if passed else "FAIL"
        f.write(f"\n[{datetime.now().isoformat()}] {status}: {file_path}\n")
        for issue in issues:
            f.write(f"  - {issue}\n")


def validate_basic(file_path: str) -> tuple[bool, list[str]]:
    """Basic syntax and pattern checks."""
    issues = []

    with open(file_path, "r") as f:
        content = f.read()
        lines = content.split("\n")

    # Check for common issues
    for i, line in enumerate(lines, 1):
        # Console.log in production code (warning)
        if "console.log(" in line and "// debug" not in line.lower():
            if "/test" not in file_path and ".test." not in file_path:
                pass  # Skip - context dependent

        # Any type usage
        if ": any" in line or "as any" in line:
            issues.append(f"Line {i}: 'any' type used - consider specific type")

        # Empty catch blocks
        if re.search(r"catch\s*\([^)]*\)\s*{\s*}", line):
            issues.append(f"Line {i}: Empty catch block - handle or log error")

    # Check for balanced braces (very basic)
    open_braces = content.count("{") + content.count("[") + content.count("(")
    close_braces = content.count("}") + content.count("]") + content.count(")")
    if open_braces != close_braces:
        issues.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")

    return len(issues) == 0, issues


def validate_with_tsc(file_path: str) -> tuple[bool, list[str]]:
    """Run TypeScript compiler for full validation (if available)."""
    issues = []

    # Find tsconfig.json
    current = Path(file_path).parent
    tsconfig = None
    while current != current.parent:
        potential = current / "tsconfig.json"
        if potential.exists():
            tsconfig = potential
            break
        current = current.parent

    if not tsconfig:
        return True, []  # No tsconfig, skip tsc validation

    try:
        # Run tsc --noEmit on the specific file
        result = subprocess.run(
            ["npx", "tsc", "--noEmit", "--skipLibCheck", file_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(tsconfig.parent)
        )

        if result.returncode != 0:
            # Parse tsc errors
            for line in result.stdout.split("\n"):
                if line.strip() and "error TS" in line:
                    issues.append(line.strip())

        return len(issues) == 0, issues

    except FileNotFoundError:
        return True, []  # tsc not available
    except subprocess.TimeoutExpired:
        return True, ["TypeScript check timed out"]
    except Exception as e:
        return True, [f"TypeScript check failed: {e}"]


def main():
    if len(sys.argv) < 2:
        print("Usage: python typescript_validator.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    valid_extensions = (".ts", ".tsx", ".js", ".jsx")
    if not file_path.endswith(valid_extensions):
        print(f"Not a TypeScript/JavaScript file: {file_path}")
        sys.exit(0)

    all_issues = []

    # Basic checks
    passed, issues = validate_basic(file_path)
    all_issues.extend(issues)

    # TSC check (if available)
    _, issues = validate_with_tsc(file_path)
    all_issues.extend(issues)

    log_result(file_path, len(all_issues) == 0, all_issues)

    if all_issues:
        print(f"\n❌ TypeScript validation failed: {file_path}")
        print("\nResolve these issues:")
        for issue in all_issues[:10]:  # Limit output
            print(f"  - {issue}")
        if len(all_issues) > 10:
            print(f"  ... and {len(all_issues) - 10} more")
        print(f"\nFix the issues in {file_path}")
        sys.exit(1)
    else:
        print(f"✅ TypeScript validation passed: {file_path}")
        sys.exit(0)


if __name__ == "__main__":
    main()
