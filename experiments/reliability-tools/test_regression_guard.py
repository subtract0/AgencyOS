"""
Tests for Regression Guard - Phase 1, Task 1
Zero-regression verification before commits

TDD: Tests written FIRST (Article VI compliance)
"""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from tools.regression_guard import (
    RegressionGuard,
    ChangedFile,
    TestExecutionResult,
    RegressionCheckResult,
)
from shared.type_definitions.result import Ok, Err


class TestRegressionGuardInit:
    """Test RegressionGuard initialization"""

    def test_init_with_defaults(self):
        """Should initialize with default project root"""
        guard = RegressionGuard()
        assert guard.project_root == Path.cwd()
        assert guard.test_timeout == 300  # 5 minutes default

    def test_init_with_custom_root(self, tmp_path):
        """Should initialize with custom project root"""
        guard = RegressionGuard(project_root=tmp_path)
        assert guard.project_root == tmp_path


class TestGetChangedFiles:
    """Test detection of changed files"""

    @patch("subprocess.run")
    def test_get_changed_files_success(self, mock_run):
        """Should detect changed files from git diff"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="M\ttools/example.py\nA\ttests/test_example.py\n",
            stderr="",
        )

        guard = RegressionGuard()
        changed = guard.get_changed_files()

        assert changed.is_ok()
        files = changed.unwrap()
        assert len(files) == 2
        assert any(f.path == "tools/example.py" for f in files)
        assert any(f.path == "tests/test_example.py" for f in files)

    @patch("subprocess.run")
    def test_get_changed_files_with_staged(self, mock_run):
        """Should include staged files"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="M\ttools/staged.py\n",
            stderr="",
        )

        guard = RegressionGuard()
        changed = guard.get_changed_files(include_staged=True)

        assert changed.is_ok()
        mock_run.assert_called_once()
        # Should use --cached flag for staged files
        call_args = mock_run.call_args[0][0]
        assert "--cached" in call_args

    @patch("subprocess.run")
    def test_get_changed_files_git_error(self, mock_run):
        """Should handle git command errors"""
        mock_run.return_value = Mock(
            returncode=128, stdout="", stderr="fatal: not a git repository"
        )

        guard = RegressionGuard()
        changed = guard.get_changed_files()

        assert changed.is_err()
        error = changed.unwrap_err()
        assert "git" in error.lower()

    @patch("subprocess.run")
    def test_get_changed_files_empty(self, mock_run):
        """Should handle no changed files"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        guard = RegressionGuard()
        changed = guard.get_changed_files()

        assert changed.is_ok()
        files = changed.unwrap()
        assert len(files) == 0


class TestFindAffectedTests:
    """Test smart test selection"""

    def test_find_affected_tests_direct_mapping(self):
        """Should map tools/foo.py to tests/test_foo.py"""
        guard = RegressionGuard()
        changed = [ChangedFile(path="tools/git_unified.py", change_type="M")]

        tests = guard.find_affected_tests(changed)

        assert tests.is_ok()
        test_files = tests.unwrap()
        assert len(test_files) > 0
        # Should include direct test mapping
        assert any("test_git_unified" in str(t) for t in test_files)

    def test_find_affected_tests_agent_mapping(self):
        """Should map agent files to agent tests"""
        guard = RegressionGuard()
        changed = [ChangedFile(path="auditor_agent/auditor_agent.py", change_type="M")]

        tests = guard.find_affected_tests(changed)

        assert tests.is_ok()
        test_files = tests.unwrap()
        # Should map to agent tests
        assert any("auditor_agent" in str(t) or "test_auditor" in str(t) for t in test_files)

    def test_find_affected_tests_shared_changes(self):
        """Should run all tests when shared/ changes"""
        guard = RegressionGuard()
        changed = [ChangedFile(path="shared/type_definitions/result.py", change_type="M")]

        tests = guard.find_affected_tests(changed)

        assert tests.is_ok()
        test_files = tests.unwrap()
        # Shared changes affect many tests, should be comprehensive
        assert len(test_files) > 5

    def test_find_affected_tests_constitution_changes(self):
        """Should run all tests when constitution.md changes"""
        guard = RegressionGuard()
        changed = [ChangedFile(path="constitution.md", change_type="M")]

        tests = guard.find_affected_tests(changed)

        assert tests.is_ok()
        test_files = tests.unwrap()
        # Constitutional changes require constitutional/quality test coverage
        assert len(test_files) >= 3  # At least a few constitutional tests

    def test_find_affected_tests_test_file_changed(self):
        """Should run the test file itself when it changes"""
        guard = RegressionGuard()
        changed = [ChangedFile(path="tests/test_git_unified.py", change_type="M")]

        tests = guard.find_affected_tests(changed)

        assert tests.is_ok()
        test_files = tests.unwrap()
        # Should find the test file (check basename to handle absolute vs relative paths)
        assert any(t.name == "test_git_unified.py" for t in test_files)


class TestRunAffectedTests:
    """Test test execution"""

    @patch("subprocess.run")
    def test_run_affected_tests_all_pass(self, mock_run):
        """Should return success when all tests pass"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="====== 10 passed in 2.5s ======",
            stderr="",
        )

        guard = RegressionGuard()
        test_files = [Path("tests/test_example.py")]
        result = guard.run_affected_tests(test_files)

        assert result.is_ok()
        test_result = result.unwrap()
        assert test_result.passed
        assert test_result.total_tests > 0

    @patch("subprocess.run")
    def test_run_affected_tests_with_failures(self, mock_run):
        """Should return failure when tests fail"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="====== 8 passed, 2 failed in 3.1s ======",
            stderr="",
        )

        guard = RegressionGuard()
        test_files = [Path("tests/test_example.py")]
        result = guard.run_affected_tests(test_files)

        assert result.is_ok()
        test_result = result.unwrap()
        assert not test_result.passed
        assert test_result.failed_tests > 0

    @patch("subprocess.run")
    def test_run_affected_tests_timeout(self, mock_run):
        """Should handle test timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired("pytest", 300)

        guard = RegressionGuard(test_timeout=1)
        test_files = [Path("tests/test_example.py")]
        result = guard.run_affected_tests(test_files)

        assert result.is_err()
        error = result.unwrap_err()
        assert "timed out" in error.lower()

    @patch("subprocess.run")
    def test_run_affected_tests_empty_list(self, mock_run):
        """Should handle empty test list"""
        guard = RegressionGuard()
        test_files = []
        result = guard.run_affected_tests(test_files)

        assert result.is_ok()
        test_result = result.unwrap()
        assert test_result.passed
        assert test_result.total_tests == 0
        # Should not run pytest
        mock_run.assert_not_called()


