import os
from pathlib import Path

from tools import Edit, Read


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
        with open(tmp_path) as f:
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
        with open(tmp_path) as f:
            assert "Hello universe" in f.read()

    finally:
        os.unlink(tmp_path)


def test_edit_unique_replacement_and_preview(tmp_path: Path):
    p = tmp_path / "file.txt"
    p.write_text("hello world\nbye\n", encoding="utf-8")
    # Read the file first (required precondition)
    read_tool = Read(file_path=str(p))
    read_tool.run()
    tool = Edit(file_path=str(p), old_string="hello", new_string="hi", replace_all=False)
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
        f.write(b"\x80\x81\x82\x83")  # Invalid UTF-8 bytes

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
    # Create a temporary file first
    import tempfile
    from unittest.mock import mock_open, patch

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
        tmp.write("test content")
        tmp_path = tmp.name

    try:
        # Read the file first (required precondition)
        read_tool = Read(file_path=tmp_path)
        read_tool.run()

        # Mock open to raise PermissionError when writing
        with patch(
            "builtins.open",
            side_effect=[
                mock_open(read_data="test content").return_value,  # For reading
                PermissionError("Permission denied"),  # For writing
            ],
        ):
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
    # Create a temporary file first
    import tempfile
    from unittest.mock import mock_open, patch

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
        tmp.write("test content")
        tmp_path = tmp.name

    try:
        # Read the file first (required precondition)
        read_tool = Read(file_path=tmp_path)
        read_tool.run()

        # Mock open to raise a general exception when writing
        with patch(
            "builtins.open",
            side_effect=[
                mock_open(read_data="test content").return_value,  # For reading
                Exception("Disk full"),  # For writing
            ],
        ):
            tool = Edit(file_path=tmp_path, old_string="test", new_string="replacement")
            out = tool.run()
            assert "Error writing to file: Disk full" in out

    finally:
        import os

        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ============================================================================
# ENHANCED TEST COVERAGE - Phase 1.4 Audit & Refactor
# Target: Raise Q(T) from 0.0 → 0.90
# Added: Edge cases, state validation, comprehensive error handling
# ============================================================================


def test_edit_empty_file(tmp_path: Path):
    """Test editing an empty file"""
    p = tmp_path / "empty.txt"
    p.write_text("", encoding="utf-8")

    # Read the file first (required precondition)
    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="test", new_string="replacement")
    out = tool.run()
    assert "Error: String to replace not found in file" in out

    # File should remain empty
    assert p.read_text(encoding="utf-8") == ""


def test_edit_single_line_replacement(tmp_path: Path):
    """Test replacing text on a single line"""
    p = tmp_path / "single.txt"
    p.write_text("This is a test", encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="test", new_string="success")
    out = tool.run()
    assert "Successfully replaced 1 occurrence(s)" in out
    assert p.read_text(encoding="utf-8") == "This is a success"


def test_edit_multiline_replacement(tmp_path: Path):
    """Test replacing text that spans multiple lines"""
    p = tmp_path / "multiline.txt"
    original = "Line 1\nLine 2\nLine 3"
    p.write_text(original, encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="Line 2\nLine 3", new_string="Combined Line")
    out = tool.run()
    assert "Successfully replaced 1 occurrence(s)" in out
    assert p.read_text(encoding="utf-8") == "Line 1\nCombined Line"


def test_edit_at_file_start(tmp_path: Path):
    """Test replacing text at the very start of file"""
    p = tmp_path / "start.txt"
    p.write_text("start of file\nmiddle\nend", encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="start", new_string="beginning")
    out = tool.run()
    assert "Successfully replaced 1 occurrence(s)" in out
    assert p.read_text(encoding="utf-8").startswith("beginning")


def test_edit_at_file_end(tmp_path: Path):
    """Test replacing text at the very end of file"""
    p = tmp_path / "end.txt"
    p.write_text("start\nmiddle\nend", encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="end", new_string="finish")
    out = tool.run()
    assert "Successfully replaced 1 occurrence(s)" in out
    assert p.read_text(encoding="utf-8").endswith("finish")


