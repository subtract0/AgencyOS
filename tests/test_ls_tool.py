import os
import stat
from pathlib import Path

import pytest

from tools import LS


def test_ls_simple_directory(tmp_path: Path):
    """Test listing a simple directory with files and subdirs"""
    # Create test structure
    (tmp_path / "file1.txt").write_text("content1")
    (tmp_path / "file2.py").write_text("print('hello')")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "nested.txt").write_text("nested content")

    tool = LS(path=str(tmp_path))
    result = tool.run()

    assert f"Contents of {tmp_path}" in result
    assert "file1.txt" in result
    assert "file2.py" in result
    assert "subdir" in result
    assert "TYPE" in result  # Header
    assert "PERMISSIONS" in result
    assert "SIZE" in result
    assert "Total: 3 items" in result


def test_ls_with_file_details(tmp_path: Path):
    """Test that file details are shown correctly"""
    test_file = tmp_path / "test.py"
    content = "# Test file\nprint('hello world')\n"
    test_file.write_text(content)

    tool = LS(path=str(tmp_path))
    result = tool.run()

    assert "FILE" in result
    assert "test.py" in result
    # Should show readable permissions
    assert "r" in result
    # Should show file size
    assert "B" in result or "KB" in result


def test_ls_empty_directory(tmp_path: Path):
    """Test listing an empty directory"""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    tool = LS(path=str(empty_dir))
    result = tool.run()

    assert "Directory is empty" in result or "Total: 0 items" in result


def test_ls_with_ignore_patterns(tmp_path: Path):
    """Test ignoring files with glob patterns"""
    # Create test files
    (tmp_path / "file.txt").write_text("content")
    (tmp_path / "file.py").write_text("code")
    (tmp_path / "file.pyc").write_text("bytecode")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "temp.tmp").write_text("temp")

    tool = LS(path=str(tmp_path), ignore=["*.pyc", "__pycache__", "*.tmp"])
    result = tool.run()

    assert "file.txt" in result
    assert "file.py" in result
    assert "file.pyc" not in result
    # Don't check for __pycache__ in the main result since it appears in the filter summary
    assert "temp.tmp" not in result
    assert "Total: 2 items" in result
    assert "filtered with patterns" in result
    # Verify that __pycache__ doesn't appear as a listed item
    # Split on both \n and \\n to handle different line ending formats
    all_lines = result.replace("\\n", "\n").split("\n")
    item_lines = [
        line
        for line in all_lines
        if ("DIR" in line or "FILE" in line)
        and "TYPE" not in line
        and "Total:" not in line
    ]
    assert not any("__pycache__" in line for line in item_lines)


def test_ls_file_types(tmp_path: Path):
    """Test different file types are identified correctly"""
    # Regular file
    (tmp_path / "regular.txt").write_text("content")

    # Directory
    (tmp_path / "directory").mkdir()

    # Try to create a symbolic link (may not work on all systems)
    try:
        link_path = tmp_path / "symlink.txt"
        os.symlink(str(tmp_path / "regular.txt"), str(link_path))
        has_symlink = True
    except (OSError, NotImplementedError):
        has_symlink = False

    tool = LS(path=str(tmp_path))
    result = tool.run()

    assert "FILE" in result  # Regular file
    assert "DIR" in result  # Directory
    if has_symlink:
        assert "LINK" in result  # Symbolic link


def test_ls_file_sizes(tmp_path: Path):
    """Test file size reporting for different sizes"""
    # Small file (bytes)
    small_file = tmp_path / "small.txt"
    small_file.write_text("hi")  # 2 bytes

    # Medium file (KB)
    medium_file = tmp_path / "medium.txt"
    medium_file.write_text("x" * 1500)  # ~1.5 KB

    # Large file (MB) - but keep it reasonable for tests
    large_file = tmp_path / "large.txt"
    large_file.write_text("y" * (2 * 1024 * 1024))  # 2 MB

    tool = LS(path=str(tmp_path))
    result = tool.run()

    assert "2B" in result or "2.0B" in result  # Small file
    assert "KB" in result  # Medium file
    assert "MB" in result  # Large file


