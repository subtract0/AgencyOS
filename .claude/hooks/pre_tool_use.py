#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Pre-Tool-Use Quality Gate Hook for Claude Code.

Validates Python code quality BEFORE writing files to disk.
Eliminates merge-time waste by catching errors at generation time.

Quality Gates:
1. Ruff lint (exit 0 required)
2. Ruff format --check (exit 0 required)
3. Dict[str, Any] ban check (constitutional violation)
4. Function length <50 lines (constitutional law #8)

Exit Codes:
    0: Allow tool use (quality OK)
    2: Block tool use (quality violations found)
    1: Script error

Constitutional Compliance:
    - Article I: Validates BEFORE action (complete context)
    - Article II: 100% quality enforcement (deterministic rules)
    - Law #2: No Dict[Any, Any] types
    - Law #8: Functions <50 lines
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def validate_python_code(content: str, file_path: str) -> tuple[bool, list[str]]:
    """
    Validate Python code against all quality gates.

    Args:
        content: Python source code to validate
        file_path: Target file path (for error messages)

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Write to temp file for ruff validation
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Quality Gate 1: Ruff lint check
        result = subprocess.run(
            ["ruff", "check", temp_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            errors.append(f"Ruff lint errors:\n{result.stdout}")

        # Quality Gate 2: Ruff format check
        result = subprocess.run(
            ["ruff", "format", "--check", temp_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            errors.append(
                f"Ruff format required (run: ruff format {file_path})"
            )

        # Quality Gate 3: Dict[str, Any] ban check (Constitutional Law #2)
        if "dict[str, Any]" in content or "Dict[str, Any]" in content:
            errors.append(
                "Dict[str, Any] violation - use Pydantic models with typed fields (Constitutional Law #2)"
            )

        # Quality Gate 4: Function length check (Constitutional Law #8)
        func_violations = check_function_length(content)
        if func_violations:
            errors.extend(func_violations)

        return len(errors) == 0, errors

    finally:
        Path(temp_path).unlink()


def check_function_length(content: str) -> list[str]:
    """
    Check that all functions are under 50 lines.

    Args:
        content: Python source code

    Returns:
        List of violation messages (empty if all pass)
    """
    violations = []
    lines = content.split("\n")

    # Pattern to detect function definitions
    func_pattern = re.compile(r"^\s*(async\s+)?def\s+(\w+)\s*\(")

    in_function = False
    func_start = 0
    func_name = ""
    func_indent = 0

    for i, line in enumerate(lines, 1):
        match = func_pattern.match(line)

        if match:
            # New function starting
            if in_function:
                # Previous function ended implicitly
                func_length = i - func_start
                if func_length > 50:
                    violations.append(
                        f"Function '{func_name}' exceeds 50 lines ({func_length} lines at line {func_start}) - Constitutional Law #8"
                    )

            in_function = True
            func_start = i
            func_name = match.group(2)
            func_indent = len(line) - len(line.lstrip())

        elif in_function and line.strip():
            # Check if we've exited the function (dedent to same or less level)
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= func_indent and not line.strip().startswith(
                "#"
            ):
                # Function ended
                func_length = i - func_start
                if func_length > 50:
                    violations.append(
                        f"Function '{func_name}' exceeds 50 lines ({func_length} lines at line {func_start}) - Constitutional Law #8"
                    )
                in_function = False

    # Check last function if still in one
    if in_function:
        func_length = len(lines) - func_start + 1
        if func_length > 50:
            violations.append(
                f"Function '{func_name}' exceeds 50 lines ({func_length} lines at line {func_start}) - Constitutional Law #8"
            )

    return violations


def main():
    """Main hook entrypoint."""
    try:
        # Read JSON from stdin
        input_data = json.load(sys.stdin)

        tool_name = input_data.get("tool_name", "")
        args = input_data.get("args", {})

        # Intercept file writing tools
        if tool_name in ["Write", "MultiEdit", "NotebookEdit"]:
            file_path = args.get("file_path", "")

            # Only validate Python files
            if file_path.endswith(".py"):
                # Get content to be written
                if tool_name == "Write":
                    content = args.get("content", "")
                elif tool_name == "NotebookEdit":
                    content = args.get("new_source", "")
                else:
                    # MultiEdit - would need to reconstruct full file
                    # For now, skip validation (complex reconstruction)
                    sys.exit(0)

                if content:
                    is_valid, errors = validate_python_code(
                        content, file_path
                    )

                    if not is_valid:
                        sys.stderr.write(
                            f"❌ Quality Gate Failed for {file_path}:\n"
                        )
                        for error in errors:
                            sys.stderr.write(f"\n{error}\n")
                        sys.stderr.write(
                            f"\n🔧 Fix these issues before writing the file.\n"
                        )
                        sys.exit(2)  # BLOCK the write

        # Edit tool bypasses validation (surgical edits to existing files)
        # Non-Python files bypass validation
        # Non-file tools bypass validation

        # Allow tool use
        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"Error in pre-tool-use hook: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
