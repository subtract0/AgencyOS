"""
Git Workflow Tool for Agency OS.

Provides professional Git workflow operations:
- Branch management (create, switch, delete)
- Atomic commits with validation
- Push operations with upstream tracking
- Pull Request creation via GitHub CLI
- Complete workflow protocol enforcement

Constitutional Compliance:
- Article II: 100% verification (Green Main enforcement)
- Article III: Automated merge enforcement (PR required)
- Article V: Spec-driven development (commit message validation)

Usage:
    # Low-level operations
    tool = GitWorkflowTool(repo_path="/path/to/repo")
    result = tool.create_branch("feature/new-feature")
    result = tool.commit("feat: Add new feature")
    result = tool.push_branch("feature/new-feature")

    # High-level protocol
    protocol = GitWorkflowProtocol(repo_path="/path/to/repo")
    result = protocol.start_feature("new-feature")
    result = protocol.commit_changes("feat: Implementation", ["file.py"])
    result = protocol.create_pr("Title", "Body", reviewers=["user"])
"""

import os
import subprocess
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field
from shared.type_definitions.result import Result, Ok, Err


# ============================================================================
# DATA MODELS
# ============================================================================

class GitOperationError(Exception):
    """Git operation error with details."""

    def __init__(
        self,
        operation: str,
        message: str,
        return_code: int = 1,
        stderr: str = ""
    ):
        self.operation = operation
        self.message = message
        self.return_code = return_code
        self.stderr = stderr
        super().__init__(f"{operation} failed: {message}")


@dataclass
class BranchInfo:
    """Information about a Git branch."""
    name: str
    created: bool
    base_branch: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class CommitInfo:
    """Information about a Git commit."""
    sha: str
    message: str
    author: str
    timestamp: datetime
    files_changed: List[str]


@dataclass
class PullRequestInfo:
    """Information about a Pull Request."""
    number: Optional[int]
    url: str
    title: str
    body: str
    base: str
    head: str
    state: str = "open"


# ============================================================================
# GIT WORKFLOW TOOL
# ============================================================================

