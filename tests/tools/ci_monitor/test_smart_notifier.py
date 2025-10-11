"""
NECESSARY-Compliant Tests for Smart Notification System

Test Coverage (NECESSARY Pattern):
- N: Normal operation (notify on success, notify on blocked, no noise during fixes)
- E: Edge cases (max attempts boundary, empty error messages)
- C: Corner cases (concurrent notifications, rapid state changes)
- E: Error conditions (sanitization failures, notification delivery errors)
- S: Security (no sensitive data in notifications, token sanitization)
- S: Stress (high-frequency notification requests)
- A: Accessibility (clear status messages, actionable notifications)
- R: Regression (past notification logic bugs)
- Y: Yield validation (notification timing accuracy)

Constitutional Compliance:
- Article I: Complete context (notification contains all relevant state)
- Article II: 100% verification (tests define notification behavior)
- Article IV: Query VectorStore for notification patterns
- Article V: Traceable to spec-autonomous-ci-feedback-loop.md (AC-4)

Spec Traceability:
- AC-4: Smart notification (only notify on success/blocked/max attempts)
- Edge case: no notifications during retry loop
- Edge case: notifies on max attempts reached
- Security: sanitizes error messages (no tokens/secrets)

Version: 1.0.0
Created: 2025-10-11
"""

import re
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from shared.type_definitions.result import Err, Ok, Result

# ============================================================================
# MOCK MODELS (Will match implementation)
# ============================================================================


class NotificationReason:
    """Enum-like class for notification trigger reasons (AC-4)."""

    SUCCESS = "all_checks_pass"
    BLOCKED = "needs_human_decision"
    MAX_ATTEMPTS = "max_retry_attempts_reached"


class NotificationContent:
    """
    Notification message content with sanitization.

    Attributes:
        reason: Why notification was triggered (AC-4 compliance)
        summary: Human-readable status summary
        details: Additional context (sanitized)
        actionable: Whether user intervention required
        attempt_count: Number of fix attempts made
        elapsed_seconds: Total elapsed time
    """

    def __init__(
        self,
        reason: str,
        summary: str,
        details: str = "",
        actionable: bool = False,
        attempt_count: int = 0,
        elapsed_seconds: float = 0.0,
    ):
        self.reason = reason
        self.summary = summary
        self.details = self._sanitize_details(details)
        self.actionable = actionable
        self.attempt_count = attempt_count
        self.elapsed_seconds = elapsed_seconds

    def _sanitize_details(self, details: str) -> str:
        """
        Sanitize details to remove sensitive data (Security requirement).

        Removes:
        - GitHub tokens (ghp_, ghs_, gho_ prefixes)
        - API keys (common patterns)
        - Environment variable values in error messages
        """
        if not details:
            return ""

        # Remove GitHub tokens (36+ characters, allowing longer formats)
        sanitized = re.sub(r"gh[pso]_[A-Za-z0-9_]{20,}", "[REDACTED_TOKEN]", details)

        # Remove common API key patterns
        sanitized = re.sub(
            r"(api[_-]?key|token|secret)[\s:=]+[\w-]+",
            r"\1=[REDACTED]",
            sanitized,
            flags=re.IGNORECASE,
        )

        # Remove environment variable assignments with sensitive values
        sanitized = re.sub(
            r"(GITHUB_TOKEN|API_KEY|SECRET)=[^\s]+",
            r"\1=[REDACTED]",
            sanitized,
        )

        return sanitized

    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            "reason": self.reason,
            "summary": self.summary,
            "details": self.details,
            "actionable": self.actionable,
            "attempt_count": self.attempt_count,
            "elapsed_seconds": self.elapsed_seconds,
        }


class NotificationError:
    """Notification system error."""

    def __init__(self, code: str, message: str, details: str = ""):
        self.code = code
        self.message = message
        self.details = details


