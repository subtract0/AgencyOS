"""
Auto-Recovery System - Mission 5 Autonomous Failure Recovery

Detects failures during autonomous execution and automatically recovers through:
- Automatic rollback to last known good state
- Retry logic with exponential backoff
- Escalation to user when recovery fails

TDD Protocol (Article VI):
- Tests written FIRST in tests/test_auto_recovery.py (22 tests)
- This implementation makes tests pass (GREEN phase)

Usage:
    from tools.auto_recovery import AutoRecovery

    recovery = AutoRecovery()

    # Create snapshot before execution
    snapshot = recovery.create_snapshot("task_123")

    # If failure occurs
    failure = recovery.detect_failure(result)
    if failure:
        result = recovery.handle_failure("task_123", failure, snapshot)
"""

import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from shared.models.auto_recovery import (
    AutoRecoveryConfig,
    EscalationRecord,
    RecoveryAttempt,
)

logger = logging.getLogger(__name__)


class AutoRecovery:
    """
    Auto-Recovery System - Autonomous Failure Recovery (Mission 5).

    Provides automatic failure detection, rollback, retry, and escalation:
    - Failure Detection: Test failures, build errors, git failures, timeouts
    - Automatic Rollback: Git-based rollback to last known good state
    - Retry Logic: Exponential backoff for transient errors
    - Escalation: User notification when recovery fails

    Methods:
    - detect_failure(result): Detect failure type from command result
    - create_snapshot(task_id): Create git snapshot before execution
    - rollback(task_id, snapshot): Rollback to snapshot
    - handle_failure(task_id, failure, snapshot): Orchestrate recovery
    - create_escalation(...): Escalate to user
    """

    def __init__(
        self,
        config: Optional[AutoRecoveryConfig] = None,
        state_dir: Optional[str] = None,
    ):
        """
        Initialize Auto-Recovery system.

        Args:
            config: Configuration (default: defaults)
            state_dir: Directory for state and logs (default: ~/.agency)
        """
        if config is None:
            config = AutoRecoveryConfig()

        if state_dir is None:
            state_dir = str(Path.home() / ".agency")

        self.config = config
        self.state_dir = Path(state_dir)
        self.escalation_dir = self.state_dir / "escalations"
        self.log_dir = self.state_dir / "logs" / "auto_recovery"

        # Create directories
        self.escalation_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging to file and console."""
        log_file = self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)

    def detect_failure(self, result) -> Optional[dict[str, Any]]:
        """
        Detect failure type from command result.

        Args:
            result: Command result (Mock or subprocess.CompletedProcess)

        Returns:
            dict: Failure details or None if no failure detected
        """
        # Extract result details
        returncode = result.returncode
        stdout = getattr(result, "stdout", "")
        stderr = getattr(result, "stderr", "")

        if returncode == 0:
            return None  # Success, no failure

        # Detect failure type
        error_message = stderr or stdout or ""

        # Resource exhaustion (OOM) - check FIRST (highest priority)
        if returncode == 137 or "memoryerror" in error_message.lower() or "out of memory" in error_message.lower():
            return {
                "type": "resource_exhaustion",
                "error_message": error_message,
                "exit_code": returncode,
            }

        # Timeout
        if returncode == 124 or "timed out" in error_message.lower():
            return {
                "type": "timeout",
                "error_message": error_message,
                "exit_code": returncode,
            }

        # Test failure
        if "FAILED" in stdout or "test" in error_message.lower():
            return {
                "type": "test_failure",
                "error_message": error_message,
                "exit_code": returncode,
            }

        # Git failure
        if "failed to push" in error_message or "git" in error_message.lower():
            return {
                "type": "git_failure",
                "error_message": error_message,
                "exit_code": returncode,
            }

        # Build error (SyntaxError, etc.)
        if "SyntaxError" in error_message or "Error" in error_message:
            return {
                "type": "build_error",
                "error_message": error_message,
                "exit_code": returncode,
            }

        # Unknown failure
        return {
            "type": "unknown",
            "error_message": error_message,
            "exit_code": returncode,
        }

    def create_snapshot(self, task_id: str) -> str:
        """
        Create git snapshot before task execution.

        Args:
            task_id: Task ID

        Returns:
            str: Snapshot ID (git commit hash)
        """
        try:
            # Get current commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            commit_hash = result.stdout.strip()

            # Create git tag for snapshot
            tag_name = f"auto_snapshot_{task_id}_{int(datetime.now().timestamp())}"
            subprocess.run(
                ["git", "tag", tag_name],
                check=True,
            )

            logger.info(f"Created snapshot: {tag_name} (commit: {commit_hash})")
            return commit_hash

        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            return ""

    def rollback(
        self,
        task_id: str,
        snapshot: str,
        verify: bool = False,
    ) -> dict[str, Any]:
        """
        Rollback to last known good state.

        Args:
            task_id: Task ID
            snapshot: Snapshot ID (git commit hash)
            verify: Whether to verify tests pass after rollback

        Returns:
            dict: Rollback result
        """
        try:
            if not self.config.enable_rollback:
                logger.info("Rollback disabled in config, skipping")
                return {"success": False, "error": "Rollback disabled"}

            logger.info(f"Rolling back to snapshot: {snapshot}")

            # Git reset to snapshot
            subprocess.run(
                ["git", "reset", "--hard", snapshot],
                check=True,
            )

            logger.info(f"Rollback successful: {snapshot}")

            # Verify tests if requested
            verified = True
            if verify:
                logger.info("Verifying tests after rollback")
                result = subprocess.run(
                    ["pytest", "-x"],
                    capture_output=True,
                    text=True,
                )
                verified = result.returncode == 0

                if not verified:
                    logger.error("Tests failed after rollback")

            return {
                "success": True,
                "snapshot": snapshot,
                "verified": verified,
            }

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return {"success": False, "error": str(e)}

    def _attempt_recovery(
        self,
        task_id: str,
        failure: dict[str, Any],
        snapshot: str,
    ) -> dict[str, Any]:
        """
        Attempt recovery from failure.

        Args:
            task_id: Task ID
            failure: Failure details
            snapshot: Snapshot to rollback to

        Returns:
            dict: Recovery result
        """
        failure_type = failure["type"]

        # For test failures and build errors, rollback
        if failure_type in ["test_failure", "build_error"]:
            return self.rollback(task_id, snapshot, verify=True)

        # For git failures, rollback
        if failure_type == "git_failure":
            return self.rollback(task_id, snapshot, verify=False)

        # For other failures, return failure
        return {"success": False, "error": f"No recovery strategy for {failure_type}"}

    def handle_failure(
        self,
        task_id: str,
        failure: dict[str, Any],
        snapshot: str,
    ) -> dict[str, Any]:
        """
        Orchestrate recovery from failure.

        Steps:
        1. Check if retryable
        2. Attempt recovery with exponential backoff
        3. Escalate if max retries exhausted

        Args:
            task_id: Task ID
            failure: Failure details
            snapshot: Snapshot to rollback to

        Returns:
            dict: Final recovery result
        """
        failure_type = failure["type"]
        is_retryable = failure_type in self.config.retryable_errors

        recovery_attempts = []

        # If not retryable, escalate immediately
        if not is_retryable:
            logger.info(f"Failure type '{failure_type}' not retryable, escalating")
            return {
                "action": "escalate",
                "failure": failure,
                "retry_count": 0,
            }

        # Attempt recovery with retry logic
        for attempt_num in range(self.config.max_retries + 1):
            logger.info(f"Recovery attempt {attempt_num + 1}/{self.config.max_retries + 1}")

            # Attempt recovery
            result = self._attempt_recovery(task_id, failure, snapshot)

            # Record attempt
            recovery_attempts.append(
                RecoveryAttempt(
                    task_id=task_id,
                    attempt_number=attempt_num + 1,
                    failure_type=failure_type,
                    error_message=failure["error_message"],
                    stack_trace=failure.get("stack_trace", ""),
                    recovery_action="retry" if is_retryable else "rollback",
                    outcome="success" if result.get("success") else "failure",
                )
            )

            # If successful, return
            if result.get("success"):
                logger.info(f"Recovery successful on attempt {attempt_num + 1}")
                return {
                    "action": "retry",
                    "success": True,
                    "retry_count": attempt_num,
                }

            # If not last attempt, wait before retrying
            if attempt_num < self.config.max_retries:
                delay = self.config.retry_delays_seconds[
                    min(attempt_num, len(self.config.retry_delays_seconds) - 1)
                ]
                logger.info(f"Retrying in {delay} seconds")
                time.sleep(delay)

        # Max retries exhausted, escalate
        logger.error(f"Max retries exhausted, escalating")
        return {
            "action": "escalate",
            "failure": failure,
            "retry_count": self.config.max_retries,
            "recovery_attempts": recovery_attempts,
        }

    def create_escalation(
        self,
        task_id: str,
        failure_reason: str,
        recovery_attempts: list[RecoveryAttempt],
        stack_trace: str = "",
    ) -> EscalationRecord:
        """
        Create escalation record and file.

        Args:
            task_id: Task ID
            failure_reason: Reason for failure
            recovery_attempts: Recovery attempts made
            stack_trace: Stack trace from failure

        Returns:
            EscalationRecord: Escalation record
        """
        escalation = EscalationRecord(
            task_id=task_id,
            failure_reason=failure_reason,
            recovery_attempts=recovery_attempts,
            stack_trace=stack_trace,
        )

        # Save escalation file
        escalation_file = self.escalation_dir / f"{task_id}.json"
        with open(escalation_file, "w") as f:
            json.dump(escalation.model_dump(), f, default=str, indent=2)

        logger.info(f"Escalation created: {escalation_file}")

        return escalation
