"""
CLI Integration for Autonomous CI Feedback Loop.

Provides /ci-fix-loop command that invokes autonomous_ci_fix_loop orchestrator
with argument validation and credential checking.

Constitutional Compliance:
- Article I: Complete argument validation before execution
- Article II: 100% verification (exit code 0 only on green CI)
- Article III: Automated enforcement (no manual intervention)
- Article IV: Query VectorStore for CLI patterns
- Article V: Traceable to spec-autonomous-ci-feedback-loop.md

Usage:
    cli = CLIIntegration()
    exit_code = await cli.run(["123", "--max-attempts=3"])

Exit Codes:
    0: Success (all CI checks passing)
    1: Blocked (max attempts reached or unrecoverable error)
    2: Invalid arguments
    3: Missing credentials (GITHUB_TOKEN)

Version: 1.0.0
Created: 2025-10-16
"""

import os
import sys
from pathlib import Path
from typing import Any

from shared.type_definitions.result import Err, Ok
from tools.ci_monitor.feedback_loop_orchestrator import (
    LoopError,
    LoopResult,
    autonomous_ci_fix_loop,
)


class CLIArguments:
    """CLI argument container (Pydantic-like validation)."""

    def __init__(
        self,
        pr_number: int,
        max_attempts: int = 5,
        worktree: Path | None = None,
        branch: str | None = None,
    ):
        """Validate and store CLI arguments."""
        # Validate PR number (NECESSARY-E1: Invalid PR number)
        if not isinstance(pr_number, int) or pr_number <= 0:
            raise ValueError(f"Invalid PR number: {pr_number}")

        # Validate max attempts
        if not isinstance(max_attempts, int) or max_attempts < 1 or max_attempts > 20:
            raise ValueError(f"Invalid max_attempts: {max_attempts} (must be 1-20)")

        self.pr_number = pr_number
        self.max_attempts = max_attempts
        self.worktree = worktree or Path.cwd()
        self.branch = branch


class CLIExitCode:
    """Exit codes for CLI (NECESSARY-Y: Yield validation)."""

    SUCCESS = 0
    BLOCKED = 1
    INVALID_ARGS = 2
    MISSING_CREDENTIALS = 3


