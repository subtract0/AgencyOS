import os
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


def test_edit_same_old_and_new_string(tmp_path: Path):
    """Test error when old_string and new_string are identical"""
    p = tmp_path / "same.txt"
    p.write_text("hello world", encoding="utf-8")

    # Read the file first (required precondition)
    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="hello", new_string="hello")
    out = tool.run()
    assert "Error: old_string and new_string must be different" in out


def test_edit_nonexistent_file():
    """Test error when file doesn't exist"""
    # This test actually hits the read prerequisite check first
    tool = Edit(file_path="/nonexistent/path/file.txt", old_string="test", new_string="replacement")
    out = tool.run()
    # The read prerequisite check comes first, so we get that error
    assert "must use Read tool" in out or "read the file first" in out.lower()


def test_edit_nonexistent_file_after_mock_read():
    """Test error when file doesn't exist after bypassing read check"""
    from unittest.mock import patch
    from tools.edit import _global_read_files

    nonexistent_path = "/nonexistent/path/file.txt"
    abs_path = os.path.abspath(nonexistent_path)

    # Mock the read state to bypass the read prerequisite
    _global_read_files.add(abs_path)

    try:
        tool = Edit(file_path=nonexistent_path, old_string="test", new_string="replacement")
        out = tool.run()
        assert "Error: File does not exist" in out
    finally:
        # Clean up the mock read state
        _global_read_files.discard(abs_path)


def test_edit_path_is_directory(tmp_path: Path):
    """Test error when path points to a directory"""
    dir_path = tmp_path / "testdir"
    dir_path.mkdir()

    # Try to read the directory first to satisfy precondition check
    read_tool = Read(file_path=str(dir_path))
    try:
        read_tool.run()
    except Exception:
        pass  # Expected to fail

    tool = Edit(file_path=str(dir_path), old_string="test", new_string="replacement")
    out = tool.run()
    assert "Error: Path is not a file" in out


def test_edit_binary_file_error(tmp_path: Path):
    """Test error when trying to edit a binary file"""
    binary_file = tmp_path / "binary.bin"
    # Create a binary file with non-UTF-8 content
    with open(binary_file, "wb") as f:
        f.write(b'\x80\x81\x82\x83')  # Invalid UTF-8 bytes

    # Read the file first (required precondition)
    read_tool = Read(file_path=str(binary_file))
    try:
        read_tool.run()
    except Exception:
        pass  # Expected to fail for binary files

    tool = Edit(file_path=str(binary_file), old_string="test", new_string="replacement")
    out = tool.run()
    assert "Error: Unable to decode file" in out and "binary file" in out


def test_edit_string_not_found(tmp_path: Path):
    """Test error when string to replace is not found"""
    p = tmp_path / "notfound.txt"
    p.write_text("hello world", encoding="utf-8")

    # Read the file first (required precondition)
    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="xyz", new_string="replacement")
    out = tool.run()
    assert "Error: String to replace not found in file" in out


def test_edit_replace_all_functionality(tmp_path: Path):
    """Test replace_all=True functionality"""
    p = tmp_path / "replaceall.txt"
    p.write_text("foo bar foo baz foo", encoding="utf-8")

    # Read the file first (required precondition)
    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="foo", new_string="FOO", replace_all=True)
    out = tool.run()
    assert "Successfully replaced 3 occurrence(s)" in out

    # Verify all occurrences were replaced
    content = p.read_text(encoding="utf-8")
    assert "FOO bar FOO baz FOO" == content


def test_edit_replace_all_with_multiple_preview(tmp_path: Path):
    """Test replace_all with multiple occurrences shows first and last in preview"""
    p = tmp_path / "multipreview.txt"
    p.write_text("start foo middle foo end", encoding="utf-8")

    # Read the file first (required precondition)
    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="foo", new_string="BAR", replace_all=True)
    out = tool.run()
    assert "Successfully replaced 2 occurrence(s)" in out
    assert "Preview:" in out


def test_edit_permission_error():
    """Test handling of permission denied when writing"""
    from unittest.mock import patch, mock_open

    # Create a temporary file first
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
        tmp.write("test content")
        tmp_path = tmp.name

    try:
        # Read the file first (required precondition)
        read_tool = Read(file_path=tmp_path)
        read_tool.run()

        # Mock open to raise PermissionError when writing
        with patch('builtins.open', side_effect=[
            mock_open(read_data="test content").return_value,  # For reading
            PermissionError("Permission denied")  # For writing
        ]):
            tool = Edit(file_path=tmp_path, old_string="test", new_string="replacement")
            out = tool.run()
            assert "Error: Permission denied writing to file" in out

    finally:
        import os
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def test_edit_general_write_exception():
    """Test handling of general exceptions during file writing"""
    from unittest.mock import patch, mock_open

    # Create a temporary file first
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
        tmp.write("test content")
        tmp_path = tmp.name

    try:
        # Read the file first (required precondition)
        read_tool = Read(file_path=tmp_path)
        read_tool.run()

        # Mock open to raise a general exception when writing
        with patch('builtins.open', side_effect=[
            mock_open(read_data="test content").return_value,  # For reading
            Exception("Disk full")  # For writing
        ]):
            tool = Edit(file_path=tmp_path, old_string="test", new_string="replacement")
            out = tool.run()
            assert "Error writing to file: Disk full" in out

    finally:
        import os
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
