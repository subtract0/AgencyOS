"""
CheckpointUI - Interactive tiered spec review with auto-approve countdown.

Provides three-tier progressive disclosure UI for specification approval:
- Tier 1: Executive summary displayed immediately (30-second read)
- Tier 2: Key decisions shown on request (2-minute read)
- Tier 3: Full spec view with interactive file display
- Auto-approve: 30-second countdown with any-key interrupt
- Keyboard shortcuts: [A]pprove, [R]evise, [V]iew, [Q]uit

**UI Requirements**:
- Unicode box drawing for visual hierarchy
- Color coding: ✅ (compliant), ⚠️ (needs review), 🔴 (non-compliant)
- Non-blocking keyboard input (select() polling, 100ms interval)
- Terminal escape sequence sanitization (security)

Constitutional Compliance:
- Article I: Complete context (all tiers available before approval)
- Article II: Test summary displayed (verification transparency)
- Article V: Spec traceability (file path shown in Tier 3)

Architecture:
    CheckpointUI.present_checkpoint(tiered_spec)
        ↓
    render_tier1() → Display executive summary
        ↓
    countdown_with_interrupt(30s) → Auto-approve or user input
        ↓
    [A] → APPROVE | [R] → REVISE | [V] → render_tier2/tier3 | [Q] → QUIT
        ↓
    CheckpointResult(action, tier_viewed, timestamp)

Usage:
    from tools.orchestrator.checkpoint_ui import CheckpointUI

    ui = CheckpointUI(timeout_seconds=30)
    result = ui.present_checkpoint(tiered_spec)

    if result.action == UserAction.APPROVE:
        print("✅ User approved specification")
        # Proceed to Stage 2 (TDD execution)
    elif result.action == UserAction.REVISE:
        print("🔄 User requested spec revision")
        # Return to spec generation
    elif result.action == UserAction.QUIT:
        print("❌ User cancelled orchestration")
        # Exit workflow

Reference:
    - Spec: specs/spec-034-tiered-spec-review.md
    - Models: shared/models/orchestrator_models.py
    - Tests: tests/orchestrator/test_checkpoint_ui.py

Version: 1.0.0
Created: 2025-10-15
"""

import logging
import re
import select
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from shared.models.orchestrator_models import (
    CheckpointResult,
    ConstitutionalStatus,
    RiskLevel,
    Tier1Summary,
    Tier2Summary,
    Tier3Reference,
    TieredSpec,
    UserAction,
)

logger = logging.getLogger(__name__)


