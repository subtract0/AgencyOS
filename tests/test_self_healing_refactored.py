"""
Comprehensive tests for refactored SelfHealingCore.

NECESSARY Pattern Coverage:
- Named: Test names clearly describe what is being tested
- Executable: Each test is isolated and can run independently
- Comprehensive: Covers all self-healing workflow steps
- Error handling: Validates error detection, fixing, and rollback
- State changes: Tests file modifications with proper cleanup
- Side effects: Uses mocks and temp files to prevent actual commits
- Assertions: Meaningful validation checks for healing workflow
- Repeatable: Deterministic results with proper isolation
- Yield: Fast execution with mocked subprocess calls
"""

import os
import tempfile
from unittest.mock import MagicMock, Mock, mock_open, patch

from core.self_healing import Finding, SelfHealingCore


class TestErrorDetection:
    """Test detect_errors() method (NECESSARY: Normal operation)."""

    def test_detect_errors_finds_nonetype_attribute_error(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        log_content = """
Traceback (most recent call last):
  File "test.py", line 10, in <module>
    result = obj.method()
AttributeError: 'NoneType' object has no attribute 'method'
"""

        # Act
        findings = core.detect_errors(log_content)

        # Assert
        assert len(findings) > 0
        assert findings[0].error_type == "NoneType"
        assert "method" in findings[0].snippet

    def test_detect_errors_finds_nonetype_type_error(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        log_content = """
Traceback (most recent call last):
  File "app.py", line 25, in process
    for item in result:
TypeError: 'NoneType' object is not iterable
"""

        # Act
        findings = core.detect_errors(log_content)

        # Assert
        assert len(findings) > 0
        assert findings[0].error_type == "NoneType"
        assert "iterable" in findings[0].snippet.lower()

    def test_detect_errors_from_file_path(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        log_content = "AttributeError: 'NoneType' object has no attribute 'test'"

        # Act
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, dir="/tmp") as f:
            f.write(log_content)
            temp_path = f.name

        try:
            findings = core.detect_errors(temp_path)

            # Assert
            assert len(findings) > 0
            assert findings[0].error_type == "NoneType"
        finally:
            os.unlink(temp_path)

    def test_detect_errors_blocks_path_traversal(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        malicious_path = "../../../etc/passwd"

        # Act
        findings = core.detect_errors(malicious_path)

        # Assert
        assert len(findings) == 0  # Should reject malicious path

    def test_detect_errors_blocks_outside_allowed_directories(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        home_path = os.path.expanduser("~/malicious.log")

        # Act
        findings = core.detect_errors(home_path)

        # Assert
        # Should treat as string content since path is rejected
        assert len(findings) == 0 or findings[0].file == "unknown"


class TestGenerateFix:
    """Test _generate_fix() method (NECESSARY: Comprehensive)."""

    def test_generate_fix_adds_null_check(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        content = """def process():
    result = obj.method()
    return result
"""
        error = Finding(file="test.py", line=2, error_type="NoneType", snippet="obj.method()")

        # Act
        fixed_content = core._generate_fix(content, error)

        # Assert
        assert fixed_content is not None
        assert "if obj is not None:" in fixed_content
        assert "else:" in fixed_content

    def test_generate_fix_preserves_indentation(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        content = """def process():
        result = data.value
        return result
"""
        error = Finding(file="test.py", line=2, error_type="NoneType", snippet="data.value")

        # Act
        fixed_content = core._generate_fix(content, error)

        # Assert
        assert fixed_content is not None
        # Should preserve 8-space indentation
        assert "        if data is not None:" in fixed_content

    def test_generate_fix_returns_none_for_invalid_line(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        content = "line 1\nline 2\nline 3\n"
        error = Finding(file="test.py", line=999, error_type="NoneType", snippet="invalid")

        # Act
        fixed_content = core._generate_fix(content, error)

        # Assert
        assert fixed_content is None


class TestApplyFixSafely:
    """Test _apply_fix_to_file() method (NECESSARY: State changes)."""

    def test_apply_fix_to_file_writes_content(self):
        # Arrange
        core = SelfHealingCore(dry_run=False)  # Allow writes for this test
        fixed_content = "fixed code"

        # Act
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir="/tmp") as f:
            temp_path = f.name

        try:
            result = core._apply_fix_to_file(temp_path, fixed_content)

            # Assert
            assert result is True
            with open(temp_path) as f:
                assert f.read() == fixed_content
        finally:
            os.unlink(temp_path)

    def test_apply_fix_handles_write_errors(self):
        # Arrange
        core = SelfHealingCore(dry_run=False)

        # Act
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            result = core._apply_fix_to_file("/tmp/test.py", "content")

        # Assert
        assert result is False


class TestVerifyFixWithTests:
    """Test verify() method (NECESSARY: Quality validation)."""

    def test_verify_runs_test_suite(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)

        # Act
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="✅ All tests passed!", stderr=""
            )
            result = core.verify()

        # Assert
        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "run_tests.py" in str(args)

    def test_verify_detects_test_failures(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)

        # Act
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="FAILED tests/test_example.py", stderr=""
            )
            result = core.verify()

        # Assert
        assert result is False

    def test_verify_handles_test_timeout(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)

        # Act
        with patch("subprocess.run") as mock_run:
            import subprocess

            mock_run.side_effect = subprocess.TimeoutExpired(cmd="run_tests.py", timeout=120)
            result = core.verify()

        # Assert
        assert result is False


class TestRollbackOnFailure:
    """Test _rollback_on_failure() method (NECESSARY: Error handling)."""

    def test_rollback_restores_original_content(self):
        # Arrange
        core = SelfHealingCore(dry_run=False)
        original_content = "original code"

        # Act
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir="/tmp") as f:
            temp_path = f.name
            f.write("bad fix")

        try:
            core._rollback_on_failure(temp_path, original_content)

            # Assert
            with open(temp_path) as f:
                assert f.read() == original_content
        finally:
            os.unlink(temp_path)

    def test_rollback_handles_write_errors(self):
        # Arrange
        core = SelfHealingCore(dry_run=False)

        # Act
        with patch("builtins.open", side_effect=OSError("Write failed")):
            # Should not raise, just log error
            core._rollback_on_failure("/tmp/test.py", "original")

        # Assert - If we get here, error was handled gracefully
        assert True


class TestCommitFix:
    """Test _commit_fix() method (NECESSARY: Integration)."""

    def test_commit_skipped_in_dry_run_mode(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        error = Finding(file="test.py", line=10, error_type="NoneType", snippet="test")

        # Act
        with patch("subprocess.run") as mock_run:
            core._commit_fix(error)

        # Assert
        mock_run.assert_not_called()

    def test_commit_requires_environment_variable(self):
        # Arrange
        core = SelfHealingCore(dry_run=False)
        error = Finding(file="test.py", line=10, error_type="NoneType", snippet="test")

        # Act
        with patch.dict("os.environ", {}, clear=True):
            with patch("subprocess.run") as mock_run:
                core._commit_fix(error)

        # Assert
        mock_run.assert_not_called()

    def test_commit_executes_git_workflow(self):
        # Arrange
        core = SelfHealingCore(dry_run=False)
        error = Finding(file="test.py", line=10, error_type="NoneType", snippet="test error")

        # Act
        with patch.dict("os.environ", {"SELF_HEALING_AUTO_COMMIT": "true"}):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")
                core._commit_fix(error)

        # Assert
        # Should call git add, git commit, and git rev-parse
        assert mock_run.call_count == 3


class TestFixErrorEndToEnd:
    """Test fix_error() end-to-end workflow (NECESSARY: Integration)."""

    def test_fix_error_full_workflow_in_dry_run(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        error = Finding(file="test.py", line=2, error_type="NoneType", snippet="obj.method()")

        # Act
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir="/tmp") as f:
            f.write("def test():\n    result = obj.method()\n    return result\n")
            temp_path = f.name

        try:
            error.file = temp_path
            result = core.fix_error(error)

            # Assert
            assert result is True  # Dry-run mode pretends success
        finally:
            os.unlink(temp_path)

    def test_fix_error_rollback_on_test_failure(self):
        # Arrange
        core = SelfHealingCore(dry_run=False)
        original_content = "def test():\n    result = obj.method()\n    return result\n"
        error = Finding(file="test.py", line=2, error_type="NoneType", snippet="obj.method()")

        # Act
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir="/tmp") as f:
            f.write(original_content)
            temp_path = f.name

        try:
            error.file = temp_path

            with patch.object(core, "verify", return_value=False):
                result = core.fix_error(error)

            # Assert
            assert result is False
            # File should be rolled back to original
            with open(temp_path) as f:
                assert f.read() == original_content
        finally:
            os.unlink(temp_path)

    def test_fix_error_skips_unknown_file(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        error = Finding(file="unknown", line=10, error_type="NoneType", snippet="test")

        # Act
        result = core.fix_error(error)

        # Assert
        assert result is False

    def test_fix_error_skips_nonexistent_file(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        error = Finding(
            file="/tmp/does_not_exist.py", line=10, error_type="NoneType", snippet="test"
        )

        # Act
        result = core.fix_error(error)

        # Assert
        assert result is False


class TestPatternLearning:
    """Test _learn_from_fix() method (NECESSARY: Learning integration)."""

    def test_learn_from_fix_stores_pattern(self):
        # Arrange
        mock_pattern_store = Mock()
        core = SelfHealingCore(dry_run=True)
        core.pattern_store = mock_pattern_store

        error = Finding(file="test.py", line=10, error_type="NoneType", snippet="obj.method()")
        original_content = "original"
        fixed_content = "fixed"

        # Act
        core._learn_from_fix(error, original_content, fixed_content)

        # Assert
        mock_pattern_store.store_pattern.assert_called_once()

    def test_learn_from_fix_skips_when_no_pattern_store(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        core.pattern_store = None

        error = Finding(file="test.py", line=10, error_type="NoneType", snippet="test")

        # Act
        # Should not raise
        core._learn_from_fix(error, "original", "fixed")

        # Assert
        assert True


class TestTelemetryIntegration:
    """Test _emit_event() telemetry integration (NECESSARY: Observability)."""

    def test_emit_event_uses_telemetry_when_available(self):
        # Arrange
        mock_telemetry = Mock()
        core = SelfHealingCore(dry_run=True)
        core.telemetry = mock_telemetry

        # Act
        core._emit_event("test_event", {"key": "value"})

        # Assert
        mock_telemetry.log.assert_called_once_with(
            "self_healing.test_event", {"key": "value"}, "info"
        )

    def test_emit_event_falls_back_to_file_when_no_telemetry(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        core.telemetry = None

        # Act
        with patch("builtins.open", mock_open()) as mock_file:
            core._emit_event("test_event", {"key": "value"})

        # Assert
        # Should have attempted to write to fallback log
        mock_file.assert_called()


class TestDryRunSafety:
    """Test dry-run mode safety features (NECESSARY: Security)."""

    def test_dry_run_prevents_file_writes(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        error = Finding(file="test.py", line=2, error_type="NoneType", snippet="test")

        # Act
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir="/tmp") as f:
            f.write("original content")
            temp_path = f.name

        try:
            error.file = temp_path
            original_content = open(temp_path).read()

            with patch.object(core, "verify", return_value=True):
                core.fix_error(error)

            # Assert
            # File should be unchanged in dry-run mode
            assert open(temp_path).read() == original_content
        finally:
            os.unlink(temp_path)

    def test_dry_run_prevents_git_commits(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        error = Finding(file="test.py", line=10, error_type="NoneType", snippet="test")

        # Act
        with patch("subprocess.run") as mock_run:
            core._commit_fix(error)

        # Assert
        mock_run.assert_not_called()

    def test_dry_run_is_default(self):
        # Arrange & Act
        core = SelfHealingCore()

        # Assert
        assert core.dry_run is True


class TestFeatureFlagIntegration:
    """Test feature flag integration (NECESSARY: Configuration)."""

    def test_enabled_flag_defaults_to_true(self):
        # Arrange & Act
        with patch.dict("os.environ", {}, clear=True):
            core = SelfHealingCore()

        # Assert
        assert core.enabled is True

    def test_enabled_flag_respects_environment(self):
        # Arrange & Act
        with patch.dict("os.environ", {"ENABLE_UNIFIED_CORE": "false"}):
            core = SelfHealingCore()

        # Assert
        assert core.enabled is False


class TestErrorPatternExtraction:
    """Test _extract_finding_from_match() helper (NECESSARY: Comprehensive)."""

    def test_extract_finding_parses_line_number(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        import re

        content = 'File "test.py", line 42, in function\n'
        pattern = r"AttributeError: 'NoneType' object has no attribute '(\w+)'"
        match = re.search(pattern, "AttributeError: 'NoneType' object has no attribute 'method'")

        # Act
        finding = core._extract_finding_from_match(match, content)

        # Assert
        assert finding.line == 42

    def test_extract_finding_parses_file_path(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        import re

        content = 'File "app/models.py", line 10, in process\n'
        pattern = r"TypeError: 'NoneType' object is not (\w+)"
        match = re.search(pattern, "TypeError: 'NoneType' object is not iterable")

        # Act
        finding = core._extract_finding_from_match(match, content)

        # Assert
        assert finding.file == "app/models.py"


class TestPerformanceRequirements:
    """Test that operations are fast (NECESSARY: Yield - performance)."""

    def test_detect_errors_completes_quickly(self):
        # Arrange
        import time

        core = SelfHealingCore(dry_run=True)
        log_content = "AttributeError: 'NoneType' object has no attribute 'test'"

        # Act
        start_time = time.time()
        core.detect_errors(log_content)
        elapsed_time = time.time() - start_time

        # Assert
        assert elapsed_time < 0.1, f"Detection took {elapsed_time}s, expected < 0.1s"

    def test_generate_fix_completes_quickly(self):
        # Arrange
        import time

        core = SelfHealingCore(dry_run=True)
        content = "def test():\n    obj.method()\n"
        error = Finding(file="test.py", line=2, error_type="NoneType", snippet="obj.method()")

        # Act
        start_time = time.time()
        core._generate_fix(content, error)
        elapsed_time = time.time() - start_time

        # Assert
        assert elapsed_time < 0.1, f"Fix generation took {elapsed_time}s, expected < 0.1s"


class TestRepeatability:
    """Test that operations are deterministic (NECESSARY: Repeatable)."""

    def test_detect_errors_gives_consistent_results(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        log_content = "AttributeError: 'NoneType' object has no attribute 'method'"

        # Act
        results = []
        for _ in range(5):
            findings = core.detect_errors(log_content)
            results.append(len(findings))

        # Assert
        assert len(set(results)) == 1, "Detection gave inconsistent results"

    def test_generate_fix_gives_consistent_results(self):
        # Arrange
        core = SelfHealingCore(dry_run=True)
        content = "def test():\n    result = obj.method()\n"
        error = Finding(file="test.py", line=2, error_type="NoneType", snippet="obj.method()")

        # Act
        results = []
        for _ in range(5):
            fixed = core._generate_fix(content, error)
            results.append(fixed)

        # Assert
        # All results should be identical
        assert all(r == results[0] for r in results), "Fix generation gave inconsistent results"