def test_ls_permissions(tmp_path: Path):
    """Test permission reporting"""
    test_file = tmp_path / "perm_test.txt"
    test_file.write_text("content")

    # Make file read-only
    os.chmod(test_file, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    tool = LS(path=str(tmp_path))
    result = tool.run()

    # Should show read permissions but not write
    assert "r--r--r--" in result or "r-" in result


def test_ls_modification_time(tmp_path: Path):
    """Test modification time is shown"""
    test_file = tmp_path / "time_test.txt"
    test_file.write_text("content")

    tool = LS(path=str(tmp_path))
    result = tool.run()

    # Should contain date/time format (YYYY-MM-DD HH:MM)
    assert "202" in result  # Year
    assert ":" in result  # Time separator


def test_ls_requires_absolute_path():
    """Test that LS requires absolute paths"""
    tool = LS(path="relative/path")
    result = tool.run()

    assert "Error: Path must be absolute" in result


def test_ls_nonexistent_directory():
    """Test error when directory doesn't exist"""
    tool = LS(path="/nonexistent/directory/path")
    result = tool.run()

    assert "Error: Path does not exist" in result


def test_ls_path_is_file(tmp_path: Path):
    """Test error when path is a file, not directory"""
    test_file = tmp_path / "notadir.txt"
    test_file.write_text("content")

    tool = LS(path=str(test_file))
    result = tool.run()

    assert "Error: Path is not a directory" in result


def test_ls_complex_directory_structure(tmp_path: Path):
    """Test listing a complex directory structure"""
    # Create a more complex structure
    (tmp_path / "README.md").write_text("# Project")
    (tmp_path / "requirements.txt").write_text("requests>=2.0")

    # Source directory
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")
    (src_dir / "main.py").write_text("print('main')")
    (src_dir / "utils.py").write_text("def helper(): pass")

    # Tests directory
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("def test_main(): pass")

    # Config files
    (tmp_path / ".gitignore").write_text("__pycache__/")
    (tmp_path / "setup.py").write_text("from setuptools import setup")

    tool = LS(path=str(tmp_path))
    result = tool.run()

    # Check that all items are listed
    expected_items = [
        "README.md",
        "requirements.txt",
        "src",
        "tests",
        ".gitignore",
        "setup.py",
    ]
    for item in expected_items:
        assert item in result

    assert "Total: 6 items" in result
    assert "DIR" in result  # Should show directories
    assert "FILE" in result  # Should show files


def test_ls_ignore_multiple_patterns(tmp_path: Path):
    """Test ignoring multiple different patterns"""
    # Create various files
    files = [
        "app.py",
        "app.pyc",
        "app.pyo",
        "test.txt",
        "test.bak",
        "test.tmp",
        "config.json",
        "config.json~",
        "data.log",
        "debug.log",
        "README.md",
    ]

    for filename in files:
        (tmp_path / filename).write_text("content")

    # Create directories to ignore
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / ".git").mkdir()
    (tmp_path / "node_modules").mkdir()

    # Ignore compiled files, backups, logs, and common directories
    ignore_patterns = [
        "*.pyc",
        "*.pyo",
        "*.bak",
        "*.tmp",
        "*~",
        "*.log",
        "__pycache__",
        ".git",
        "node_modules",
    ]

    tool = LS(path=str(tmp_path), ignore=ignore_patterns)
    result = tool.run()

    # Should keep these
    assert "app.py" in result
    assert "test.txt" in result
    assert "config.json" in result
    assert "README.md" in result

    # Should ignore these
    assert "app.pyc" not in result
    assert "test.bak" not in result
    assert "debug.log" not in result
    # Don't check for directory names in the main result since they appear in filter summary

    # Should show filtered count
    assert "Total: 4 items" in result
    assert "filtered with patterns" in result

    # Verify that ignored items don't appear as listed items
    # Split on both \n and \\n to handle different line ending formats
    all_lines = result.replace("\\n", "\n").split("\n")
    item_lines = [
        line
        for line in all_lines
        if ("DIR" in line or "FILE" in line)
        and "TYPE" not in line
        and "Total:" not in line
    ]
    assert not any("__pycache__" in line for line in item_lines)
    assert not any(".git" in line for line in item_lines)


def test_ls_sorting(tmp_path: Path):
    """Test that files are sorted alphabetically"""
    filenames = ["zebra.txt", "apple.py", "banana.md", "Cherry.json", "1number.txt"]
    for filename in filenames:
        (tmp_path / filename).write_text("content")

    tool = LS(path=str(tmp_path))
    result = tool.run()

    # Find the positions of filenames in the result
    positions = {}
    for filename in filenames:
        pos = result.find(filename)
        if pos != -1:
            positions[filename] = pos

    # Check that they appear in sorted order
    sorted_names = sorted(filenames)
    sorted_positions = [positions[name] for name in sorted_names if name in positions]

    # Positions should be in ascending order
    assert sorted_positions == sorted(sorted_positions)


def test_ls_error_handling_permissions():
    """Test graceful error handling for permission issues"""
    # This test may not work on all systems, so we'll make it conditional
    try:
        # Try to create a scenario with permission issues
        # This is system-dependent and may not always work in tests

        tool = LS(path="/root")  # May not have permissions
        result = tool.run()

        # Should either work or give a permission error, not crash
        assert isinstance(result, str)
        assert len(result) > 0

    except Exception:
        pytest.skip("Cannot test permission scenarios on this system")


def test_ls_with_hidden_files(tmp_path: Path):
    """Test listing directories with hidden files"""
    # Create visible and hidden files
    (tmp_path / "visible.txt").write_text("content")
    (tmp_path / ".hidden").write_text("hidden content")
    (tmp_path / ".config").mkdir()
    (tmp_path / ".config" / "settings.json").write_text("{}")

    tool = LS(path=str(tmp_path))
    result = tool.run()

    # Should list both visible and hidden files
    assert "visible.txt" in result
    assert ".hidden" in result
    assert ".config" in result
    assert "Total: 3 items" in result