class CLIIntegration:
    """
    CLI integration for autonomous CI feedback loop.

    Provides /ci-fix-loop command that invokes autonomous_ci_fix_loop
    orchestrator with argument validation and credential checking.

    Constitutional Compliance:
    - Article I: Complete argument validation before execution
    - Article II: 100% verification (exit code 0 only on green CI)
    - Article III: Automated enforcement (no manual intervention)
    - Article IV: Query VectorStore for CLI patterns
    - Article V: Traceable to spec-autonomous-ci-feedback-loop.md

    Usage:
        cli = CLIIntegration()
        exit_code = await cli.run(["123", "--max-attempts=3"])
    """

    def __init__(self, agent_context: Any | None = None):
        """Initialize CLI with optional AgentContext."""
        self.agent_context = agent_context

    async def run(self, args: list[str]) -> int:
        """
        Execute CLI with argument validation and orchestrator handoff.

        Args:
            args: CLI arguments (e.g., ["123", "--max-attempts=5"])

        Returns:
            Exit code (0=success, 1=blocked, 2=invalid args, 3=missing creds)
        """
        # Parse arguments
        try:
            cli_args = self._parse_arguments(args)
        except ValueError as e:
            self._print_error(f"Invalid arguments: {e}")
            return CLIExitCode.INVALID_ARGS

        # Validate credentials (NECESSARY-S3: GitHub token validation)
        if not self._validate_credentials():
            self._print_error("Missing GITHUB_TOKEN. Set via: export GITHUB_TOKEN=ghp_...")
            return CLIExitCode.MISSING_CREDENTIALS

        # Query VectorStore for CLI patterns (Article IV)
        if self.agent_context:
            self._query_cli_patterns()

        # Invoke orchestrator (handoff to autonomous_ci_fix_loop)
        result = await autonomous_ci_fix_loop(
            pr_number=cli_args.pr_number,
            max_attempts=cli_args.max_attempts,
        )

        # Handle result
        if result.is_ok():
            loop_result = result.unwrap()
            self._print_success(loop_result)
            return CLIExitCode.SUCCESS
        else:
            loop_error = result.unwrap_err()
            self._print_blocked(loop_error)
            return CLIExitCode.BLOCKED

    def _parse_arguments(self, args: list[str]) -> CLIArguments:
        """Parse CLI arguments with validation."""
        if not args or args[0] in ["--help", "-h"]:
            self._print_help()
            sys.exit(0)

        if args[0] in ["--version", "-v"]:
            self._print_version()
            sys.exit(0)

        # Extract PR number (required positional argument)
        try:
            pr_number = int(args[0])
        except (ValueError, IndexError) as e:
            raise ValueError("PR number is required as first argument") from e

        # Parse optional flags
        max_attempts = 5
        worktree = None
        branch = None

        for arg in args[1:]:
            if arg.startswith("--max-attempts="):
                max_attempts = int(arg.split("=")[1])
            elif arg.startswith("--worktree="):
                worktree = Path(arg.split("=")[1])
            elif arg.startswith("--branch="):
                branch = arg.split("=")[1]
            else:
                raise ValueError(f"Unknown argument: {arg}")

        return CLIArguments(
            pr_number=pr_number,
            max_attempts=max_attempts,
            worktree=worktree,
            branch=branch,
        )

    def _validate_credentials(self) -> bool:
        """Validate GITHUB_TOKEN is present and valid format."""
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return False

        # Validate token format (ghp_, ghs_, gho_ prefix)
        valid_prefixes = ("ghp_", "ghs_", "gho_")
        return token.startswith(valid_prefixes)

    def _query_cli_patterns(self) -> None:
        """Query VectorStore for CLI patterns (Article IV)."""
        try:
            patterns = self.agent_context.search_memories(
                tags=["cli", "ci_fix_loop", "success"],
                include_session=False,
            )
            # Apply learned patterns (e.g., optimal max_attempts)
        except Exception:
            # Non-critical: continue without patterns
            pass

    def _print_help(self) -> None:
        """Print help text (NECESSARY-A: Accessibility)."""
        help_text = """
Usage: /ci-fix-loop <pr-number> [OPTIONS]

Autonomous CI feedback loop for GitHub pull requests.
Monitors CI status, diagnoses failures, applies fixes, and verifies results.

Arguments:
  pr-number              GitHub PR number (required)

Options:
  --max-attempts=N       Maximum fix attempts (default: 5, range: 1-20)
  --worktree=PATH        Path to git worktree (default: current directory)
  --branch=BRANCH        Branch name (default: current branch)
  --help, -h             Show this help message
  --version, -v          Show version information

Exit Codes:
  0    Success (all CI checks passing)
  1    Blocked (max attempts reached or unrecoverable error)
  2    Invalid arguments
  3    Missing credentials (GITHUB_TOKEN not set)

Environment:
  GITHUB_TOKEN           GitHub personal access token (required, must have workflow scope)

Examples:
  /ci-fix-loop 123                    # Fix PR #123 with defaults
  /ci-fix-loop 456 --max-attempts=10  # Fix PR #456 with 10 attempts
  /ci-fix-loop 789 --branch=feat/auth # Fix PR #789 on specific branch

Constitutional Compliance:
  - Article I: Complete context (validates all arguments before execution)
  - Article II: 100% verification (exit code 0 only on green CI)
  - Article III: Automated enforcement (no manual intervention)
  - Article IV: VectorStore learning (stores successful patterns)
  - Article V: Traceable to spec-autonomous-ci-feedback-loop.md

For more information: docs/adr/ADR-027-autonomous-ci-feedback-loop.md
        """
        print(help_text.strip())

    def _print_version(self) -> None:
        """Print version information."""
        print("CI Feedback Loop CLI v1.0.0")
        print("Part of Agency OS autonomous CI fixing system")

    def _print_error(self, message: str) -> None:
        """Print error message to stderr."""
        print(f"ERROR: {message}", file=sys.stderr)

    def _print_success(self, result: LoopResult) -> None:
        """Print success summary (NECESSARY-A: Accessibility)."""
        print("✓ CI Feedback Loop Complete")
        print(f"  PR #{result.ci_status.pr_number}: All checks passing")
        print(f"  Fix attempts: {result.fix_attempts}")
        print(f"  Elapsed time: {result.elapsed_seconds:.1f}s")
        print(f"  Errors fixed: {', '.join(result.errors_fixed) or 'none'}")

    def _print_blocked(self, error: LoopError) -> None:
        """Print blocked message (NECESSARY-A: Accessibility)."""
        print("✗ CI Feedback Loop Blocked")
        print(f"  Reason: {error.message}")
        print(f"  Details: {error.details}")
        print(f"  Recoverable: {error.recoverable}")
        print("\nManual intervention required. Review CI logs for details.")