class GitWorkflowTool:
    """
    Low-level Git operations tool.

    Provides atomic git operations with Result<T,E> error handling.
    All operations are validated before execution.
    """

    def __init__(self, repo_path: str = ".", skip_validation: bool = False):
        """
        Initialize Git workflow tool.

        Args:
            repo_path: Path to git repository (default: current directory)
            skip_validation: Skip .git validation (for testing)
        """
        import warnings
        warnings.warn(
            "GitWorkflowTool is deprecated. Use GitUnified instead. "
            "Migration guide: FEATURE_INVENTORY_GIT_UNIFIED.md. "
            "This tool will be removed after 2025-11-02.",
            DeprecationWarning,
            stacklevel=2
        )
        self.repo_path = Path(repo_path).resolve()

        # Validate repository (unless in test mode)
        if not skip_validation and not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")

    # ========================================================================
    # BRANCH OPERATIONS
    # ========================================================================

    def create_branch(self, branch_name: str, base: str = "main") -> Result[BranchInfo, GitOperationError]:
        """
        Create a new branch from base.

        Args:
            branch_name: Name of new branch
            base: Base branch to create from (default: main)

        Returns:
            Result[BranchInfo, GitOperationError]
        """
        try:
            # Ensure we're on base branch first
            checkout_base = self._run_git_command(["checkout", base])
            if checkout_base.returncode != 0:
                return Err(GitOperationError(
                    operation="checkout_base",
                    message=f"Failed to checkout base branch {base}",
                    return_code=checkout_base.returncode,
                    stderr=checkout_base.stderr
                ))

            # Create and switch to new branch
            result = self._run_git_command(["checkout", "-b", branch_name])

            if result.returncode == 0:
                return Ok(BranchInfo(
                    name=branch_name,
                    created=True,
                    base_branch=base,
                    created_at=datetime.now(timezone.utc)
                ))
            else:
                return Err(GitOperationError(
                    operation="create_branch",
                    message=f"Failed to create branch {branch_name}",
                    return_code=result.returncode,
                    stderr=result.stderr
                ))

        except Exception as e:
            return Err(GitOperationError(
                operation="create_branch",
                message=str(e),
                return_code=-1
            ))

    def switch_branch(self, branch_name: str) -> Result[None, GitOperationError]:
        """
        Switch to existing branch.

        Args:
            branch_name: Branch to switch to

        Returns:
            Result[None, GitOperationError]
        """
        try:
            result = self._run_git_command(["checkout", branch_name])

            if result.returncode == 0:
                return Ok(None)
            else:
                return Err(GitOperationError(
                    operation="switch_branch",
                    message=f"Failed to switch to {branch_name}",
                    return_code=result.returncode,
                    stderr=result.stderr
                ))

        except Exception as e:
            return Err(GitOperationError(
                operation="switch_branch",
                message=str(e),
                return_code=-1
            ))

    def delete_branch(self, branch_name: str, force: bool = False) -> Result[None, GitOperationError]:
        """
        Delete a branch.

        Args:
            branch_name: Branch to delete
            force: Force deletion even if not merged

        Returns:
            Result[None, GitOperationError]
        """
        try:
            flag = "-D" if force else "-d"
            result = self._run_git_command(["branch", flag, branch_name])

            if result.returncode == 0:
                return Ok(None)
            else:
                return Err(GitOperationError(
                    operation="delete_branch",
                    message=f"Failed to delete {branch_name}",
                    return_code=result.returncode,
                    stderr=result.stderr
                ))

        except Exception as e:
            return Err(GitOperationError(
                operation="delete_branch",
                message=str(e),
                return_code=-1
            ))

    def get_current_branch(self) -> Result[str, GitOperationError]:
        """
        Get name of current branch.

        Returns:
            Result[str, GitOperationError]: Branch name
        """
        try:
            result = self._run_git_command(["branch", "--show-current"])

            if result.returncode == 0:
                return Ok(result.stdout.strip())
            else:
                return Err(GitOperationError(
                    operation="get_current_branch",
                    message="Failed to get current branch",
                    return_code=result.returncode,
                    stderr=result.stderr
                ))

        except Exception as e:
            return Err(GitOperationError(
                operation="get_current_branch",
                message=str(e),
                return_code=-1
            ))

    # ========================================================================
    # COMMIT OPERATIONS
    # ========================================================================

    def stage_files(self, files: List[str]) -> Result[None, GitOperationError]:
        """
        Stage specific files for commit.

        Args:
            files: List of file paths to stage

        Returns:
            Result[None, GitOperationError]
        """
        try:
            result = self._run_git_command(["add"] + files)

            if result.returncode == 0:
                return Ok(None)
            else:
                return Err(GitOperationError(
                    operation="stage_files",
                    message=f"Failed to stage files: {files}",
                    return_code=result.returncode,
                    stderr=result.stderr
                ))

        except Exception as e:
            return Err(GitOperationError(
                operation="stage_files",
                message=str(e),
                return_code=-1
            ))

    def stage_all(self) -> Result[None, GitOperationError]:
        """
        Stage all modified and new files.

        Returns:
            Result[None, GitOperationError]
        """
        try:
            result = self._run_git_command(["add", "."])

            if result.returncode == 0:
                return Ok(None)
            else:
                return Err(GitOperationError(
                    operation="stage_all",
                    message="Failed to stage all files",
                    return_code=result.returncode,
                    stderr=result.stderr
                ))

        except Exception as e:
            return Err(GitOperationError(
                operation="stage_all",
                message=str(e),
                return_code=-1
            ))

    def commit(self, message: str) -> Result[CommitInfo, GitOperationError]:
        """
        Create a commit with staged changes.

        Args:
            message: Commit message

        Returns:
            Result[CommitInfo, GitOperationError]
        """
        # Validate message
        if not message or not message.strip():
            return Err(GitOperationError(
                operation="commit",
                message="Commit message cannot be empty",
                return_code=-1
            ))

        try:
            # Create commit
            result = self._run_git_command(["commit", "-m", message])

            if result.returncode != 0:
                return Err(GitOperationError(
                    operation="commit",
                    message="Commit failed",
                    return_code=result.returncode,
                    stderr=result.stderr
                ))

            # Get commit info
            sha_result = self._run_git_command(["rev-parse", "HEAD"])
            if sha_result.returncode != 0:
                # Commit succeeded but couldn't get SHA
                return Ok(CommitInfo(
                    sha="unknown",
                    message=message,
                    author="unknown",
                    timestamp=datetime.now(timezone.utc),
                    files_changed=[]
                ))

            sha = sha_result.stdout.strip()

            return Ok(CommitInfo(
                sha=sha,
                message=message,
                author="current_user",
                timestamp=datetime.now(timezone.utc),
                files_changed=[]
            ))

        except Exception as e:
            return Err(GitOperationError(
                operation="commit",
                message=str(e),
                return_code=-1
            ))

    # ========================================================================
    # PUSH OPERATIONS
    # ========================================================================

    def push_branch(self, branch_name: str, set_upstream: bool = False) -> Result[None, GitOperationError]:
        """
        Push branch to remote.

        Args:
            branch_name: Branch to push
            set_upstream: Set upstream tracking

        Returns:
            Result[None, GitOperationError]
        """
        try:
            cmd = ["push"]
            if set_upstream:
                cmd.extend(["-u", "origin", branch_name])
            else:
                cmd.extend(["origin", branch_name])

            result = self._run_git_command(cmd)

            if result.returncode == 0:
                return Ok(None)
            else:
                return Err(GitOperationError(
                    operation="push_branch",
                    message=f"Failed to push {branch_name}",
                    return_code=result.returncode,
                    stderr=result.stderr
                ))

        except Exception as e:
            return Err(GitOperationError(
                operation="push_branch",
                message=str(e),
                return_code=-1
            ))

    # ========================================================================
    # PULL REQUEST OPERATIONS
    # ========================================================================

    def create_pull_request(
        self,
        title: str,
        body: str,
        base: str = "main",
        reviewers: Optional[List[str]] = None
    ) -> Result[PullRequestInfo, GitOperationError]:
        """
        Create a pull request using GitHub CLI.

        Args:
            title: PR title
            body: PR description
            base: Base branch (default: main)
            reviewers: List of reviewer usernames

        Returns:
            Result[PullRequestInfo, GitOperationError]
        """
        try:
            # Get current branch
            current_branch_result = self.get_current_branch()
            if not current_branch_result.is_ok():
                return Err(current_branch_result.unwrap_err())

            current_branch = current_branch_result.unwrap()

            # Build gh pr create command
            cmd = [
                "gh", "pr", "create",
                "--title", title,
                "--body", body,
                "--base", base
            ]

            if reviewers:
                for reviewer in reviewers:
                    cmd.extend(["--reviewer", reviewer])

            # Create PR
            result = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Extract PR URL from output
                url = result.stdout.strip()

                # Extract PR number if possible
                pr_number = None
                match = re.search(r'/pull/(\d+)', url)
                if match:
                    pr_number = int(match.group(1))

                return Ok(PullRequestInfo(
                    number=pr_number,
                    url=url,
                    title=title,
                    body=body,
                    base=base,
                    head=current_branch,
                    state="open"
                ))
            else:
                return Err(GitOperationError(
                    operation="create_pull_request",
                    message="Failed to create PR",
                    return_code=result.returncode,
                    stderr=result.stderr
                ))

        except subprocess.TimeoutExpired:
            return Err(GitOperationError(
                operation="create_pull_request",
                message="PR creation timed out",
                return_code=-1
            ))
        except FileNotFoundError:
            return Err(GitOperationError(
                operation="create_pull_request",
                message="GitHub CLI (gh) not found. Install from: https://cli.github.com/",
                return_code=127
            ))
        except Exception as e:
            return Err(GitOperationError(
                operation="create_pull_request",
                message=str(e),
                return_code=-1
            ))

    # ========================================================================
    # STATUS AND INFO
    # ========================================================================

    def get_status(self) -> Result[str, GitOperationError]:
        """
        Get git status output.

        Returns:
            Result[str, GitOperationError]: Status output
        """
        try:
            result = self._run_git_command(["status", "--short"])

            if result.returncode == 0:
                return Ok(result.stdout)
            else:
                return Err(GitOperationError(
                    operation="get_status",
                    message="Failed to get status",
                    return_code=result.returncode,
                    stderr=result.stderr
                ))

        except Exception as e:
            return Err(GitOperationError(
                operation="get_status",
                message=str(e),
                return_code=-1
            ))

    def has_uncommitted_changes(self) -> Result[bool, GitOperationError]:
        """
        Check if there are uncommitted changes.

        Returns:
            Result[bool, GitOperationError]: True if uncommitted changes exist
        """
        status_result = self.get_status()
        if not status_result.is_ok():
            return Err(status_result.unwrap_err())

        status = status_result.unwrap()
        return Ok(bool(status.strip()))

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def validate_commit_message(self, message: str) -> Result[Dict[str, Any], GitOperationError]:
        """
        Validate commit message follows conventions.

        Checks for:
        - Conventional commit format (feat:, fix:, etc.)
        - Minimum length
        - Spec references for features

        Args:
            message: Commit message to validate

        Returns:
            Result with validation info
        """
        warnings = []

        # Check conventional commit format
        conventional_pattern = r'^(feat|fix|docs|style|refactor|perf|test|chore|build|ci)(\(.+\))?: .+'
        if not re.match(conventional_pattern, message, re.MULTILINE):
            warnings.append("Message doesn't follow conventional commit format")

        # Check minimum length
        if len(message.strip()) < 10:
            warnings.append("Message too short (< 10 characters)")

        # Check for spec reference on features
        if message.startswith("feat:") and "spec" not in message.lower():
            warnings.append("Feature commit should reference specification")

        return Ok({
            "valid": len(warnings) == 0,
            "warnings": warnings
        })

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    def _run_git_command(self, args: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
        """
        Run a git command.

        Args:
            args: Git command arguments (without 'git' prefix)
            timeout: Command timeout in seconds

        Returns:
            CompletedProcess result
        """
        return subprocess.run(
            ["git"] + args,
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
            timeout=timeout
        )


# ============================================================================
# GIT WORKFLOW PROTOCOL
# ============================================================================

class GitWorkflowProtocol:
    """
    High-level Git workflow protocol.

    Enforces Agency's Git workflow:
    1. Create branch from main
    2. Make atomic commits
    3. Run tests before push (Green Main)
    4. Create PR with reviewers
    5. Clean up after merge

    Constitutional Compliance:
    - Article II: Enforces test passage before merge
    - Article III: Requires PR (no direct main commits)
    """

    def __init__(self, repo_path: str = ".", test_command: str = "pytest", skip_validation: bool = False):
        """
        Initialize Git workflow protocol.

        Args:
            repo_path: Path to repository
            test_command: Command to run tests (default: pytest)
            skip_validation: Skip .git validation (for testing)
        """
        self.tool = GitWorkflowTool(repo_path=repo_path, skip_validation=skip_validation)
        self.repo_path = Path(repo_path).resolve()
        self.test_command = test_command

    # ========================================================================
    # WORKFLOW STEPS
    # ========================================================================

    def start_feature(self, feature_name: str, base: str = "main") -> Result[Dict[str, Any], GitOperationError]:
        """
        Start a new feature workflow.

        Creates branch: feature/{feature_name}

        Args:
            feature_name: Feature name (without prefix)
            base: Base branch (default: main)

        Returns:
            Result with workflow info
        """
        branch_name = f"feature/{feature_name}"

        # Create branch
        result = self.tool.create_branch(branch_name, base=base)
        if not result.is_ok():
            return Err(result.unwrap_err())

        branch_info = result.unwrap()

        return Ok({
            "branch_name": branch_info.name,
            "base_branch": base,
            "started_at": branch_info.created_at.isoformat() if branch_info.created_at else None
        })

    def commit_changes(
        self,
        message: str,
        files: Optional[List[str]] = None,
        allow_untracked: bool = True
    ) -> Result[CommitInfo, GitOperationError]:
        """
        Commit changes with validation.

        Args:
            message: Commit message
            files: Specific files to commit (None = all)
            allow_untracked: Allow untracked files in repo

        Returns:
            Result[CommitInfo, GitOperationError]
        """
        # Validate message
        validation = self.tool.validate_commit_message(message)
        if validation.is_ok() and validation.unwrap()["warnings"]:
            # Log warnings but don't fail
            pass

        # Stage files
        if files:
            stage_result = self.tool.stage_files(files)
        else:
            stage_result = self.tool.stage_all()

        if not stage_result.is_ok():
            return Err(stage_result.unwrap_err())

        # Create commit
        return self.tool.commit(message)

    def push_current_branch(self, set_upstream: bool = True) -> Result[None, GitOperationError]:
        """
        Push current branch to remote.

        Args:
            set_upstream: Set upstream tracking

        Returns:
            Result[None, GitOperationError]
        """
        # Get current branch
        branch_result = self.tool.get_current_branch()
        if not branch_result.is_ok():
            return Err(branch_result.unwrap_err())

        branch = branch_result.unwrap()

        # Push
        return self.tool.push_branch(branch, set_upstream=set_upstream)

    def create_pr(
        self,
        title: str,
        body: str,
        base: str = "main",
        reviewers: Optional[List[str]] = None
    ) -> Result[PullRequestInfo, GitOperationError]:
        """
        Create pull request.

        Args:
            title: PR title
            body: PR description
            base: Base branch
            reviewers: Reviewer usernames

        Returns:
            Result[PullRequestInfo, GitOperationError]
        """
        # Push current branch first
        push_result = self.push_current_branch()
        if not push_result.is_ok():
            return Err(push_result.unwrap_err())

        # Create PR
        return self.tool.create_pull_request(
            title=title,
            body=body,
            base=base,
            reviewers=reviewers
        )

    def create_pr_with_validation(
        self,
        title: str,
        body: str,
        test_command: Optional[str] = None,
        base: str = "main",
        reviewers: Optional[List[str]] = None
    ) -> Result[PullRequestInfo, GitOperationError]:
        """
        Create PR with test validation (Article II: Green Main).

        Args:
            title: PR title
            body: PR description
            test_command: Test command (default: self.test_command)
            base: Base branch
            reviewers: Reviewer usernames

        Returns:
            Result[PullRequestInfo, GitOperationError]
        """
        # Run tests
        cmd = test_command or self.test_command
        result = subprocess.run(
            cmd.split(),
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            return Err(GitOperationError(
                operation="test_validation",
                message=f"Tests failed. Cannot create PR (Article II: Green Main).\n{result.stderr}",
                return_code=result.returncode,
                stderr=result.stderr
            ))

        # Tests passed, create PR
        return self.create_pr(title, body, base, reviewers)

    def cleanup_after_merge(self, feature_branch: str) -> Result[None, GitOperationError]:
        """
        Clean up after PR merge.

        1. Switch to main
        2. Pull latest
        3. Delete feature branch

        Args:
            feature_branch: Feature branch to delete

        Returns:
            Result[None, GitOperationError]
        """
        # Switch to main
        switch_result = self.tool.switch_branch("main")
        if not switch_result.is_ok():
            return Err(switch_result.unwrap_err())

        # Pull latest
        pull_result = self.tool._run_git_command(["pull"])
        if pull_result.returncode != 0:
            return Err(GitOperationError(
                operation="pull",
                message="Failed to pull latest from main",
                return_code=pull_result.returncode,
                stderr=pull_result.stderr
            ))

        # Delete feature branch
        return self.tool.delete_branch(feature_branch)

    # ========================================================================
    # VALIDATION HELPERS
    # ========================================================================

    def validate_commit_atomicity(self, files: List[str]) -> Result[Dict[str, Any], GitOperationError]:
        """
        Validate that commit is atomic (single logical change).

        Args:
            files: Files in commit

        Returns:
            Result with validation info
        """
        warning = None

        # Check if files span multiple directories (potential non-atomic)
        dirs = set()
        for file in files:
            parts = Path(file).parts
            if len(parts) > 1:
                dirs.add(parts[0])

        if len(dirs) > 2:
            warning = f"Commit spans {len(dirs)} directories. Consider splitting into atomic commits."

        return Ok({
            "atomic": len(dirs) <= 2,
            "warning": warning,
            "directories": list(dirs)
        })
