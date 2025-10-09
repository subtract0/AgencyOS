"""
Integration tests for UserPromptSubmit hook script.

Tests the hook as an external process with JSON stdin/stdout.
"""

import json
import subprocess
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent.parent / "hook_user_prompt_submit.py"


class TestUserPromptSubmitHook:
    """Integration tests for UserPromptSubmit hook."""

    def test_compliant_prompt_returns_exit_0(self):
        """Compliant prompts should return exit code 0."""
        input_data = {"prompt": "Implement feature X with full test coverage"}
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Ignore UV installation output in stderr
        assert "Constitutional Violation" not in result.stderr

    def test_skip_tests_prompt_returns_exit_2(self):
        """Prompts with 'skip tests' should return exit code 2."""
        input_data = {"prompt": "skip tests for now"}
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "Constitutional Violation" in result.stderr
        assert "Article I" in result.stderr

    def test_dict_any_any_prompt_blocked(self):
        """Dict[Any, Any] pattern should be blocked."""
        input_data = {"prompt": "Use Dict[Any, Any] for config"}
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "Article I" in result.stderr

    def test_no_verify_pattern_blocked(self):
        """--no-verify pattern should be blocked."""
        input_data = {"prompt": "git commit --no-verify"}
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2

    def test_force_push_pattern_blocked(self):
        """Force push pattern should be blocked."""
        input_data = {"prompt": "force push to main"}
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2

    def test_invalid_json_returns_exit_1(self):
        """Invalid JSON should return exit code 1 (script error)."""
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input="not valid json",
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Invalid JSON" in result.stderr

    def test_missing_prompt_field_returns_exit_1(self):
        """Missing 'prompt' field should return exit code 1."""
        input_data = {"wrong_field": "value"}
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1

    def test_empty_prompt_passes(self):
        """Empty prompt should pass (no violations)."""
        input_data = {"prompt": ""}
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

    def test_case_insensitive_matching(self):
        """Pattern matching should be case-insensitive."""
        input_data = {"prompt": "SKIP TESTS for this"}
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
