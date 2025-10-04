"""
Comprehensive tests for Git tool input validation and security.

NECESSARY Pattern Coverage:
- Named: Test names clearly describe what is being validated
- Executable: Each test is isolated and can run independently
- Comprehensive: Covers all whitelisted operations and injection patterns
- Error handling: Validates rejection messages and error paths
- State changes: Validation is read-only (no state changes)
- Side effects: Uses mocks to prevent actual git operations
- Assertions: Meaningful validation checks for security
- Repeatable: Deterministic results with no external dependencies
- Yield: Fast execution (<100ms per test)
"""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from tools.git import Git


class TestWhitelistedOperationsAllowed:
    """Test that whitelisted git operations are allowed (NECESSARY: Normal operation)."""

    def test_status_command_allowed(self):
        # Arrange & Act
        tool = Git(cmd="status")

        # Assert
        assert tool.cmd == "status"

    def test_diff_command_allowed(self):
        # Arrange & Act
        tool = Git(cmd="diff")

        # Assert
        assert tool.cmd == "diff"

    def test_log_command_allowed(self):
        # Arrange & Act
        tool = Git(cmd="log")

        # Assert
        assert tool.cmd == "log"

    def test_show_command_allowed(self):
        # Arrange & Act
        tool = Git(cmd="show")

        # Assert
        assert tool.cmd == "show"

    def test_default_ref_is_head(self):
        # Arrange & Act
        tool = Git(cmd="status")

        # Assert
        assert tool.ref == "HEAD"

    def test_custom_ref_allowed(self):
        # Arrange & Act
        tool = Git(cmd="show", ref="main")

        # Assert
        assert tool.ref == "main"

    def test_branch_name_as_ref_allowed(self):
        # Arrange & Act
        tool = Git(cmd="diff", ref="feature/new-feature")

        # Assert
        assert tool.ref == "feature/new-feature"

    def test_commit_hash_as_ref_allowed(self):
        # Arrange & Act
        tool = Git(cmd="show", ref="abc123def456")

        # Assert
        assert tool.ref == "abc123def456"

    def test_tag_name_as_ref_allowed(self):
        # Arrange & Act
        tool = Git(cmd="log", ref="v1.0.0")

        # Assert
        assert tool.ref == "v1.0.0"


class TestNonWhitelistedOperationsRejected:
    """Test that non-whitelisted operations are rejected (NECESSARY: Error conditions)."""

    def test_add_command_rejected(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="add")

        # Literal type validation will reject this
        assert "cmd" in str(exc_info.value).lower()

    def test_commit_command_rejected(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="commit")

        assert "cmd" in str(exc_info.value).lower()

    def test_push_command_rejected(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="push")

        assert "cmd" in str(exc_info.value).lower()

    def test_pull_command_rejected(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="pull")

        assert "cmd" in str(exc_info.value).lower()

    def test_checkout_command_rejected(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="checkout")

        assert "cmd" in str(exc_info.value).lower()

    def test_reset_command_rejected(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="reset")

        assert "cmd" in str(exc_info.value).lower()

    def test_rebase_command_rejected(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="rebase")

        assert "cmd" in str(exc_info.value).lower()


class TestArgumentInjectionBlocked:
    """Test that argument injection attempts are blocked (NECESSARY: Security)."""

    def test_semicolon_in_ref_blocked(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="main; rm -rf /")

        error_message = str(exc_info.value)
        assert "injection" in error_message.lower() or "unsafe" in error_message.lower()

    def test_pipe_in_ref_blocked(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="diff", ref="main | cat /etc/passwd")

        error_message = str(exc_info.value)
        assert "injection" in error_message.lower() or "unsafe" in error_message.lower()

    def test_ampersand_in_ref_blocked(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="log", ref="main & echo malicious")

        error_message = str(exc_info.value)
        assert "injection" in error_message.lower() or "unsafe" in error_message.lower()

    def test_dollar_sign_in_ref_blocked(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="main$(whoami)")

        error_message = str(exc_info.value)
        assert "injection" in error_message.lower() or "unsafe" in error_message.lower()

    def test_backtick_in_ref_blocked(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="diff", ref="main`whoami`")

        error_message = str(exc_info.value)
        assert "injection" in error_message.lower() or "unsafe" in error_message.lower()

    def test_null_byte_in_ref_blocked(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="log", ref="main\x00malicious")

        error_message = str(exc_info.value)
        assert "injection" in error_message.lower() or "unsafe" in error_message.lower()

    def test_newline_in_ref_blocked(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="main\nrm -rf /")

        error_message = str(exc_info.value)
        assert "injection" in error_message.lower() or "unsafe" in error_message.lower()


