from pathlib import Path

from tools import Edit
from tools import Read


def test_edit_requires_prior_read():
    """Test that Edit tool requires using Read tool first"""
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
        tmp.write("Hello world\nThis is a test")
        tmp_path = tmp.name

    try:
        # Try to edit without reading first - should fail
        tool = Edit(file_path=tmp_path, old_string="world", new_string="universe")
        result = tool.run()

        # Should get an error message about needing to read first
        assert "must use Read tool" in result or "read the file first" in result.lower()

        # File should remain unchanged
        with open(tmp_path, "r") as f:
            assert "Hello world" in f.read()

    finally:
        os.unlink(tmp_path)


def test_edit_works_after_read():
    """Test that Edit tool works after using Read tool first"""
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
        tmp.write("Hello world\nThis is a test")
        tmp_path = tmp.name

    try:
        # Read the file first (prerequisite)
        read_tool = Read(file_path=tmp_path)
        read_tool.run()

        # Now edit should work
        tool = Edit(file_path=tmp_path, old_string="world", new_string="universe")
        result = tool.run()

        assert "Successfully replaced" in result

        # File should be changed
        with open(tmp_path, "r") as f:
            assert "Hello universe" in f.read()

    finally:
        os.unlink(tmp_path)


def test_edit_unique_replacement_and_preview(tmp_path: Path):
    p = tmp_path / "file.txt"
    p.write_text("hello world\nbye\n", encoding="utf-8")
    # Read the file first (required precondition)
    read_tool = Read(file_path=str(p))
    read_tool.run()
    tool = Edit(
        file_path=str(p), old_string="hello", new_string="hi", replace_all=False
    )
    out = tool.run()
    assert "Successfully replaced 1 occurrence" in out
    assert "Preview:" in out


def test_edit_multiple_occurrences_error_with_previews(tmp_path: Path):
    p = tmp_path / "multi.txt"
    p.write_text("a test a test a\n", encoding="utf-8")
    # Read the file first (required precondition)
    read_tool = Read(file_path=str(p))
    read_tool.run()
    tool = Edit(file_path=str(p), old_string="a", new_string="b", replace_all=False)
    out = tool.run()
    assert "Error: String appears" in out
    assert "First matches:" in out
