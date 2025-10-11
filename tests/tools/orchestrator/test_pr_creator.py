"""
Tests for PRCreator: Git worktree isolation workflow for autonomous PR creation.

Test Coverage:
- Worktree creation with validation
- Commit message templating with Co-Authored-By
- PR body generation with constitutional compliance
- Mergeability verification via gh pr checks
- Cleanup automation after merge
- Error handling and rollback scenarios

Constitutional Compliance:
- Article I: Complete context validation
- Article II: 100% test coverage (TDD)
- Article IV: Pattern storage verification

Version: 1.0.0
Created: 2025-10-11
"""

import asyncio
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from tools.orchestrator.pr_creator import (
    CommitInfo,
    MergeabilityStatus,
    PRCreator,
    PRError,
    PRUrl,
    WorktreeInfo,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def pr_creator(tmp_path):
    """Create PRCreator instance with temp repo."""
    return PRCreator(repo_path=tmp_path)


@pytest.fixture
def mock_worktree():
    """Mock WorktreeInfo."""
    return WorktreeInfo(
        path=Path("/tmp/Agency-abc123-feat-test"),
        branch="feat/test-feature",
        session_id="abc123",
    )


@pytest.fixture
def mock_commit():
    """Mock CommitInfo."""
    return CommitInfo(
        sha="abc123def456",
        message="feat: Test feature\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
        files_changed=3,
    )


# ============================================================================
# BRANCH NAME VALIDATION
# ============================================================================


def test_valid_branch_names(pr_creator):
    """Test valid branch name patterns."""
    valid_names = [
        "feat/jwt-auth",
        "fix/bug-123",
        "refactor/clean-code",
        "docs/update-readme",
        "test/add-integration",
        "style/format-code",
        "chore/update-deps",
    ]

    for name in valid_names:
        assert pr_creator._is_valid_branch_name(name), f"Should accept: {name}"


def test_invalid_branch_names(pr_creator):
    """Test invalid branch name patterns."""
    invalid_names = [
        "feat/JWT-Auth",  # Uppercase
        "feature/test",  # Wrong type
        "feat",  # Missing description
        "feat/",  # Empty description
        "feat/test_feature",  # Underscore
        "/feat/test",  # Leading slash
        "feat/test/",  # Trailing slash
    ]

    for name in invalid_names:
        assert not pr_creator._is_valid_branch_name(name), f"Should reject: {name}"


# ============================================================================
# COMMIT MESSAGE GENERATION
# ============================================================================


def test_commit_message_generation(pr_creator):
    """Test commit message template with Co-Authored-By."""
    title = "Add JWT authentication"
    description = "Implement token validation for API endpoints"

    message = pr_creator._generate_commit_message(title, description)

    assert "feat: Leap 7 TDD Autonomy - Add JWT authentication" in message
    assert description in message
    assert "Co-Authored-By: Claude <noreply@anthropic.com>" in message
    assert message.count("\n\n") == 2  # Two blank line separators


def test_commit_message_multiline_description(pr_creator):
    """Test commit message with multiline description."""
    title = "Refactor auth module"
    description = (
        "Split auth logic into separate components:\n- Token validation\n- User session management"
    )

    message = pr_creator._generate_commit_message(title, description)

    assert "feat: Leap 7 TDD Autonomy - Refactor auth module" in message
    assert "Token validation" in message
    assert "User session management" in message
    assert "Co-Authored-By: Claude <noreply@anthropic.com>" in message


# ============================================================================
# PR BODY GENERATION
# ============================================================================


def test_pr_body_generation(pr_creator):
    """Test PR body template with all sections."""
    description = "Implement JWT authentication for API security"
    files = ["src/auth.py", "src/middleware.py", "tests/test_auth.py"]

    body = pr_creator._generate_pr_body(description, files)

    # Verify required sections
    assert "## Summary" in body
    assert "## Test Plan" in body
    assert "## Constitutional Compliance" in body

    # Verify content
    assert description in body
    assert "**Files Changed** (3 files):" in body
    assert "src/auth.py" in body
    assert "tests/test_auth.py" in body

    # Verify checkboxes
    assert "- [ ] Unit tests pass" in body
    assert "- [x] **Article I**" in body
    assert "- [x] **Article II**" in body
    assert "- [x] **Article III**" in body
    assert "- [x] **Article IV**" in body
    assert "- [x] **Article V**" in body

    # Verify footer
    assert "🤖 Generated with [Claude Code]" in body


def test_pr_body_many_files(pr_creator):
    """Test PR body truncates long file lists."""
    description = "Mass refactor"
    files = [f"file{i}.py" for i in range(15)]

    body = pr_creator._generate_pr_body(description, files)

    assert "**Files Changed** (15 files):" in body
    assert "file0.py" in body
    assert "file9.py" in body
    assert "... and 5 more files" in body


# ============================================================================
# PR NUMBER EXTRACTION
# ============================================================================


def test_extract_pr_number_success(pr_creator):
    """Test PR number extraction from GitHub URL."""
    urls = [
        "https://github.com/org/repo/pull/123",
        "https://github.com/user/project/pull/456",
        "http://github.com/test/test/pull/789",  # HTTP
    ]

    expected = [123, 456, 789]

    for url, expected_number in zip(urls, expected):
        pr_number = pr_creator._extract_pr_number(url)
        assert pr_number == expected_number


def test_extract_pr_number_invalid(pr_creator):
    """Test PR number extraction with invalid URLs."""
    invalid_urls = [
        "https://github.com/org/repo",  # No PR path
        "https://github.com/org/repo/issues/123",  # Issue, not PR
        "not a url",
        "",
    ]

    for url in invalid_urls:
        pr_number = pr_creator._extract_pr_number(url)
        assert pr_number is None


# ============================================================================
# WORKTREE CREATION
# ============================================================================


@pytest.mark.asyncio
async def test_create_worktree_success(pr_creator, tmp_path):
    """Test successful worktree creation."""
    branch_name = "feat/test-feature"

    # Mock subprocess call
    mock_result = subprocess.CompletedProcess(
        args=["git", "worktree", "add"],
        returncode=0,
        stdout="Preparing worktree",
        stderr="",
    )

    with patch.object(
        pr_creator,
        "_run_git",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        result = await pr_creator._create_worktree(branch_name)

    assert result.is_ok()
    worktree = result.unwrap()
    assert worktree.branch == branch_name
    assert "feat-test-feature" in str(worktree.path)
    assert len(worktree.session_id) == 8  # UUID4 prefix


@pytest.mark.asyncio
async def test_create_worktree_invalid_branch(pr_creator):
    """Test worktree creation with invalid branch name."""
    invalid_branch = "InvalidBranch"  # Uppercase not allowed

    result = await pr_creator._create_worktree(invalid_branch)

    assert result.is_err()
    error = result.unwrap_err()
    assert error.code == "invalid_branch_name"
    assert "InvalidBranch" in error.message


@pytest.mark.asyncio
async def test_create_worktree_git_failure(pr_creator):
    """Test worktree creation with git command failure."""
    branch_name = "feat/test-feature"

    # Mock git failure
    mock_result = subprocess.CompletedProcess(
        args=["git", "worktree", "add"],
        returncode=128,
        stdout="",
        stderr="fatal: 'feat/test-feature' is already checked out",
    )

    with patch.object(
        pr_creator,
        "_run_git",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        result = await pr_creator._create_worktree(branch_name)

    assert result.is_err()
    error = result.unwrap_err()
    assert error.code == "worktree_creation_failed"
    assert "already checked out" in error.details


# ============================================================================
# COMMIT CHANGES
# ============================================================================


@pytest.mark.asyncio
async def test_commit_changes_success(pr_creator, mock_worktree):
    """Test successful commit with Claude co-authorship."""
    files = ["src/auth.py", "tests/test_auth.py"]
    title = "Add JWT auth"
    description = "Implement token validation"

    # Mock git add success
    add_result = subprocess.CompletedProcess(
        args=["git", "add"],
        returncode=0,
        stdout="",
        stderr="",
    )

    # Mock git commit success
    commit_result = subprocess.CompletedProcess(
        args=["git", "commit"],
        returncode=0,
        stdout="[feat/test abc123] feat: Leap 7 TDD Autonomy - Add JWT auth",
        stderr="",
    )

    # Mock git rev-parse success
    sha_result = subprocess.CompletedProcess(
        args=["git", "rev-parse", "HEAD"],
        returncode=0,
        stdout="abc123def456\n",
        stderr="",
    )

    with patch.object(
        pr_creator,
        "_run_git",
        new_callable=AsyncMock,
        side_effect=[add_result, commit_result, sha_result],
    ):
        result = await pr_creator._commit_changes(mock_worktree, files, title, description)

    assert result.is_ok()
    commit = result.unwrap()
    assert commit.sha == "abc123def456"
    assert commit.files_changed == 2


@pytest.mark.asyncio
async def test_commit_changes_staging_failure(pr_creator, mock_worktree):
    """Test commit failure during staging."""
    files = ["nonexistent.py"]

    # Mock git add failure
    add_result = subprocess.CompletedProcess(
        args=["git", "add"],
        returncode=128,
        stdout="",
        stderr="fatal: pathspec 'nonexistent.py' did not match any files",
    )

    with patch.object(
        pr_creator,
        "_run_git",
        new_callable=AsyncMock,
        return_value=add_result,
    ):
        result = await pr_creator._commit_changes(mock_worktree, files, "Test", "Test")

    assert result.is_err()
    error = result.unwrap_err()
    assert error.code == "git_add_failed"


# ============================================================================
# PUSH BRANCH
# ============================================================================


@pytest.mark.asyncio
async def test_push_branch_success(pr_creator, mock_worktree):
    """Test successful branch push."""
    push_result = subprocess.CompletedProcess(
        args=["git", "push"],
        returncode=0,
        stdout="To github.com:org/repo.git\n * [new branch]      feat/test -> feat/test",
        stderr="",
    )

    with patch.object(
        pr_creator,
        "_run_git",
        new_callable=AsyncMock,
        return_value=push_result,
    ):
        result = await pr_creator._push_branch(mock_worktree)

    assert result.is_ok()


@pytest.mark.asyncio
async def test_push_branch_failure(pr_creator, mock_worktree):
    """Test branch push failure."""
    push_result = subprocess.CompletedProcess(
        args=["git", "push"],
        returncode=128,
        stdout="",
        stderr="fatal: remote 'origin' does not appear to be a git repository",
    )

    with patch.object(
        pr_creator,
        "_run_git",
        new_callable=AsyncMock,
        return_value=push_result,
    ):
        result = await pr_creator._push_branch(mock_worktree)

    assert result.is_err()
    error = result.unwrap_err()
    assert error.code == "git_push_failed"


# ============================================================================
# CREATE GITHUB PR
# ============================================================================


@pytest.mark.asyncio
async def test_create_github_pr_success(pr_creator, mock_worktree):
    """Test successful GitHub PR creation."""
    title = "Add JWT auth"
    body = "## Summary\nImplement JWT authentication"
    base = "main"

    # Mock gh pr create success
    gh_result = subprocess.CompletedProcess(
        args=["gh", "pr", "create"],
        returncode=0,
        stdout="https://github.com/org/repo/pull/123\n",
        stderr="",
    )

    with patch.object(
        pr_creator,
        "_run_command",
        new_callable=AsyncMock,
        return_value=gh_result,
    ):
        result = await pr_creator._create_github_pr(mock_worktree, title, body, base)

    assert result.is_ok()
    pr_url, pr_number = result.unwrap()
    assert pr_url == "https://github.com/org/repo/pull/123"
    assert pr_number == 123


@pytest.mark.asyncio
async def test_create_github_pr_gh_cli_not_found(pr_creator, mock_worktree):
    """Test PR creation when gh CLI is not installed."""
    with patch.object(
        pr_creator,
        "_run_command",
        new_callable=AsyncMock,
        side_effect=FileNotFoundError(),
    ):
        result = await pr_creator._create_github_pr(
            mock_worktree,
            "Test",
            "Body",
            "main",
        )

    assert result.is_err()
    error = result.unwrap_err()
    assert error.code == "gh_cli_not_found"
    assert "https://cli.github.com/" in error.details


@pytest.mark.asyncio
async def test_create_github_pr_failure(pr_creator, mock_worktree):
    """Test PR creation failure."""
    gh_result = subprocess.CompletedProcess(
        args=["gh", "pr", "create"],
        returncode=1,
        stdout="",
        stderr="error: could not create pull request: GraphQL: pull request create failed",
    )

    with patch.object(
        pr_creator,
        "_run_command",
        new_callable=AsyncMock,
        return_value=gh_result,
    ):
        result = await pr_creator._create_github_pr(
            mock_worktree,
            "Test",
            "Body",
            "main",
        )

    assert result.is_err()
    error = result.unwrap_err()
    assert error.code == "gh_pr_create_failed"


# ============================================================================
# VERIFY MERGEABILITY
# ============================================================================


@pytest.mark.asyncio
async def test_verify_mergeability_success(pr_creator):
    """Test mergeability verification with passing checks."""
    pr_number = 123

    # Mock gh pr checks success
    checks_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks"],
        returncode=0,
        stdout='[{"name": "CI", "state": "success"}]',
        stderr="",
    )

    with patch.object(
        pr_creator,
        "_run_command",
        new_callable=AsyncMock,
        return_value=checks_result,
    ):
        result = await pr_creator._verify_mergeability(pr_number)

    assert result.is_ok()
    status = result.unwrap()
    assert status.mergeable is True
    assert status.checks_passing is True


@pytest.mark.asyncio
async def test_verify_mergeability_failing_checks(pr_creator):
    """Test mergeability verification with failing checks."""
    pr_number = 123

    # Mock gh pr checks failure
    checks_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks"],
        returncode=0,
        stdout='[{"name": "CI", "state": "failure"}]',
        stderr="",
    )

    with patch.object(
        pr_creator,
        "_run_command",
        new_callable=AsyncMock,
        return_value=checks_result,
    ):
        result = await pr_creator._verify_mergeability(pr_number)

    assert result.is_ok()
    status = result.unwrap()
    assert status.mergeable is False
    assert status.checks_passing is False


@pytest.mark.asyncio
async def test_verify_mergeability_no_pr_number(pr_creator):
    """Test mergeability verification with None PR number."""
    result = await pr_creator._verify_mergeability(None)

    assert result.is_err()
    error = result.unwrap_err()
    assert error.code == "invalid_pr_number"


# ============================================================================
# CLEANUP
# ============================================================================


@pytest.mark.asyncio
async def test_cleanup_after_merge_success(pr_creator, tmp_path):
    """Test successful worktree cleanup."""
    worktree_path = tmp_path / "Agency-test-worktree"
    worktree_path.mkdir()

    # Mock git worktree remove success
    remove_result = subprocess.CompletedProcess(
        args=["git", "worktree", "remove"],
        returncode=0,
        stdout="",
        stderr="",
    )

    prune_result = subprocess.CompletedProcess(
        args=["git", "worktree", "prune"],
        returncode=0,
        stdout="",
        stderr="",
    )

    with patch.object(
        pr_creator,
        "_run_git",
        new_callable=AsyncMock,
        side_effect=[remove_result, prune_result],
    ):
        result = await pr_creator.cleanup_after_merge(str(worktree_path))

    assert result.is_ok()


@pytest.mark.asyncio
async def test_cleanup_after_merge_not_found(pr_creator):
    """Test cleanup when worktree doesn't exist."""
    result = await pr_creator.cleanup_after_merge("/nonexistent/path")

    assert result.is_err()
    error = result.unwrap_err()
    assert error.code == "worktree_not_found"


@pytest.mark.asyncio
async def test_cleanup_after_merge_removal_failure(pr_creator, tmp_path):
    """Test cleanup when removal fails."""
    worktree_path = tmp_path / "Agency-test-worktree"
    worktree_path.mkdir()

    # Mock git worktree remove failure
    remove_result = subprocess.CompletedProcess(
        args=["git", "worktree", "remove"],
        returncode=128,
        stdout="",
        stderr="fatal: worktree has modifications",
    )

    with patch.object(
        pr_creator,
        "_run_git",
        new_callable=AsyncMock,
        return_value=remove_result,
    ):
        result = await pr_creator.cleanup_after_merge(str(worktree_path))

    assert result.is_err()
    error = result.unwrap_err()
    assert error.code == "worktree_remove_failed"


# ============================================================================
# INTEGRATION TEST (MOCKED)
# ============================================================================


@pytest.mark.asyncio
async def test_create_pr_full_workflow(pr_creator):
    """Test complete PR creation workflow (mocked)."""
    branch_name = "feat/test-feature"
    files = ["src/auth.py", "tests/test_auth.py"]
    title = "Add JWT authentication"
    description = "Implement token validation"

    # Mock all subprocess calls
    worktree_result = subprocess.CompletedProcess(
        args=["git", "worktree", "add"],
        returncode=0,
        stdout="",
        stderr="",
    )

    add_result = subprocess.CompletedProcess(
        args=["git", "add"],
        returncode=0,
        stdout="",
        stderr="",
    )

    commit_result = subprocess.CompletedProcess(
        args=["git", "commit"],
        returncode=0,
        stdout="",
        stderr="",
    )

    sha_result = subprocess.CompletedProcess(
        args=["git", "rev-parse"],
        returncode=0,
        stdout="abc123\n",
        stderr="",
    )

    push_result = subprocess.CompletedProcess(
        args=["git", "push"],
        returncode=0,
        stdout="",
        stderr="",
    )

    gh_result = subprocess.CompletedProcess(
        args=["gh", "pr", "create"],
        returncode=0,
        stdout="https://github.com/org/repo/pull/123\n",
        stderr="",
    )

    checks_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks"],
        returncode=0,
        stdout='[{"state": "success"}]',
        stderr="",
    )

    cleanup_result = subprocess.CompletedProcess(
        args=["git", "worktree", "remove"],
        returncode=0,
        stdout="",
        stderr="",
    )

    with (
        patch.object(
            pr_creator,
            "_run_git",
            new_callable=AsyncMock,
            side_effect=[
                worktree_result,  # create worktree
                add_result,  # stage files
                commit_result,  # commit
                sha_result,  # get sha
                push_result,  # push
                cleanup_result,  # cleanup (if called)
            ],
        ),
        patch.object(
            pr_creator,
            "_run_command",
            new_callable=AsyncMock,
            side_effect=[
                gh_result,  # create PR
                checks_result,  # verify mergeability
            ],
        ),
    ):
        result = await pr_creator.create_pr(
            branch_name=branch_name,
            files=files,
            title=title,
            description=description,
        )

    assert result.is_ok()
    pr_url = result.unwrap()
    assert pr_url.url == "https://github.com/org/repo/pull/123"
    assert pr_url.pr_number == 123
    assert pr_url.branch == branch_name
    assert pr_url.commit_sha == "abc123"