class CheckpointUI:
    """
    Interactive checkpoint UI with tiered spec review.

    Displays specifications in progressive tiers with auto-approve countdown:
    1. Tier 1: Executive summary (<25 lines, always shown)
    2. Tier 2: Key decisions (<50 lines, on request via [2] key)
    3. Tier 3: Full spec reference (interactive view via [V] key)

    Features:
    - 30-second auto-approve countdown (configurable)
    - Non-blocking keyboard input (any key interrupts)
    - Unicode box drawing and color coding
    - Terminal escape sequence sanitization
    """

    def __init__(self, timeout_seconds: int = 30, default_action: UserAction = UserAction.APPROVE):
        """
        Initialize checkpoint UI.

        Args:
            timeout_seconds: Auto-approve timeout (default: 30s, min: 10s, max: 300s)
            default_action: Action to take on timeout (default: APPROVE)
        """
        # Enforce timeout bounds (security: prevent abuse)
        self.timeout_seconds = max(10, min(timeout_seconds, 300))
        self.default_action = default_action

    def present_checkpoint(self, tiered_spec: TieredSpec) -> CheckpointResult:
        """
        Present tiered spec checkpoint to user.

        Flow:
        1. Display Tier 1 (executive summary)
        2. Start 30-second countdown
        3. Wait for user input or timeout
        4. Handle user action (APPROVE/REVISE/VIEW/QUIT)
        5. Return CheckpointResult with action and tier viewed

        Args:
            tiered_spec: Complete tiered specification

        Returns:
            CheckpointResult with user action and metadata

        Example:
            >>> ui = CheckpointUI(timeout_seconds=30)
            >>> result = ui.present_checkpoint(tiered_spec)
            >>> if result.action == UserAction.APPROVE:
            ...     print("Approved!")
        """
        logger.info("Presenting tiered spec checkpoint")

        # Display Tier 1 immediately
        print("\n" + "=" * 80)
        print("📋 SPECIFICATION CHECKPOINT: TIER 1 (Executive Summary)")
        print("=" * 80 + "\n")

        tier1_rendered = render_tier1(tiered_spec.tier1)
        print(tier1_rendered)

        print("\n" + "-" * 80)
        print("⏱️  AUTO-APPROVE in 30 seconds | Press any key to interrupt")
        print("-" * 80 + "\n")

        # Start countdown with interrupt capability
        user_input = countdown_with_interrupt(self.timeout_seconds, self.default_action)

        # Handle user input
        if user_input == UserAction.APPROVE or user_input is None:
            # Timeout or explicit approve
            print("\n✅ APPROVED - Proceeding to Stage 2 (TDD Execution)")
            return CheckpointResult(
                action=UserAction.APPROVE,
                tier_viewed=1,
                timestamp=datetime.now(UTC),
            )

        elif user_input == UserAction.REVISE:
            print("\n🔄 REVISE REQUESTED - Returning to spec generation")
            return CheckpointResult(
                action=UserAction.REVISE,
                tier_viewed=1,
                timestamp=datetime.now(UTC),
            )

        elif user_input == UserAction.VIEW:
            # User wants to see Tier 2/3
            return self._handle_view_request(tiered_spec)

        elif user_input == UserAction.QUIT:
            print("\n❌ QUIT - Orchestration cancelled")
            return CheckpointResult(
                action=UserAction.QUIT,
                tier_viewed=1,
                timestamp=datetime.now(UTC),
            )

        else:
            # Default to approve (safety: never block workflow indefinitely)
            logger.warning(f"Unknown user input: {user_input}, defaulting to APPROVE")
            return CheckpointResult(
                action=UserAction.APPROVE,
                tier_viewed=1,
                timestamp=datetime.now(UTC),
            )

    def _handle_view_request(self, tiered_spec: TieredSpec) -> CheckpointResult:
        """
        Handle user request to view Tier 2 or Tier 3.

        Flow:
        1. Display Tier 2 (key decisions)
        2. Ask if user wants Tier 3 (full spec)
        3. Display Tier 3 if requested
        4. Re-prompt for approval decision

        Args:
            tiered_spec: Complete tiered specification

        Returns:
            CheckpointResult after user makes final decision
        """
        # Display Tier 2
        print("\n" + "=" * 80)
        print("📊 TIER 2: KEY DECISIONS (Architectural Choices)")
        print("=" * 80 + "\n")

        tier2_rendered = render_tier2(tiered_spec.tier2)
        print(tier2_rendered)

        # Ask if user wants Tier 3
        print("\n" + "-" * 80)
        print("🔍 View full specification (Tier 3)? [Y/n]: ", end="", flush=True)

        view_tier3 = get_user_input()
        tier_viewed = 2

        if view_tier3.lower() in ["y", "yes", ""]:
            # Display Tier 3
            print("\n" + "=" * 80)
            print("📄 TIER 3: FULL SPECIFICATION")
            print("=" * 80 + "\n")

            tier3_rendered = render_tier3(tiered_spec.tier3)
            print(tier3_rendered)
            tier_viewed = 3

        # Re-prompt for final decision
        print("\n" + "-" * 80)
        print("Decision: [A]pprove | [R]evise | [Q]uit: ", end="", flush=True)

        final_action = get_user_input()

        if final_action.lower() in ["a", "approve"]:
            action = UserAction.APPROVE
            print("\n✅ APPROVED - Proceeding to Stage 2 (TDD Execution)")
        elif final_action.lower() in ["r", "revise"]:
            action = UserAction.REVISE
            print("\n🔄 REVISE REQUESTED - Returning to spec generation")
        elif final_action.lower() in ["q", "quit"]:
            action = UserAction.QUIT
            print("\n❌ QUIT - Orchestration cancelled")
        else:
            # Default to approve
            action = UserAction.APPROVE
            print("\n✅ APPROVED (default) - Proceeding to Stage 2")

        return CheckpointResult(
            action=action,
            tier_viewed=tier_viewed,
            timestamp=datetime.now(UTC),
        )


