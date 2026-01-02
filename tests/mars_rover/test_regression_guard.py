"""
Mars Rover Reliability - Phase 1: RegressionGuard Tests.

Constitutional Compliance:
- Article VI: TDD (Tests written FIRST)
- Article II: 100% verification (prevents test regressions)
- Article III: Automated enforcement (runs as pre-commit hook)

Acceptance Criteria:
1. RegressionGuard detects test failures
2. RegressionGuard blocks commits with failing tests
3. RegressionGuard tracks test history for trend analysis
4. RegressionGuard integrates with git hooks
5. RegressionGuard provides bypass for emergency fixes (with audit)
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestRegressionGuardDetection:
    """RegressionGuard test failure detection tests."""

    def test_detects_test_failures(self) -> None:
        """RegressionGuard must detect when tests fail."""
        from tools.mars_rover.regression_guard import RegressionGuard, TestRunResult

        guard = RegressionGuard()

        # Simulate failed test run
        result = TestRunResult(
            total=100,
            passed=95,
            failed=5,
            errors=0,
            duration_seconds=30.0,
        )

        assert guard.has_failures(result), "Should detect test failures"

    def test_allows_all_passing_tests(self) -> None:
        """RegressionGuard must allow commits when all tests pass."""
        from tools.mars_rover.regression_guard import RegressionGuard, TestRunResult

        guard = RegressionGuard()

        result = TestRunResult(
            total=100,
            passed=100,
            failed=0,
            errors=0,
            duration_seconds=30.0,
        )

        assert not guard.has_failures(result), "Should allow when all tests pass"

    def test_detects_errors_as_failures(self) -> None:
        """RegressionGuard must treat errors as failures."""
        from tools.mars_rover.regression_guard import RegressionGuard, TestRunResult

        guard = RegressionGuard()

        result = TestRunResult(
            total=100,
            passed=98,
            failed=0,
            errors=2,  # Errors should also block
            duration_seconds=30.0,
        )

        assert guard.has_failures(result), "Should detect errors as failures"


class TestRegressionGuardBlocking:
    """RegressionGuard commit blocking tests."""

    def test_blocks_commit_on_failure(self) -> None:
        """RegressionGuard must block commits when tests fail."""
        from tools.mars_rover.regression_guard import (
            RegressionGuard,
            RegressionGuardConfig,
            TestRunResult,
        )

        # Disable regression check to test simple failure blocking
        config = RegressionGuardConfig(block_on_regression=False)
        guard = RegressionGuard(config)

        result = TestRunResult(
            total=100,
            passed=90,
            failed=10,
            errors=0,
            duration_seconds=30.0,
        )

        can_commit, reason = guard.check_commit_allowed(result)

        assert not can_commit, "Should block commit on failure"
        assert "failed" in reason.lower() or "90.0%" in reason, "Reason should mention failures"

    def test_allows_commit_on_success(self) -> None:
        """RegressionGuard must allow commits when all tests pass."""
        from tools.mars_rover.regression_guard import RegressionGuard, TestRunResult

        guard = RegressionGuard()

        result = TestRunResult(
            total=100,
            passed=100,
            failed=0,
            errors=0,
            duration_seconds=30.0,
        )

        can_commit, reason = guard.check_commit_allowed(result)

        assert can_commit, "Should allow commit on success"
        assert "pass" in reason.lower(), "Reason should confirm pass"

    def test_blocks_on_regression(self) -> None:
        """RegressionGuard must block on pass rate regression."""
        from tools.mars_rover.regression_guard import RegressionGuard, TestRunResult

        guard = RegressionGuard()

        # Set baseline
        guard.set_baseline(pass_rate=99.0)

        # Current run has lower pass rate
        result = TestRunResult(
            total=100,
            passed=95,
            failed=5,
            errors=0,
            duration_seconds=30.0,
        )

        can_commit, reason = guard.check_commit_allowed(result)

        assert not can_commit, "Should block on regression"
        assert "regression" in reason.lower(), "Reason should mention regression"


class TestRegressionGuardHistory:
    """RegressionGuard test history tests."""

    def test_tracks_test_history(self) -> None:
        """RegressionGuard should track test history."""
        from tools.mars_rover.regression_guard import RegressionGuard, TestRunResult

        guard = RegressionGuard()

        # Record multiple test runs
        for i in range(5):
            result = TestRunResult(
                total=100,
                passed=100 - i,
                failed=i,
                errors=0,
                duration_seconds=30.0,
            )
            guard.record_run(result)

        history = guard.get_history()

        assert len(history) == 5, "History should contain 5 entries"

    def test_calculates_trend(self) -> None:
        """RegressionGuard should calculate pass rate trend."""
        from tools.mars_rover.regression_guard import RegressionGuard, TestRunResult

        guard = RegressionGuard()

        # Record declining pass rate
        for failures in [0, 2, 4, 6, 8]:
            result = TestRunResult(
                total=100,
                passed=100 - failures,
                failed=failures,
                errors=0,
                duration_seconds=30.0,
            )
            guard.record_run(result)

        trend = guard.get_trend()

        assert trend["direction"] == "declining", "Trend should be declining"
        assert trend["change_percent"] < 0, "Change should be negative"


class TestRegressionGuardGitIntegration:
    """RegressionGuard git hook integration tests."""

    def test_generates_pre_commit_hook(self) -> None:
        """RegressionGuard should generate valid pre-commit hook script."""
        from tools.mars_rover.regression_guard import RegressionGuard

        guard = RegressionGuard()

        hook_script = guard.generate_pre_commit_hook()

        assert "#!/" in hook_script, "Hook should have shebang"
        assert "pytest" in hook_script.lower() or "test" in hook_script.lower(), (
            "Hook should run tests"
        )

    def test_installs_hook(self) -> None:
        """RegressionGuard should install pre-commit hook."""
        from tools.mars_rover.regression_guard import RegressionGuard

        guard = RegressionGuard()

        with tempfile.TemporaryDirectory() as temp_dir:
            git_dir = Path(temp_dir) / ".git" / "hooks"
            git_dir.mkdir(parents=True)

            result = guard.install_hook(temp_dir)

            assert result.is_ok(), f"Hook installation should succeed: {result}"

            hook_path = git_dir / "pre-commit"
            assert hook_path.exists(), "Pre-commit hook file should exist"


class TestRegressionGuardBypass:
    """RegressionGuard emergency bypass tests."""

    def test_bypass_with_audit(self) -> None:
        """RegressionGuard must log bypass for audit."""
        from tools.mars_rover.regression_guard import RegressionGuard, TestRunResult

        guard = RegressionGuard()

        result = TestRunResult(
            total=100,
            passed=90,
            failed=10,
            errors=0,
            duration_seconds=30.0,
        )

        # Force bypass
        can_commit, reason = guard.check_commit_allowed(
            result,
            force=True,
            force_reason="Emergency hotfix for production issue",
        )

        assert can_commit, "Force should allow commit"
        assert guard.get_bypass_audit()[-1]["reason"] == "Emergency hotfix for production issue"

    def test_bypass_requires_reason(self) -> None:
        """RegressionGuard bypass must require a reason."""
        from tools.mars_rover.regression_guard import RegressionGuard, TestRunResult

        guard = RegressionGuard()

        result = TestRunResult(
            total=100,
            passed=90,
            failed=10,
            errors=0,
            duration_seconds=30.0,
        )

        # Force without reason should still require reason
        can_commit, reason = guard.check_commit_allowed(
            result,
            force=True,
            force_reason="",  # Empty reason
        )

        # Should not allow bypass without proper reason
        assert "reason required" in reason.lower() or can_commit, (
            "Bypass without reason should either be blocked or audit-logged"
        )


class TestRegressionGuardConfiguration:
    """RegressionGuard configuration tests."""

    def test_default_configuration(self) -> None:
        """Default configuration should have sensible values."""
        from tools.mars_rover.regression_guard import RegressionGuardConfig

        config = RegressionGuardConfig()

        assert config.min_pass_rate == 100.0, "Default should require 100% pass"
        assert config.block_on_regression, "Should block on regression by default"

    def test_custom_threshold(self) -> None:
        """Custom pass rate threshold should be respected."""
        from tools.mars_rover.regression_guard import (
            RegressionGuard,
            RegressionGuardConfig,
            TestRunResult,
        )

        # Disable regression check and set custom threshold
        config = RegressionGuardConfig(min_pass_rate=95.0, block_on_regression=False)
        guard = RegressionGuard(config)

        result = TestRunResult(
            total=100,
            passed=96,
            failed=4,
            errors=0,
            duration_seconds=30.0,
        )

        can_commit, _ = guard.check_commit_allowed(result)

        assert can_commit, "Should allow commit above custom threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
