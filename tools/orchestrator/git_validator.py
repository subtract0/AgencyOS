"""
Git Validation for Phase 0 (Pre-Orchestrator Execution).

Validates git branch safety before orchestrator execution, enforcing Article III
(Automated Merge Enforcement) by preventing execution on protected branches.

Protected branches (execution prohibited):
- main
- master
- develop
- production
- staging

Valid branch patterns (execution allowed):
- feat/* (features)
- fix/* (bug fixes)
- docs/* (documentation)
- refactor/* (code refactoring)
- test/* (test suite work)

Performance Target: <50ms per validation (PERF-003)

Constitutional Compliance:
- Article I: Retry on timeout with exponential backoff (2x, 3x)
- Article III: No bypass mechanism exists (no --force flag)
- Error messages reference Article III and provide recovery hints

Usage:
    from tools.orchestrator.git_validator import validate_branch_safety

    # Validate current branch
    result = validate_branch_safety(repo_path=".")
    if result.is_err():
        raise result.unwrap_err()

    # Decorator pattern
    @require_feature_branch(repo_path=".")
    def orchestrate_workflow():
        ...  # Only runs if branch is safe

Example Error Messages:
    "Execution on 'main' is prohibited (Article III: Automated Merge Enforcement).
     Protected branches: main, master, develop, production, staging.
     Please checkout a feature branch: git checkout -b feat/your-feature-name"
"""

import functools
import re
import subprocess
from pathlib import Path
from typing import cast

from shared.models.orchestrator_models import (
    BranchInfo,
    GitValidationError,
    GitValidationResult,
)
from shared.type_definitions.result import Err, Ok, Result

# Protected branches (Article III: No execution allowed)
PROTECTED_BRANCHES = frozenset(["main", "master", "develop", "production", "staging"])

# Valid branch patterns (regex: ^(feat|fix|docs|refactor|test)/.+$)
VALID_BRANCH_PATTERN = re.compile(r"^(feat|fix|docs|refactor|test)/.+$")

# Performance target (PERF-003)
GIT_COMMAND_TIMEOUT = 5  # seconds


def get_current_branch(repo_path: Path | str = ".") -> Result[str, GitValidationError]:
    """
    Get current git branch name.

    Uses `git symbolic-ref --short HEAD` to extract branch name.
    Detects detached HEAD state (when symbolic-ref fails).

    Args:
        repo_path: Path to git repository (default: current directory)

    Returns:
        Ok(branch_name) on success
        Err(GitValidationError) if detached HEAD or not in git repo

    Performance:
        Target: <50ms (PERF-003)
        Implementation: Single git command, minimal overhead

    Article I Compliance:
        Retries on timeout with 2x timeout (max 3 attempts)

    Example:
        >>> result = get_current_branch(repo_path="/Users/am/Code/Agency")
        >>> assert result.is_ok()
        >>> print(result.unwrap())
        'feat/test-suite-audit'

        >>> # Detached HEAD
        >>> result = get_current_branch(repo_path="/tmp/detached")
        >>> assert result.is_err()
        >>> print(result.unwrap_err().message)
        'Detached HEAD state detected...'
    """
    repo_path_obj = Path(repo_path)

    # Article I: Retry logic with exponential backoff
    max_retries = 3
    timeout = GIT_COMMAND_TIMEOUT

    for attempt in range(max_retries):
        try:
            # Get branch name via git symbolic-ref
            proc = subprocess.run(
                ["git", "symbolic-ref", "--short", "HEAD"],
                cwd=repo_path_obj,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,  # Don't raise on non-zero exit
            )

            if proc.returncode == 0:
                branch_name = proc.stdout.strip()
                return Ok(branch_name)

            # Non-zero exit: likely detached HEAD or not a git repo
            stderr = proc.stderr.strip()

            # Detached HEAD: "fatal: ref HEAD is not a symbolic ref"
            if "not a symbolic ref" in stderr or "detached" in stderr.lower():
                return Err(
                    GitValidationError(
                        message="Detached HEAD state detected. You are not on a branch.",
                        branch_name=None,
                        recovery_hint=("Create a new branch: git checkout -b feat/<feature-name>"),
                    )
                )

            # Not a git repository (check for multiple language variants)
            stderr_lower = stderr.lower()
            if (
                "not a git repository" in stderr_lower
                or "kein git-repository" in stderr_lower  # German
                or "non è un repository git" in stderr_lower  # Italian
                or "pas un dépôt git" in stderr_lower  # French
            ):
                return Err(
                    GitValidationError(
                        message=f"Not a git repository: {repo_path_obj}",
                        branch_name=None,
                        recovery_hint="Initialize git: git init",
                    )
                )

            # Generic git error
            return Err(
                GitValidationError(
                    message=f"Git command failed: {stderr}",
                    branch_name=None,
                    recovery_hint="Check git repository integrity: git status",
                )
            )

        except subprocess.TimeoutExpired:
            # Article I: Retry with 2x timeout
            if attempt < max_retries - 1:
                timeout *= 2
                continue

            # Max retries exceeded
            return Err(
                GitValidationError(
                    message=f"Git command timeout after {max_retries} retries",
                    branch_name=None,
                    recovery_hint="Check git repository (may be locked or corrupted)",
                )
            )

        except FileNotFoundError:
            return Err(
                GitValidationError(
                    message="Git executable not found in PATH",
                    branch_name=None,
                    recovery_hint="Install git: brew install git (macOS) or apt install git (Linux)",
                )
            )

        except Exception as e:
            return Err(
                GitValidationError(
                    message=f"Unexpected error: {e}",
                    branch_name=None,
                    recovery_hint="Check git repository and filesystem permissions",
                )
            )

    # Fallback (should never reach here)
    return Err(
        GitValidationError(
            message="Failed to get current branch (unknown error)",
            branch_name=None,
            recovery_hint="Check git repository integrity",
        )
    )


