from tools import Git


def test_git_status_current_repo():
    tool = Git(cmd="status")
    out = tool.run()
    print("\nSTATUS:\n" + out)
    assert isinstance(out, str)
    assert out.strip() != ""
    lines = [l for l in out.splitlines() if l.strip()]
    markers = ("?? ", " M ", " A ", " D ", " S ")
    has_marker = any(l.startswith(markers) for l in lines)
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
    lines = out.splitlines()
    # Should respect max_lines limit or be shorter if less history


def test_git_unknown_command():
    tool = Git(cmd="invalid_command")
    out = tool.run()
    assert "Exit code: 1" in out
    assert "Unknown cmd" in out


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
