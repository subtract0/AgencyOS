"""
Integration tests for codegen CLI.
"""
import os
import json
import subprocess
import sys


def test_cli_refactor_basic(tmp_path):
    """Test refactor CLI command."""
    # Create test Python file
    test_file = tmp_path / "sample.py"
    test_file.write_text("""
def func():
    try:
        pass
    except Exception:
        pass
""")

    # Run CLI command
    result = subprocess.run([
        sys.executable, "-m", "tools.codegen.cli",
        "refactor",
        "--paths", str(test_file)
    ], capture_output=True, text=True, cwd=os.getcwd())

    assert result.returncode == 0
    assert "suggestions" in result.stdout.lower() or "analyzing" in result.stdout.lower()


def test_cli_gen_tests_basic(tmp_path):
    """Test gen-tests CLI command."""
    # Create test spec file
    spec_file = tmp_path / "test-spec.md"
    spec_file.write_text("""
# Test Spec

## Acceptance Criteria
- AC1: Basic functionality should work
- AC2: Error handling should be robust
""")

    out_dir = tmp_path / "test_output"

    # Run CLI command
    result = subprocess.run([
        sys.executable, "-m", "tools.codegen.cli",
        "gen-tests",
        "--spec", str(spec_file),
        "--out", str(out_dir)
    ], capture_output=True, text=True, cwd=os.getcwd())

    assert result.returncode == 0
    assert "generated" in result.stdout.lower()

    # Verify test files were created
    test_dir = out_dir / "test_test-spec"
    assert test_dir.exists()


def test_cli_scaffold_basic(tmp_path):
    """Test scaffold CLI command."""
    out_dir = tmp_path / "scaffold_output"

    # Run CLI command
    result = subprocess.run([
        sys.executable, "-m", "tools.codegen.cli",
        "scaffold",
        "--template", "tool",
        "--name", "test_scaffold",
        "--out", str(out_dir)
    ], capture_output=True, text=True, cwd=os.getcwd())

    assert result.returncode == 0
    assert "created" in result.stdout.lower()

    # Verify files were created
    assert (out_dir / "__init__.py").exists()
    assert (out_dir / "test_scaffold.py").exists()


def test_cli_help():
    """Test CLI help output."""
    result = subprocess.run([
        sys.executable, "-m", "tools.codegen.cli",
        "--help"
    ], capture_output=True, text=True, cwd=os.getcwd())

    assert result.returncode == 0
    assert "refactor" in result.stdout
    assert "gen-tests" in result.stdout
    assert "scaffold" in result.stdout


def test_cli_no_command():
    """Test CLI with no command."""
    result = subprocess.run([
        sys.executable, "-m", "tools.codegen.cli"
    ], capture_output=True, text=True, cwd=os.getcwd())

    assert result.returncode == 1
    # Should show help when no command given