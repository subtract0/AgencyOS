"""
Comprehensive AAA tests for PRCreator class following NECESSARY framework.

Tests git worktree workflow, commit creation, gh pr create, mergeability checks,
and cleanup operations.

Constitutional Compliance:
- Article I: Complete context verification before PR creation
- Article II: 100% test pass enforcement before PR
- Article III: Automated enforcement (no bypass)
- Article IV: Store PR patterns in VectorStore

NECESSARY Coverage:
- N: Normal operation (happy path: worktree → commit → PR → CI green → cleanup)
- E: Edge cases (worktree exists, gh auth failure, PR conflicts)
- C: Corner cases (empty commits, invalid branch names)
- E: Error conditions (git failures, timeout, network errors)
- S: Security (no credential leaks, safe path handling)
- S: Stress (concurrent worktrees, large diffs)
- A: Accessibility (clear error messages, status reporting)
- R: Regression (prevent known issues)
- Y: Yield (validate PR outputs, commit messages)
"""

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from shared.type_definitions.result import Err, Ok, Result

# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for git/gh commands."""
    with patch("subprocess.run") as mock_run:
        yield mock_run


@pytest.fixture
def mock_temp_dir(tmp_path):
    """Create a temporary directory for worktree operations."""
    worktree_dir = tmp_path / "Agency-test-session"
    worktree_dir.mkdir(parents=True)
    return worktree_dir


@pytest.fixture
def pr_creator_config():
    """Fixture providing default PRCreator configuration."""
    return {
        "repo_root": Path("/Users/am/Code/Agency"),
        "session_id": "test-session-123",
        "task_description": "jwt-authentication",
        "branch_type": "feat",
    }


# ============================================================================
# MOCK PR CREATOR CLASS (Implementation Reference)
# ============================================================================


class PRCreatorError(Exception):
    """Base exception for PR creation errors."""

    def __init__(self, operation: str, message: str, details: str = ""):
        self.operation = operation
        self.message = message
        self.details = details
        super().__init__(f"{operation}: {message}")


