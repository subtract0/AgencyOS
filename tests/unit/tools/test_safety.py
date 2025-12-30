"""Unit tests for safety infrastructure.

Tests the safety module that protects autonomous operations:
- Rate limiting
- Code validation
- Path validation
- Diff size validation
"""

import pytest
from pathlib import Path

import sys

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestCodeValidation:
    """Tests for code validation functions."""

    def test_validate_code_allows_safe_code(self):
        """Test that safe code passes validation."""
        from tools.safety import validate_code

        result = validate_code("def foo(): return 1")
        assert result.is_ok()

    def test_validate_code_blocks_eval(self):
        """Test that eval is blocked."""
        from tools.safety import validate_code

        result = validate_code("x = eval('1+1')")
        assert result.is_err()
        assert "Forbidden pattern" in result.unwrap_err()

    def test_validate_code_blocks_exec(self):
        """Test that exec is blocked."""
        from tools.safety import validate_code

        result = validate_code("exec('print(1)')")
        assert result.is_err()

    def test_validate_code_blocks_compile(self):
        """Test that compile is blocked."""
        from tools.safety import validate_code

        result = validate_code("compile('x=1', '', 'exec')")
        assert result.is_err()

    def test_validate_code_blocks_os_system(self):
        """Test that os.system is blocked."""
        from tools.safety import validate_code

        result = validate_code("import os; os.system('rm -rf /')")
        assert result.is_err()

    def test_validate_code_blocks_subprocess_shell(self):
        """Test that subprocess with shell=True is blocked."""
        from tools.safety import validate_code

        result = validate_code("subprocess.call('ls', shell=True)")
        assert result.is_err()

    def test_validate_code_allows_safe_subprocess(self):
        """Test that safe subprocess calls are allowed."""
        from tools.safety import validate_code

        result = validate_code("subprocess.run(['ls', '-la'])")
        assert result.is_ok()

    def test_validate_code_catches_syntax_errors(self):
        """Test that syntax errors are caught."""
        from tools.safety import validate_code

        result = validate_code("def foo( return 1")
        assert result.is_err()
        assert "Syntax error" in result.unwrap_err()

    def test_validate_code_blocks_import_hack(self):
        """Test that __import__ is blocked."""
        from tools.safety import validate_code

        result = validate_code("__import__('os').system('ls')")
        assert result.is_err()


class TestPathValidation:
    """Tests for path validation functions."""

    def test_validate_path_allows_tools(self):
        """Test that tools/ paths are allowed."""
        from tools.safety import validate_path

        result = validate_path("tools/safety.py")
        assert result.is_ok()

    def test_validate_path_allows_shared(self):
        """Test that shared/ paths are allowed."""
        from tools.safety import validate_path

        result = validate_path("shared/utils.py")
        assert result.is_ok()

    def test_validate_path_allows_agents(self):
        """Test that agent paths are allowed."""
        from tools.safety import validate_path

        result = validate_path("coding_agent/main.py")
        assert result.is_ok()

    def test_validate_path_blocks_tests(self):
        """Test that tests/ paths are blocked."""
        from tools.safety import validate_path

        result = validate_path("tests/unit/test_foo.py")
        assert result.is_err()
        assert "Forbidden" in result.unwrap_err()

    def test_validate_path_blocks_git(self):
        """Test that .git/ paths are blocked."""
        from tools.safety import validate_path

        result = validate_path(".git/config")
        assert result.is_err()

    def test_validate_path_blocks_venv(self):
        """Test that venv paths are blocked."""
        from tools.safety import validate_path

        result = validate_path("venv/lib/python3.11/site-packages/foo.py")
        assert result.is_err()

    def test_validate_path_blocks_env_files(self):
        """Test that .env files are blocked."""
        from tools.safety import validate_path

        result = validate_path(".env")
        assert result.is_err()

    def test_validate_path_blocks_unknown_paths(self):
        """Test that paths not in allowed list are blocked."""
        from tools.safety import validate_path

        result = validate_path("random/unknown/path.py")
        assert result.is_err()
        assert "not in allowed list" in result.unwrap_err()


class TestDiffSizeValidation:
    """Tests for diff size validation."""

    def test_validate_diff_size_allows_small_changes(self):
        """Test that small changes are allowed."""
        from tools.safety import validate_diff_size

        original = "line1\nline2\nline3"
        modified = "line1\nmodified\nline3"

        result = validate_diff_size(original, modified)
        assert result.is_ok()
        # Should return number of changed lines
        assert result.unwrap() > 0

    def test_validate_diff_size_blocks_large_changes(self):
        """Test that large changes are blocked."""
        from tools.safety import validate_diff_size, MAX_LINES_CHANGED

        original = "\n".join([f"line{i}" for i in range(10)])
        modified = "\n".join([f"new{i}" for i in range(MAX_LINES_CHANGED + 50)])

        result = validate_diff_size(original, modified)
        assert result.is_err()
        assert "Too many lines changed" in result.unwrap_err()