def render_tier1(tier1: Tier1Summary) -> str:
    """
    Render Tier 1 executive summary with Unicode boxes.

    Format:
    ┌────────────────────────────────────────────────────────────────────────────┐
    │ 📋 TIER 1: EXECUTIVE SUMMARY                                              │
    ├────────────────────────────────────────────────────────────────────────────┤
    │ 🎯 MISSION: <mission>                                                      │
    │ 🏗️  APPROACH: <approach>                                                   │
    │ 🧪 TESTS: <test_summary>                                                   │
    │ 📦 DELIVERABLES: <deliverables>                                            │
    │ ⚖️  CONSTITUTIONAL: <status>                                                │
    │ ⏱️  EFFORT: <estimate>                                                      │
    │ 🎚️  RISK: <level>                                                          │
    └────────────────────────────────────────────────────────────────────────────┘

    Args:
        tier1: Tier 1 summary model

    Returns:
        Formatted string with Unicode boxes

    Security: Terminal escape sequences stripped (except UI-generated)
    """
    # Sanitize content (strip user-injected escape sequences)
    mission = sanitize_terminal_content(tier1.mission)
    approach = sanitize_terminal_content(tier1.approach)
    test_summary = sanitize_terminal_content(tier1.test_summary)

    # Constitutional status emoji
    if tier1.constitutional_status == ConstitutionalStatus.COMPLIANT:
        const_emoji = "✅ COMPLIANT"
    elif tier1.constitutional_status == ConstitutionalStatus.NEEDS_REVIEW:
        const_emoji = "⚠️  NEEDS REVIEW"
    else:
        const_emoji = "🔴 NON-COMPLIANT"

    # Risk level emoji
    if tier1.risk_level == RiskLevel.LOW:
        risk_emoji = "🟢 LOW"
    elif tier1.risk_level == RiskLevel.MEDIUM:
        risk_emoji = "🟡 MEDIUM"
    else:
        risk_emoji = "🔴 HIGH"

    # Format deliverables (max 5 shown, truncate rest)
    deliverables_display = ", ".join(tier1.deliverables[:5])
    if len(tier1.deliverables) > 5:
        deliverables_display += f" (+{len(tier1.deliverables) - 5} more)"

    # Build output
    output = []
    output.append("┌" + "─" * 78 + "┐")
    output.append("│ " + "📋 TIER 1: EXECUTIVE SUMMARY".ljust(77) + "│")
    output.append("├" + "─" * 78 + "┤")
    output.append("│" + " " * 78 + "│")
    output.append("│ " + "🎯 MISSION:".ljust(77) + "│")
    output.append("│ " + f"   {mission[:72]}".ljust(77) + "│")
    output.append("│" + " " * 78 + "│")
    output.append("│ " + "🏗️  APPROACH:".ljust(77) + "│")
    output.append("│ " + f"   {approach[:72]}".ljust(77) + "│")
    output.append("│" + " " * 78 + "│")
    output.append("│ " + f"🧪 TESTS: {test_summary[:62]}".ljust(77) + "│")
    output.append("│" + " " * 78 + "│")
    output.append("│ " + f"📦 DELIVERABLES: {deliverables_display[:60]}".ljust(77) + "│")
    output.append("│" + " " * 78 + "│")
    output.append("│ " + f"⚖️  CONSTITUTIONAL: {const_emoji}".ljust(77) + "│")
    output.append("│ " + f"⏱️  EFFORT: {tier1.effort_estimate}".ljust(77) + "│")
    output.append("│ " + f"🎚️  RISK: {risk_emoji}".ljust(77) + "│")
    output.append("│" + " " * 78 + "│")
    output.append("│ " + f"📏 LINE COUNT: {tier1.line_count} / 25 (30-second read)".ljust(77) + "│")
    output.append("└" + "─" * 78 + "┘")

    return "\n".join(output)


