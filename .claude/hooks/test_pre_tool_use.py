#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Test suite for pre_tool_use.py quality gate hook.

Tests validate that the hook correctly:
1. Allows valid Python code (exit 0)
2. Blocks lint violations (exit 2)
3. Blocks format violations (exit 2)
4. Blocks Dict[Any] violations (exit 2)
5. Blocks long functions >50 lines (exit 2)
"""

import json
import subprocess
import sys
from pathlib import Path


def run_hook(tool_name: str, args: dict) -> tuple[int, str, str]:
    """
    Run the pre_tool_use.py hook with given inputs.

    Returns:
        (exit_code, stdout, stderr)
    """
    hook_path = Path(__file__).parent / "pre_tool_use.py"
    input_data = json.dumps({"tool_name": tool_name, "args": args})

    result = subprocess.run(
        ["python", str(hook_path)],
        input=input_data,
        capture_output=True,
        text=True,
    )

    return result.returncode, result.stdout, result.stderr


def test_allows_valid_code():
    """Test that valid Python code passes all quality gates."""
    valid_code = '''"""Valid module with clean code."""

from pydantic import BaseModel


class User(BaseModel):
    """User model with typed fields."""

    name: str
    email: str
    age: int


def create_user(data: dict[str, str]) -> User:
    """Create user from dict."""
    return User(**data)
'''

    exit_code, stdout, stderr = run_hook("Write", {"file_path": "test.py", "content": valid_code})

    assert exit_code == 0, f"Expected exit 0, got {exit_code}. Stderr: {stderr}"
    print("✅ Test 1 passed: Valid code allowed")


def test_blocks_lint_violations():
    """Test that ruff lint violations block the write."""
    lint_violation = """
import os
import sys  # Unused import - lint violation

def test():
    pass
"""

    exit_code, stdout, stderr = run_hook(
        "Write", {"file_path": "test.py", "content": lint_violation}
    )

    assert exit_code == 2, f"Expected exit 2 (block), got {exit_code}"
    assert "Ruff lint errors" in stderr or "unused" in stderr.lower()
    print("✅ Test 2 passed: Lint violations blocked")


def test_blocks_format_violations():
    """Test that ruff format violations block the write."""
    format_violation = """
def test(  ):  # Extra spaces - format violation
    x=1+2  # Missing spaces around operators
    return   x
"""

    exit_code, stdout, stderr = run_hook(
        "Write", {"file_path": "test.py", "content": format_violation}
    )

    assert exit_code == 2, f"Expected exit 2 (block), got {exit_code}"
    assert "Ruff format" in stderr
    print("✅ Test 3 passed: Format violations blocked")


def test_blocks_dict_any_violations():
    """Test that Dict[str, Any] violations block the write."""
    dict_any_violation = '''
from typing import Any

def process_data(data: dict[str, Any]) -> None:
    """Process data - violates no Dict[Any] rule."""
    pass
'''

    exit_code, stdout, stderr = run_hook(
        "Write", {"file_path": "test.py", "content": dict_any_violation}
    )

    assert exit_code == 2, f"Expected exit 2 (block), got {exit_code}"
    assert "Dict[str, Any]" in stderr or "dict[str, Any]" in stderr
    print("✅ Test 4 passed: Dict[Any] violations blocked")


def test_blocks_long_functions():
    """Test that functions >50 lines block the write."""
    long_function = '''
def very_long_function():
    """This function exceeds 50 lines."""
    line_1 = 1
    line_2 = 2
    line_3 = 3
    line_4 = 4
    line_5 = 5
    line_6 = 6
    line_7 = 7
    line_8 = 8
    line_9 = 9
    line_10 = 10
    line_11 = 11
    line_12 = 12
    line_13 = 13
    line_14 = 14
    line_15 = 15
    line_16 = 16
    line_17 = 17
    line_18 = 18
    line_19 = 19
    line_20 = 20
    line_21 = 21
    line_22 = 22
    line_23 = 23
    line_24 = 24
    line_25 = 25
    line_26 = 26
    line_27 = 27
    line_28 = 28
    line_29 = 29
    line_30 = 30
    line_31 = 31
    line_32 = 32
    line_33 = 33
    line_34 = 34
    line_35 = 35
    line_36 = 36
    line_37 = 37
    line_38 = 38
    line_39 = 39
    line_40 = 40
    line_41 = 41
    line_42 = 42
    line_43 = 43
    line_44 = 44
    line_45 = 45
    line_46 = 46
    line_47 = 47
    line_48 = 48
    line_49 = 49
    line_50 = 50
    line_51 = 51  # This exceeds 50 lines
    return line_51
'''

    exit_code, stdout, stderr = run_hook(
        "Write", {"file_path": "test.py", "content": long_function}
    )

    assert exit_code == 2, f"Expected exit 2 (block), got {exit_code}"
    assert "exceeds 50 lines" in stderr
    print("✅ Test 5 passed: Long functions blocked")


def test_allows_edit_tool():
    """Test that Edit tool bypasses validation (surgical edits)."""
    exit_code, stdout, stderr = run_hook(
        "Edit",
        {
            "file_path": "test.py",
            "old_string": "old",
            "new_string": "new",
        },
    )

    assert exit_code == 0, f"Expected exit 0 (allow Edit), got {exit_code}"
    print("✅ Test 6 passed: Edit tool allowed (surgical edits)")


def test_ignores_non_python_files():
    """Test that non-Python files bypass validation."""
    exit_code, stdout, stderr = run_hook(
        "Write", {"file_path": "test.md", "content": "# Some markdown"}
    )

    assert exit_code == 0, f"Expected exit 0 (non-Python), got {exit_code}"
    print("✅ Test 7 passed: Non-Python files ignored")


def test_ignores_non_file_tools():
    """Test that non-file-writing tools bypass hook."""
    exit_code, stdout, stderr = run_hook("Bash", {"command": "echo test"})

    assert exit_code == 0, f"Expected exit 0 (non-file tool), got {exit_code}"
    print("✅ Test 8 passed: Non-file tools ignored")


def main():
    """Run all tests."""
    tests = [
        test_allows_valid_code,
        test_blocks_lint_violations,
        test_blocks_format_violations,
        test_blocks_dict_any_violations,
        test_blocks_long_functions,
        test_allows_edit_tool,
        test_ignores_non_python_files,
        test_ignores_non_file_tools,
    ]

    print("Running pre_tool_use.py quality gate tests...\n")

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {len(tests) - failed}/{len(tests)} tests passed")

    if failed > 0:
        print(f"❌ {failed} tests FAILED")
        sys.exit(1)
    else:
        print("✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