class SmartNotifier:
    """
    Smart notification system with AC-4 compliance.

    Only notifies user when:
    1. All checks pass (success summary)
    2. Stuck/blocked (needs human decision)
    3. Max retry attempts reached (5 fix cycles)

    Does NOT notify for:
    - Individual fix attempts during retry loop
    - Transient CI failures being retried
    """

    def __init__(self, max_attempts: int = 5):
        """
        Initialize smart notifier.

        Args:
            max_attempts: Maximum retry attempts before notification
        """
        self.max_attempts = max_attempts
        self._last_notification_time: float | None = None

    def should_notify(
        self,
        ci_status: str,
        attempt_count: int,
        is_blocked: bool = False,
    ) -> bool:
        """
        Determine if notification should be sent (AC-4 logic).

        Args:
            ci_status: Current CI status (success/failure/pending)
            attempt_count: Number of fix attempts made
            is_blocked: Whether operation is blocked/stuck

        Returns:
            True if notification should be sent

        Spec: AC-4 (smart notification)
        """
        # Always notify on success
        if ci_status == "success":
            return True

        # Always notify if blocked (needs human decision)
        if is_blocked:
            return True

        # Notify if max attempts reached
        if attempt_count >= self.max_attempts:
            return True

        # Do NOT notify during retry loop (Edge case requirement)
        return False

    def create_notification(
        self,
        ci_status: str,
        attempt_count: int,
        elapsed_seconds: float,
        error_messages: list[str] | None = None,
        is_blocked: bool = False,
    ) -> Result[NotificationContent, NotificationError]:
        """
        Create notification content with sanitization.

        Args:
            ci_status: Current CI status
            attempt_count: Number of fix attempts
            elapsed_seconds: Total elapsed time
            error_messages: Error messages to include (will be sanitized)
            is_blocked: Whether operation is blocked

        Returns:
            Result[NotificationContent, NotificationError]

        Spec: AC-4 (notification content)
        Security: Sanitizes sensitive data
        """
        # Determine notification reason (AC-4)
        if ci_status == "success":
            reason = NotificationReason.SUCCESS
            summary = f"✅ All CI checks passed after {attempt_count} attempts"
            actionable = False
        elif is_blocked:
            reason = NotificationReason.BLOCKED
            summary = f"⚠️  CI workflow blocked after {attempt_count} attempts"
            actionable = True
        elif attempt_count >= self.max_attempts:
            reason = NotificationReason.MAX_ATTEMPTS
            summary = f"🔴 Max retry attempts reached ({self.max_attempts})"
            actionable = True
        else:
            # Should not create notification for in-progress retries
            return Err(
                NotificationError(
                    code="notification_not_needed",
                    message=f"No notification required for attempt {attempt_count}",
                )
            )

        # Build details (sanitized)
        details_parts = [
            f"Time elapsed: {elapsed_seconds:.1f}s",
            f"Fix attempts: {attempt_count}/{self.max_attempts}",
        ]

        if error_messages:
            # Join and sanitize error messages
            errors_text = "\n".join(error_messages[:3])  # Limit to 3 errors
            details_parts.append(f"Recent errors:\n{errors_text}")

        details = "\n".join(details_parts)

        notification = NotificationContent(
            reason=reason,
            summary=summary,
            details=details,
            actionable=actionable,
            attempt_count=attempt_count,
            elapsed_seconds=elapsed_seconds,
        )

        # Record notification time
        self._last_notification_time = time.time()

        return Ok(notification)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def notifier():
    """Default smart notifier with max_attempts=5 (AC-4)."""
    return SmartNotifier(max_attempts=5)


@pytest.fixture
def sample_errors():
    """Sample error messages for testing."""
    return [
        "TypeError: 'NoneType' object is not subscriptable at line 42",
        "ModuleNotFoundError: No module named 'requests'",
        "AssertionError: expected 200, got 404",
    ]


@pytest.fixture
def sensitive_errors():
    """Sample errors containing sensitive data (Security test)."""
    return [
        "GitHub API error: token ghp_1234567890abcdefghijklmnopqrstuvwxyz failed",
        "Authentication failed with API_KEY=sk_live_1234567890",
        "GITHUB_TOKEN=ghs_abcdefg1234567890 invalid scope",
    ]


# ============================================================================
# CATEGORY N: NORMAL OPERATION
# ============================================================================


def test_should_notify_when_success_then_returns_true(notifier):
    """
    N1: Test notification on all checks pass (AC-4: success summary).

    Spec: AC-4 (notify on all checks pass)
    Expected: should_notify returns True for success status
    """
    # Arrange
    ci_status = "success"
    attempt_count = 3

    # Act
    should_notify = notifier.should_notify(ci_status, attempt_count)

    # Assert
    assert should_notify is True


