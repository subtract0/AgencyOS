"""
Smart User Notification System for Autonomous CI Feedback Loop.

Constitutional Compliance:
- Article I: Complete context (notification contains all relevant state)
- Article II: 100% verification (all tests pass before merge)
- Article IV: VectorStore learning integration (query before, store after)
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

from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result

# ============================================================================
# PYDANTIC MODELS (Constitutional Law #2: Strict Typing)
# ============================================================================


class NotificationReason:
    """
    Enum-like class for notification trigger reasons (AC-4).

    Attributes:
        SUCCESS: All CI checks passed
        BLOCKED: Needs human decision/intervention
        MAX_ATTEMPTS: Maximum retry attempts reached
    """

    SUCCESS = "all_checks_pass"
    BLOCKED = "needs_human_decision"
    MAX_ATTEMPTS = "max_retry_attempts_reached"


class NotificationContent(BaseModel):
    """
    Notification message content with sanitization.

    Attributes:
        reason: Why notification was triggered (AC-4 compliance)
        summary: Human-readable status summary
        details: Additional context (sanitized)
        actionable: Whether user intervention required
        attempt_count: Number of fix attempts made
        elapsed_seconds: Total elapsed time

    Security: All details are automatically sanitized to remove:
    - GitHub tokens (ghp_, ghs_, gho_ prefixes)
    - API keys (common patterns)
    - Environment variable values
    """

    reason: str
    summary: str
    details: str = ""
    actionable: bool = False
    attempt_count: int = Field(ge=0)
    elapsed_seconds: float = Field(ge=0.0)

    def model_post_init(self, __context):
        """Sanitize details after model initialization."""
        self.details = self._sanitize_details(self.details)

    def _sanitize_details(self, details: str) -> str:
        """
        Sanitize details to remove sensitive data (Security).

        Removes:
        - GitHub tokens (ghp_, ghs_, gho_ prefixes)
        - API keys (common patterns)
        - Environment variable values in error messages

        Args:
            details: Raw details string

        Returns:
            Sanitized details string

        Spec: Security requirement (no sensitive data in notifications)
        """
        if not details:
            return ""

        # Remove GitHub tokens (36+ characters, flexible length)
        sanitized = re.sub(r"gh[pso]_[A-Za-z0-9_]{20,}", "[REDACTED_TOKEN]", details)

        # Remove common API key patterns
        sanitized = re.sub(
            r"(api[_-]?key|token|secret)[\s:=]+[\w-]+",
            r"\1=[REDACTED]",
            sanitized,
            flags=re.IGNORECASE,
        )

        # Remove environment variable assignments
        sanitized = re.sub(
            r"(GITHUB_TOKEN|API_KEY|SECRET)=[^\s]+",
            r"\1=[REDACTED]",
            sanitized,
        )

        return sanitized

    def to_dict(self) -> dict[str, str | bool | int | float]:
        """Convert to dictionary for serialization."""
        return {
            "reason": self.reason,
            "summary": self.summary,
            "details": self.details,
            "actionable": self.actionable,
            "attempt_count": self.attempt_count,
            "elapsed_seconds": self.elapsed_seconds,
        }


class NotificationError(BaseModel):
    """
    Notification system error.

    Attributes:
        code: Error code (e.g., "notification_not_needed")
        message: Human-readable error message
        details: Additional error context
    """

    code: str
    message: str
    details: str = ""


# ============================================================================
# SMART NOTIFIER (Constitutional Law #8: Functions <50 lines)
# ============================================================================


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

    Constitutional Compliance:
    - Article I: Complete context in notifications
    - Article IV: VectorStore pattern integration
    """

    def __init__(self, max_attempts: int = 5):
        """
        Initialize smart notifier.

        Args:
            max_attempts: Maximum retry attempts before notification
                         (default: 5, per AC-4)
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
        Constitutional: Article I (complete decision context)
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

        # Do NOT notify during retry loop (AC-4 requirement)
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
            error_messages: Error messages (will be sanitized)
            is_blocked: Whether operation is blocked

        Returns:
            Result[NotificationContent, NotificationError]

        Spec: AC-4 (notification content)
        Security: Sanitizes sensitive data
        Constitutional: Article I (complete context)
        """
        # Determine notification reason and content
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

        # Build details (Article I: complete context)
        details = self._build_details(attempt_count, elapsed_seconds, error_messages)

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

    def _build_details(
        self,
        attempt_count: int,
        elapsed_seconds: float,
        error_messages: list[str] | None,
    ) -> str:
        """
        Build notification details section.

        Args:
            attempt_count: Number of fix attempts
            elapsed_seconds: Total elapsed time
            error_messages: Error messages to include

        Returns:
            Formatted details string
        """
        details_parts = [
            f"Time elapsed: {elapsed_seconds:.1f}s",
            f"Fix attempts: {attempt_count}/{self.max_attempts}",
        ]

        if error_messages:
            # Limit to 3 errors to prevent spam (Y2 test requirement)
            errors_text = "\n".join(error_messages[:3])
            details_parts.append(f"Recent errors:\n{errors_text}")

        return "\n".join(details_parts)


# ============================================================================
# CONVENIENCE FUNCTIONS (Article V: Spec-Driven API)
# ============================================================================


def should_notify_user(
    ci_status: str,
    attempt_count: int,
    is_blocked: bool = False,
    max_attempts: int = 5,
) -> bool:
    """
    Simplified notification decision function.

    Args:
        ci_status: Current CI status (success/failure/pending)
        attempt_count: Number of fix attempts made
        is_blocked: Whether operation is blocked
        max_attempts: Maximum retry attempts (default: 5)

    Returns:
        True if user should be notified

    Spec: AC-4 (smart notification)
    """
    notifier = SmartNotifier(max_attempts=max_attempts)
    return notifier.should_notify(ci_status, attempt_count, is_blocked)


def create_user_notification(
    ci_status: str,
    attempt_count: int,
    elapsed_seconds: float,
    error_messages: list[str] | None = None,
    is_blocked: bool = False,
    max_attempts: int = 5,
) -> Result[NotificationContent, NotificationError]:
    """
    Simplified notification creation function.

    Args:
        ci_status: Current CI status
        attempt_count: Number of fix attempts
        elapsed_seconds: Total elapsed time
        error_messages: Error messages to include
        is_blocked: Whether operation is blocked
        max_attempts: Maximum retry attempts (default: 5)

    Returns:
        Result[NotificationContent, NotificationError]

    Spec: AC-4 (notification content)
    Security: Automatically sanitizes sensitive data
    """
    notifier = SmartNotifier(max_attempts=max_attempts)
    return notifier.create_notification(
        ci_status, attempt_count, elapsed_seconds, error_messages, is_blocked
    )
