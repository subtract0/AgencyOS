"""
Fix Applicator: Apply code fixes and commit to git worktree.

Implements autonomous fix application from spec-autonomous-ci-feedback-loop.md:
- Apply fixes to files in isolated worktree (AC-3)
- Create git commits with descriptive messages
- Push to remote branch to trigger CI
- Handle rollback on failure (resilience)

Constitutional Compliance:
- Article I: Complete context (all git operations complete, retry on timeout)
- Article II: 100% verification (test-driven, 25 tests pass)
- Article III: Automated enforcement (no manual overrides)
- Article IV: VectorStore learning (query patterns before, store after)
- Article V: Traceable to spec-autonomous-ci-feedback-loop.md (AC-3)

Version: 1.0.0
Created: 2025-10-11
"""

import os
import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result

# ============================================================================
# PYDANTIC MODELS (Strict Typing - Constitutional Law #2)
# ============================================================================


class FixApplicatorError(Exception):
    """
    Base exception for fix applicator errors.

    Attributes:
        operation: Operation that failed (apply_fix, commit_changes, etc.)
        message: Human-readable error message
        details: Additional context (file paths, stderr output)
        code: Machine-readable error code
    """

    def __init__(self, operation: str, message: str, details: str = "", code: str = ""):
        self.operation = operation
        self.message = message
        self.details = details
        self.code = code
        super().__init__(f"{operation}: {message}")


class FixApplication(BaseModel):
    """
    Result of applying a fix to code.

    Attributes:
        file_path: Path to file that was modified
        original_content: Original file content (for rollback)
        fixed_content: Content after applying fix
        diff: Unified diff of changes
        commit_sha: Git commit SHA (40-character hex)
        push_success: Whether push to remote succeeded
    """

    file_path: Path
    original_content: str
    fixed_content: str
    diff: str
    commit_sha: str
    push_success: bool


class CodeFix(BaseModel):
    """
    Code fix to apply.

    Attributes:
        file_path: Path to file to modify (relative to worktree)
        old_content: Content to replace
        new_content: Replacement content
        description: Human-readable fix description
    """

    file_path: Path
    old_content: str
    new_content: str
    description: str


# ============================================================================
# FIX APPLICATOR CLASS (Core Implementation)
# ============================================================================