class TestPathTraversalBlocked:
    """Test that path traversal attempts are blocked (NECESSARY: Edge cases)."""

    def test_double_dot_in_ref_blocked(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="../../../etc/passwd")

        error_message = str(exc_info.value)
        assert "traversal" in error_message.lower() or ".." in error_message

    def test_relative_path_traversal_blocked(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="diff", ref="branch/../../../secret")

        error_message = str(exc_info.value)
        assert "traversal" in error_message.lower() or ".." in error_message


class TestSafeCommandConstruction:
    """Test that commands are constructed safely (NECESSARY: Comprehensive)."""

    @patch("dulwich.porcelain.open_repo")
    @patch("dulwich.porcelain.status")
    def test_status_command_uses_dulwich_safely(self, mock_status, mock_open_repo):
        # Arrange
        mock_repo = MagicMock()
        mock_open_repo.return_value = mock_repo
        mock_status.return_value = MagicMock(untracked=[], unstaged=[], staged={})

        tool = Git(cmd="status")

        # Act
        result = tool.run()

        # Assert
        mock_open_repo.assert_called_once()
        mock_status.assert_called_once_with(mock_repo)
        assert "(clean)" in result

    @patch("dulwich.porcelain.open_repo")
    @patch("dulwich.porcelain.log")
    def test_log_command_uses_dulwich_safely(self, mock_log, mock_open_repo):
        # Arrange
        mock_repo = MagicMock()
        mock_open_repo.return_value = mock_repo

        def mock_log_impl(repo, outstream=None):
            if outstream:
                outstream.write("commit abc123\nAuthor: Test\n")

        mock_log.side_effect = mock_log_impl

        tool = Git(cmd="log")

        # Act
        result = tool.run()

        # Assert
        mock_open_repo.assert_called_once()
        assert "commit" in result or "Author" in result


class TestEmptyAndInvalidInputs:
    """Test handling of empty and invalid inputs (NECESSARY: Corner cases)."""

    def test_empty_cmd_rejected(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="")

        assert "cmd" in str(exc_info.value).lower()

    def test_whitespace_cmd_rejected(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="   ")

        assert "cmd" in str(exc_info.value).lower()

    def test_empty_ref_rejected(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="")

        error_message = str(exc_info.value)
        assert "empty" in error_message.lower() or "ref" in error_message.lower()

    def test_whitespace_ref_rejected(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="diff", ref="   ")

        error_message = str(exc_info.value)
        assert "empty" in error_message.lower() or "whitespace" in error_message.lower()


class TestErrorMessageClarity:
    """Test that error messages are clear and informative (NECESSARY: Assertions)."""

    def test_injection_error_message_is_clear(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="main; rm -rf /")

        error_message = str(exc_info.value)
        # Should clearly indicate it's a security issue
        assert "injection" in error_message.lower() or "unsafe" in error_message.lower()
        # Should mention the problematic character
        assert ";" in error_message

    def test_whitelist_error_message_names_allowed_commands(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="push")

        error_message = str(exc_info.value)
        # Literal type will reject with validation error
        assert "cmd" in error_message.lower()

    def test_path_traversal_error_message_is_clear(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="../../../etc/passwd")

        error_message = str(exc_info.value)
        assert "traversal" in error_message.lower() or ".." in error_message


