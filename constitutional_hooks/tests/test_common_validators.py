"""
Tests for common validator functions (TDD).

Following Agency OS TDD principle: Write tests BEFORE implementation.
"""

from unittest.mock import Mock, patch


class TestValidatePromptContent:
    """Test prompt content validation against Article I rules."""

    def test_compliant_prompt_passes(self):
        """Compliant prompts should return Ok(True)."""
        from constitutional_hooks.common_validators import validate_prompt_content

        result = validate_prompt_content("Implement feature X with full test coverage")
        assert result.is_ok()
        assert result.unwrap() is True

    def test_skip_tests_pattern_blocked(self):
        """Prompts containing 'skip tests' should be blocked."""
        from constitutional_hooks.common_validators import validate_prompt_content

        result = validate_prompt_content("skip tests for now")
        assert result.is_err()
        error = result.unwrap_err()
        assert "Article I" in error.rule_id
        assert "prohibited pattern" in error.message.lower()

    def test_dict_any_any_pattern_blocked(self):
        """Prompts containing 'Dict[Any, Any]' should be blocked."""
        from constitutional_hooks.common_validators import validate_prompt_content

        result = validate_prompt_content("Use Dict[Any, Any] for config")
        assert result.is_err()
        error = result.unwrap_err()
        assert "Article I" in error.rule_id

    def test_no_verify_pattern_blocked(self):
        """Prompts containing '--no-verify' should be blocked."""
        from constitutional_hooks.common_validators import validate_prompt_content

        result = validate_prompt_content("git commit --no-verify")
        assert result.is_err()
        error = result.unwrap_err()
        assert "Article I" in error.rule_id

    def test_case_insensitive_matching(self):
        """Pattern matching should be case-insensitive."""
        from constitutional_hooks.common_validators import validate_prompt_content

        result = validate_prompt_content("SKIP TESTS for this")
        assert result.is_err()

    def test_empty_prompt_passes(self):
        """Empty prompt should pass (no violations)."""
        from constitutional_hooks.common_validators import validate_prompt_content

        result = validate_prompt_content("")
        assert result.is_ok()


class TestCheckTestResults:
    """Test Article II enforcement: 100% test pass rate."""

    @patch("subprocess.run")
    @patch("builtins.open")
    def test_all_tests_pass_returns_ok(self, mock_open, mock_run):
        """All tests passing should return Ok(True)."""
        import io

        from constitutional_hooks.common_validators import check_test_results

        # Mock pytest success output
        mock_run.return_value = Mock(returncode=0, stdout="")

        # Mock JSON report file
        mock_file = io.StringIO('{"total": 100, "passed": 100, "failed": 0, "skipped": 0}')
        mock_open.return_value.__enter__.return_value = mock_file

        result = check_test_results()
        assert result.is_ok()
        assert result.unwrap() is True

    @patch("subprocess.run")
    @patch("builtins.open")
    def test_failed_tests_returns_err(self, mock_open, mock_run):
        """Failed tests should return Err with Article II violation."""
        import io

        from constitutional_hooks.common_validators import check_test_results

        # Mock pytest with failures
        mock_run.return_value = Mock(returncode=1, stdout="")

        # Mock JSON report file
        mock_file = io.StringIO('{"total": 100, "passed": 95, "failed": 5, "skipped": 0}')
        mock_open.return_value.__enter__.return_value = mock_file

        result = check_test_results()
        assert result.is_err()
        error = result.unwrap_err()
        assert "Article II" in error.rule_id
        assert "5" in error.message  # Should mention number of failures

    @patch("subprocess.run")
    @patch("builtins.open")
    def test_skipped_tests_returns_err(self, mock_open, mock_run):
        """Skipped tests should return Err (incomplete context)."""
        import io

        from constitutional_hooks.common_validators import check_test_results

        mock_run.return_value = Mock(returncode=0, stdout="")

        # Mock JSON report file
        mock_file = io.StringIO('{"total": 100, "passed": 90, "failed": 0, "skipped": 10}')
        mock_open.return_value.__enter__.return_value = mock_file

        result = check_test_results()
        assert result.is_err()
        error = result.unwrap_err()
        assert "Article II" in error.rule_id
        assert "skipped" in error.message.lower()

    @patch("subprocess.run")
    def test_no_tests_run_returns_err(self, mock_run):
        """No tests run should return Err (no verification)."""
        from constitutional_hooks.common_validators import check_test_results

        mock_run.return_value = Mock(
            returncode=0, stdout='{"total": 0, "passed": 0, "failed": 0, "skipped": 0}'
        )

        result = check_test_results()
        assert result.is_err()
        error = result.unwrap_err()
        assert "Article II" in error.rule_id

    @patch("subprocess.run")
    def test_pytest_execution_error_returns_err(self, mock_run):
        """Pytest execution errors should return Err."""
        from constitutional_hooks.common_validators import check_test_results

        mock_run.side_effect = Exception("pytest not found")

        result = check_test_results()
        assert result.is_err()


class TestCheckGitStatus:
    """Test git status validation for clean working directory."""

    @patch("subprocess.run")
    def test_clean_working_directory_returns_ok(self, mock_run):
        """Clean git status should return Ok(True)."""
        from constitutional_hooks.common_validators import check_git_status

        mock_run.return_value = Mock(returncode=0, stdout="")

        result = check_git_status()
        assert result.is_ok()
        assert result.unwrap() is True

    @patch("subprocess.run")
    def test_dirty_working_directory_returns_err(self, mock_run):
        """Dirty git status should return Err."""
        from constitutional_hooks.common_validators import check_git_status

        mock_run.return_value = Mock(returncode=0, stdout=" M file.py\n?? untracked.py\n")

        result = check_git_status()
        assert result.is_err()
        error = result.unwrap_err()
        assert "dirty" in error.message.lower() or "uncommitted" in error.message.lower()

    @patch("subprocess.run")
    def test_git_command_error_returns_err(self, mock_run):
        """Git command errors should return Err."""
        from constitutional_hooks.common_validators import check_git_status

        mock_run.side_effect = Exception("not a git repository")

        result = check_git_status()
        assert result.is_err()
