"""
CLI command for autonomous CI feedback loop.

Usage:
    /ci-fix-loop <pr-number> [--max-attempts=5]

Description:
    Autonomously monitors, diagnoses, and fixes CI failures for the specified PR.
    Implements the watch-diagnose-fix-verify cycle without manual intervention.

Arguments:
    pr-number: GitHub PR number (required, must be positive integer)

Options:
    --max-attempts=N: Maximum fix attempts (default: 5, range: 1-10)
    --help: Show this help text

Exit Codes:
    0: Success (all CI checks passing)
    1: Blocked (max attempts reached or unrecoverable error)
    2: Invalid arguments
    3: Missing credentials (GITHUB_TOKEN)

Examples:
    /ci-fix-loop 123
    /ci-fix-loop 456 --max-attempts=3

Spec: specs/spec-autonomous-ci-feedback-loop.md
Constitutional Compliance: Articles I-V verified
"""

import asyncio
import os
import sys
from typing import Any

# Import the orchestrator
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from shared.type_definitions.result import Result
from tools.ci_monitor.feedback_loop_orchestrator import autonomous_ci_fix_loop


def parse_arguments(args: list[str]) -> Result[dict[str, Any], str]:
    """
    Parse CLI arguments for /ci-fix-loop command.

    Args:
        args: Command-line arguments

    Returns:
        Result with parsed arguments dict or error message
    """
    if not args or args[0] in ["--help", "-h"]:
        return Result.err(HELP_TEXT)

    # Parse PR number (required)
    try:
        pr_number = int(args[0])
        if pr_number <= 0:
            return Result.err("Error: PR number must be a positive integer")
    except ValueError:
        return Result.err(f"Error: Invalid PR number '{args[0]}'. Must be an integer.")

    # Parse optional flags
    max_attempts = 5  # default

    for arg in args[1:]:
        if arg.startswith("--max-attempts="):
            try:
                max_attempts = int(arg.split("=")[1])
                if not (1 <= max_attempts <= 10):
                    return Result.err("Error: --max-attempts must be between 1 and 10")
            except ValueError:
                return Result.err(f"Error: Invalid --max-attempts value: {arg}")
        else:
            return Result.err(f"Error: Unknown argument '{arg}'. Use --help for usage.")

    return Result.ok({
        "pr_number": pr_number,
        "max_attempts": max_attempts
    })


def validate_credentials() -> Result[None, str]:
    """
    Validate GitHub credentials before execution.

    Returns:
        Result with None on success or error message
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return Result.err(
            "Error: GITHUB_TOKEN environment variable not set.\n"
            "Set it with: export GITHUB_TOKEN=ghp_your_token"
        )

    # Validate token format (basic check)
    if not (token.startswith("ghp_") or token.startswith("ghs_") or token.startswith("gho_")):
        return Result.err(
            "Error: GITHUB_TOKEN has invalid format.\n"
            "Expected format: ghp_*, ghs_*, or gho_*"
        )

    return Result.ok(None)


async def run_feedback_loop(pr_number: int, max_attempts: int) -> int:
    """
    Run the autonomous CI feedback loop.

    Args:
        pr_number: GitHub PR number
        max_attempts: Maximum fix attempts

    Returns:
        Exit code (0=success, 1=blocked, 3=error)
    """
    print(f"🚀 Starting autonomous CI feedback loop for PR #{pr_number}")
    print(f"   Max attempts: {max_attempts}")
    print("   Monitoring CI status...\n")

    result = await autonomous_ci_fix_loop(pr_number, max_attempts)

    if result.is_ok():
        loop_result = result.unwrap()
        if loop_result.all_passing:
            print(f"\n✅ Success! All CI checks passing after {loop_result.fix_attempts} attempts")
            print(f"   Errors fixed: {loop_result.errors_fixed}")
            print(f"   Elapsed time: {loop_result.elapsed_seconds:.1f}s")
            return 0
        else:
            print("\n⚠️ Blocked: Unable to resolve CI failures")
            print(f"   Final state: {loop_result.final_state}")
            print(f"   Attempts used: {loop_result.fix_attempts}/{max_attempts}")
            return 1
    else:
        error = result.unwrap_err()
        print(f"\n❌ Error: {error.message}")
        if error.details:
            print(f"   Details: {error.details}")
        return 1


def main(args: list[str]) -> int:
    """
    Main entry point for /ci-fix-loop command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0-3)
    """
    # Parse arguments
    parse_result = parse_arguments(args)
    if parse_result.is_err():
        error_msg = parse_result.unwrap_err()
        print(error_msg)
        return 2 if error_msg.startswith("Error:") else 0  # 0 for --help

    parsed = parse_result.unwrap()

    # Validate credentials
    creds_result = validate_credentials()
    if creds_result.is_err():
        print(creds_result.unwrap_err())
        return 3

    # Run feedback loop
    try:
        exit_code = asyncio.run(run_feedback_loop(
            parsed["pr_number"],
            parsed["max_attempts"]
        ))
        return exit_code
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


HELP_TEXT = """
🤖 Autonomous CI Feedback Loop

USAGE:
    /ci-fix-loop <pr-number> [--max-attempts=N]

DESCRIPTION:
    Autonomously monitors, diagnoses, and fixes CI failures for the specified PR.
    Implements the watch-diagnose-fix-verify cycle without manual intervention.

ARGUMENTS:
    pr-number          GitHub PR number (required, positive integer)

OPTIONS:
    --max-attempts=N   Maximum fix attempts (default: 5, range: 1-10)
    --help, -h         Show this help text

EXIT CODES:
    0  Success (all CI checks passing)
    1  Blocked (max attempts reached or unrecoverable error)
    2  Invalid arguments
    3  Missing credentials (GITHUB_TOKEN)

EXAMPLES:
    /ci-fix-loop 123
    /ci-fix-loop 456 --max-attempts=3

FEATURES:
    ✅ Autonomous monitoring (30s polling)
    ✅ Automatic log fetching (gh run view)
    ✅ Error pattern recognition (5+ types)
    ✅ Intelligent fix generation
    ✅ CI retriggering (60s timeout)
    ✅ Smart notifications (terminal states only)
    ✅ VectorStore learning (continuous improvement)

CONSTITUTIONAL COMPLIANCE:
    Article I:   Complete context (retry on timeout)
    Article II:  100% verification (tests validate behavior)
    Article III: Automated enforcement (no manual overrides)
    Article IV:  VectorStore learning (query before, store after)
    Article V:   Spec-driven (traceable to spec-autonomous-ci-feedback-loop.md)

SPEC: specs/spec-autonomous-ci-feedback-loop.md
DOCS: docs/CI_FEEDBACK_LOOP.md
"""


# Entry point when invoked as slash command
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