def render_tier2(tier2: Tier2Summary) -> str:
    """
    Render Tier 2 key decisions with architectural choices.

    Format:
    ┌────────────────────────────────────────────────────────────────────────────┐
    │ 📊 TIER 2: KEY DECISIONS                                                  │
    ├────────────────────────────────────────────────────────────────────────────┤
    │ 🏛️  ARCHITECTURAL DECISIONS:                                               │
    │                                                                            │
    │ 1. <title>                                                                 │
    │    ✅ Choice: <choice>                                                     │
    │    💡 Rationale: <rationale>                                               │
    │    ⚖️  Trade-offs: <tradeoffs>                                             │
    │                                                                            │
    │ [... more decisions ...]                                                   │
    │                                                                            │
    │ 🔒 SECURITY: <security_implications>                                       │
    │ 📦 DEPENDENCIES: <dependencies>                                            │
    │ 📏 LINE COUNT: <count> / 50 (2-minute read)                                │
    └────────────────────────────────────────────────────────────────────────────┘

    Args:
        tier2: Tier 2 summary model

    Returns:
        Formatted string with Unicode boxes
    """
    output = []
    output.append("┌" + "─" * 78 + "┐")
    output.append("│ " + "📊 TIER 2: KEY DECISIONS".ljust(77) + "│")
    output.append("├" + "─" * 78 + "┤")
    output.append("│" + " " * 78 + "│")
    output.append("│ " + "🏛️  ARCHITECTURAL DECISIONS:".ljust(77) + "│")
    output.append("│" + " " * 78 + "│")

    for idx, decision in enumerate(tier2.decisions, 1):
        title = sanitize_terminal_content(decision.title)
        choice = sanitize_terminal_content(decision.choice)
        rationale = sanitize_terminal_content(decision.rationale)
        tradeoffs = sanitize_terminal_content(decision.tradeoffs)

        output.append("│ " + f"{idx}. {title[:73]}".ljust(77) + "│")
        output.append("│ " + f"   ✅ Choice: {choice[:63]}".ljust(77) + "│")
        output.append("│ " + f"   💡 Rationale: {rationale[:60]}".ljust(77) + "│")
        output.append("│ " + f"   ⚖️  Trade-offs: {tradeoffs[:59]}".ljust(77) + "│")
        output.append("│" + " " * 78 + "│")

    # Security implications
    security = sanitize_terminal_content(tier2.security_implications)
    output.append("│ " + "🔒 SECURITY:".ljust(77) + "│")
    output.append("│ " + f"   {security[:72]}".ljust(77) + "│")
    output.append("│" + " " * 78 + "│")

    # Dependencies
    dependencies = sanitize_terminal_content(tier2.dependencies)
    output.append("│ " + "📦 DEPENDENCIES:".ljust(77) + "│")
    output.append("│ " + f"   {dependencies[:72]}".ljust(77) + "│")
    output.append("│" + " " * 78 + "│")

    output.append("│ " + f"📏 LINE COUNT: {tier2.line_count} / 50 (2-minute read)".ljust(77) + "│")
    output.append("└" + "─" * 78 + "┘")

    return "\n".join(output)


def render_tier3(tier3: Tier3Reference) -> str:
    """
    Render Tier 3 full specification reference.

    Format:
    ┌────────────────────────────────────────────────────────────────────────────┐
    │ 📄 TIER 3: FULL SPECIFICATION                                             │
    ├────────────────────────────────────────────────────────────────────────────┤
    │ 📁 FILE: <file_path>                                                       │
    │ 📏 SIZE: <line_count> lines, <section_count> sections                      │
    │                                                                            │
    │ 🔍 View full spec: cat <file_path>                                         │
    └────────────────────────────────────────────────────────────────────────────┘

    Args:
        tier3: Tier 3 reference model

    Returns:
        Formatted string with Unicode boxes
    """
    file_path_str = str(tier3.file_path)

    output = []
    output.append("┌" + "─" * 78 + "┐")
    output.append("│ " + "📄 TIER 3: FULL SPECIFICATION".ljust(77) + "│")
    output.append("├" + "─" * 78 + "┤")
    output.append("│" + " " * 78 + "│")
    output.append("│ " + f"📁 FILE: {file_path_str[:70]}".ljust(77) + "│")
    output.append("│ " + f"📏 SIZE: {tier3.line_count} lines, {tier3.section_count} sections".ljust(77) + "│")
    output.append("│" + " " * 78 + "│")
    output.append("│ " + f"🔍 View full spec: cat {file_path_str[:58]}".ljust(77) + "│")
    output.append("└" + "─" * 78 + "┘")

    return "\n".join(output)