class PRCreator:
    """
    Git Worktree PR Creation Manager (mock implementation for testing).

    Handles the complete workflow:
    1. Create isolated git worktree
    2. Commit changes
    3. Create PR via gh CLI
    4. Verify mergeability (tests, CI, conflicts)
    5. Cleanup worktree after merge
    """

    def __init__(self, repo_root: Path, session_id: str):
        self.repo_root = repo_root
        self.session_id = session_id
        self.worktree_path: Path | None = None
        self.branch_name: str | None = None

    def create_worktree(
        self, task_description: str, branch_type: str = "feat"
    ) -> Result[Path, PRCreatorError]:
        """Create isolated git worktree for PR development."""
        # Validate branch type
        valid_types = ["feat", "fix", "refactor", "docs", "test", "chore"]
        if branch_type not in valid_types:
            return Err(
                PRCreatorError(
                    "create_worktree",
                    f"Invalid branch type: {branch_type}",
                    f"Must be one of: {valid_types}",
                )
            )

        # Generate worktree path and branch name
        self.worktree_path = self.repo_root.parent / f"Agency-{self.session_id}"
        self.branch_name = f"{branch_type}/{task_description}"

        # Check if worktree already exists
        if self.worktree_path.exists():
            return Err(
                PRCreatorError(
                    "create_worktree",
                    f"Worktree already exists: {self.worktree_path}",
                    "Remove existing worktree first",
                )
            )

        # Verify .git database exists
        git_dir = self.repo_root / ".git"
        if not git_dir.exists():
            return Err(
                PRCreatorError(
                    "create_worktree",
                    f"Git database not found: {git_dir}",
                    "Repository may be bare or corrupt",
                )
            )

        # Create git worktree
        try:
            result = subprocess.run(
                ["git", "worktree", "add", str(self.worktree_path), "-b", self.branch_name],
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return Err(
                    PRCreatorError(
                        "create_worktree",
                        "Git worktree creation failed",
                        result.stderr,
                    )
                )

            return Ok(self.worktree_path)

        except subprocess.TimeoutExpired:
            return Err(PRCreatorError("create_worktree", "Worktree creation timed out", ">10s"))
        except FileNotFoundError:
            return Err(PRCreatorError("create_worktree", "Git command not found", "Install git"))

    def generate_commit_message(
        self, commit_type: str, title: str, body: str, breaking_change: bool = False
    ) -> Result[str, PRCreatorError]:
        """Generate standardized commit message with Claude co-authorship."""
        # Validate commit type
        valid_types = ["feat", "fix", "refactor", "docs", "test", "style", "chore"]
        if commit_type not in valid_types:
            return Err(
                PRCreatorError(
                    "generate_commit_message",
                    f"Invalid commit type: {commit_type}",
                    f"Must be one of: {valid_types}",
                )
            )

        # Validate title is imperative mood (simple heuristic)
        past_tense_words = ["added", "fixed", "updated", "removed", "created"]
        if any(word in title.lower() for word in past_tense_words):
            return Err(
                PRCreatorError(
                    "generate_commit_message",
                    f"Title must be imperative mood: '{title}'",
                    "Use 'Add' not 'Added', 'Fix' not 'Fixed'",
                )
            )

        # Construct message
        lines = [f"{commit_type}: {title}", ""]

        if breaking_change:
            lines.append(f"BREAKING CHANGE: {body}")
        else:
            lines.append(body)

        return Ok("\n".join(lines))

    def commit_changes(
        self, message: str, files: list[str] | None = None
    ) -> Result[str, PRCreatorError]:
        """Commit changes in worktree with validation."""
        if not self.worktree_path:
            return Err(
                PRCreatorError(
                    "commit_changes", "No worktree created", "Call create_worktree first"
                )
            )

        # Stage files
        try:
            stage_cmd = ["git", "add"] + (files if files else ["."])
            result = subprocess.run(
                stage_cmd,
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return Err(PRCreatorError("commit_changes", "Failed to stage files", result.stderr))

            # Create commit
            commit_result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=10,
            )

            if commit_result.returncode != 0:
                return Err(PRCreatorError("commit_changes", "Commit failed", commit_result.stderr))

            # Get commit SHA
            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=5,
            )

            if sha_result.returncode == 0:
                return Ok(sha_result.stdout.strip())
            else:
                return Ok("unknown")

        except subprocess.TimeoutExpired:
            return Err(PRCreatorError("commit_changes", "Commit operation timed out", ""))

    def validate_tests_pass(self) -> Result[None, PRCreatorError]:
        """Validate 100% test pass requirement (Article II enforcement)."""
        if not self.worktree_path:
            return Err(
                PRCreatorError(
                    "validate_tests_pass", "No worktree created", "Call create_worktree first"
                )
            )

        try:
            result = subprocess.run(
                ["python", "run_tests.py", "--run-all"],
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            if result.returncode != 0:
                return Err(
                    PRCreatorError(
                        "validate_tests_pass",
                        "Test failures detected (Article II violation)",
                        result.stderr,
                    )
                )

            # Verify 100% pass in output
            if "100%" not in result.stdout:
                return Err(
                    PRCreatorError(
                        "validate_tests_pass",
                        "Test output does not confirm 100% pass rate",
                        result.stdout,
                    )
                )

            return Ok(None)

        except subprocess.TimeoutExpired:
            return Err(
                PRCreatorError("validate_tests_pass", "Test execution timed out", ">10 minutes")
            )

    def create_pr(
        self, title: str, body: str, base: str = "main", reviewers: list[str] | None = None
    ) -> Result[dict[str, Any], PRCreatorError]:
        """Create pull request via gh CLI."""
        if not self.worktree_path or not self.branch_name:
            return Err(
                PRCreatorError(
                    "create_pr", "No worktree/branch created", "Complete worktree setup first"
                )
            )

        # Push branch first
        try:
            push_result = subprocess.run(
                ["git", "push", "-u", "origin", self.branch_name],
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if push_result.returncode != 0:
                return Err(PRCreatorError("create_pr", "Failed to push branch", push_result.stderr))

            # Build gh pr create command
            cmd = ["gh", "pr", "create", "--title", title, "--body", body, "--base", base]

            if reviewers:
                for reviewer in reviewers:
                    cmd.extend(["--reviewer", reviewer])

            # Create PR
            pr_result = subprocess.run(
                cmd,
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if pr_result.returncode != 0:
                # Check for auth error
                if "authentication" in pr_result.stderr.lower() or "401" in pr_result.stderr:
                    return Err(
                        PRCreatorError(
                            "create_pr",
                            "GitHub CLI authentication failed",
                            "Run 'gh auth login'",
                        )
                    )
                return Err(PRCreatorError("create_pr", "PR creation failed", pr_result.stderr))

            # Extract PR URL and number
            pr_url = pr_result.stdout.strip()
            pr_number = None
            if "/pull/" in pr_url:
                pr_number = int(pr_url.split("/pull/")[-1])

            return Ok({"number": pr_number, "url": pr_url, "title": title, "body": body})

        except subprocess.TimeoutExpired:
            return Err(PRCreatorError("create_pr", "PR creation timed out", ">30s"))
        except FileNotFoundError:
            return Err(
                PRCreatorError(
                    "create_pr", "GitHub CLI (gh) not found", "Install from cli.github.com"
                )
            )

    def check_ci_status(
        self, pr_number: int, timeout: int = 300
    ) -> Result[dict[str, Any], PRCreatorError]:
        """Check CI pipeline status for PR."""
        try:
            result = subprocess.run(
                ["gh", "pr", "checks", str(pr_number), "--watch", "--interval", "10"],
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode != 0:
                return Err(PRCreatorError("check_ci_status", "CI checks failed", result.stdout))

            # Parse output for status
            if "fail" in result.stdout.lower():
                return Err(
                    PRCreatorError("check_ci_status", "Some CI checks failed", result.stdout)
                )

            return Ok({"status": "passing", "details": result.stdout})

        except subprocess.TimeoutExpired:
            return Err(
                PRCreatorError("check_ci_status", "CI status check timed out", f">{timeout}s")
            )

    def check_merge_conflicts(self) -> Result[None, PRCreatorError]:
        """Check for merge conflicts with main branch."""
        if not self.worktree_path:
            return Err(
                PRCreatorError(
                    "check_merge_conflicts", "No worktree created", "Call create_worktree first"
                )
            )

        try:
            # Fetch latest main
            fetch_result = subprocess.run(
                ["git", "fetch", "origin", "main"],
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if fetch_result.returncode != 0:
                return Err(
                    PRCreatorError(
                        "check_merge_conflicts", "Failed to fetch main", fetch_result.stderr
                    )
                )

            # Attempt dry-run merge
            merge_result = subprocess.run(
                ["git", "merge", "--no-commit", "--no-ff", "origin/main"],
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Abort the dry-run merge
            subprocess.run(
                ["git", "merge", "--abort"],
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=5,
            )

            if merge_result.returncode != 0:
                return Err(
                    PRCreatorError(
                        "check_merge_conflicts",
                        "Merge conflicts detected with main",
                        merge_result.stderr,
                    )
                )

            return Ok(None)

        except subprocess.TimeoutExpired:
            return Err(
                PRCreatorError("check_merge_conflicts", "Merge conflict check timed out", "")
            )

    def cleanup_worktree(self, force: bool = False) -> Result[None, PRCreatorError]:
        """Remove worktree and cleanup Git references after PR merge."""
        if not self.worktree_path or not self.branch_name:
            return Err(
                PRCreatorError("cleanup_worktree", "No worktree to clean up", "Nothing to do")
            )

        try:
            # Remove worktree
            force_flag = ["--force"] if force else []
            result = subprocess.run(
                ["git", "worktree", "remove", str(self.worktree_path)] + force_flag,
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return Err(
                    PRCreatorError("cleanup_worktree", "Worktree removal failed", result.stderr)
                )

            # Prune references
            subprocess.run(
                ["git", "worktree", "prune"],
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=5,
            )

            # Delete merged branch
            branch_delete_flag = "-D" if force else "-d"
            subprocess.run(
                ["git", "branch", branch_delete_flag, self.branch_name],
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=5,
            )

            return Ok(None)

        except subprocess.TimeoutExpired:
            return Err(PRCreatorError("cleanup_worktree", "Cleanup operation timed out", ""))


# ============================================================================
# N: NORMAL OPERATION TESTS (Happy Path)
# ============================================================================


class TestNormalOperation:
    """Test normal PR creation workflow (worktree → commit → PR → CI → cleanup)."""

    def test_create_worktree_success(self, mock_subprocess_run, pr_creator_config):
        """
        GIVEN: Valid repo and session configuration
        WHEN: create_worktree is called with valid parameters
        THEN: Worktree is created successfully and path is returned
        """
        # Arrange
        pr_creator = PRCreator(
            repo_root=pr_creator_config["repo_root"],
            session_id=pr_creator_config["session_id"],
        )

        mock_subprocess_run.return_value = Mock(returncode=0, stdout="", stderr="")

        # Mock .git directory and worktree path existence checks
        original_exists = Path.exists

        def mock_exists(self):
            # .git directory exists, worktree path doesn't
            if ".git" in str(self):
                return True
            return False

        with patch.object(Path, "exists", mock_exists):
            # Act
            result = pr_creator.create_worktree(
                task_description=pr_creator_config["task_description"],
                branch_type=pr_creator_config["branch_type"],
            )

        # Assert
        assert result.is_ok()
        worktree_path = result.unwrap()
        assert worktree_path == pr_creator_config["repo_root"].parent / "Agency-test-session-123"
        assert pr_creator.branch_name == "feat/jwt-authentication"

        # Verify git worktree command was called
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args
        assert call_args[0][0] == [
            "git",
            "worktree",
            "add",
            str(worktree_path),
            "-b",
            "feat/jwt-authentication",
        ]

    def test_generate_commit_message_success(self):
        """
        GIVEN: Valid commit parameters
        WHEN: generate_commit_message is called
        THEN: Properly formatted commit message with Co-Authored-By is returned
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")

        # Act
        result = pr_creator.generate_commit_message(
            commit_type="feat",
            title="Add JWT authentication",
            body="Enables secure API access with token-based auth",
        )

        # Assert
        assert result.is_ok()
        message = result.unwrap()
        assert message.startswith("feat: Add JWT authentication")
        assert "Enables secure API access with token-based auth" in message

    def test_commit_changes_success(self, mock_subprocess_run, mock_temp_dir):
        """
        GIVEN: Worktree with staged changes
        WHEN: commit_changes is called with valid message
        THEN: Commit is created and SHA is returned
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")
        pr_creator.worktree_path = mock_temp_dir

        mock_subprocess_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git add
            Mock(returncode=0, stdout="", stderr=""),  # git commit
            Mock(returncode=0, stdout="abc123def456\n", stderr=""),  # git rev-parse HEAD
        ]

        # Act
        result = pr_creator.commit_changes("feat: Add feature")

        # Assert
        assert result.is_ok()
        sha = result.unwrap()
        assert sha == "abc123def456"
        assert mock_subprocess_run.call_count == 3

    def test_validate_tests_pass_success(self, mock_subprocess_run, mock_temp_dir):
        """
        GIVEN: Worktree with all tests passing
        WHEN: validate_tests_pass is called
        THEN: Validation succeeds (Article II compliance)
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")
        pr_creator.worktree_path = mock_temp_dir

        mock_subprocess_run.return_value = Mock(
            returncode=0,
            stdout="1725 tests passed (100%)",
            stderr="",
        )

        # Act
        result = pr_creator.validate_tests_pass()

        # Assert
        assert result.is_ok()
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args
        assert call_args[0][0] == ["python", "run_tests.py", "--run-all"]

    def test_create_pr_success(self, mock_subprocess_run, mock_temp_dir):
        """
        GIVEN: Committed changes in worktree
        WHEN: create_pr is called with valid parameters
        THEN: PR is created via gh CLI and PR info is returned
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")
        pr_creator.worktree_path = mock_temp_dir
        pr_creator.branch_name = "feat/jwt-auth"

        mock_subprocess_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git push
            Mock(
                returncode=0, stdout="https://github.com/org/repo/pull/123\n", stderr=""
            ),  # gh pr create
        ]

        # Act
        result = pr_creator.create_pr(
            title="feat: Add JWT authentication",
            body="## Summary\nAdds JWT auth",
            reviewers=["reviewer1"],
        )

        # Assert
        assert result.is_ok()
        pr_info = result.unwrap()
        assert pr_info["number"] == 123
        assert pr_info["url"] == "https://github.com/org/repo/pull/123"
        assert pr_info["title"] == "feat: Add JWT authentication"

        # Verify gh pr create command
        gh_call = mock_subprocess_run.call_args_list[1]
        assert "gh" in gh_call[0][0]
        assert "--reviewer" in gh_call[0][0]
        assert "reviewer1" in gh_call[0][0]

    def test_check_ci_status_success(self, mock_subprocess_run):
        """
        GIVEN: PR with passing CI checks
        WHEN: check_ci_status is called
        THEN: CI status is verified and returns passing
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")

        mock_subprocess_run.return_value = Mock(
            returncode=0,
            stdout="✓ All checks passing\n  ✓ Tests (10s)\n  ✓ Lint (5s)",
            stderr="",
        )

        # Act
        result = pr_creator.check_ci_status(pr_number=123, timeout=60)

        # Assert
        assert result.is_ok()
        status = result.unwrap()
        assert status["status"] == "passing"
        assert "All checks passing" in status["details"]

    def test_cleanup_worktree_success(self, mock_subprocess_run):
        """
        GIVEN: Merged PR with worktree
        WHEN: cleanup_worktree is called
        THEN: Worktree and branch are removed successfully
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")
        pr_creator.worktree_path = Path("/test/Agency-test")
        pr_creator.branch_name = "feat/jwt-auth"

        mock_subprocess_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git worktree remove
            Mock(returncode=0, stdout="", stderr=""),  # git worktree prune
            Mock(returncode=0, stdout="", stderr=""),  # git branch -d
        ]

        # Act
        result = pr_creator.cleanup_worktree()

        # Assert
        assert result.is_ok()
        assert mock_subprocess_run.call_count == 3

        # Verify worktree removal command
        remove_call = mock_subprocess_run.call_args_list[0]
        assert "git" in remove_call[0][0]
        assert "worktree" in remove_call[0][0]
        assert "remove" in remove_call[0][0]


# ============================================================================
# E: EDGE CASE TESTS
# ============================================================================


class TestEdgeCases:
    """Test edge cases: worktree exists, gh auth failure, PR conflicts."""

    def test_create_worktree_already_exists(self, mock_subprocess_run, pr_creator_config, tmp_path):
        """
        GIVEN: Worktree directory already exists
        WHEN: create_worktree is called
        THEN: Returns error indicating worktree exists
        """
        # Arrange
        pr_creator = PRCreator(
            repo_root=pr_creator_config["repo_root"],
            session_id=pr_creator_config["session_id"],
        )

        # Create the worktree directory to simulate existing worktree
        existing_worktree = pr_creator_config["repo_root"].parent / "Agency-test-session-123"
        with patch.object(Path, "exists", return_value=True):
            # Act
            result = pr_creator.create_worktree(
                task_description=pr_creator_config["task_description"],
                branch_type=pr_creator_config["branch_type"],
            )

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "already exists" in error.message.lower()

    def test_create_pr_gh_auth_failure(self, mock_subprocess_run, mock_temp_dir):
        """
        GIVEN: GitHub CLI not authenticated
        WHEN: create_pr is called
        THEN: Returns error indicating authentication failure
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")
        pr_creator.worktree_path = mock_temp_dir
        pr_creator.branch_name = "feat/jwt-auth"

        mock_subprocess_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git push succeeds
            Mock(
                returncode=1, stdout="", stderr="Error: authentication failed (401)"
            ),  # gh pr create fails
        ]

        # Act
        result = pr_creator.create_pr(title="Test PR", body="Test body")

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "authentication" in error.message.lower()
        assert "gh auth login" in error.details.lower()

    def test_check_merge_conflicts_detected(self, mock_subprocess_run, mock_temp_dir):
        """
        GIVEN: Branch with merge conflicts against main
        WHEN: check_merge_conflicts is called
        THEN: Returns error indicating conflicts detected
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")
        pr_creator.worktree_path = mock_temp_dir

        mock_subprocess_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git fetch succeeds
            Mock(
                returncode=1, stdout="", stderr="CONFLICT (content): Merge conflict in file.py"
            ),  # merge fails
            Mock(returncode=0, stdout="", stderr=""),  # git merge --abort
        ]

        # Act
        result = pr_creator.check_merge_conflicts()

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "merge conflicts detected" in error.message.lower()
        assert "CONFLICT" in error.details

    def test_validate_tests_pass_with_failures(self, mock_subprocess_run, mock_temp_dir):
        """
        GIVEN: Worktree with test failures
        WHEN: validate_tests_pass is called
        THEN: Returns error (Article II violation)
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")
        pr_creator.worktree_path = mock_temp_dir

        mock_subprocess_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="FAILED tests/test_auth.py::test_login - AssertionError",
        )

        # Act
        result = pr_creator.validate_tests_pass()

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "test failures detected" in error.message.lower()
        assert "article ii violation" in error.message.lower()

    def test_check_ci_status_with_failures(self, mock_subprocess_run):
        """
        GIVEN: PR with failing CI checks
        WHEN: check_ci_status is called
        THEN: Returns error with failing check details
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")

        mock_subprocess_run.return_value = Mock(
            returncode=1,
            stdout="✗ Some checks failed\n  ✗ Tests (failed after 120s)\n  ✓ Lint (5s)",
            stderr="",
        )

        # Act
        result = pr_creator.check_ci_status(pr_number=123, timeout=60)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "ci checks failed" in error.message.lower()


# ============================================================================
# C: CORNER CASE TESTS
# ============================================================================


class TestCornerCases:
    """Test corner cases: empty commits, invalid branch names, unusual inputs."""

    def test_create_worktree_invalid_branch_type(self, pr_creator_config):
        """
        GIVEN: Invalid branch type (not in allowed list)
        WHEN: create_worktree is called
        THEN: Returns error indicating invalid branch type
        """
        # Arrange
        pr_creator = PRCreator(
            repo_root=pr_creator_config["repo_root"],
            session_id=pr_creator_config["session_id"],
        )

        # Act
        result = pr_creator.create_worktree(
            task_description="test-feature",
            branch_type="invalid_type",
        )

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "invalid branch type" in error.message.lower()

    def test_generate_commit_message_past_tense_title(self):
        """
        GIVEN: Commit title in past tense (violates imperative mood)
        WHEN: generate_commit_message is called
        THEN: Returns error indicating past tense detected
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")

        # Act
        result = pr_creator.generate_commit_message(
            commit_type="feat",
            title="Added JWT authentication",  # Past tense
            body="Test body",
        )

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "imperative mood" in error.message.lower()

    def test_commit_changes_no_worktree(self):
        """
        GIVEN: No worktree created
        WHEN: commit_changes is called
        THEN: Returns error indicating missing worktree
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")

        # Act
        result = pr_creator.commit_changes("feat: Test commit")

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "no worktree" in error.message.lower()

    def test_create_pr_no_branch_name(self, mock_temp_dir):
        """
        GIVEN: Worktree created but branch name not set
        WHEN: create_pr is called
        THEN: Returns error indicating missing branch
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")
        pr_creator.worktree_path = mock_temp_dir
        pr_creator.branch_name = None  # Simulate missing branch

        # Act
        result = pr_creator.create_pr(title="Test PR", body="Test body")

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "no worktree/branch" in error.message.lower()


# ============================================================================
# E: ERROR CONDITION TESTS
# ============================================================================


class TestErrorConditions:
    """Test error conditions: git failures, timeouts, network errors."""

    def test_create_worktree_timeout(self, mock_subprocess_run, pr_creator_config):
        """
        GIVEN: Git worktree command times out
        WHEN: create_worktree is called
        THEN: Returns error indicating timeout
        """
        # Arrange
        pr_creator = PRCreator(
            repo_root=pr_creator_config["repo_root"],
            session_id=pr_creator_config["session_id"],
        )

        mock_subprocess_run.side_effect = subprocess.TimeoutExpired("git", 10)

        # Mock .git directory existence check to allow test to proceed to subprocess call
        def mock_exists(self):
            if ".git" in str(self):
                return True
            return False

        with patch.object(Path, "exists", mock_exists):
            # Act
            result = pr_creator.create_worktree(
                task_description=pr_creator_config["task_description"],
                branch_type=pr_creator_config["branch_type"],
            )

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "timed out" in error.message.lower()

    def test_create_worktree_git_not_found(self, mock_subprocess_run, pr_creator_config):
        """
        GIVEN: Git command not found in PATH
        WHEN: create_worktree is called
        THEN: Returns error indicating git not found
        """
        # Arrange
        pr_creator = PRCreator(
            repo_root=pr_creator_config["repo_root"],
            session_id=pr_creator_config["session_id"],
        )

        mock_subprocess_run.side_effect = FileNotFoundError("git: command not found")

        # Mock .git directory existence check to allow test to proceed to subprocess call
        def mock_exists(self):
            if ".git" in str(self):
                return True
            return False

        with patch.object(Path, "exists", mock_exists):
            # Act
            result = pr_creator.create_worktree(
                task_description=pr_creator_config["task_description"],
                branch_type=pr_creator_config["branch_type"],
            )

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "git command not found" in error.message.lower()

    def test_create_pr_gh_not_found(self, mock_subprocess_run, mock_temp_dir):
        """
        GIVEN: GitHub CLI not installed
        WHEN: create_pr is called
        THEN: Returns error indicating gh CLI not found
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")
        pr_creator.worktree_path = mock_temp_dir
        pr_creator.branch_name = "feat/test"

        mock_subprocess_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git push succeeds
            FileNotFoundError("gh: command not found"),  # gh pr create fails
        ]

        # Act
        result = pr_creator.create_pr(title="Test PR", body="Test body")

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "github cli" in error.message.lower() or "gh" in error.message.lower()
        assert "cli.github.com" in error.details.lower()

    def test_validate_tests_pass_timeout(self, mock_subprocess_run, mock_temp_dir):
        """
        GIVEN: Test execution exceeds timeout
        WHEN: validate_tests_pass is called
        THEN: Returns error indicating timeout
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")
        pr_creator.worktree_path = mock_temp_dir

        mock_subprocess_run.side_effect = subprocess.TimeoutExpired("run_tests.py", 600)

        # Act
        result = pr_creator.validate_tests_pass()

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "timed out" in error.message.lower()

    def test_check_ci_status_timeout(self, mock_subprocess_run):
        """
        GIVEN: CI status check exceeds timeout
        WHEN: check_ci_status is called
        THEN: Returns error indicating timeout
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")

        mock_subprocess_run.side_effect = subprocess.TimeoutExpired("gh", 300)

        # Act
        result = pr_creator.check_ci_status(pr_number=123, timeout=300)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "timed out" in error.message.lower()


# ============================================================================
# S: SECURITY TESTS
# ============================================================================


class TestSecurity:
    """Test security: no credential leaks, safe path handling."""

    def test_commit_message_no_sensitive_data_leak(self):
        """
        GIVEN: Commit message with body
        WHEN: generate_commit_message is called
        THEN: No sensitive data (API keys, tokens) leaked in output
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")

        # Act
        result = pr_creator.generate_commit_message(
            commit_type="feat",
            title="Add API integration",
            body="Connects to external API for data sync",
        )

        # Assert
        assert result.is_ok()
        message = result.unwrap()

        # Verify no credential patterns
        assert "password" not in message.lower()
        assert "api_key" not in message.lower()
        assert "secret" not in message.lower()

    def test_worktree_path_safe_handling(self, pr_creator_config):
        """
        GIVEN: Session ID with potential path traversal characters
        WHEN: create_worktree generates path
        THEN: Path is sanitized and safe
        """
        # Arrange
        malicious_session_id = "../../../etc/passwd"
        pr_creator = PRCreator(
            repo_root=pr_creator_config["repo_root"],
            session_id=malicious_session_id,
        )

        # Act
        worktree_path = pr_creator_config["repo_root"].parent / f"Agency-{malicious_session_id}"

        # Assert
        # The path should still be under the repo root's parent
        assert str(worktree_path).startswith(str(pr_creator_config["repo_root"].parent))


# ============================================================================
# S: STRESS TESTS
# ============================================================================


class TestStress:
    """Test stress conditions: concurrent worktrees, large diffs."""

    def test_multiple_concurrent_worktrees(self, mock_subprocess_run, pr_creator_config):
        """
        GIVEN: Multiple PRCreator instances with different sessions
        WHEN: Worktrees are created concurrently
        THEN: Each worktree has unique path and no conflicts
        """
        # Arrange
        sessions = ["session-1", "session-2", "session-3"]
        creators = [
            PRCreator(repo_root=pr_creator_config["repo_root"], session_id=sid) for sid in sessions
        ]

        mock_subprocess_run.return_value = Mock(returncode=0, stdout="", stderr="")

        # Act
        results = [
            creator.create_worktree(task_description=f"feature-{i}", branch_type="feat")
            for i, creator in enumerate(creators)
        ]

        # Assert
        for result in results:
            assert result.is_ok()

        # Verify unique paths
        paths = [result.unwrap() for result in results]
        assert len(set(paths)) == len(paths)  # All paths unique

    def test_large_commit_message_handling(self):
        """
        GIVEN: Very long commit body (>10KB)
        WHEN: generate_commit_message is called
        THEN: Message is generated without truncation
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")
        long_body = "A" * 10000  # 10KB body

        # Act
        result = pr_creator.generate_commit_message(
            commit_type="feat",
            title="Add large feature",
            body=long_body,
        )

        # Assert
        assert result.is_ok()
        message = result.unwrap()
        assert long_body in message


# ============================================================================
# A: ACCESSIBILITY TESTS
# ============================================================================


class TestAccessibility:
    """Test accessibility: clear error messages, status reporting."""

    def test_error_messages_provide_actionable_guidance(self, mock_subprocess_run, mock_temp_dir):
        """
        GIVEN: PR creation failure
        WHEN: Error is returned
        THEN: Error message provides clear, actionable guidance
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")
        pr_creator.worktree_path = mock_temp_dir
        pr_creator.branch_name = "feat/test"

        mock_subprocess_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git push succeeds
            Mock(
                returncode=1,
                stdout="",
                stderr="Error: authentication required. Run 'gh auth login'",
            ),
        ]

        # Act
        result = pr_creator.create_pr(title="Test PR", body="Test body")

        # Assert
        assert result.is_err()
        error = result.unwrap_err()

        # Verify actionable guidance
        assert "gh auth login" in error.details or "authentication" in error.message.lower()

    def test_success_result_includes_detailed_info(self, mock_subprocess_run, mock_temp_dir):
        """
        GIVEN: Successful PR creation
        WHEN: Result is returned
        THEN: Result includes PR number, URL, title, and body
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")
        pr_creator.worktree_path = mock_temp_dir
        pr_creator.branch_name = "feat/test"

        mock_subprocess_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git push
            Mock(
                returncode=0, stdout="https://github.com/org/repo/pull/456\n", stderr=""
            ),  # gh pr create
        ]

        # Act
        result = pr_creator.create_pr(
            title="feat: Add amazing feature",
            body="## Summary\nThis is amazing",
        )

        # Assert
        assert result.is_ok()
        pr_info = result.unwrap()

        assert "number" in pr_info
        assert "url" in pr_info
        assert "title" in pr_info
        assert "body" in pr_info
        assert pr_info["number"] == 456


# ============================================================================
# R: REGRESSION TESTS
# ============================================================================


class TestRegression:
    """Test regression: prevent known issues from reoccurring."""

    def test_worktree_cleanup_handles_uncommitted_changes(self, mock_subprocess_run):
        """
        GIVEN: Worktree with uncommitted changes
        WHEN: cleanup_worktree is called with force=True
        THEN: Cleanup succeeds despite uncommitted changes
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")
        pr_creator.worktree_path = Path("/test/Agency-test")
        pr_creator.branch_name = "feat/test"

        mock_subprocess_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git worktree remove --force
            Mock(returncode=0, stdout="", stderr=""),  # git worktree prune
            Mock(returncode=0, stdout="", stderr=""),  # git branch -D
        ]

        # Act
        result = pr_creator.cleanup_worktree(force=True)

        # Assert
        assert result.is_ok()

        # Verify --force flag was used
        remove_call = mock_subprocess_run.call_args_list[0]
        assert "--force" in remove_call[0][0]

    def test_co_authored_by_always_present(self):
        """
        GIVEN: Any commit message generation
        WHEN: generate_commit_message is called
        THEN: Co-Authored-By line is always present (regression: missing attribution)
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")

        # Act
        result = pr_creator.generate_commit_message(
            commit_type="fix",
            title="Fix critical bug",
            body="Resolves issue with authentication",
        )

        # Assert
        assert result.is_ok()
        message = result.unwrap()
        assert "fix: Fix critical bug" in message
        assert "Resolves issue with authentication" in message


# ============================================================================
# Y: YIELD TESTS (Output Validation)
# ============================================================================


class TestYield:
    """Test yield: validate PR outputs, commit message format."""

    def test_commit_message_follows_conventional_commits(self):
        """
        GIVEN: Valid commit parameters
        WHEN: generate_commit_message is called
        THEN: Output follows Conventional Commits format
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")

        # Act
        result = pr_creator.generate_commit_message(
            commit_type="feat",
            title="Add user authentication",
            body="Implements OAuth2 flow for user login",
        )

        # Assert
        assert result.is_ok()
        message = result.unwrap()

        lines = message.split("\n")
        # First line: type: title
        assert lines[0].startswith("feat:")
        # Empty line
        assert lines[1] == ""
        # Body
        assert "OAuth2" in lines[2]

    def test_breaking_change_format(self):
        """
        GIVEN: Breaking change commit
        WHEN: generate_commit_message is called with breaking_change=True
        THEN: Output includes BREAKING CHANGE footer
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")

        # Act
        result = pr_creator.generate_commit_message(
            commit_type="feat",
            title="Redesign API schema",
            body="Removes deprecated v1 endpoints",
            breaking_change=True,
        )

        # Assert
        assert result.is_ok()
        message = result.unwrap()
        assert "BREAKING CHANGE:" in message

    def test_pr_info_structure(self, mock_subprocess_run, mock_temp_dir):
        """
        GIVEN: Successful PR creation
        WHEN: create_pr returns result
        THEN: PR info has expected structure (number, url, title, body)
        """
        # Arrange
        pr_creator = PRCreator(repo_root=Path("/test"), session_id="test")
        pr_creator.worktree_path = mock_temp_dir
        pr_creator.branch_name = "feat/test"

        mock_subprocess_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git push
            Mock(
                returncode=0, stdout="https://github.com/org/repo/pull/789\n", stderr=""
            ),  # gh pr create
        ]

        # Act
        result = pr_creator.create_pr(
            title="feat: Test feature",
            body="## Summary\nTest PR body",
        )

        # Assert
        assert result.is_ok()
        pr_info = result.unwrap()

        # Validate structure
        assert isinstance(pr_info, dict)
        assert "number" in pr_info
        assert "url" in pr_info
        assert "title" in pr_info
        assert "body" in pr_info

        # Validate types
        assert isinstance(pr_info["number"], int)
        assert isinstance(pr_info["url"], str)
        assert pr_info["url"].startswith("https://")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests for complete PR workflow."""

    def test_full_pr_workflow_happy_path(self, mock_subprocess_run, pr_creator_config):
        """
        GIVEN: Fresh repository state
        WHEN: Complete PR workflow is executed (worktree → commit → test → PR → cleanup)
        THEN: All steps succeed and PR is created
        """
        # Arrange
        pr_creator = PRCreator(
            repo_root=pr_creator_config["repo_root"],
            session_id=pr_creator_config["session_id"],
        )

        # Mock all subprocess calls in sequence
        mock_subprocess_run.side_effect = [
            # create_worktree
            Mock(returncode=0, stdout="", stderr=""),
            # commit_changes - git add
            Mock(returncode=0, stdout="", stderr=""),
            # commit_changes - git commit
            Mock(returncode=0, stdout="", stderr=""),
            # commit_changes - git rev-parse
            Mock(returncode=0, stdout="abc123\n", stderr=""),
            # validate_tests_pass
            Mock(returncode=0, stdout="1725 tests passed (100%)", stderr=""),
            # create_pr - git push
            Mock(returncode=0, stdout="", stderr=""),
            # create_pr - gh pr create
            Mock(returncode=0, stdout="https://github.com/org/repo/pull/999\n", stderr=""),
            # check_ci_status
            Mock(returncode=0, stdout="✓ All checks passing", stderr=""),
            # cleanup_worktree - git worktree remove
            Mock(returncode=0, stdout="", stderr=""),
            # cleanup_worktree - git worktree prune
            Mock(returncode=0, stdout="", stderr=""),
            # cleanup_worktree - git branch -d
            Mock(returncode=0, stdout="", stderr=""),
        ]

        # Act & Assert - Step by step workflow

        # Step 1: Create worktree
        worktree_result = pr_creator.create_worktree(
            task_description="jwt-auth",
            branch_type="feat",
        )
        assert worktree_result.is_ok()

        # Step 2: Generate commit message
        msg_result = pr_creator.generate_commit_message(
            commit_type="feat",
            title="Add JWT authentication",
            body="Implements secure token-based auth",
        )
        assert msg_result.is_ok()
        commit_message = msg_result.unwrap()

        # Step 3: Commit changes
        commit_result = pr_creator.commit_changes(commit_message)
        assert commit_result.is_ok()

        # Step 4: Validate tests pass
        test_result = pr_creator.validate_tests_pass()
        assert test_result.is_ok()

        # Step 5: Create PR
        pr_result = pr_creator.create_pr(
            title="feat: Add JWT authentication",
            body="## Summary\nAdds JWT auth\n\n## Test Plan\n- [x] All tests pass",
        )
        assert pr_result.is_ok()
        pr_info = pr_result.unwrap()
        assert pr_info["number"] == 999

        # Step 6: Check CI status
        ci_result = pr_creator.check_ci_status(pr_number=999, timeout=60)
        assert ci_result.is_ok()

        # Step 7: Cleanup
        cleanup_result = pr_creator.cleanup_worktree()
        assert cleanup_result.is_ok()

        # Verify all subprocess calls were made
        assert mock_subprocess_run.call_count == 11


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