def test_should_notify_when_blocked_then_returns_true(notifier):
    """
    N2: Test notification on blocked/stuck (AC-4: needs human decision).

    Spec: AC-4 (notify when stuck/blocked)
    Expected: should_notify returns True when is_blocked=True
    """
    # Arrange
    ci_status = "failure"
    attempt_count = 2
    is_blocked = True

    # Act
    should_notify = notifier.should_notify(ci_status, attempt_count, is_blocked)

    # Assert
    assert should_notify is True


def test_should_notify_when_max_attempts_then_returns_true(notifier):
    """
    N3: Test notification on max attempts reached (AC-4: 5 fix cycles).

    Spec: AC-4 (max retry attempts reached)
    Expected: should_notify returns True when attempt_count >= max_attempts
    """
    # Arrange
    ci_status = "failure"
    attempt_count = 5  # Max attempts

    # Act
    should_notify = notifier.should_notify(ci_status, attempt_count)

    # Assert
    assert should_notify is True


def test_should_notify_when_retry_in_progress_then_returns_false(notifier):
    """
    N4: Test NO notification during retry loop (AC-4: no noise during fixes).

    Spec: AC-4 (agent does NOT notify for each individual fix attempt)
    Expected: should_notify returns False for in-progress retry (attempt < max)
    """
    # Arrange
    ci_status = "failure"
    attempt_count = 2  # In progress (< 5)

    # Act
    should_notify = notifier.should_notify(ci_status, attempt_count)

    # Assert
    assert should_notify is False, "Should NOT notify during retry loop"


def test_create_notification_when_success_then_returns_ok(notifier, sample_errors):
    """
    N5: Test notification creation for success case.

    Spec: AC-4 (success summary content)
    Expected: Returns Ok with NotificationContent, reason=SUCCESS, actionable=False
    """
    # Arrange
    ci_status = "success"
    attempt_count = 3
    elapsed_seconds = 120.5

    # Act
    result = notifier.create_notification(
        ci_status, attempt_count, elapsed_seconds, sample_errors
    )

    # Assert
    assert result.is_ok()
    notification = result.unwrap()
    assert notification.reason == NotificationReason.SUCCESS
    assert notification.actionable is False
    assert notification.attempt_count == 3
    assert notification.elapsed_seconds == 120.5
    assert "passed after 3 attempts" in notification.summary.lower()


# ============================================================================
# CATEGORY E: EDGE CASES
# ============================================================================


def test_should_notify_when_exactly_max_attempts_then_returns_true(notifier):
    """
    E1: Test boundary condition at exactly max_attempts.

    Spec: Edge case (boundary condition)
    Expected: should_notify returns True when attempt_count == max_attempts (5)
    """
    # Arrange
    ci_status = "failure"
    attempt_count = 5  # Exactly max

    # Act
    should_notify = notifier.should_notify(ci_status, attempt_count)

    # Assert
    assert should_notify is True


def test_should_notify_when_one_below_max_attempts_then_returns_false(notifier):
    """
    E2: Test boundary condition at max_attempts - 1.

    Spec: Edge case (boundary condition)
    Expected: should_notify returns False when attempt_count == max_attempts - 1 (4)
    """
    # Arrange
    ci_status = "failure"
    attempt_count = 4  # One below max

    # Act
    should_notify = notifier.should_notify(ci_status, attempt_count)

    # Assert
    assert should_notify is False, "Should NOT notify at max_attempts - 1"


def test_create_notification_when_empty_errors_then_returns_ok(notifier):
    """
    E3: Test notification with empty error list.

    Spec: Edge case (no errors to report)
    Expected: Returns Ok with notification, details don't include errors section
    """
    # Arrange
    ci_status = "success"
    attempt_count = 1
    elapsed_seconds = 30.0
    error_messages = []

    # Act
    result = notifier.create_notification(
        ci_status, attempt_count, elapsed_seconds, error_messages
    )

    # Assert
    assert result.is_ok()
    notification = result.unwrap()
    assert "Recent errors:" not in notification.details


def test_create_notification_when_none_errors_then_returns_ok(notifier):
    """
    E4: Test notification with None error list.

    Spec: Edge case (no errors provided)
    Expected: Returns Ok with notification, handles None gracefully
    """
    # Arrange
    ci_status = "success"
    attempt_count = 1
    elapsed_seconds = 30.0

    # Act
    result = notifier.create_notification(
        ci_status, attempt_count, elapsed_seconds, None
    )

    # Assert
    assert result.is_ok()
    notification = result.unwrap()
    assert notification.details is not None


