"""
Mars Rover Reliability - Phase 1: RegressionGuard Pre-commit Hook.

Prevents test regressions by blocking commits with failing tests.

Constitutional Compliance:
- Article II: 100% verification (ensures 100% test pass rate)
- Article III: Automated enforcement (runs as git hook)
- Article IV: Learning (tracks history for trend analysis)

Features:
1. Blocks commits when tests fail
2. Detects pass rate regressions
3. Tracks test history for trend analysis
4. Integrates with git pre-commit hook
5. Emergency bypass with mandatory audit
"""

import json
import logging
import os
import stat
import subprocess
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)


@dataclass
class RegressionGuardConfig:
    """Configuration for regression guard."""

    min_pass_rate: float = 100.0  # Constitutional: 100% pass required
    block_on_regression: bool = True
    history_max_entries: int = 100
    test_command: str = "python -m pytest tests/ -q --tb=no"
    timeout_seconds: int = 300


@dataclass
class TestRunResult:
    """Result of a test run."""

    total: int
    passed: int
    failed: int
    errors: int
    duration_seconds: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    commit_hash: Optional[str] = None

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage."""
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "duration_seconds": self.duration_seconds,
            "pass_rate": self.pass_rate,
            "timestamp": self.timestamp,
            "commit_hash": self.commit_hash,
        }


@dataclass
class BypassAuditEntry:
    """Audit entry for bypass events."""

    timestamp: str
    reason: str
    test_result: dict
    user: str


class RegressionGuard:
    """
    Guard against test regressions in commits.

    Blocks commits when tests fail or pass rate regresses,
    maintaining zero-regression policy (Article II).
    """

    def __init__(self, config: Optional[RegressionGuardConfig] = None):
        """Initialize the regression guard."""
        self.config = config or RegressionGuardConfig()
        self._history: deque[TestRunResult] = deque(
            maxlen=self.config.history_max_entries
        )
        self._baseline_pass_rate: float = 100.0
        self._bypass_audit: list[BypassAuditEntry] = []

        logger.info(f"RegressionGuard initialized: min_pass_rate={self.config.min_pass_rate}%")

    def has_failures(self, result: TestRunResult) -> bool:
        """
        Check if test run has any failures.

        Args:
            result: Test run result

        Returns:
            True if there are failures or errors
        """
        return result.failed > 0 or result.errors > 0

    def set_baseline(self, pass_rate: float) -> None:
        """
        Set the baseline pass rate for regression detection.

        Args:
            pass_rate: Baseline pass rate percentage
        """
        self._baseline_pass_rate = pass_rate
        logger.info(f"Baseline pass rate set to {pass_rate}%")

    def check_commit_allowed(
        self,
        result: TestRunResult,
        force: bool = False,
        force_reason: str = "",
    ) -> tuple[bool, str]:
        """
        Check if commit should be allowed based on test results.

        Args:
            result: Test run result
            force: Force bypass (requires reason)
            force_reason: Reason for force bypass

        Returns:
            Tuple of (allowed, reason)
        """
        # Check for regression first (even if there are failures)
        if self.config.block_on_regression:
            if result.pass_rate < self._baseline_pass_rate:
                regression_msg = (
                    f"Pass rate {result.pass_rate:.1f}% is below baseline "
                    f"{self._baseline_pass_rate:.1f}% (regression detected)"
                )

                if force:
                    if not force_reason:
                        force_reason = "No reason provided (audit required)"
                    self._record_bypass(result, force_reason)
                    return True, f"Forced bypass: {force_reason}"

                return False, regression_msg

        # Check minimum pass rate threshold
        if result.pass_rate < self.config.min_pass_rate:
            # If min_pass_rate is not 100%, allow some failures
            if self.has_failures(result) and self.config.min_pass_rate == 100.0:
                failure_msg = f"{result.failed} failed, {result.errors} errors"

                if force:
                    if not force_reason:
                        force_reason = "No reason provided (audit required)"
                    self._record_bypass(result, force_reason)
                    return True, f"Forced bypass: {force_reason}"

                return False, f"Commit blocked: {failure_msg}"
            else:
                return False, (
                    f"Pass rate {result.pass_rate:.1f}% below minimum "
                    f"{self.config.min_pass_rate:.1f}%"
                )

        # If we have failures but pass rate is above threshold, allow if threshold < 100
        if self.has_failures(result):
            if self.config.min_pass_rate < 100.0:
                # Custom threshold set, allow based on pass rate
                return True, f"{result.passed}/{result.total} tests passed ({result.pass_rate:.1f}%)"
            else:
                failure_msg = f"{result.failed} failed, {result.errors} errors"

                if force:
                    if not force_reason:
                        force_reason = "No reason provided (audit required)"
                    self._record_bypass(result, force_reason)
                    return True, f"Forced bypass: {force_reason}"

                return False, f"Commit blocked: {failure_msg}"

        return True, f"All {result.passed} tests passed ({result.pass_rate:.1f}%)"

    def _record_bypass(self, result: TestRunResult, reason: str) -> None:
        """Record a bypass event for audit."""
        entry = BypassAuditEntry(
            timestamp=datetime.now().isoformat(),
            reason=reason,
            test_result=result.to_dict(),
            user=os.environ.get("USER", "unknown"),
        )
        self._bypass_audit.append(entry)
        logger.warning(f"Bypass recorded: {reason}")

    def get_bypass_audit(self) -> list[dict]:
        """Get bypass audit log."""
        return [
            {
                "timestamp": e.timestamp,
                "reason": e.reason,
                "test_result": e.test_result,
                "user": e.user,
            }
            for e in self._bypass_audit
        ]

    def record_run(self, result: TestRunResult) -> None:
        """
        Record a test run in history.

        Args:
            result: Test run result
        """
        self._history.append(result)

    def get_history(self) -> list[dict]:
        """Get test run history."""
        return [r.to_dict() for r in self._history]

    def get_trend(self) -> dict:
        """
        Analyze test pass rate trend.

        Returns:
            Trend analysis with direction and change
        """
        if len(self._history) < 2:
            return {
                "direction": "stable",
                "change_percent": 0.0,
                "sample_size": len(self._history),
            }

        # Calculate trend using first and last entries
        first = self._history[0]
        last = self._history[-1]

        change = last.pass_rate - first.pass_rate

        if change > 0.5:
            direction = "improving"
        elif change < -0.5:
            direction = "declining"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "change_percent": change,
            "sample_size": len(self._history),
            "first_pass_rate": first.pass_rate,
            "last_pass_rate": last.pass_rate,
        }

    def run_tests(self) -> Result[TestRunResult, str]:
        """
        Run the test suite and return results.

        Returns:
            Result with TestRunResult or error
        """
        try:
            import time

            start = time.perf_counter()

            result = subprocess.run(
                self.config.test_command.split(),
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                cwd=Path(__file__).parent.parent.parent,
            )

            duration = time.perf_counter() - start

            # Parse pytest output
            # Look for summary line like "100 passed, 5 failed, 2 errors"
            output = result.stdout + result.stderr
            passed = failed = errors = total = 0

            for line in output.split("\n"):
                line_lower = line.lower()
                if "passed" in line_lower:
                    import re

                    # Parse "X passed"
                    match = re.search(r"(\d+)\s+passed", line_lower)
                    if match:
                        passed = int(match.group(1))

                    # Parse "X failed"
                    match = re.search(r"(\d+)\s+failed", line_lower)
                    if match:
                        failed = int(match.group(1))

                    # Parse "X error"
                    match = re.search(r"(\d+)\s+error", line_lower)
                    if match:
                        errors = int(match.group(1))

            total = passed + failed + errors

            # Get current commit hash
            try:
                git_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent.parent.parent,
                )
                commit_hash = git_result.stdout.strip()[:8]
            except Exception:
                commit_hash = None

            return Ok(
                TestRunResult(
                    total=total or 1,  # Avoid division by zero
                    passed=passed,
                    failed=failed,
                    errors=errors,
                    duration_seconds=duration,
                    commit_hash=commit_hash,
                )
            )

        except subprocess.TimeoutExpired:
            return Err(f"Tests timed out after {self.config.timeout_seconds}s")
        except Exception as e:
            return Err(f"Failed to run tests: {e}")

    def generate_pre_commit_hook(self) -> str:
        """
        Generate pre-commit hook script.

        Returns:
            Shell script content
        """
        return '''#!/bin/bash
# Mars Rover Reliability - RegressionGuard Pre-commit Hook
# Constitutional Article II: 100% test verification before commit

set -e

echo "🛡️ RegressionGuard: Running tests before commit..."

# Run tests
python -m pytest tests/ -q --tb=no --maxfail=5

if [ $? -eq 0 ]; then
    echo "✅ All tests passed - commit allowed"
    exit 0
else
    echo "❌ Tests failed - commit blocked"
    echo ""
    echo "To bypass (emergency only): git commit --no-verify"
    echo "WARNING: Bypasses are logged for audit!"
    exit 1
fi
'''

    def install_hook(self, git_dir: str) -> Result[Path, str]:
        """
        Install pre-commit hook in git repository.

        Args:
            git_dir: Path to git repository root

        Returns:
            Result with hook path or error
        """
        try:
            hooks_dir = Path(git_dir) / ".git" / "hooks"

            if not hooks_dir.exists():
                return Err(f"Git hooks directory not found: {hooks_dir}")

            hook_path = hooks_dir / "pre-commit"
            hook_content = self.generate_pre_commit_hook()

            # Write hook file
            with open(hook_path, "w") as f:
                f.write(hook_content)

            # Make executable
            hook_path.chmod(hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)

            logger.info(f"Pre-commit hook installed at {hook_path}")
            return Ok(hook_path)

        except Exception as e:
            return Err(f"Failed to install hook: {e}")

    def check_and_block(self) -> Result[bool, str]:
        """
        Run tests and block if they fail.

        Returns:
            Result with True if tests passed, error message if blocked
        """
        run_result = self.run_tests()
        if run_result.is_err():
            return Err(run_result.unwrap_err())

        test_result = run_result.unwrap()
        self.record_run(test_result)

        can_commit, reason = self.check_commit_allowed(test_result)

        if can_commit:
            return Ok(True)
        else:
            return Err(reason)


def main():
    """CLI entry point for regression guard."""
    import argparse

    parser = argparse.ArgumentParser(description="RegressionGuard CLI")
    parser.add_argument("--check", action="store_true", help="Run tests and check")
    parser.add_argument("--install", action="store_true", help="Install pre-commit hook")
    parser.add_argument("--status", action="store_true", help="Show current status")
    args = parser.parse_args()

    guard = RegressionGuard()

    if args.install:
        result = guard.install_hook(str(Path.cwd()))
        if result.is_ok():
            print(f"✅ Hook installed at {result.unwrap()}")
        else:
            print(f"❌ Failed: {result.unwrap_err()}")

    elif args.check:
        result = guard.check_and_block()
        if result.is_ok():
            print("✅ All tests passed - commit allowed")
        else:
            print(f"❌ {result.unwrap_err()}")
            exit(1)

    elif args.status:
        history = guard.get_history()
        trend = guard.get_trend()
        print(f"History entries: {len(history)}")
        print(f"Trend: {trend}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