class TestCheckRegression:
    """Test end-to-end regression check"""

    @patch("tools.regression_guard.RegressionGuard.get_changed_files")
    @patch("tools.regression_guard.RegressionGuard.find_affected_tests")
    @patch("tools.regression_guard.RegressionGuard.run_affected_tests")
    def test_check_regression_no_changes(
        self, mock_run_tests, mock_find_tests, mock_get_changed
    ):
        """Should pass when no files changed"""
        mock_get_changed.return_value = Ok([])

        guard = RegressionGuard()
        result = guard.check_regression()

        assert result.is_ok()
        check_result = result.unwrap()
        assert check_result.passed
        assert len(check_result.changed_files) == 0
        # Should not run tests if no changes
        mock_find_tests.assert_not_called()
        mock_run_tests.assert_not_called()

    @patch("tools.regression_guard.RegressionGuard.get_changed_files")
    @patch("tools.regression_guard.RegressionGuard.find_affected_tests")
    @patch("tools.regression_guard.RegressionGuard.run_affected_tests")
    def test_check_regression_all_tests_pass(
        self, mock_run_tests, mock_find_tests, mock_get_changed
    ):
        """Should pass when all affected tests pass"""
        mock_get_changed.return_value = Ok(
            [ChangedFile(path="tools/example.py", change_type="M")]
        )
        mock_find_tests.return_value = Ok([Path("tests/test_example.py")])
        mock_run_tests.return_value = Ok(
            TestExecutionResult(passed=True, total_tests=10, failed_tests=0, duration_seconds=2.5)
        )

        guard = RegressionGuard()
        result = guard.check_regression()

        assert result.is_ok()
        check_result = result.unwrap()
        assert check_result.passed
        assert len(check_result.changed_files) == 1
        assert len(check_result.affected_tests) == 1

    @patch("tools.regression_guard.RegressionGuard.get_changed_files")
    @patch("tools.regression_guard.RegressionGuard.find_affected_tests")
    @patch("tools.regression_guard.RegressionGuard.run_affected_tests")
    def test_check_regression_test_failures(
        self, mock_run_tests, mock_find_tests, mock_get_changed
    ):
        """Should fail when tests fail"""
        mock_get_changed.return_value = Ok(
            [ChangedFile(path="tools/example.py", change_type="M")]
        )
        mock_find_tests.return_value = Ok([Path("tests/test_example.py")])
        mock_run_tests.return_value = Ok(
            TestExecutionResult(passed=False, total_tests=10, failed_tests=2, duration_seconds=3.1)
        )

        guard = RegressionGuard()
        result = guard.check_regression()

        assert result.is_ok()
        check_result = result.unwrap()
        assert not check_result.passed
        assert check_result.test_result.failed_tests == 2

    @patch("tools.regression_guard.RegressionGuard.get_changed_files")
    def test_check_regression_git_error(self, mock_get_changed):
        """Should handle git errors gracefully"""
        mock_get_changed.return_value = Err("fatal: not a git repository")

        guard = RegressionGuard()
        result = guard.check_regression()

        assert result.is_err()
        error = result.unwrap_err()
        assert "git" in error.lower()


class TestRegressionGuardCLI:
    """Test CLI interface"""

    @patch("tools.regression_guard.RegressionGuard.check_regression")
    def test_cli_success(self, mock_check, capsys):
        """Should exit 0 when regression check passes"""
        mock_check.return_value = Ok(
            RegressionCheckResult(
                passed=True,
                changed_files=[ChangedFile(path="tools/example.py", change_type="M")],
                affected_tests=[Path("tests/test_example.py")],
                test_result=TestExecutionResult(
                    passed=True, total_tests=10, failed_tests=0, duration_seconds=2.5
                ),
            )
        )

        from tools.regression_guard import main

        with pytest.raises(SystemExit) as exc:
            main(["--staged"])

        assert exc.value.code == 0

    @patch("tools.regression_guard.RegressionGuard.check_regression")
    def test_cli_failure(self, mock_check, capsys):
        """Should exit 1 when regression check fails"""
        mock_check.return_value = Ok(
            RegressionCheckResult(
                passed=False,
                changed_files=[ChangedFile(path="tools/example.py", change_type="M")],
                affected_tests=[Path("tests/test_example.py")],
                test_result=TestExecutionResult(
                    passed=False, total_tests=10, failed_tests=2, duration_seconds=3.1
                ),
            )
        )

        from tools.regression_guard import main

        with pytest.raises(SystemExit) as exc:
            main([])

        assert exc.value.code == 1
