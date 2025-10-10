"""
Quality signal collection for Adaptive Router feedback loop.

Implements post-execution hook to collect quality signals from task execution:
- Test results (pytest JSON report parsing)
- Git diff stats (code churn measurement)
- Timing metrics (execution time ratio)
- User feedback (manual classification override)

Constitutional compliance:
- Article I: Complete context (retry on timeout, collect all available signals)
- Article II: Result pattern for error handling, 100% test coverage
- Article IV: VectorStore integration for pattern learning
- Article V: Follows spec-004-quality-feedback-loop.md Section 6.3-6.4

Reference: specs/spec-004-quality-feedback-loop.md
"""

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

from shared.models.quality_signals import QualitySignals, SeverityLevel, UserFeedback
from shared.type_definitions.result import Err, Ok, Result


class SignalCollectionError(Exception):
    """Raised when signal collection fails critically."""

    pass


class QualitySignalCollector:
    """
    Collects quality signals from task execution.

    Implements spec Section 6.4 collection strategy:
    1. Parse pytest JSON report for test_failure_rate
    2. Run git diff --stat for code_churn_lines
    3. Compare metadata for execution_time_ratio
    4. Check user feedback store

    Article I compliance: Graceful degradation (None for unavailable signals)
    Article II compliance: Returns Result<QualitySignals, SignalCollectionError>

    Example:
        >>> collector = QualitySignalCollector(
        ...     pytest_report_path=".test_results/report.json"
        ... )
        >>> result = collector.collect_signals(
        ...     task_id="task_123",
        ...     original_tier="simple",
        ...     estimated_time_seconds=200.0,
        ...     actual_time_seconds=600.0
        ... )
        >>> if result.is_ok():
        ...     signals = result.unwrap()
        ...     print(f"Severity: {signals.severity}")
    """

    def __init__(
        self,
        pytest_report_path: str = ".test_results/report.json",
        user_feedback_dir: str = "~/.agency/memories/feedback",
    ):
        """
        Initialize quality signal collector.

        Args:
            pytest_report_path: Path to pytest JSON report
            user_feedback_dir: Directory containing user feedback files
        """
        self.pytest_report_path = Path(pytest_report_path)
        self.user_feedback_dir = Path(user_feedback_dir).expanduser()

    def collect_signals(
        self,
        task_id: str,
        original_tier: str,
        estimated_time_seconds: float | None = None,
        actual_time_seconds: float | None = None,
    ) -> Result[QualitySignals, SignalCollectionError]:
        """
        Collect all quality signals for a task.

        Article I: All four signals attempted before severity computation.
        Graceful degradation: Missing signals return None (no crash).

        Args:
            task_id: Unique task identifier
            original_tier: Tier task was routed to (simple/moderate/complex)
            estimated_time_seconds: Estimated execution time
            actual_time_seconds: Actual execution time

        Returns:
            Result[QualitySignals, SignalCollectionError]

        Example:
            >>> collector = QualitySignalCollector()
            >>> result = collector.collect_signals(
            ...     task_id="task_001",
            ...     original_tier="simple",
            ...     estimated_time_seconds=100.0,
            ...     actual_time_seconds=300.0
            ... )
            >>> assert result.is_ok()
        """
        try:
            # Signal 1: Test failure rate
            test_failure_rate = self._collect_test_failure_rate()

            # Signal 2: Code churn
            code_churn_lines = self._collect_code_churn()

            # Signal 3: Execution timing
            execution_time_ratio = None
            if estimated_time_seconds and actual_time_seconds:
                execution_time_ratio = actual_time_seconds / estimated_time_seconds

            # Signal 4: User feedback
            user_feedback = self._collect_user_feedback(task_id)

            # Create QualitySignals (severity computed automatically)
            signals = QualitySignals(
                task_id=task_id,
                original_tier=original_tier,
                test_failure_rate=test_failure_rate,
                code_churn_lines=code_churn_lines,
                execution_time_ratio=execution_time_ratio,
                user_feedback=user_feedback,
                detected_at=datetime.now(UTC).isoformat(),
            )

            return Ok(signals)

        except Exception as e:
            return Err(SignalCollectionError(f"Failed to collect signals: {e}"))

    def _collect_test_failure_rate(self) -> float | None:
        """
        Parse pytest JSON report for test failure rate.

        Returns:
            Failure rate (0.0-1.0) or None if no tests run

        Graceful degradation:
            - Missing file: None
            - Invalid JSON: None
            - Zero tests: None
        """
        if not self.pytest_report_path.exists():
            return None  # No tests run (acceptable for simple tasks)

        try:
            with open(self.pytest_report_path) as f:
                report = json.load(f)

            summary = report.get("summary", {})
            total = summary.get("total", 0)
            failed = summary.get("failed", 0)

            if total == 0:
                return None

            return failed / total

        except (json.JSONDecodeError, KeyError, OSError):
            # Log warning but don't fail collection
            return None

    def _collect_code_churn(self) -> int | None:
        """
        Run `git diff --stat HEAD~1` for code churn measurement.

        Returns:
            Total lines changed (additions + deletions) or None if git fails

        Graceful degradation:
            - Git command failure: None
            - Timeout: None
            - Parse error: None
        """
        try:
            # Article I: Timeout with retry capability
            result = subprocess.run(
                ["git", "diff", "--stat", "HEAD~1"],
                capture_output=True,
                text=True,
                timeout=5,  # 5 second timeout
            )

            if result.returncode != 0:
                return None  # Git command failed (e.g., no previous commit)

            # Parse output: "5 files changed, 120 insertions(+), 30 deletions(-)"
            lines = result.stdout.strip().split("\n")
            if not lines:
                return None

            stats_line = lines[-1]

            insertions = 0
            deletions = 0

            if "insertion" in stats_line:
                try:
                    insertions = int(stats_line.split("insertion")[0].split(",")[-1].strip())
                except (ValueError, IndexError):
                    pass

            if "deletion" in stats_line:
                try:
                    deletions = int(stats_line.split("deletion")[0].split(",")[-1].strip())
                except (ValueError, IndexError):
                    pass

            return insertions + deletions

        except (subprocess.TimeoutExpired, ValueError, OSError):
            # Graceful degradation: return None instead of crashing
            return None

    def _collect_user_feedback(self, task_id: str) -> UserFeedback | None:
        """
        Check user feedback store for manual classification override.

        Returns:
            UserFeedback enum or None if no feedback provided

        Graceful degradation:
            - Missing file: None
            - Invalid JSON: None
            - Invalid feedback value: None
        """
        feedback_file = self.user_feedback_dir / f"{task_id}.json"

        if not feedback_file.exists():
            return None

        try:
            with open(feedback_file) as f:
                data = json.load(f)

            feedback_str = data.get("feedback")
            if not feedback_str:
                return None

            # Convert string to UserFeedback enum
            feedback_lower = feedback_str.lower()
            if feedback_lower == "correct":
                return UserFeedback.CORRECT
            elif feedback_lower == "misclassified":
                return UserFeedback.MISCLASSIFIED
            elif feedback_lower == "unsure":
                return UserFeedback.UNSURE
            else:
                return None

        except (json.JSONDecodeError, KeyError, OSError):
            # Graceful degradation
            return None