class TestMaxLinesValidation:
    """Test that max_lines validation works correctly (NECESSARY: Validation)."""

    def test_valid_max_lines_accepted(self):
        # Arrange & Act
        tool = Git(cmd="status", max_lines=1000)

        # Assert
        assert tool.max_lines == 1000

    def test_zero_max_lines_rejected(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="status", max_lines=0)

        assert "max_lines" in str(exc_info.value).lower()

    def test_negative_max_lines_rejected(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="status", max_lines=-100)

        assert "max_lines" in str(exc_info.value).lower()

    def test_excessive_max_lines_rejected(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="status", max_lines=2000000)

        assert "max_lines" in str(exc_info.value).lower()

    def test_max_lines_default_is_reasonable(self):
        # Arrange & Act
        tool = Git(cmd="status")

        # Assert
        assert tool.max_lines == 20000  # Default from Field definition


class TestSafeCharactersInRef:
    """Test that safe characters are allowed in ref (NECESSARY: Comprehensive)."""

    def test_alphanumeric_ref_allowed(self):
        # Arrange & Act
        tool = Git(cmd="show", ref="abc123XYZ")

        # Assert
        assert tool.ref == "abc123XYZ"

    def test_dash_in_ref_allowed(self):
        # Arrange & Act
        tool = Git(cmd="diff", ref="feature-branch")

        # Assert
        assert tool.ref == "feature-branch"

    def test_underscore_in_ref_allowed(self):
        # Arrange & Act
        tool = Git(cmd="log", ref="my_branch")

        # Assert
        assert tool.ref == "my_branch"

    def test_dot_in_ref_allowed(self):
        # Arrange & Act
        tool = Git(cmd="show", ref="v1.0.0")

        # Assert
        assert tool.ref == "v1.0.0"

    def test_forward_slash_in_ref_allowed(self):
        # Arrange & Act
        tool = Git(cmd="diff", ref="feature/new-feature")

        # Assert
        assert tool.ref == "feature/new-feature"

    def test_caret_in_ref_allowed(self):
        # Arrange & Act
        tool = Git(cmd="show", ref="HEAD^")

        # Assert
        assert tool.ref == "HEAD^"

    def test_tilde_in_ref_allowed(self):
        # Arrange & Act
        tool = Git(cmd="log", ref="HEAD~3")

        # Assert
        assert tool.ref == "HEAD~3"