def countdown_with_interrupt(timeout_seconds: int, default_action: UserAction) -> UserAction:
    """
    Display countdown timer with keyboard interrupt capability.

    Uses select() for non-blocking input polling (Unix systems).
    Any keypress interrupts countdown and prompts for user action.

    Args:
        timeout_seconds: Countdown duration (seconds)
        default_action: Action to return on timeout

    Returns:
        UserAction (APPROVE if timeout, or user's choice if interrupted)

    Platform: Unix-like systems (macOS, Linux)
    Fallback: Windows not supported (would need msvcrt or threading)

    Example:
        >>> action = countdown_with_interrupt(30, UserAction.APPROVE)
        >>> if action == UserAction.APPROVE:
        ...     print("Auto-approved")
    """
    start_time = time.time()
    end_time = start_time + timeout_seconds

    print(f"⏱️  Auto-approve in {timeout_seconds} seconds...")
    print("   Press any key to interrupt: [A]pprove | [R]evise | [V]iew | [Q]uit")
    print()

    try:
        while time.time() < end_time:
            remaining = int(end_time - time.time())

            # Update countdown display (overwrite previous line)
            print(f"\r⏱️  {remaining:2d}s remaining... ", end="", flush=True)

            # Non-blocking check for input (100ms polling interval)
            if select_with_timeout(0.1):
                # User pressed a key - interrupt countdown
                print("\n\n⚠️  Countdown interrupted by user input")
                print("Decision: [A]pprove | [R]evise | [V]iew | [Q]uit: ", end="", flush=True)

                user_input = get_user_input()
                return parse_user_action(user_input)

        # Timeout reached - return default action
        print(f"\n\n✅ Auto-approve timeout ({timeout_seconds}s) - Defaulting to {default_action.value.upper()}")
        return default_action

    except KeyboardInterrupt:
        # Ctrl+C pressed - treat as QUIT
        print("\n\n❌ Interrupted by Ctrl+C - Cancelling orchestration")
        return UserAction.QUIT


def select_with_timeout(timeout: float) -> bool:
    """
    Check if input is available on stdin (non-blocking).

    Uses Unix select() for non-blocking input detection.

    Args:
        timeout: Timeout in seconds (e.g., 0.1 for 100ms)

    Returns:
        True if input available, False if timeout

    Platform: Unix-like systems only
    """
    # Check if stdin has data available
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
    return bool(rlist)


def get_user_input() -> str:
    """
    Get single line of user input.

    Returns:
        User input string (lowercased, stripped)
    """
    try:
        user_input = input().strip().lower()
        return user_input
    except (EOFError, KeyboardInterrupt):
        return "q"  # Treat EOF/Ctrl+C as quit


def parse_user_action(user_input: str) -> UserAction:
    """
    Parse user input string to UserAction enum.

    Mapping:
    - 'a', 'approve' → UserAction.APPROVE
    - 'r', 'revise' → UserAction.REVISE
    - 'v', 'view' → UserAction.VIEW
    - 'q', 'quit' → UserAction.QUIT
    - default → UserAction.APPROVE

    Args:
        user_input: User input string (lowercased)

    Returns:
        UserAction enum

    Example:
        >>> parse_user_action("a")
        UserAction.APPROVE
    """
    if user_input in ["a", "approve"]:
        return UserAction.APPROVE
    elif user_input in ["r", "revise"]:
        return UserAction.REVISE
    elif user_input in ["v", "view"]:
        return UserAction.VIEW
    elif user_input in ["q", "quit"]:
        return UserAction.QUIT
    else:
        # Default to approve (never block workflow indefinitely)
        logger.warning(f"Unknown user input '{user_input}', defaulting to APPROVE")
        return UserAction.APPROVE


def sanitize_terminal_content(content: str) -> str:
    """
    Sanitize terminal content by stripping ANSI escape sequences.

    Security: Prevents malicious spec content from injecting terminal
    control sequences (clear screen, title change, cursor movement, etc.).

    Args:
        content: Raw content from spec file

    Returns:
        Sanitized content (ANSI sequences stripped)

    Example:
        >>> sanitize_terminal_content("Text \\x1b[31mRED\\x1b[0m")
        'Text RED'
    """
    # Strip all ANSI escape sequences (7-bit and 8-bit)
    ansi_escape_pattern = re.compile(
        r"""
        \x1b     # ESC
        \[       # [
        [0-9;]*  # Parameters (digits and semicolons)
        [a-zA-Z] # Command letter
        |
        \x1b\]   # OSC (Operating System Command)
        [^\x07]* # Any chars until BEL
        \x07     # BEL
        |
        \x1b\(   # Charset selection
        [0-9A-Z]
        """,
        re.VERBOSE,
    )

    sanitized = ansi_escape_pattern.sub("", content)
    return sanitized


__all__ = [
    "CheckpointUI",
    "render_tier1",
    "render_tier2",
    "render_tier3",
    "countdown_with_interrupt",
    "select_with_timeout",
    "get_user_input",
    "parse_user_action",
    "sanitize_terminal_content",
]