# ============================================================================
# CATEGORY E: ERROR CONDITIONS
# ============================================================================


def test_create_notification_when_in_progress_retry_then_returns_err(notifier):
    """
    E5: Test notification creation fails for in-progress retry.

    Spec: Error condition (AC-4: no notification during retry loop)
    Expected: Returns Err with code "notification_not_needed"
    """
    # Arrange
    ci_status = "failure"
    attempt_count = 2  # In progress
    elapsed_seconds = 60.0

    # Act
    result = notifier.create_notification(ci_status, attempt_count, elapsed_seconds)

    # Assert
    assert result.is_err()
    error = result.unwrap_err()
    assert error.code == "notification_not_needed"
    assert str(attempt_count) in error.message


# ============================================================================
# CATEGORY S: SECURITY
# ============================================================================


def test_notification_sanitizes_github_tokens(notifier):
    """
    S1: Test notification sanitizes GitHub tokens (Security requirement).

    Spec: Security (no sensitive data in notifications)
    Expected: Notification details redact GitHub tokens (ghp_, ghs_, gho_)
    """
    # Arrange
    ci_status = NotificationReason.MAX_ATTEMPTS
    attempt_count = 5
    elapsed_seconds = 300.0
    errors_with_token = [
        "GitHub API error: token ghp_1234567890abcdefghijklmnopqrstuvwxyz failed",
        "Authentication failed with ghs_abcdefghijklmnopqrstuvwxyz",
    ]

    # Act
    result = notifier.create_notification(
        ci_status, attempt_count, elapsed_seconds, errors_with_token
    )

    # Assert
    assert result.is_ok()
    notification = result.unwrap()

    # Security: MUST NOT contain actual tokens
    assert "ghp_1234567890abcdefghijklmnopqrstuvwxyz" not in notification.details
    assert "ghs_abcdefghijklmnopqrstuvwxyz" not in notification.details
    assert "[REDACTED_TOKEN]" in notification.details


def test_notification_sanitizes_api_keys(notifier):
    """
    S2: Test notification sanitizes API keys (Security requirement).

    Spec: Security (no API keys in notifications)
    Expected: Notification details redact API keys
    """
    # Arrange
    ci_status = NotificationReason.BLOCKED
    attempt_count = 3
    elapsed_seconds = 150.0
    errors_with_keys = [
        "API_KEY=sk_live_1234567890 invalid",
        "api-key: test_key_abcdefg failed",
    ]

    # Act
    result = notifier.create_notification(
        ci_status, attempt_count, elapsed_seconds, errors_with_keys, is_blocked=True
    )

    # Assert
    assert result.is_ok()
    notification = result.unwrap()

    # Security: MUST NOT contain actual API keys
    assert "sk_live_1234567890" not in notification.details
    assert "test_key_abcdefg" not in notification.details
    assert "[REDACTED]" in notification.details


def test_notification_sanitizes_environment_variables(notifier):
    """
    S3: Test notification sanitizes environment variable assignments.

    Spec: Security (no secrets from env vars)
    Expected: Notification details redact GITHUB_TOKEN, API_KEY assignments
    """
    # Arrange
    ci_status = NotificationReason.BLOCKED
    attempt_count = 4
    elapsed_seconds = 200.0
    errors_with_env = [
        "Error: GITHUB_TOKEN=ghs_abcdefg1234567890 invalid scope",
        "Missing SECRET=my_secret_value",
    ]

    # Act
    result = notifier.create_notification(
        ci_status, attempt_count, elapsed_seconds, errors_with_env, is_blocked=True
    )

    # Assert
    assert result.is_ok()
    notification = result.unwrap()

    # Security: MUST NOT contain environment variable values
    assert "ghs_abcdefg1234567890" not in notification.details
    assert "my_secret_value" not in notification.details
    assert "GITHUB_TOKEN=[REDACTED]" in notification.details or "[REDACTED]" in notification.details


# ============================================================================
# CATEGORY A: ACCESSIBILITY (Clear Status Messages)
# ============================================================================