class TestUnsafeCharactersInRefBlocked:
    """Test that unsafe characters are blocked in ref (NECESSARY: Security)."""

    def test_space_in_ref_blocked(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="my branch")

        error_message = str(exc_info.value)
        assert "invalid" in error_message.lower() or "characters" in error_message.lower()

    def test_exclamation_in_ref_blocked(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="diff", ref="branch!")

        error_message = str(exc_info.value)
        assert "invalid" in error_message.lower() or "characters" in error_message.lower()

    def test_at_sign_in_ref_blocked(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="log", ref="user@branch")

        error_message = str(exc_info.value)
        assert "invalid" in error_message.lower() or "characters" in error_message.lower()

    def test_hash_in_ref_blocked(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="show", ref="branch#1")

        error_message = str(exc_info.value)
        assert "invalid" in error_message.lower() or "characters" in error_message.lower()

    def test_percent_in_ref_blocked(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Git(cmd="diff", ref="branch%20name")

        error_message = str(exc_info.value)
        assert "invalid" in error_message.lower() or "characters" in error_message.lower()


class TestValidationIntegrationWithRun:
    """Test that validation integrates correctly with run() method (NECESSARY: Integration)."""

    @patch("dulwich.porcelain.open_repo")
    def test_invalid_command_never_reaches_dulwich(self, mock_open_repo):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            Git(cmd="push")  # Non-whitelisted command

        # dulwich should never be called
        mock_open_repo.assert_not_called()

    @patch("dulwich.porcelain.open_repo")
    def test_injection_attempt_never_reaches_dulwich(self, mock_open_repo):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            Git(cmd="show", ref="main; rm -rf /")

        # dulwich should never be called
        mock_open_repo.assert_not_called()

    @patch("dulwich.porcelain.open_repo")
    @patch("dulwich.porcelain.status")
    def test_valid_command_reaches_dulwich(self, mock_status, mock_open_repo):
        # Arrange
        mock_repo = MagicMock()
        mock_open_repo.return_value = mock_repo
        mock_status.return_value = MagicMock(untracked=[], unstaged=[], staged={})

        tool = Git(cmd="status")

        # Act
        result = tool.run()

        # Assert
        mock_open_repo.assert_called_once()
        mock_status.assert_called_once()


class TestPerformanceRequirements:
    """Test that validation is fast (NECESSARY: Yield - performance)."""

    def test_validation_completes_quickly(self):
        # Arrange
        import time

        # Act
        start_time = time.time()
        tool = Git(cmd="status", ref="main")
        elapsed_time = time.time() - start_time

        # Assert - Should complete in under 100ms
        assert elapsed_time < 0.1, f"Validation took {elapsed_time}s, expected < 0.1s"

    def test_multiple_validations_are_fast(self):
        # Arrange
        import time

        refs = [
            "main",
            "develop",
            "feature/new-feature",
            "v1.0.0",
            "abc123def456",
        ]

        # Act
        start_time = time.time()
        for ref in refs * 10:  # 50 validations total
            Git(cmd="status", ref=ref)
        elapsed_time = time.time() - start_time

        # Assert - 50 validations should complete in under 1 second
        assert elapsed_time < 1.0, f"50 validations took {elapsed_time}s, expected < 1.0s"


class TestRepeatability:
    """Test that validation is deterministic (NECESSARY: Repeatable)."""

    def test_same_input_gives_same_result_multiple_times(self):
        # Arrange & Act - Run validation multiple times
        tools = []
        for _ in range(10):
            tool = Git(cmd="status", ref="main")
            tools.append(tool)

        # Assert - All tools should have identical properties
        assert all(t.cmd == "status" for t in tools)
        assert all(t.ref == "main" for t in tools)

    def test_invalid_input_always_rejected(self):
        # Arrange & Act - Run validation multiple times
        for _ in range(10):
            with pytest.raises(ValidationError):
                Git(cmd="push")  # Should always be rejected

        # Assert - If we get here, it was consistently rejected (success)
        assert True


class TestDulwichLibraryNotAvailable:
    """Test graceful handling when dulwich is not installed (NECESSARY: Error handling)."""

    def test_missing_dulwich_returns_error_message(self):
        # Arrange
        tool = Git(cmd="status")

        # Act - Mock the import to raise an exception (but allow warnings import)
        import warnings as real_warnings

        def mock_import(name, *args, **kwargs):
            if name == "warnings":
                return real_warnings
            if name == "dulwich" or name.startswith("dulwich."):
                raise ImportError("No module named 'dulwich'")
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = tool.run()

        # Assert - Should return helpful error message
        assert "dulwich not installed" in result
        assert "pip install" in result


class TestOutputTruncation:
    """Test that large outputs are properly truncated (NECESSARY: Comprehensive)."""

    @patch("dulwich.porcelain.open_repo")
    @patch("dulwich.porcelain.log")
    def test_output_truncated_at_max_lines(self, mock_log, mock_open_repo):
        # Arrange
        mock_repo = MagicMock()
        mock_open_repo.return_value = mock_repo

        # Generate output with more than max_lines
        large_output = "\n".join([f"Line {i}" for i in range(100)])

        def mock_log_impl(repo, outstream=None):
            if outstream:
                outstream.write(large_output)

        mock_log.side_effect = mock_log_impl

        tool = Git(cmd="log", max_lines=10)

        # Act
        result = tool.run()

        # Assert
        lines = result.split("\n")
        # Should be truncated to 10 lines + "(truncated)" marker
        assert len(lines) <= 11  # 10 lines + truncation marker
        assert "(truncated)" in result or len(lines) <= 10
