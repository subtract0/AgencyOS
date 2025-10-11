"""
CI Monitor: Autonomous CI status polling and feedback loop.

Implements autonomous monitoring workflow from spec-autonomous-ci-feedback-loop.md:
1. Poll CI status every 30s (AC-1)
2. Fetch failure logs automatically (AC-2)
3. Retrigger CI after fixes (AC-3)
4. Smart notification (AC-4)
5. Error pattern recognition (AC-5)

Constitutional Compliance:
- Article I: Complete context (fetch all logs automatically)
- Article II: 100% test coverage (TDD)
- Article III: Automated enforcement (no manual intervention)
- Article IV: Learn patterns (store successful fixes to VectorStore)
- Article V: Traceable to spec-autonomous-ci-feedback-loop.md

Version: 1.0.0
Created: 2025-10-11
"""

__all__ = [
    # Status Poller (AC-1: Autonomous monitoring)
    "StatusPoller",
    "CIStatus",
    "CheckResult",
    "CheckState",
    "PollResult",
    "StatusPollerError",
    "poll_until_complete",
    # Log Fetcher (AC-2: Autonomous log fetching)
    "fetch_failure_logs",
    "LogContent",
    "LogSection",
    "LogError",
    # Error Parser (AC-5: Error pattern recognition)
    "parse_ci_logs",
    "sanitize_log_output",
    "ErrorPattern",
    "ParseError",
    # CI Retrigger (AC-3: Autonomous retrigger)
    "CIRetrigger",
    "RetriggerResult",
    "RetriggerError",
    "BranchProtection",
    "wait_and_retrigger_ci",
    # Fix Applicator (AC-3: Apply fixes and push)
    "FixApplicator",
    "FixApplication",
    "CodeFix",
    "FixApplicatorError",
    "apply_fix_and_push",
    # Smart Notifier (AC-4: Smart notification)
    "SmartNotifier",
    "NotificationContent",
    "NotificationReason",
    "NotificationError",
    "should_notify_user",
    "create_user_notification",
]

# Log Fetcher (AC-2: Autonomous log fetching)
from .log_fetcher import LogContent, LogError, LogSection, fetch_failure_logs

# Status Poller exports (AC-1: Autonomous monitoring)
from .status_poller import (
    CIStatus,
    CheckResult,
    CheckState,
    PollResult,
    StatusPoller,
    StatusPollerError,
    poll_until_complete,
)

# Error Parser exports (AC-5: Error pattern recognition)
from .code_error_parser import (
    ErrorPattern,
    ParseError,
    parse_ci_logs,
    sanitize_log_output,
)

# CI Retrigger exports (AC-3: Autonomous retrigger)
from .ci_retrigger import (
    BranchProtection,
    CIRetrigger,
    RetriggerError,
    RetriggerResult,
    wait_and_retrigger_ci,
)

# Fix Applicator exports (AC-3: Apply fixes and push)
from .fix_applicator import (
    CodeFix,
    FixApplication,
    FixApplicator,
    FixApplicatorError,
    apply_fix_and_push,
)

# Smart Notifier exports (AC-4: Smart notification)
from .smart_notifier import (
    NotificationContent,
    NotificationError,
    NotificationReason,
    SmartNotifier,
    create_user_notification,
    should_notify_user,
)