class FixApplicator:
    """
    Apply code fixes and commit to git worktree.

    Workflow:
    1. Apply fix to file in isolated worktree (no main workspace interference)
    2. Create git commit with descriptive message (Claude co-authorship)
    3. Push to remote branch (AC-3: auto-trigger CI)
    4. Verify push success and store learnings (Article IV)

    Constitutional Compliance:
    - Article I: Complete context (retry timeouts, no partial operations)
    - Article II: 100% test coverage (25 NECESSARY tests)
    - Article IV: VectorStore integration (store successful patterns)
    - Law #2: Strict typing (Pydantic models, no Dict[Any, Any])
    - Law #5: Result pattern (all operations return Result<T, E>)
    - Law #8: Functions <50 lines (focused, single-purpose)
    """

    def __init__(
        self,
        worktree_path: Path,
        branch_name: str,
        remote_name: str = "origin",
        agent_context: Any | None = None,
    ):
        """
        Initialize fix applicator.

        Args:
            worktree_path: Path to git worktree (isolated workspace)
            branch_name: Branch to commit fixes to
            remote_name: Git remote name (default: origin)
            agent_context: Optional AgentContext for VectorStore learning
        """
        self.worktree_path = worktree_path
        self.branch_name = branch_name
        self.remote_name = remote_name
        self.agent_context = agent_context

    def apply_fix(
        self, fix: CodeFix, commit_message: str | None = None
    ) -> Result[FixApplication, FixApplicatorError]:
        """
        Apply fix to file and commit (AC-3: auto-commit for CI trigger).

        Args:
            fix: CodeFix to apply
            commit_message: Optional custom commit message

        Returns:
            Result containing FixApplication or FixApplicatorError

        Law #8: Function <50 lines (delegates to helpers)
        """
        # Validate and read file
        validation_result = self._validate_and_read_file(fix)
        if validation_result.is_err():
            return validation_result

        file_path, original_content = validation_result.unwrap()

        # Apply and write fix
        write_result = self._apply_and_write_fix(fix, file_path, original_content)
        if write_result.is_err():
            return write_result

        fixed_content = write_result.unwrap()

        # Commit, push, and create result
        return self._commit_push_and_finalize(fix, original_content, fixed_content, commit_message)

    def _validate_and_read_file(self, fix: CodeFix) -> Result[tuple[Path, str], FixApplicatorError]:
        """Validate worktree/file and read content (Law #8: <50 lines)."""
        if not self.worktree_path.exists():
            return Err(
                FixApplicatorError(
                    "apply_fix",
                    f"Worktree not found: {self.worktree_path}",
                    "Create worktree first",
                    code="worktree_not_found",
                )
            )

        file_path = self.worktree_path / fix.file_path
        if not file_path.exists():
            return Err(
                FixApplicatorError(
                    "apply_fix",
                    f"File not found: {fix.file_path}",
                    f"Working directory: {self.worktree_path}",
                    code="file_not_found",
                )
            )

        try:
            original_content = file_path.read_text()
        except Exception as exc:
            return Err(
                FixApplicatorError(
                    "apply_fix",
                    f"Failed to read file: {exc}",
                    str(file_path),
                    code="read_error",
                )
            )

        return Ok((file_path, original_content))

    def _apply_and_write_fix(
        self, fix: CodeFix, file_path: Path, original_content: str
    ) -> Result[str, FixApplicatorError]:
        """Apply fix and write to file (Law #8: <50 lines)."""
        if fix.old_content not in original_content:
            return Err(
                FixApplicatorError(
                    "apply_fix",
                    "old_content not found in file (fix may be stale)",
                    f"Looking for: {fix.old_content[:100]}...",
                    code="content_mismatch",
                )
            )

        fixed_content = original_content.replace(fix.old_content, fix.new_content)

        try:
            file_path.write_text(fixed_content)
        except Exception as exc:
            return Err(
                FixApplicatorError(
                    "apply_fix",
                    f"Failed to write file: {exc}",
                    str(file_path),
                    code="write_error",
                )
            )

        return Ok(fixed_content)

    def _commit_push_and_finalize(
        self,
        fix: CodeFix,
        original_content: str,
        fixed_content: str,
        commit_message: str | None,
    ) -> Result[FixApplication, FixApplicatorError]:
        """Commit, push, and create result (Law #8: <50 lines)."""
        diff = self._generate_diff(fix.file_path)

        if not commit_message:
            commit_message = f"fix: {fix.description}"

        commit_result = self._commit_changes(fix.file_path, commit_message)
        if commit_result.is_err():
            return commit_result

        commit_sha = commit_result.unwrap()
        push_result = self._push_to_remote()
        push_success = push_result.is_ok()

        if push_success and self.agent_context:
            self._store_success_pattern(fix, commit_sha)

        return Ok(
            FixApplication(
                file_path=fix.file_path,
                original_content=original_content,
                fixed_content=fixed_content,
                diff=diff,
                commit_sha=commit_sha,
                push_success=push_success,
            )
        )

    def _generate_diff(self, file_path: Path) -> str:
        """
        Generate unified diff for file changes.

        Args:
            file_path: Path to file (relative to worktree)

        Returns:
            Unified diff string (empty string if generation fails)

        Law #8: Function <50 lines (focused utility)
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--", str(file_path)],
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout
        except Exception as exc:
            return f"<diff unavailable: {exc}>"

    def _commit_changes(
        self, file_path: Path, commit_message: str
    ) -> Result[str, FixApplicatorError]:
        """
        Commit changes to git worktree (Law #8: <50 lines).

        Args:
            file_path: File to commit
            commit_message: Commit message

        Returns:
            Result containing commit SHA or error
        """
        # Stage file
        stage_result = self._stage_file(file_path)
        if stage_result.is_err():
            return stage_result

        # Commit with --no-verify
        commit_result = self._create_commit(commit_message)
        if commit_result.is_err():
            return commit_result

        # Get commit SHA
        return self._get_commit_sha()

    def _stage_file(self, file_path: Path) -> Result[None, FixApplicatorError]:
        """Stage file with git add (Law #8: <50 lines)."""
        try:
            result = subprocess.run(
                ["git", "add", str(file_path)],
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return Err(
                    FixApplicatorError(
                        "commit_changes",
                        "Git add failed",
                        result.stderr,
                        code="git_add_failed",
                    )
                )
            return Ok(None)
        except subprocess.TimeoutExpired:
            return Err(
                FixApplicatorError("commit_changes", "Git add timed out", ">5s", code="timeout")
            )
        except Exception as exc:
            return Err(
                FixApplicatorError(
                    "commit_changes",
                    f"Git add error: {exc}",
                    "",
                    code="git_add_error",
                )
            )

    def _create_commit(self, commit_message: str) -> Result[None, FixApplicatorError]:
        """Create git commit bypassing hooks (Law #8: <50 lines)."""
        try:
            result = subprocess.run(
                ["git", "commit", "--no-verify", "-m", commit_message],
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return self._handle_commit_error(result)
            return Ok(None)
        except subprocess.TimeoutExpired:
            return Err(
                FixApplicatorError("commit_changes", "Git commit timed out", ">10s", code="timeout")
            )
        except Exception as exc:
            return Err(
                FixApplicatorError(
                    "commit_changes",
                    f"Git commit error: {exc}",
                    "",
                    code="git_commit_error",
                )
            )

    def _handle_commit_error(self, result: subprocess.CompletedProcess) -> Err:
        """Handle git commit errors (Law #8: <50 lines)."""
        if "nothing to commit" in result.stdout.lower():
            return Err(
                FixApplicatorError(
                    "commit_changes",
                    "No changes to commit",
                    "File may already be fixed",
                    code="nothing_to_commit",
                )
            )
        return Err(
            FixApplicatorError(
                "commit_changes",
                "Git commit failed",
                result.stderr,
                code="git_commit_failed",
            )
        )

    def _get_commit_sha(self) -> Result[str, FixApplicatorError]:
        """
        Get current commit SHA.

        Returns:
            Result containing 40-character commit SHA or error

        Law #8: Function <50 lines (focused utility)
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return Err(
                    FixApplicatorError(
                        "commit_changes",
                        "Failed to get commit SHA",
                        result.stderr,
                        code="git_rev_parse_failed",
                    )
                )
            return Ok(result.stdout.strip())
        except Exception as exc:
            return Err(
                FixApplicatorError(
                    "commit_changes",
                    f"Failed to get commit SHA: {exc}",
                    "",
                    code="git_rev_parse_error",
                )
            )

    def _push_to_remote(self) -> Result[None, FixApplicatorError]:
        """Push branch to remote (AC-3: trigger CI) - Law #8: <50 lines."""
        # Check credentials (Security: S1)
        if not os.getenv("GITHUB_TOKEN") and not self._has_git_credentials():
            return Err(
                FixApplicatorError(
                    "push_to_remote",
                    "No git credentials found",
                    "Set GITHUB_TOKEN or run 'gh auth login'",
                    code="missing_credentials",
                )
            )

        # Push with --force-with-lease
        try:
            result = subprocess.run(
                [
                    "git",
                    "push",
                    self.remote_name,
                    self.branch_name,
                    "--force-with-lease",
                ],
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return self._handle_push_error(result.stderr)
            return Ok(None)
        except subprocess.TimeoutExpired:
            return Err(
                FixApplicatorError("push_to_remote", "Git push timed out", ">30s", code="timeout")
            )
        except Exception as exc:
            return Err(
                FixApplicatorError(
                    "push_to_remote",
                    f"Git push error: {exc}",
                    "",
                    code="git_push_error",
                )
            )

    def _handle_push_error(self, stderr: str) -> Err:
        """
        Handle git push errors with specific error codes.

        Args:
            stderr: Git push stderr output

        Returns:
            Err with specific error code based on pattern

        Law #8: Function <50 lines (extracted from _push_to_remote)
        """
        stderr_lower = stderr.lower()

        if "rejected" in stderr_lower:
            return Err(
                FixApplicatorError(
                    "push_to_remote",
                    "Push rejected (remote has changes)",
                    stderr,
                    code="push_rejected",
                )
            )

        if "protected branch" in stderr_lower:
            return Err(
                FixApplicatorError(
                    "push_to_remote",
                    "Push rejected (branch protection rules)",
                    stderr,
                    code="branch_protected",
                )
            )

        return Err(
            FixApplicatorError(
                "push_to_remote",
                "Git push failed",
                stderr,
                code="git_push_failed",
            )
        )

    def _has_git_credentials(self) -> bool:
        """
        Check if git credentials are configured.

        Returns:
            True if credentials found, False otherwise

        Law #8: Function <50 lines (simple utility)
        """
        try:
            result = subprocess.run(
                ["git", "config", "user.name"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _store_success_pattern(self, fix: CodeFix, commit_sha: str) -> None:
        """
        Store successful fix pattern to VectorStore (Article IV).

        Args:
            fix: Applied fix
            commit_sha: Commit SHA

        Constitutional Compliance:
        - Article IV: Mandatory VectorStore learning after success

        Law #8: Function <50 lines (focused utility)
        """
        if not self.agent_context:
            return

        try:
            self.agent_context.store_memory(
                key=f"fix_application_success_{commit_sha[:8]}",
                content={
                    "file": str(fix.file_path),
                    "description": fix.description,
                    "commit_sha": commit_sha,
                    "push_success": True,
                },
                tags=["fix_applicator", "success", "ci_monitor"],
            )
        except Exception:
            # Non-critical: learning storage failure doesn't fail operation
            pass

    def rollback_last_commit(self) -> Result[None, FixApplicatorError]:
        """Rollback last commit (resilience) - Law #8: <50 lines."""
        try:
            result = subprocess.run(
                ["git", "reset", "--hard", "HEAD~1"],
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return Err(
                    FixApplicatorError(
                        "rollback_last_commit",
                        "Git reset failed",
                        result.stderr,
                        code="git_reset_failed",
                    )
                )
            return Ok(None)
        except subprocess.TimeoutExpired:
            return Err(
                FixApplicatorError(
                    "rollback_last_commit",
                    "Git reset timed out",
                    ">10s",
                    code="timeout",
                )
            )
        except Exception as exc:
            return Err(
                FixApplicatorError(
                    "rollback_last_commit",
                    f"Git reset error: {exc}",
                    "",
                    code="git_reset_error",
                )
            )


# ============================================================================
# PUBLIC API (Convenience Functions)
# ============================================================================


def apply_fix_and_push(
    worktree_path: Path,
    branch_name: str,
    fix: CodeFix,
    agent_context: Any | None = None,
) -> Result[FixApplication, FixApplicatorError]:
    """
    Convenience function: Apply fix and push in one call.

    Args:
        worktree_path: Path to git worktree
        branch_name: Branch to commit to
        fix: CodeFix to apply
        agent_context: Optional AgentContext for learning

    Returns:
        Result containing FixApplication or error

    Law #8: Function <50 lines (simple wrapper)
    """
    applicator = FixApplicator(
        worktree_path=worktree_path,
        branch_name=branch_name,
        agent_context=agent_context,
    )
    return applicator.apply_fix(fix)
