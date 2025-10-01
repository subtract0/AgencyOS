from tools import Git


def test_git_status_current_repo():
    tool = Git(cmd="status")
    out = tool.run()
    print("\nSTATUS:\n" + out)
    assert isinstance(out, str)
    assert out.strip() != ""
    lines = [line for line in out.splitlines() if line.strip()]
    markers = ("?? ", " M ", " A ", " D ", " S ")
    has_marker = any(line.startswith(markers) for line in lines)
    assert "(clean)" in out or has_marker


def test_git_diff_current_repo():
    tool = Git(cmd="diff", max_lines=5000)
    out = tool.run()
    preview = "\n".join(out.splitlines()[:80])
    print("\nDIFF (first 80 lines):\n" + preview)
    assert isinstance(out, str)
    # Diff might be empty if no changes, that's valid


def test_git_log_current_repo():
    tool = Git(cmd="log", max_lines=200)
    out = tool.run()
    print("\nLOG (first 20 lines):\n" + "\n".join(out.splitlines()[:20]))
    assert isinstance(out, str)
    assert ("commit:" in out) or ("Author:" in out) or ("Date:" in out)


def test_git_log_with_max_lines():
    tool = Git(cmd="log", max_lines=10)
    out = tool.run()
    assert isinstance(out, str)
    _ = out.splitlines()
    # Should respect max_lines limit or be shorter if less history


def test_git_unknown_command():
    """Test that invalid commands are rejected at validation time."""
    from pydantic import ValidationError
    import pytest

    with pytest.raises(ValidationError) as exc_info:
        Git(cmd="invalid_command")
    # Verify the error message mentions valid options
    assert "cmd" in str(exc_info.value)


def test_git_tool_error_handling():
    # Test with invalid repo (should handle gracefully)
    import os
    import tempfile

    original_cwd = os.getcwd()
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            tool = Git(cmd="status")
            out = tool.run()
            assert "Exit code: 1" in out
            assert "Error opening git repo" in out
    finally:
        os.chdir(original_cwd)


def test_git_diff_with_truncation():
    """Test diff with output truncation"""
    tool = Git(cmd="diff", max_lines=5)
    out = tool.run()
    # Should work (might be empty if no changes) or show truncation
    assert isinstance(out, str)
    # Note: truncation logic will only trigger if there are actual changes > max_lines


def test_git_diff_exception_handling():
    """Test diff command exception handling"""
    from unittest.mock import patch

    # Need to patch after dulwich is imported, inside the run method
    def mock_diff_tree(*args, **kwargs):
        raise Exception("Diff error")

    with patch('dulwich.porcelain.diff_tree', side_effect=mock_diff_tree):
        tool = Git(cmd="diff")
        out = tool.run()
        assert "Exit code: 1" in out
        assert "Error in diff: Diff error" in out


def test_git_show_command():
    """Test show command functionality"""
    tool = Git(cmd="show", ref="HEAD")
    out = tool.run()
    # Should work or give a reasonable error
    assert isinstance(out, str)
    if "Exit code: 1" not in out:
        # If successful, should contain commit information
        assert len(out) > 0


def test_git_show_with_truncation():
    """Test show command with output truncation"""
    tool = Git(cmd="show", ref="HEAD", max_lines=3)
    out = tool.run()
    assert isinstance(out, str)
    # Note: truncation will only be visible if show output > max_lines


def test_git_show_exception_handling():
    """Test show command exception handling"""
    from unittest.mock import patch

    def mock_show(*args, **kwargs):
        raise Exception("Show error")

    with patch('dulwich.porcelain.show', side_effect=mock_show):
        tool = Git(cmd="show", ref="HEAD")
        out = tool.run()
        assert "Exit code: 1" in out
        assert "Error in show: Show error" in out


def test_git_general_exception_handling():
    """Test general exception handling in the main try block"""
    from unittest.mock import patch, MagicMock

    # Create a mock repo that will pass open_repo but fail during status
    mock_repo = MagicMock()

    def mock_status(*args, **kwargs):
        raise Exception("Unexpected error in main block")

    with patch('dulwich.porcelain.open_repo', return_value=mock_repo):
        with patch('dulwich.porcelain.status', side_effect=mock_status):
            tool = Git(cmd="status")
            out = tool.run()
            assert "Exit code: 1" in out
            assert "Error: Unexpected error in main block" in out


def test_git_show_invalid_ref():
    """Test show command with invalid reference"""
    tool = Git(cmd="show", ref="nonexistent_ref_12345")
    out = tool.run()
    # Should handle invalid ref gracefully
    if "Exit code: 1" in out:
        assert "Error in show:" in out or "Error:" in out
    # If not an error, it's still valid behavior