def validate_branch_safety(
    repo_path: Path | str = ".",
    graceful_fallback: bool = False,
) -> Result[str, GitValidationError]:
    """
    Validate current branch is safe for execution (Article III enforcement).

    Checks:
    1. Branch is NOT in PROTECTED_BRANCHES (main, master, develop, production, staging)
    2. Branch matches VALID_BRANCH_PATTERN (feat/*, fix/*, docs/*, refactor/*, test/*)

    Args:
        repo_path: Path to git repository (default: current directory)
        graceful_fallback: If True, return Ok("non-repo") for non-repo contexts instead of error (default: False)

    Returns:
        Ok(branch_name) if branch is safe for execution
        Ok("non-repo") if graceful_fallback=True and not in git repository
        Err(GitValidationError) if branch is protected, invalid pattern, or detached HEAD

    Article III Compliance:
        No bypass mechanism exists for protected branches (no --force flag, no override parameter)
        Detached HEAD state always raises ValidationError (GIT-004) unless graceful_fallback=True
        Error messages reference Article III and provide recovery hints

    Performance:
        Target: <50ms (PERF-003)
        Implementation: Single get_current_branch() call + regex match

    Example:
        >>> # Safe branch
        >>> result = validate_branch_safety(repo_path=".")
        >>> assert result.is_ok()
        >>> print(result.unwrap())
        'feat/test'

        >>> # Detached HEAD (default: error)
        >>> result = validate_branch_safety(repo_path="/tmp/detached")
        >>> assert result.is_err()
        >>> print(result.unwrap_err().message)
        'Detached HEAD state detected...'

        >>> # Protected branch
        >>> result = validate_branch_safety(repo_path=".")
        >>> assert result.is_err()
        >>> print(result.unwrap_err().message)
        "Execution on 'main' is prohibited (Article III)..."
    """
    # Step 1: Get current branch
    branch_result = get_current_branch(repo_path)

    if branch_result.is_err():
        error = branch_result.unwrap_err()

        # Graceful fallback for non-repo contexts (ONLY if explicitly enabled)
        if graceful_fallback and (
            "not a git repository" in error.message.lower()
        ):
            # Return Ok with special "non-repo" marker
            return Ok("non-repo")

        # Propagate error from get_current_branch (detached HEAD, git errors)
        return Err(error)

    branch_name = branch_result.unwrap()

    # Step 2: Check if branch is protected (Article III)
    if branch_name in PROTECTED_BRANCHES:
        error_message = (
            f"Execution on '{branch_name}' is prohibited (Article III: Automated Merge Enforcement). "
            f"Protected branches: {', '.join(sorted(PROTECTED_BRANCHES))}. "
            f"Please checkout a feature branch: git checkout -b feat/your-feature-name"
        )

        return Err(
            GitValidationError(
                message=error_message,
                branch_name=branch_name,
                recovery_hint="Checkout a feature branch: git checkout -b feat/<feature-name>",
            )
        )

    # Step 3: Check if branch matches valid pattern
    pattern_match = VALID_BRANCH_PATTERN.match(branch_name)

    if pattern_match is None:
        # Branch doesn't match valid patterns
        error_message = (
            f"Branch '{branch_name}' does not match valid patterns. "
            f"Expected: (feat|fix|docs|refactor|test)/<description>. "
            f"Example: git checkout -b feat/my-feature"
        )

        return Err(
            GitValidationError(
                message=error_message,
                branch_name=branch_name,
                recovery_hint="Use valid pattern: git checkout -b (feat|fix|docs|refactor|test)/<description>",
            )
        )

    # Branch is safe for execution - return branch name
    return Ok(branch_name)


def require_feature_branch(repo_path: Path | str = "."):
    """
    Decorator to enforce feature branch validation before function execution.

    Validates git branch safety and raises GitValidationError if validation fails.
    NO bypass mechanism exists (Article III enforcement).

    Args:
        repo_path: Path to git repository (default: current directory)

    Raises:
        GitValidationError: If branch is unsafe (protected or invalid pattern)

    Article III Compliance:
        No --force, --bypass, or --skip parameters (constitutional mandate)
        Validation is absolute (no emergency override mechanism)

    Usage:
        @require_feature_branch(repo_path=".")
        def orchestrate_workflow(mission: str):
            # Only executes if branch is safe
            ...

        # Raises GitValidationError if on main/master/develop

    Performance:
        Adds <50ms overhead to decorated function (PERF-003)

    Example:
        >>> @require_feature_branch()
        ... def deploy():
        ...     print("Deploying...")
        >>> deploy()  # On feat/test branch
        Deploying...

        >>> deploy()  # On main branch
        GitValidationError: Execution on 'main' is prohibited (Article III)...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Validate branch safety
            result = validate_branch_safety(repo_path)

            if result.is_err():
                # Branch is unsafe (protected or invalid pattern)
                # Propagate GitValidationError
                raise result.unwrap_err()

            # Branch is safe - proceed with function execution
            return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = [
    "get_current_branch",
    "validate_branch_safety",
    "require_feature_branch",
    "PROTECTED_BRANCHES",
    "VALID_BRANCH_PATTERN",
]