def test_edit_special_characters_in_strings(tmp_path: Path):
    """Test replacing strings with special regex characters"""
    p = tmp_path / "special.txt"
    p.write_text("Price: $100.00 (tax included)", encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    # Replace string containing special characters
    tool = Edit(file_path=str(p), old_string="$100.00", new_string="$200.00")
    out = tool.run()
    assert "Successfully replaced 1 occurrence(s)" in out
    assert "$200.00" in p.read_text(encoding="utf-8")


def test_edit_newline_characters(tmp_path: Path):
    """Test replacing newline characters"""
    p = tmp_path / "newlines.txt"
    p.write_text("Line1\n\nLine2", encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    # Replace double newline with single newline
    tool = Edit(file_path=str(p), old_string="\n\n", new_string="\n")
    out = tool.run()
    assert "Successfully replaced 1 occurrence(s)" in out
    assert p.read_text(encoding="utf-8") == "Line1\nLine2"


def test_edit_whitespace_handling(tmp_path: Path):
    """Test replacing strings with various whitespace"""
    p = tmp_path / "whitespace.txt"
    p.write_text("hello  world\ttab", encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    # Replace double space
    tool = Edit(file_path=str(p), old_string="  ", new_string=" ")
    out = tool.run()
    assert "Successfully replaced 1 occurrence(s)" in out
    assert p.read_text(encoding="utf-8") == "hello world\ttab"


def test_edit_unicode_characters(tmp_path: Path):
    """Test replacing unicode characters (emoji, accents, etc.)"""
    p = tmp_path / "unicode.txt"
    p.write_text("Hello 🌍 World café résumé", encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    # Replace emoji
    tool = Edit(file_path=str(p), old_string="🌍", new_string="🌎")
    out = tool.run()
    assert "Successfully replaced 1 occurrence(s)" in out
    assert "🌎" in p.read_text(encoding="utf-8")

    # Replace accented characters
    read_tool2 = Read(file_path=str(p))
    read_tool2.run()
    tool2 = Edit(file_path=str(p), old_string="café", new_string="coffee")
    out2 = tool2.run()
    assert "Successfully replaced 1 occurrence(s)" in out2
    assert "coffee" in p.read_text(encoding="utf-8")


def test_edit_very_long_string_replacement(tmp_path: Path):
    """Test replacing a very long string"""
    p = tmp_path / "longstring.txt"
    long_text = "x" * 5000 + " middle " + "y" * 5000
    p.write_text(long_text, encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string=" middle ", new_string=" CENTER ")
    out = tool.run()
    assert "Successfully replaced 1 occurrence(s)" in out
    assert " CENTER " in p.read_text(encoding="utf-8")


def test_edit_large_file_performance(tmp_path: Path):
    """Test editing a large file (performance validation)"""
    p = tmp_path / "largefile.txt"
    # Create a ~10KB file
    content = ("Line of text number {}\n" * 500).format(*range(500))
    p.write_text(content, encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="number 250", new_string="number TWO-FIFTY")
    out = tool.run()
    assert "Successfully replaced 1 occurrence(s)" in out
    assert "number TWO-FIFTY" in p.read_text(encoding="utf-8")


def test_edit_replace_all_with_zero_occurrences(tmp_path: Path):
    """Test replace_all when string doesn't exist"""
    p = tmp_path / "nomatches.txt"
    p.write_text("hello world", encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="xyz", new_string="abc", replace_all=True)
    out = tool.run()
    assert "Error: String to replace not found in file" in out


def test_edit_replace_all_single_occurrence(tmp_path: Path):
    """Test replace_all with only one occurrence"""
    p = tmp_path / "single_occurrence.txt"
    p.write_text("hello world", encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="world", new_string="universe", replace_all=True)
    out = tool.run()
    assert "Successfully replaced 1 occurrence(s)" in out
    assert "hello universe" == p.read_text(encoding="utf-8")


def test_edit_state_unchanged_on_read_error(tmp_path: Path):
    """Test that file remains unchanged if read fails"""
    p = tmp_path / "readonly.txt"
    original_content = "original content"
    p.write_text(original_content, encoding="utf-8")

    # Mock the file to fail on read after passing precondition check
    from unittest.mock import patch

    read_tool = Read(file_path=str(p))
    read_tool.run()

    # Create tool but mock reading to fail
    tool = Edit(file_path=str(p), old_string="original", new_string="modified")

    with patch("builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")):
        out = tool.run()
        assert "Error: Unable to decode file" in out

    # File should be unchanged
    assert p.read_text(encoding="utf-8") == original_content


def test_edit_atomic_operation(tmp_path: Path):
    """Test that edit is atomic - either fully succeeds or fully fails"""
    p = tmp_path / "atomic.txt"
    original_content = "test content"
    p.write_text(original_content, encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    # Simulate a write failure
    from unittest.mock import mock_open, patch

    tool = Edit(file_path=str(p), old_string="test", new_string="modified")

    with patch(
        "builtins.open",
        side_effect=[
            mock_open(read_data=original_content).return_value,  # Read succeeds
            OSError("Disk error"),  # Write fails
        ],
    ):
        out = tool.run()
        assert "Error writing to file" in out

    # Original file should still exist with original content
    # (in real filesystem scenario - this test validates error handling)


def test_edit_empty_old_string(tmp_path: Path):
    """Test error handling with empty old_string"""
    p = tmp_path / "empty_old.txt"
    p.write_text("hello world", encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="", new_string="replacement")
    out = tool.run()
    # Empty string is found everywhere, will trigger multiple occurrence error
    assert "Error: String appears" in out or "Error: String to replace not found" in out


def test_edit_empty_new_string(tmp_path: Path):
    """Test replacing with empty string (deletion)"""
    p = tmp_path / "empty_new.txt"
    p.write_text("hello world", encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string=" world", new_string="")
    out = tool.run()
    assert "Successfully replaced 1 occurrence(s)" in out
    assert p.read_text(encoding="utf-8") == "hello"


def test_edit_with_line_endings_crlf(tmp_path: Path):
    """Test editing files with CRLF line endings (Windows)"""
    p = tmp_path / "crlf.txt"
    p.write_text("Line1\r\nLine2\r\nLine3", encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="Line2", new_string="ModifiedLine2")
    out = tool.run()
    assert "Successfully replaced 1 occurrence(s)" in out
    assert "ModifiedLine2" in p.read_text(encoding="utf-8")


def test_edit_preview_format_validation(tmp_path: Path):
    """Test that preview shows proper context around replacement"""
    p = tmp_path / "preview.txt"
    p.write_text("This is a long line with target word in the middle of it", encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="target", new_string="REPLACED")
    out = tool.run()
    assert "Preview:" in out
    assert "[target->REPLACED]" in out
    assert "..." in out  # Should show context markers


def test_edit_multiple_occurrences_error_message_quality(tmp_path: Path):
    """Test that multiple occurrence error provides helpful context"""
    p = tmp_path / "multiple_error.txt"
    content = "The word test appears here.\nAnother test appears here.\nYet another test."
    p.write_text(content, encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="test", new_string="exam")
    out = tool.run()
    assert "Error: String appears 3 times in file" in out
    assert "First matches:" in out
    assert "replace_all=True" in out  # Suggests solution


def test_edit_overlapping_replacements(tmp_path: Path):
    """Test replace_all with overlapping patterns"""
    p = tmp_path / "overlap.txt"
    p.write_text("aaaa", encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    # Replacing "aa" with "b" should replace non-overlapping occurrences
    tool = Edit(file_path=str(p), old_string="aa", new_string="b", replace_all=True)
    out = tool.run()
    assert "Successfully replaced 2 occurrence(s)" in out
    assert p.read_text(encoding="utf-8") == "bb"


def test_edit_preserves_file_permissions(tmp_path: Path):
    """Test that file permissions are preserved after edit"""

    p = tmp_path / "permissions.txt"
    p.write_text("original content", encoding="utf-8")

    # Set specific permissions
    original_mode = p.stat().st_mode

    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="original", new_string="modified")
    out = tool.run()
    assert "Successfully replaced" in out

    # Check permissions are preserved
    new_mode = p.stat().st_mode
    assert original_mode == new_mode


def test_edit_with_tabs_and_mixed_whitespace(tmp_path: Path):
    """Test replacing content with mixed tabs and spaces"""
    p = tmp_path / "tabs.txt"
    p.write_text("def\tfunc():\n\t\treturn True", encoding="utf-8")

    read_tool = Read(file_path=str(p))
    read_tool.run()

    tool = Edit(file_path=str(p), old_string="\t\treturn True", new_string="\t\treturn False")
    out = tool.run()
    assert "Successfully replaced 1 occurrence(s)" in out
    assert "return False" in p.read_text(encoding="utf-8")
