"""
Safety infrastructure for autonomous operations.

This module MUST be imported by all autonomous tools.
Violations will cause immediate abort.

Constitutional Compliance:
- Article I: Complete context via validation before action
- Article II: 100% verification via test requirements
- Article III: Automated enforcement via rate limits and blocklists
"""

import ast
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Callable, TypeVar

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.type_definitions.result import Err, Ok, Result


# Hard limits - NEVER CHANGE WITHOUT REVIEW
MAX_FIXES_PER_HOUR = 5
MAX_LINES_CHANGED = 100
MAX_FILES_CHANGED = 3
FORBIDDEN_PATTERNS = [
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__\s*\(",
    r"subprocess\.call.*shell\s*=\s*True",
    r"os\.system\s*\(",
    r"compile\s*\(",
    r"open\s*\([^)]*,\s*['\"]w",  # Writing to arbitrary files
]
ALLOWED_PATHS = [
    "tools/",
    "shared/",
    "coding_agent/",
    "planner_agent/",
    "auditor_agent/",
    "quality_enforcer_agent/",
    "chief_architect_agent/",
    "test_generator_agent/",
    "learning_agent/",
    "merger_agent/",
    "toolsmith_agent/",
    "work_completion_summary_agent/",
]
FORBIDDEN_PATHS = [
    "tests/",
    ".git/",
    "node_modules/",
    "venv/",
    ".venv/",
    "__pycache__/",
    ".env",
    "secrets",
]


T = TypeVar("T")


class SafetyError(Exception):
    """Raised when safety check fails."""

    pass


@dataclass
class SafetyState:
    """Global safety state - singleton."""

    fixes_this_hour: int = 0
    hour_start: datetime = field(default_factory=datetime.now)
    lock: Lock = field(default_factory=Lock)

    def can_fix(self) -> tuple[bool, str]:
        """Check if we can apply another fix.

        Returns:
            Tuple of (can_proceed, reason_if_not)
        """
        with self.lock:
            now = datetime.now()
            if now - self.hour_start > timedelta(hours=1):
                self.fixes_this_hour = 0
                self.hour_start = now

            if self.fixes_this_hour >= MAX_FIXES_PER_HOUR:
                return False, f"Rate limit: {MAX_FIXES_PER_HOUR} fixes/hour exceeded"
            return True, ""

    def record_fix(self) -> None:
        """Record that a fix was applied."""
        with self.lock:
            self.fixes_this_hour += 1

    def reset(self) -> None:
        """Reset rate limit counter (for testing)."""
        with self.lock:
            self.fixes_this_hour = 0
            self.hour_start = datetime.now()


# Global singleton
_SAFETY_STATE = SafetyState()


def get_safety_state() -> SafetyState:
    """Get the global safety state."""
    return _SAFETY_STATE


def validate_code(code: str) -> Result[str, str]:
    """Validate code is safe to execute/write.

    Args:
        code: Python source code to validate

    Returns:
        Result with validated code or error message
    """
    # 1. Check for forbidden patterns
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            return Err(f"Forbidden pattern detected: {pattern}")

    # 2. Validate syntax
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return Err(f"Syntax error: {e}")

    # 3. Check for dangerous AST nodes
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ["eval", "exec", "compile"]:
                    return Err(f"Dangerous function call: {node.func.id}")
            elif isinstance(node.func, ast.Attribute):
                # Check for os.system, subprocess.call with shell=True
                if node.func.attr in ["system", "popen"]:
                    return Err(f"Dangerous method call: {node.func.attr}")

    return Ok(code)


def validate_path(path: str) -> Result[str, str]:
    """Validate path is safe to modify.

    Args:
        path: File path to validate

    Returns:
        Result with validated path or error message
    """
    path_str = str(path)

    # Check forbidden paths
    for forbidden in FORBIDDEN_PATHS:
        if forbidden in path_str:
            return Err(f"Forbidden path: {forbidden}")

    # Check allowed paths
    allowed = any(allowed in path_str for allowed in ALLOWED_PATHS)
    if not allowed:
        return Err(f"Path not in allowed list: {path_str}")

    return Ok(path_str)


def validate_diff_size(original: str, modified: str) -> Result[int, str]:
    """Validate change size is within limits.

    Args:
        original: Original file content
        modified: Modified file content

    Returns:
        Result with number of changed lines or error
    """
    import difflib

    original_lines = original.split("\n")
    modified_lines = modified.split("\n")

    # Count changed lines (additions and deletions)
    # Skip header lines (---, +++, @@)
    diff = list(difflib.unified_diff(original_lines, modified_lines))
    changed_lines = sum(
        1 for line in diff
        if (line.startswith("+") or line.startswith("-"))
        and not line.startswith("---")
        and not line.startswith("+++")
    )

    if changed_lines > MAX_LINES_CHANGED:
        return Err(f"Too many lines changed: {changed_lines} > {MAX_LINES_CHANGED}")

    return Ok(changed_lines)


def check_rate_limit() -> Result[None, str]:
    """Check if rate limit allows another fix.

    Returns:
        Result indicating if fix is allowed
    """
    can_fix, reason = _SAFETY_STATE.can_fix()
    if not can_fix:
        return Err(reason)
    return Ok(None)


def record_fix() -> None:
    """Record that a fix was applied."""
    _SAFETY_STATE.record_fix()


def safe_execute(func: Callable[..., T], *args, **kwargs) -> T:
    """Execute function with safety checks.

    Args:
        func: Function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Function result

    Raises:
        SafetyError: If rate limit exceeded
    """
    can_fix, reason = _SAFETY_STATE.can_fix()
    if not can_fix:
        raise SafetyError(reason)

    result = func(*args, **kwargs)
    _SAFETY_STATE.record_fix()
    return result


def require_tests_pass(test_path: str = "tests/unit/") -> Callable:
    """Decorator requiring tests pass after function execution.

    Args:
        test_path: Path to tests to run

    Returns:
        Decorator function
    """
    import subprocess

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Run tests
            test_result = subprocess.run(
                ["python", "-m", "pytest", test_path, "-x", "--tb=no", "-q"],
                capture_output=True,
                timeout=300,
            )

            if test_result.returncode != 0:
                raise SafetyError(f"Tests failed after {func.__name__}")

            return result

        return wrapper

    return decorator


def with_safety_checks(
    validate_paths: list[str] | None = None,
    check_rate: bool = True,
) -> Callable:
    """Decorator that applies safety checks before function execution.

    Args:
        validate_paths: List of paths to validate
        check_rate: Whether to check rate limit

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Check rate limit
            if check_rate:
                can_fix, reason = _SAFETY_STATE.can_fix()
                if not can_fix:
                    raise SafetyError(reason)

            # Validate paths
            if validate_paths:
                for path in validate_paths:
                    result = validate_path(path)
                    if result.is_err():
                        raise SafetyError(result.unwrap_err())

            # Execute function
            result = func(*args, **kwargs)

            # Record fix if rate checking was enabled
            if check_rate:
                _SAFETY_STATE.record_fix()

            return result

        return wrapper

    return decorator


def get_safety_status() -> dict:
    """Get current safety status.

    Returns:
        Dictionary with safety metrics
    """
    state = _SAFETY_STATE
    with state.lock:
        return {
            "fixes_this_hour": state.fixes_this_hour,
            "max_fixes_per_hour": MAX_FIXES_PER_HOUR,
            "remaining_fixes": max(0, MAX_FIXES_PER_HOUR - state.fixes_this_hour),
            "hour_start": state.hour_start.isoformat(),
            "allowed_paths": ALLOWED_PATHS,
            "forbidden_paths": FORBIDDEN_PATHS,
        }


if __name__ == "__main__":
    # Demo safety checks
    print("=== Safety Module Demo ===\n")

    # Test code validation
    print("Testing code validation:")
    safe_code = "def foo(): return 1"
    unsafe_code = "eval('print(1)')"

    result = validate_code(safe_code)
    print(f"  Safe code: {'OK' if result.is_ok() else 'BLOCKED'}")

    result = validate_code(unsafe_code)
    print(f"  Unsafe code (eval): {'OK' if result.is_ok() else 'BLOCKED - ' + result.unwrap_err()}")

    # Test path validation
    print("\nTesting path validation:")
    result = validate_path("tools/safety.py")
    print(f"  tools/safety.py: {'OK' if result.is_ok() else 'BLOCKED'}")

    result = validate_path("tests/test_foo.py")
    print(f"  tests/test_foo.py: {'OK' if result.is_ok() else 'BLOCKED - ' + result.unwrap_err()}")

    # Test rate limiting
    print("\nTesting rate limiting:")
    status = get_safety_status()
    print(f"  Remaining fixes: {status['remaining_fixes']}/{status['max_fixes_per_hour']}")