class TestRateLimiting:
    """Tests for rate limiting."""

    def test_rate_limit_allows_first_fix(self):
        """Test that first fix is allowed."""
        from tools.safety import get_safety_state, check_rate_limit

        state = get_safety_state()
        state.reset()  # Reset for clean test

        result = check_rate_limit()
        assert result.is_ok()

    def test_rate_limit_blocks_after_max(self):
        """Test that fixes are blocked after max reached."""
        from tools.safety import get_safety_state, check_rate_limit, MAX_FIXES_PER_HOUR

        state = get_safety_state()
        state.reset()

        # Use up all fixes
        for _ in range(MAX_FIXES_PER_HOUR):
            state.record_fix()

        result = check_rate_limit()
        assert result.is_err()
        assert "Rate limit" in result.unwrap_err()

    def test_rate_limit_resets_after_hour(self):
        """Test that rate limit resets after an hour."""
        from datetime import timedelta
        from tools.safety import get_safety_state, MAX_FIXES_PER_HOUR

        state = get_safety_state()
        state.reset()

        # Use up all fixes
        for _ in range(MAX_FIXES_PER_HOUR):
            state.record_fix()

        # Simulate hour passing
        state.hour_start = state.hour_start - timedelta(hours=2)

        can_fix, _ = state.can_fix()
        assert can_fix

    def test_record_fix_increments_counter(self):
        """Test that recording a fix increments the counter."""
        from tools.safety import get_safety_state

        state = get_safety_state()
        state.reset()

        initial = state.fixes_this_hour
        state.record_fix()
        assert state.fixes_this_hour == initial + 1


class TestSafetyStatus:
    """Tests for safety status reporting."""

    def test_get_safety_status_returns_dict(self):
        """Test that safety status is returned as dict."""
        from tools.safety import get_safety_status

        status = get_safety_status()
        assert isinstance(status, dict)
        assert "fixes_this_hour" in status
        assert "max_fixes_per_hour" in status
        assert "remaining_fixes" in status
        assert "allowed_paths" in status
        assert "forbidden_paths" in status

    def test_remaining_fixes_calculated_correctly(self):
        """Test that remaining fixes is calculated correctly."""
        from tools.safety import get_safety_state, get_safety_status, MAX_FIXES_PER_HOUR

        state = get_safety_state()
        state.reset()

        status = get_safety_status()
        assert status["remaining_fixes"] == MAX_FIXES_PER_HOUR

        state.record_fix()
        status = get_safety_status()
        assert status["remaining_fixes"] == MAX_FIXES_PER_HOUR - 1


class TestSafeExecute:
    """Tests for safe_execute wrapper."""

    def test_safe_execute_runs_function(self):
        """Test that safe_execute runs the wrapped function."""
        from tools.safety import safe_execute, get_safety_state

        state = get_safety_state()
        state.reset()

        def add(a, b):
            return a + b

        result = safe_execute(add, 1, 2)
        assert result == 3

    def test_safe_execute_records_fix(self):
        """Test that safe_execute records the fix."""
        from tools.safety import safe_execute, get_safety_state

        state = get_safety_state()
        state.reset()
        initial = state.fixes_this_hour

        def dummy():
            return True

        safe_execute(dummy)
        assert state.fixes_this_hour == initial + 1

    def test_safe_execute_raises_on_rate_limit(self):
        """Test that safe_execute raises when rate limited."""
        from tools.safety import safe_execute, get_safety_state, SafetyError, MAX_FIXES_PER_HOUR

        state = get_safety_state()
        state.reset()

        # Use up all fixes
        for _ in range(MAX_FIXES_PER_HOUR):
            state.record_fix()

        def dummy():
            return True

        with pytest.raises(SafetyError):
            safe_execute(dummy)


class TestWithSafetyChecks:
    """Tests for with_safety_checks decorator."""

    def test_decorator_validates_paths(self):
        """Test that decorator validates paths."""
        from tools.safety import with_safety_checks, SafetyError, get_safety_state

        state = get_safety_state()
        state.reset()

        @with_safety_checks(validate_paths=["tests/bad.py"], check_rate=False)
        def dummy():
            return True

        with pytest.raises(SafetyError):
            dummy()

    def test_decorator_allows_valid_paths(self):
        """Test that decorator allows valid paths."""
        from tools.safety import with_safety_checks, get_safety_state

        state = get_safety_state()
        state.reset()

        @with_safety_checks(validate_paths=["tools/good.py"], check_rate=False)
        def dummy():
            return True

        result = dummy()
        assert result is True

    def test_decorator_checks_rate_limit(self):
        """Test that decorator checks rate limit."""
        from tools.safety import with_safety_checks, SafetyError, get_safety_state, MAX_FIXES_PER_HOUR

        state = get_safety_state()
        state.reset()

        # Use up all fixes
        for _ in range(MAX_FIXES_PER_HOUR):
            state.record_fix()

        @with_safety_checks(check_rate=True)
        def dummy():
            return True

        with pytest.raises(SafetyError):
            dummy()
