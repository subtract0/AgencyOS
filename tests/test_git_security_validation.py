"""Security validation tests for Git tool.

Tests comprehensive Pydantic validation to ensure:
1. Command whitelisting prevents unauthorized operations
2. Parameter validation blocks injection attempts
3. Safe defaults are enforced
"""

import pytest
from pydantic import ValidationError

from tools.git import Git


class TestGitCommandWhitelisting:
    """Test that only whitelisted commands are accepted."""

    def test_status_command_allowed(self):
        """Verify status command is whitelisted."""
        tool = Git(cmd="status")
        assert tool.cmd == "status"

    def test_diff_command_allowed(self):
        """Verify diff command is whitelisted."""
        tool = Git(cmd="diff")
        assert tool.cmd == "diff"

    def test_log_command_allowed(self):
        """Verify log command is whitelisted."""
        tool = Git(cmd="log")
        assert tool.cmd == "log"

    def test_show_command_allowed(self):
        """Verify show command is whitelisted."""
        tool = Git(cmd="show")
        assert tool.cmd == "show"

    def test_push_command_rejected(self):
        """Verify destructive push command is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="push")
        assert "cmd" in str(exc_info.value)

    def test_commit_command_rejected(self):
        """Verify write command 'commit' is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="commit")
        assert "cmd" in str(exc_info.value)

    def test_add_command_rejected(self):
        """Verify write command 'add' is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="add")
        assert "cmd" in str(exc_info.value)

    def test_arbitrary_command_rejected(self):
        """Verify arbitrary commands are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="rm -rf /")
        assert "cmd" in str(exc_info.value)


class TestGitReferenceValidation:
    """Test that git references are properly validated."""

    def test_head_reference_allowed(self):
        """Verify HEAD reference is allowed."""
        tool = Git(cmd="show", ref="HEAD")
        assert tool.ref == "HEAD"

    def test_branch_name_allowed(self):
        """Verify normal branch names are allowed."""
        tool = Git(cmd="show", ref="main")
        assert tool.ref == "main"

    def test_commit_hash_allowed(self):
        """Verify commit hashes are allowed."""
        tool = Git(cmd="show", ref="abc123def456")
        assert tool.ref == "abc123def456"

    def test_command_injection_in_ref_rejected(self):
        """Verify command injection attempts in ref are blocked."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="HEAD; rm -rf /")
        assert "ref" in str(exc_info.value)

    def test_backtick_injection_in_ref_rejected(self):
        """Verify backtick injection attempts are blocked."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="`whoami`")
        assert "ref" in str(exc_info.value)

    def test_dollar_injection_in_ref_rejected(self):
        """Verify dollar sign injection attempts are blocked."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="$DANGEROUS_VAR")
        assert "ref" in str(exc_info.value)

    def test_pipe_injection_in_ref_rejected(self):
        """Verify pipe injection attempts are blocked."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="HEAD | cat /etc/passwd")
        assert "ref" in str(exc_info.value)

    def test_ampersand_injection_in_ref_rejected(self):
        """Verify ampersand injection attempts are blocked."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="HEAD && echo hacked")
        assert "ref" in str(exc_info.value)


class TestGitMaxLinesValidation:
    """Test that max_lines parameter is properly validated."""

    def test_default_max_lines(self):
        """Verify default max_lines value."""
        tool = Git(cmd="status")
        assert tool.max_lines == 20000

    def test_positive_max_lines_allowed(self):
        """Verify positive max_lines values are allowed."""
        tool = Git(cmd="status", max_lines=100)
        assert tool.max_lines == 100

    def test_negative_max_lines_rejected(self):
        """Verify negative max_lines values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="status", max_lines=-1)
        assert "max_lines" in str(exc_info.value)

    def test_zero_max_lines_rejected(self):
        """Verify zero max_lines value is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="status", max_lines=0)
        assert "max_lines" in str(exc_info.value)

    def test_excessive_max_lines_rejected(self):
        """Verify excessively large max_lines values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="status", max_lines=1000001)
        assert "max_lines" in str(exc_info.value)


class TestGitSecurityEdgeCases:
    """Test edge cases and complex injection attempts."""

    def test_null_byte_injection_rejected(self):
        """Verify null byte injection attempts are blocked."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="HEAD\x00malicious")
        assert "ref" in str(exc_info.value)

    def test_newline_injection_rejected(self):
        """Verify newline injection attempts are blocked."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="HEAD\nrm -rf /")
        assert "ref" in str(exc_info.value)

    def test_unicode_injection_rejected(self):
        """Verify unicode-based injection attempts are blocked."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="HEAD\u0000malicious")
        assert "ref" in str(exc_info.value)

    def test_path_traversal_in_ref_rejected(self):
        """Verify path traversal attempts are blocked."""
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="../../../etc/passwd")
        assert "ref" in str(exc_info.value)

    def test_empty_command_rejected(self):
        """Verify empty command strings are rejected."""
        with pytest.raises(ValidationError):
            Git(cmd="")

    def test_whitespace_only_command_rejected(self):
        """Verify whitespace-only commands are rejected."""
        with pytest.raises(ValidationError):
            Git(cmd="   ")