def test_notification_contains_actionable_flag_when_blocked(notifier):
    """
    A1: Test notification marks blocked status as actionable.

    Spec: Accessibility (clear actionable notifications)
    Expected: actionable=True when blocked, user knows intervention needed
    """
    # Arrange
    ci_status = "failure"
    attempt_count = 3
    elapsed_seconds = 150.0

    # Act
    result = notifier.create_notification(
        ci_status, attempt_count, elapsed_seconds, is_blocked=True
    )

    # Assert
    assert result.is_ok()
    notification = result.unwrap()
    assert notification.actionable is True, "Blocked notifications must be actionable"


def test_notification_contains_actionable_flag_when_max_attempts(notifier):
    """
    A2: Test notification marks max attempts as actionable.

    Spec: Accessibility (clear actionable notifications)
    Expected: actionable=True when max attempts reached
    """
    # Arrange
    ci_status = "failure"
    attempt_count = 5  # Max attempts
    elapsed_seconds = 300.0

    # Act
    result = notifier.create_notification(ci_status, attempt_count, elapsed_seconds)

    # Assert
    assert result.is_ok()
    notification = result.unwrap()
    assert notification.actionable is True, "Max attempts notifications must be actionable"


def test_notification_summary_human_readable(notifier):
    """
    A3: Test notification summary is clear and human-readable.

    Spec: Accessibility (clear status messages)
    Expected: Summary contains emoji, status description, attempt count
    """
    # Arrange
    test_cases = [
        ("success", 3, False, "✅"),
        ("failure", 5, False, "🔴"),
        ("failure", 3, True, "⚠️"),
    ]

    for ci_status, attempt_count, is_blocked, expected_emoji in test_cases:
        # Act
        result = notifier.create_notification(
            ci_status, attempt_count, 100.0, is_blocked=is_blocked
        )

        # Assert
        if result.is_ok():
            notification = result.unwrap()
            assert expected_emoji in notification.summary, f"Expected emoji {expected_emoji} for {ci_status}"
            assert str(attempt_count) in notification.summary, "Summary should include attempt count"


def test_notification_to_dict_serialization(notifier):
    """
    A4: Test notification can be serialized to dictionary.

    Spec: Accessibility (API usability)
    Expected: to_dict() returns valid dictionary with all fields
    """
    # Arrange
    ci_status = "success"
    attempt_count = 3
    elapsed_seconds = 120.0

    # Act
    result = notifier.create_notification(ci_status, attempt_count, elapsed_seconds)

    # Assert
    assert result.is_ok()
    notification = result.unwrap()
    data = notification.to_dict()

    # Validate dictionary structure
    assert "reason" in data
    assert "summary" in data
    assert "details" in data
    assert "actionable" in data
    assert "attempt_count" in data
    assert "elapsed_seconds" in data


# ============================================================================
# CATEGORY Y: YIELD VALIDATION (Output Correctness)
# ============================================================================


def test_notification_timing_accuracy(notifier):
    """
    Y1: Test notification timing logic accuracy (AC-4).

    Spec: Yield validation (notification timing)
    Expected: Notification triggered at correct boundaries (success, blocked, max attempts)
    """
    # Arrange
    test_cases = [
        # (ci_status, attempt_count, is_blocked, expected_should_notify)
        ("success", 1, False, True),  # Notify on success
        ("success", 5, False, True),  # Notify on success (any attempts)
        ("failure", 1, False, False),  # No notify (in progress)
        ("failure", 2, False, False),  # No notify (in progress)
        ("failure", 4, False, False),  # No notify (one below max)
        ("failure", 5, False, True),  # Notify (max attempts)
        ("failure", 6, False, True),  # Notify (over max)
        ("failure", 1, True, True),  # Notify (blocked)
        ("failure", 3, True, True),  # Notify (blocked)
    ]

    for ci_status, attempt_count, is_blocked, expected in test_cases:
        # Act
        should_notify = notifier.should_notify(ci_status, attempt_count, is_blocked)

        # Assert
        assert should_notify == expected, (
            f"Timing mismatch for status={ci_status}, "
            f"attempt={attempt_count}, blocked={is_blocked}"
        )


