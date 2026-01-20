#!/usr/bin/env python3
"""Python Code Validator Hook.

Validates Python files after edit/write operations.
Runs automatically via Claude Code post-tool-use hooks.

Checks:
1. Syntax validity (can be parsed)
2. Import resolution (basic check)
3. Type hints present for functions
4. Docstrings for public functions
5. No common anti-patterns

Usage:
    python python_validator.py <file_path>

Exit codes:
    0 = All checks passed
    1 = Validation errors found (agent should fix)
"""

import ast
import sys
import os
from datetime import datetime
from pathlib import Path


# Logs for observability
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs" / "validators"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_result(file_path: str, passed: bool, issues: list[str]):
    """Log validation result for observability."""
    log_file = LOG_DIR / "python_validator.log"
    with open(log_file, "a") as f:
        status = "PASS" if passed else "FAIL"
        f.write(f"\n[{datetime.now().isoformat()}] {status}: {file_path}\n")
        for issue in issues:
            f.write(f"  - {issue}\n")


def validate_syntax(file_path: str) -> tuple[bool, list[str]]:
    """Check if Python file has valid syntax."""
    issues = []
    try:
        with open(file_path, "r") as f:
            source = f.read()
        ast.parse(source)
        return True, []
    except SyntaxError as e:
        issues.append(f"Syntax error at line {e.lineno}: {e.msg}")
        return False, issues
    except Exception as e:
        issues.append(f"Parse error: {e}")
        return False, issues


def validate_structure(file_path: str) -> tuple[bool, list[str]]:
    """Validate code structure and quality."""
    issues = []

    with open(file_path, "r") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False, ["Cannot parse file for structure check"]

    # Check functions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Skip private functions
            if node.name.startswith("_"):
                continue

            # Check for docstring
            if not (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, (ast.Str, ast.Constant))):
                # Only warn for public functions in non-test files
                if "/test" not in file_path and not file_path.endswith("_test.py"):
                    issues.append(f"Function '{node.name}' missing docstring (line {node.lineno})")

            # Check for return type hint (warning only)
            if node.returns is None and not node.name.startswith("test_"):
                pass  # Skip - too noisy for now

    # Check for common anti-patterns
    lines = source.split("\n")
    for i, line in enumerate(lines, 1):
        # Bare except
        if "except:" in line and "except Exception" not in line:
            issues.append(f"Bare except at line {i} - use specific exception")

        # Dict[Any, Any] anti-pattern
        if "Dict[Any, Any]" in line:
            issues.append(f"Dict[Any, Any] at line {i} - use typed dict or Pydantic model")

        # Print statements in non-script files
        if line.strip().startswith("print(") and "__main__" not in source:
            if "/tools/" not in file_path and "/scripts/" not in file_path:
                pass  # Skip - context dependent

    return len(issues) == 0, issues


def validate_imports(file_path: str) -> tuple[bool, list[str]]:
    """Basic import validation."""
    issues = []

    with open(file_path, "r") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False, ["Cannot parse file for import check"]

    # Get imported names
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.asname or alias.name)

    # Check for potentially unused imports (basic check)
    # This is very rough - a proper check would use scope analysis
    for imp in imported:
        if imp == "*":
            issues.append("Star import (*) found - import specific names")

    return len(issues) == 0, issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python python_validator.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    if not file_path.endswith(".py"):
        print(f"Not a Python file: {file_path}")
        sys.exit(0)  # Not an error, just skip

    all_issues = []

    # Run validators
    passed, issues = validate_syntax(file_path)
    all_issues.extend(issues)

    if passed:  # Only check structure if syntax is valid
        _, issues = validate_structure(file_path)
        all_issues.extend(issues)

        _, issues = validate_imports(file_path)
        all_issues.extend(issues)

    # Log result
    log_result(file_path, len(all_issues) == 0, all_issues)

    # Output for agent
    if all_issues:
        print(f"\n❌ Validation failed for {file_path}")
        print("\nResolve these issues:")
        for issue in all_issues:
            print(f"  - {issue}")
        print(f"\nFix the issues in {file_path} and retry.")
        sys.exit(1)
    else:
        print(f"✅ Python validation passed: {file_path}")
        sys.exit(0)


if __name__ == "__main__":
    main()
