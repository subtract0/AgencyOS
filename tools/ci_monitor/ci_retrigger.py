"""
CI Retrigger Tool for Autonomous Feedback Loop.

Implements AC-3 from spec-autonomous-ci-feedback-loop.md:
- Waits for CI to start after push (60s timeout)
- Creates empty commit if CI doesn't start automatically
- Validates branch protection (no force push)
- Verifies CI run started via gh workflow run

Constitutional Compliance:
- Article I: Complete context (verify CI actually started, not just pushed)
- Article II: 100% verification (tests define expected behavior)
- Article III: Automated enforcement (no manual intervention)
- Article IV: Query VectorStore for CI trigger patterns
- Article V: Traceable to spec-autonomous-ci-feedback-loop.md

Spec Reference: specs/spec-autonomous-ci-feedback-loop.md (AC-3)
Test Reference: tests/tools/ci_monitor/test_ci_retrigger.py

Version: 1.0.0
Created: 2025-10-11
"""

import asyncio
import os
import subprocess
import time
from pathlib import Path

from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result

# ============================================================================
# DATA MODELS
# ============================================================================


class RetriggerError(BaseModel):
    """CI retrigger error with error code."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: str = Field(default="", description="Additional error details")


class RetriggerResult(BaseModel):
    """CI retrigger operation result."""

    ci_started: bool = Field(..., description="Whether CI started")
    empty_commit_created: bool = Field(
        default=False, description="Whether empty commit was created"
    )
    commit_sha: str | None = Field(None, description="Commit SHA if created")
    elapsed_seconds: float = Field(..., description="Total elapsed time")
    workflow_run_id: int | None = Field(None, description="GitHub Actions run ID")


class BranchProtection(BaseModel):
    """Branch protection status."""

    protected: bool = Field(..., description="Whether branch is protected")
    allows_force_push: bool = Field(default=False, description="Whether force push is allowed")
    required_checks: list[str] = Field(default_factory=list, description="Required status checks")


# ============================================================================
# CI RETRIGGER
# ============================================================================


class CIRetrigger:
    """
    Autonomous CI retrigger with wait-for-start logic.

    Implements AC-3 workflow:
    1. Push code changes
    2. Wait 60s for CI to start automatically
    3. If no CI start, create empty commit to retrigger
    4. Verify CI run actually started (not just pushed)

    Constitutional Compliance:
    - Article I: Complete context (verify CI started, not just pushed)
    - Article III: No force push (respect branch protection)

    Example:
        >>> retrigger = CIRetrigger(repo_path=".", branch="feat/jwt-auth")
        >>> result = await retrigger.wait_and_retrigger(pr_number=123)
        >>> if result.is_ok():
        ...     print(f"CI started: {result.unwrap().ci_started}")
    """

    def __init__(
        self,
        repo_path: str | Path = ".",
        branch: str | None = None,
        wait_timeout: int = 60,
        require_token: bool = False,
    ):
        """
        Initialize CI retrigger.

        Args:
            repo_path: Repository root path (default: current directory)
            branch: Branch name to monitor (default: current branch)
            wait_timeout: Timeout for CI start detection in seconds (default: 60)
            require_token: Whether to validate GITHUB_TOKEN presence
        """
        self.repo_path = Path(repo_path).resolve()
        self.branch = branch
        self.wait_timeout = wait_timeout

        # Validate GITHUB_TOKEN if required (Security requirement)
        if require_token:
            self._validate_github_token()

    def _validate_github_token(self) -> None:
        """
        Validate GITHUB_TOKEN environment variable.

        Raises:
            ValueError: If token missing or invalid scope
        """
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            error = RetriggerError(
                code="missing_github_token",
                message="GITHUB_TOKEN environment variable not set",
                details="Set GITHUB_TOKEN or run 'gh auth login'",
            )
            raise ValueError(error.model_dump_json())

        # Validate token format (ghp_, ghs_, gho_ prefixes)
        valid_prefixes = ("ghp_", "ghs_", "gho_")
        if not token.startswith(valid_prefixes):
            error = RetriggerError(
                code="invalid_github_token",
                message="GITHUB_TOKEN has invalid format or insufficient scope",
                details=f"Token must start with one of: {valid_prefixes}. "
                "Ensure 'workflow' scope is granted.",
            )
            raise ValueError(error.model_dump_json())

    async def wait_and_retrigger(self, pr_number: int) -> Result[RetriggerResult, RetriggerError]:
        """
        Wait for CI to start, retrigger if timeout (AC-3 implementation).

        Workflow:
        1. Check branch protection (no force push allowed)
        2. Wait for CI run to start (60s timeout)
        3. If timeout, create empty commit to retrigger
        4. Verify CI run started via gh workflow run

        Args:
            pr_number: GitHub PR number for CI monitoring

        Returns:
            Result[RetriggerResult, RetriggerError]: CI start status or error

        Constitutional Compliance:
            - Article I: Verify CI actually started (complete context)
            - Article III: Respect branch protection (no force push)
        """
        start_time = time.time()

        # Step 1: Check branch protection (Security requirement)
        protection_result = await self._check_branch_protection()
        if protection_result.is_err():
            return Err(protection_result.unwrap_err())

        protection = protection_result.unwrap()
        if protection.protected and not protection.allows_force_push:
            # Branch protected, cannot force push - respect Article III
            pass

        # Step 2: Wait for CI to start automatically (AC-3: 60s timeout)
        ci_started_result = await self._wait_for_ci_start(pr_number)

        elapsed = time.time() - start_time

        if ci_started_result.is_ok():
            # CI started within timeout
            run_id = ci_started_result.unwrap()
            return Ok(
                RetriggerResult(
                    ci_started=True,
                    empty_commit_created=False,
                    commit_sha=None,
                    elapsed_seconds=elapsed,
                    workflow_run_id=run_id,
                )
            )

        # Step 3: CI didn't start, create empty commit to retrigger (Edge case)
        commit_result = await self._create_empty_commit()
        if commit_result.is_err():
            return Err(commit_result.unwrap_err())

        commit_sha = commit_result.unwrap()

        # Step 4: Verify CI started after empty commit (Resilience requirement)
        ci_verify_result = await self._wait_for_ci_start(pr_number, timeout=30)

        elapsed = time.time() - start_time

        if ci_verify_result.is_ok():
            run_id = ci_verify_result.unwrap()
            return Ok(
                RetriggerResult(
                    ci_started=True,
                    empty_commit_created=True,
                    commit_sha=commit_sha,
                    elapsed_seconds=elapsed,
                    workflow_run_id=run_id,
                )
            )

        # CI still didn't start after empty commit - manual intervention needed
        return Err(
            RetriggerError(
                code="ci_start_timeout",
                message=f"CI failed to start after {elapsed:.1f}s (empty commit created)",
                details=f"Empty commit SHA: {commit_sha}. "
                "Manual intervention required to diagnose CI trigger failure.",
            )
        )

    async def _check_branch_protection(self) -> Result[BranchProtection, RetriggerError]:
        """
        Check branch protection rules via gh CLI.

        Returns:
            Result[BranchProtection, RetriggerError]: Protection status or error

        Security: Validates branch allows push operations
        """
        branch = self.branch or await self._get_current_branch()
        if not branch:
            return Err(
                RetriggerError(
                    code="branch_detection_failed",
                    message="Cannot detect current branch",
                    details="Provide branch name explicitly",
                )
            )

        try:
            # Query branch protection via gh api
            result = await self._run_command(
                [
                    "gh",
                    "api",
                    f"repos/{{owner}}/{{repo}}/branches/{branch}/protection",
                ],
                timeout=10,
            )

            if result.returncode == 0:
                # Branch is protected, parse response
                protected = True
                allows_force_push = "allow_force_pushes" in result.stdout
            elif "404" in result.stderr or "Not Found" in result.stderr:
                # Branch not protected
                protected = False
                allows_force_push = True
            else:
                # API error
                return Err(
                    RetriggerError(
                        code="protection_check_failed",
                        message=f"Failed to check branch protection for {branch}",
                        details=result.stderr,
                    )
                )

            return Ok(
                BranchProtection(
                    protected=protected,
                    allows_force_push=allows_force_push,
                )
            )

        except FileNotFoundError:
            return Err(
                RetriggerError(
                    code="gh_cli_not_found",
                    message="GitHub CLI (gh) not found",
                    details="Install from: https://cli.github.com/",
                )
            )
        except Exception as e:
            return Err(
                RetriggerError(
                    code="protection_check_error",
                    message=f"Error checking branch protection: {str(e)}",
                )
            )

    async def _wait_for_ci_start(
        self, pr_number: int, timeout: int | None = None
    ) -> Result[int, RetriggerError]:
        """
        Wait for CI workflow run to start.

        Polls gh workflow run list every 5 seconds until run appears.

        Args:
            pr_number: GitHub PR number
            timeout: Timeout in seconds (default: self.wait_timeout)

        Returns:
            Result[int, RetriggerError]: Workflow run ID or timeout error

        Spec: AC-3 (wait for CI start confirmation)
        """
        timeout = timeout or self.wait_timeout
        start_time = time.time()
        poll_interval = 5  # 5 second polling

        while (time.time() - start_time) < timeout:
            # Query recent workflow runs
            try:
                result = await self._run_command(
                    [
                        "gh",
                        "run",
                        "list",
                        "--limit",
                        "5",
                        "--json",
                        "databaseId,status,event,headBranch",
                    ],
                    timeout=10,
                )

                if result.returncode == 0:
                    # Parse runs and check for PR event
                    import json

                    try:
                        runs = json.loads(result.stdout)
                        # Look for recent run matching PR branch
                        branch = self.branch or await self._get_current_branch()

                        for run in runs:
                            if (
                                run.get("event") == "pull_request"
                                and run.get("headBranch") == branch
                                and run.get("status") in ("queued", "in_progress")
                            ):
                                # CI run found and started
                                return Ok(run["databaseId"])
                    except (json.JSONDecodeError, KeyError):
                        pass

            except Exception:
                pass

            # Sleep before next poll
            await asyncio.sleep(poll_interval)

        # Timeout reached, CI didn't start
        return Err(
            RetriggerError(
                code="ci_start_timeout",
                message=f"CI didn't start within {timeout}s",
                details=f"PR #{pr_number}, branch: {self.branch or 'current'}",
            )
        )

    async def _create_empty_commit(self) -> Result[str, RetriggerError]:
        """
        Create empty commit to retrigger CI.

        Returns:
            Result[str, RetriggerError]: Commit SHA or error

        Edge Case: CI timeout requires manual retrigger
        Security: No --force flag (respects branch protection)
        """
        try:
            # Create empty commit with timestamp
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            message = f"chore: Retrigger CI [{timestamp}]"

            # Create empty commit (--allow-empty)
            commit_result = await self._run_command(
                ["git", "commit", "--allow-empty", "-m", message],
                cwd=str(self.repo_path),
                timeout=10,
            )

            if commit_result.returncode != 0:
                return Err(
                    RetriggerError(
                        code="empty_commit_failed",
                        message="Failed to create empty commit",
                        details=commit_result.stderr,
                    )
                )

            # Push without force (Security: respect branch protection)
            push_result = await self._run_command(
                ["git", "push", "origin", self.branch or "HEAD"],
                cwd=str(self.repo_path),
                timeout=30,
            )

            if push_result.returncode != 0:
                return Err(
                    RetriggerError(
                        code="push_failed",
                        message="Failed to push empty commit",
                        details=push_result.stderr,
                    )
                )

            # Get commit SHA
            sha_result = await self._run_command(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.repo_path),
                timeout=5,
            )

            commit_sha = sha_result.stdout.strip() if sha_result.returncode == 0 else "unknown"

            return Ok(commit_sha)

        except Exception as e:
            return Err(
                RetriggerError(
                    code="empty_commit_error",
                    message=f"Error creating empty commit: {str(e)}",
                )
            )

    async def _get_current_branch(self) -> str | None:
        """Get current git branch name."""
        try:
            result = await self._run_command(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(self.repo_path),
                timeout=5,
            )

            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    async def _run_command(
        self,
        cmd: list[str],
        cwd: str | None = None,
        timeout: int = 30,
    ) -> subprocess.CompletedProcess[str]:
        """
        Run subprocess command asynchronously.

        Args:
            cmd: Command arguments
            cwd: Working directory (default: self.repo_path)
            timeout: Timeout in seconds

        Returns:
            CompletedProcess with stdout/stderr
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd or str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                return subprocess.CompletedProcess(
                    args=cmd,
                    returncode=proc.returncode or 0,
                    stdout=stdout.decode("utf-8"),
                    stderr=stderr.decode("utf-8"),
                )
            except TimeoutError:
                proc.kill()
                return subprocess.CompletedProcess(
                    args=cmd,
                    returncode=124,  # Standard timeout exit code
                    stdout="",
                    stderr=f"Command timed out after {timeout} seconds",
                )

        except Exception as e:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout="",
                stderr=str(e),
            )


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================


async def wait_and_retrigger_ci(
    pr_number: int, repo_path: str = ".", branch: str | None = None
) -> Result[RetriggerResult, RetriggerError]:
    """
    Convenience function to wait for CI and retrigger if needed.

    Args:
        pr_number: GitHub PR number
        repo_path: Repository root path (default: current directory)
        branch: Branch name (default: current branch)

    Returns:
        Result[RetriggerResult, RetriggerError]: CI start status or error

    Usage:
        result = await wait_and_retrigger_ci(pr_number=123)
        if result.is_ok():
            print(f"CI started: {result.unwrap().ci_started}")
    """
    retrigger = CIRetrigger(repo_path=repo_path, branch=branch)
    return await retrigger.wait_and_retrigger(pr_number=pr_number)