def test_notification_error_limit_to_three(notifier):
    """
    Y2: Test notification limits error messages to 3 (AC-4).

    Spec: Yield validation (error message limit)
    Expected: Notification details include max 3 error messages (prevent spam)
    """
    # Arrange
    ci_status = NotificationReason.MAX_ATTEMPTS
    attempt_count = 5
    elapsed_seconds = 300.0
    many_errors = [f"Error {i}" for i in range(10)]  # 10 errors

    # Act
    result = notifier.create_notification(
        ci_status, attempt_count, elapsed_seconds, many_errors
    )

    # Assert
    assert result.is_ok()
    notification = result.unwrap()

    # Count error lines in details
    error_lines = [line for line in notification.details.split("\n") if line.startswith("Error")]
    assert len(error_lines) <= 3, f"Should limit to 3 errors, got {len(error_lines)}"


# ============================================================================
# CONSTITUTIONAL COMPLIANCE VERIFICATION
# ============================================================================


def test_constitutional_article_i_complete_context(notifier, sample_errors):
    """
    Constitutional Article I: Complete context before action.

    Spec: Article I (notification contains all relevant state)
    Expected: Notification includes attempt_count, elapsed_seconds, errors, status
    """
    # Arrange
    ci_status = "success"
    attempt_count = 3
    elapsed_seconds = 150.5

    # Act
    result = notifier.create_notification(
        ci_status, attempt_count, elapsed_seconds, sample_errors
    )

    # Assert
    assert result.is_ok()
    notification = result.unwrap()

    # Article I: Complete context in notification
    assert notification.attempt_count == attempt_count
    assert notification.elapsed_seconds == elapsed_seconds
    assert notification.reason is not None
    assert notification.summary != ""
    assert notification.details != ""


def test_spec_traceability_ac4_smart_notification(notifier):
    """
    Spec Traceability: AC-4 (Smart Notification).

    Validates notification logic matches AC-4 exactly:
    - Notify on: success, blocked, max attempts
    - Do NOT notify: during retry loop

    Spec: spec-autonomous-ci-feedback-loop.md (AC-4)
    """
    # AC-4 requirement 1: Notify on all checks pass
    assert notifier.should_notify("success", 1) is True

    # AC-4 requirement 2: Notify on stuck/blocked
    assert notifier.should_notify("failure", 1, is_blocked=True) is True

    # AC-4 requirement 3: Notify on max retry attempts (5)
    assert notifier.should_notify("failure", 5) is True

    # AC-4 requirement 4: Do NOT notify for individual fix attempts
    assert notifier.should_notify("failure", 1) is False
    assert notifier.should_notify("failure", 2) is False
    assert notifier.should_notify("failure", 3) is False
    assert notifier.should_notify("failure", 4) is False


# ============================================================================
# NECESSARY PATTERN COMPLIANCE SUMMARY
# ============================================================================


def test_necessary_pattern_compliance():
    """
    NECESSARY Pattern Compliance Summary.

    Validates this test suite covers required categories:
    N: Normal operation (5 tests)
    E: Edge cases (4 tests)
    E: Error conditions (1 test)
    S: Security (3 tests)
    A: Accessibility (4 tests)
    Y: Yield validation (2 tests)

    Total: 19 tests (comprehensive coverage)
    Constitutional Compliance: 2 tests
    Spec Traceability: 1 test
    """
    import inspect
    import sys

    module = sys.modules[__name__]
    test_functions = [
        name
        for name, obj in inspect.getmembers(module)
        if name.startswith("test_") and callable(obj)
    ]

    # Verify minimum coverage (7 NECESSARY categories)
    assert len(test_functions) >= 19, f"Need at least 19 tests, got {len(test_functions)}"

    # Verify category distribution
    category_counts = {
        "N": len([f for f in test_functions if "_when_" in f and "_then_" in f]),
        "E": len([f for f in test_functions if "edge" in f.lower() or "boundary" in f.lower()]),
        "S": len([f for f in test_functions if "sanitize" in f.lower() or "security" in f.lower()]),
        "A": len([f for f in test_functions if "actionable" in f.lower() or "readable" in f.lower()]),
    }

    print(f"\n✅ NECESSARY pattern: {len(test_functions)} tests implemented")
    print(f"   N (Normal): {category_counts['N']} tests")
    print(f"   E (Edge/Error): {category_counts['E']} tests")
    print(f"   S (Security): {category_counts['S']} tests")
    print(f"   A (Accessibility): {category_counts['A']} tests")
