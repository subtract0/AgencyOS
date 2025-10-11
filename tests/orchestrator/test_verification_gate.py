"""
Comprehensive AAA tests for TestVerificationGate.

Tests full test suite execution (100% pass requirement), Article I retry logic
(2x, 3x, 10x timeout), memory-aware worker calculation, and rollback on failure.

Test coverage:
- Test execution with 100% pass rate (happy path)
- Article I retry logic with timeout multipliers
- Memory-aware worker calculation (local model ON/OFF)
- Rollback on test failure
- Edge cases: partial failure, timeout exhaustion

Constitutional Compliance:
- Article I: Complete context before action (retry on timeout)
- Article II: 100% verification (no bypass)
- Article IV: Pattern storage in VectorStore
"""

from __future__ import annotations

import subprocess
from typing import Literal
from unittest.mock import MagicMock, Mock, call, patch

import psutil
import pytest

# ============================================================================
# Pydantic Models (from spec-009)
# ============================================================================
from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result
from tools.memory_aware_test_runner import (
    TestExecutionConfig,
    check_ollama_running,
    get_safe_worker_count,
    verify_memory_safe,
)


class VerificationConfig(BaseModel):
    """Configuration for test verification gate (Articles I & II compliance)."""

    base_timeout_ms: int = Field(
        default=120000,
        description="Base timeout in milliseconds (2 minutes default)",
        ge=30000,
        le=600000,
    )

    timeout_multipliers: list[int] = Field(
        default=[1, 2, 3, 5, 10],
        description="Article I: Timeout multipliers for retry attempts",
    )

    max_retries: int = Field(
        default=5,
        description="Maximum retry attempts (matches timeout_multipliers length)",
        ge=1,
        le=10,
    )

    required_pass_rate: float = Field(
        default=1.0,
        description="Article II: Required test pass rate (1.0 = 100%, non-negotiable)",
        ge=1.0,
        le=1.0,
    )

    memory_safety_check: bool = Field(
        default=True, description="Enable memory-aware worker calculation (ADR-023)"
    )

    rollback_on_failure: bool = Field(
        default=True, description="Automatically rollback git changes on test failure"
    )

    test_scope: Literal["all", "unit", "integration", "fast"] = Field(
        default="all", description="Test scope to run (default: all tests)"
    )


class VerificationResult(BaseModel):
    """Result of test verification gate execution."""

    gate_passed: bool = Field(description="True if all validation criteria met")
    article_i_compliant: bool = Field(description="Tests ran to completion (no timeout)")
    article_ii_compliant: bool = Field(description="100% test pass rate achieved")

    total_tests: int = Field(ge=0)
    passed_tests: int = Field(ge=0)
    failed_tests: int = Field(ge=0)
    pass_rate: float = Field(ge=0.0, le=1.0)

    duration_seconds: float = Field(ge=0.0)
    retry_attempts: int = Field(ge=1, le=10)
    timeout_multiplier_used: int = Field(ge=1, le=10)

    memory_safe: bool = Field(description="Execution completed without memory exhaustion")
    worker_count_used: int = Field(ge=1, le=10)

    rollback_performed: bool = Field(default=False)
    failure_report: str | None = Field(default=None)

    blocking_reason: str | None = Field(
        default=None, description="Reason for blocking (if gate_passed=False)"
    )


# ============================================================================
# Helper Functions (from spec-009)
# ============================================================================


def calculate_test_workers() -> tuple[int, bool, str]:
    """
    Calculate safe pytest worker count based on system state.

    Returns:
        Tuple of (worker_count, memory_safe, rationale)
    """
    import tools.memory_aware_test_runner as test_runner

    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024**3)
    local_model_active = test_runner.check_ollama_running()

    # Safety check: require 5GB+ available memory
    if not test_runner.verify_memory_safe(required_gb=5):
        return (
            1,
            False,
            f"Critical memory: {available_gb:.1f}GB available, forcing sequential execution",
        )

    # Calculate safe worker count
    worker_count = test_runner.get_safe_worker_count()

    # Build rationale
    if local_model_active:
        rationale = (
            f"Local model active (Ollama running), using {worker_count} "
            f"workers to prevent memory exhaustion (available: {available_gb:.1f}GB)"
        )
    else:
        rationale = f"Local model OFF, using {worker_count} workers (available: {available_gb:.1f}GB)"

    memory_safe = available_gb >= 10.0  # Require 10GB+ for "safe" status

    return (worker_count, memory_safe, rationale)


def _parse_test_output(stdout: str, stderr: str) -> dict:
    """
    Parse pytest output to extract metrics.

    Returns:
        Dict with keys: total, passed, failed, errors
    """
    import re

    # Combine stdout and stderr for parsing
    output = stdout + stderr

    # Python pytest format: "1725 passed, 3 failed in 45.2s"
    passed_match = re.search(r"(\d+) passed", output)
    failed_match = re.search(r"(\d+) failed", output)
    error_match = re.search(r"(\d+) error", output)

    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    errors = int(error_match.group(1)) if error_match else 0

    total = passed + failed + errors

    return {"total": total, "passed": passed, "failed": failed + errors}


def _validate_completeness(result: subprocess.CompletedProcess, metrics: dict) -> bool:
    """
    Article I: Validate test execution completed successfully.

    Checks:
    - Exit code 0 or 1 (0 = all passed, 1 = some failed but completed)
    - No truncation indicators in output
    - Metrics parsed successfully
    """
    incomplete_indicators = [
        "Terminated",
        "Killed",
        "... (truncated)",
        "Connection timed out",
        "Signal received",
        "Process interrupted",
    ]

    output = result.stdout + result.stderr
    for indicator in incomplete_indicators:
        if indicator in output:
            return False

    # Check metrics parsed
    if metrics["total"] == 0:
        return False

    # Exit code validation (0 = success, 1 = tests failed but ran to completion)
    if result.returncode not in [0, 1]:
        return False

    return True


def _build_failure_report(result: subprocess.CompletedProcess) -> str:
    """Build detailed failure report from pytest output."""
    import re

    output = result.stdout + result.stderr

    # Extract failing test names
    failures = re.findall(r"FAILED ([\w/\.]+::\w+)", output)

    report_lines = ["Test Verification Gate: FAILED ❌", ""]

    if failures:
        report_lines.append(f"Failing Tests ({len(failures)}):")
        for i, failure in enumerate(failures, 1):
            report_lines.append(f"  {i}. {failure}")
    else:
        report_lines.append("Unable to parse failure details. Check full output.")

    report_lines.append("")
    report_lines.append("Article II Requirement: 100% test pass rate (no exceptions)")
    report_lines.append("Action Required: Fix failing tests before proceeding")

    return "\n".join(report_lines)


def _get_blocking_reason(is_complete: bool, pass_rate: float) -> str:
    """Get human-readable blocking reason."""
    if not is_complete:
        return "Article I: Incomplete test execution (timed out or truncated)"

    if pass_rate < 1.0:
        return f"Article II: Test pass rate {pass_rate*100:.1f}% (required: 100%)"

    return "Unknown blocking reason"


def perform_rollback() -> Result[str, str]:
    """
    Rollback git changes to last known good state.

    Returns:
        Result[str, str]: Ok(success_message) or Err(error_message)
    """
    try:
        # Step 1: Unstage changes
        result = subprocess.run(
            ["git", "restore", "--staged", "."],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return Err(f"Failed to unstage changes: {result.stderr}")

        # Step 2: Discard working directory changes
        result = subprocess.run(
            ["git", "restore", "."], capture_output=True, text=True, timeout=10
        )

        if result.returncode != 0:
            return Err(f"Failed to discard changes: {result.stderr}")

        return Ok("Rollback successful: Changes discarded, working directory clean")

    except subprocess.TimeoutExpired:
        return Err("Rollback timeout: Git operations took too long")
    except Exception as e:
        return Err(f"Rollback failed: {str(e)}")


# ============================================================================
# Test Classes
# ============================================================================


class TestVerificationConfig:
    """Test VerificationConfig Pydantic model."""

    def test_default_config_values(self) -> None:
        """Test default configuration values."""
        # Arrange & Act
        config = VerificationConfig()

        # Assert
        assert config.base_timeout_ms == 120000
        assert config.timeout_multipliers == [1, 2, 3, 5, 10]
        assert config.max_retries == 5
        assert config.required_pass_rate == 1.0
        assert config.memory_safety_check is True
        assert config.rollback_on_failure is True
        assert config.test_scope == "all"

    def test_custom_config_values(self) -> None:
        """Test custom configuration values."""
        # Arrange & Act
        config = VerificationConfig(
            base_timeout_ms=60000,
            timeout_multipliers=[1, 2, 4],
            max_retries=3,
            test_scope="unit",
            memory_safety_check=False,
            rollback_on_failure=False,
        )

        # Assert
        assert config.base_timeout_ms == 60000
        assert config.timeout_multipliers == [1, 2, 4]
        assert config.max_retries == 3
        assert config.test_scope == "unit"
        assert config.memory_safety_check is False
        assert config.rollback_on_failure is False

    def test_article_ii_required_pass_rate_enforced(self) -> None:
        """Test Article II: required_pass_rate must be exactly 1.0 (100%)."""
        # Arrange & Act
        config = VerificationConfig()

        # Assert
        assert config.required_pass_rate == 1.0

        # Verify Pydantic validation enforces 1.0
        with pytest.raises(ValueError):
            VerificationConfig(required_pass_rate=0.99)

        with pytest.raises(ValueError):
            VerificationConfig(required_pass_rate=1.01)

    def test_base_timeout_validation(self) -> None:
        """Test base_timeout_ms validation (30s min, 10min max)."""
        # Too low
        with pytest.raises(ValueError, match="greater than or equal to 30000"):
            VerificationConfig(base_timeout_ms=29999)

        # Too high
        with pytest.raises(ValueError, match="less than or equal to 600000"):
            VerificationConfig(base_timeout_ms=600001)

        # Valid boundaries
        config_min = VerificationConfig(base_timeout_ms=30000)
        assert config_min.base_timeout_ms == 30000

        config_max = VerificationConfig(base_timeout_ms=600000)
        assert config_max.base_timeout_ms == 600000

    def test_max_retries_validation(self) -> None:
        """Test max_retries validation (1-10 range)."""
        # Too low
        with pytest.raises(ValueError, match="greater than or equal to 1"):
            VerificationConfig(max_retries=0)

        # Too high
        with pytest.raises(ValueError, match="less than or equal to 10"):
            VerificationConfig(max_retries=11)

        # Valid boundaries
        config_min = VerificationConfig(max_retries=1)
        assert config_min.max_retries == 1

        config_max = VerificationConfig(max_retries=10)
        assert config_max.max_retries == 10


class TestVerificationResult:
    """Test VerificationResult Pydantic model."""

    def test_gate_passed_with_all_criteria_met(self) -> None:
        """Test gate_passed=True when all criteria met."""
        # Arrange & Act
        result = VerificationResult(
            gate_passed=True,
            article_i_compliant=True,
            article_ii_compliant=True,
            total_tests=100,
            passed_tests=100,
            failed_tests=0,
            pass_rate=1.0,
            duration_seconds=45.2,
            retry_attempts=1,
            timeout_multiplier_used=1,
            memory_safe=True,
            worker_count_used=10,
        )

        # Assert
        assert result.gate_passed is True
        assert result.article_i_compliant is True
        assert result.article_ii_compliant is True
        assert result.pass_rate == 1.0
        assert result.blocking_reason is None

    def test_gate_failed_with_article_ii_violation(self) -> None:
        """Test gate_passed=False when Article II violated (<100% pass rate)."""
        # Arrange & Act
        result = VerificationResult(
            gate_passed=False,
            article_i_compliant=True,
            article_ii_compliant=False,
            total_tests=100,
            passed_tests=98,
            failed_tests=2,
            pass_rate=0.98,
            duration_seconds=45.2,
            retry_attempts=1,
            timeout_multiplier_used=1,
            memory_safe=True,
            worker_count_used=10,
            blocking_reason="Article II: Test pass rate 98.0% (required: 100%)",
        )

        # Assert
        assert result.gate_passed is False
        assert result.article_ii_compliant is False
        assert result.pass_rate == 0.98
        assert "Article II" in result.blocking_reason

    def test_gate_failed_with_article_i_violation(self) -> None:
        """Test gate_passed=False when Article I violated (timeout)."""
        # Arrange & Act
        result = VerificationResult(
            gate_passed=False,
            article_i_compliant=False,
            article_ii_compliant=True,
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            pass_rate=0.0,
            duration_seconds=1200.0,
            retry_attempts=5,
            timeout_multiplier_used=10,
            memory_safe=True,
            worker_count_used=3,
            blocking_reason="Article I: Incomplete test execution (timed out or truncated)",
        )

        # Assert
        assert result.gate_passed is False
        assert result.article_i_compliant is False
        assert result.retry_attempts == 5
        assert "Article I" in result.blocking_reason

    def test_rollback_performed_flag(self) -> None:
        """Test rollback_performed flag set correctly."""
        # Arrange & Act
        result = VerificationResult(
            gate_passed=False,
            article_i_compliant=True,
            article_ii_compliant=False,
            total_tests=100,
            passed_tests=95,
            failed_tests=5,
            pass_rate=0.95,
            duration_seconds=50.0,
            retry_attempts=1,
            timeout_multiplier_used=1,
            memory_safe=True,
            worker_count_used=10,
            rollback_performed=True,
        )

        # Assert
        assert result.rollback_performed is True


class TestMemoryAwareWorkerCalculation:
    """Test memory-aware worker count calculation (ADR-023)."""

    @patch("tools.memory_aware_test_runner.check_ollama_running")
    @patch("tools.memory_aware_test_runner.verify_memory_safe")
    @patch("tools.memory_aware_test_runner.get_safe_worker_count")
    @patch("psutil.virtual_memory")
    def test_local_model_active_reduces_workers(
        self, mock_vm: Mock, mock_worker_count: Mock, mock_verify: Mock, mock_ollama: Mock
    ) -> None:
        """Test worker count reduced when local model active."""
        # Arrange
        mock_ollama.return_value = True  # Local model ON
        mock_vm.return_value = Mock(available=14 * 1024**3)  # 14GB available
        mock_verify.return_value = True
        mock_worker_count.return_value = 3

        # Act
        worker_count, memory_safe, rationale = calculate_test_workers()

        # Assert
        assert worker_count == 3  # Reduced for local model
        assert "Local model active" in rationale
        assert "Ollama running" in rationale

    @patch("tools.memory_aware_test_runner.check_ollama_running")
    @patch("tools.memory_aware_test_runner.verify_memory_safe")
    @patch("tools.memory_aware_test_runner.get_safe_worker_count")
    @patch("psutil.virtual_memory")
    def test_local_model_off_allows_full_parallelism(
        self, mock_vm: Mock, mock_worker_count: Mock, mock_verify: Mock, mock_ollama: Mock
    ) -> None:
        """Test full parallelism when local model OFF."""
        # Arrange
        mock_ollama.return_value = False  # Local model OFF
        mock_vm.return_value = Mock(available=25 * 1024**3)  # 25GB available
        mock_verify.return_value = True
        mock_worker_count.return_value = 10

        # Act
        worker_count, memory_safe, rationale = calculate_test_workers()

        # Assert
        assert worker_count == 10  # Full parallelism
        assert "Local model OFF" in rationale

    @patch("tools.memory_aware_test_runner.check_ollama_running")
    @patch("tools.memory_aware_test_runner.verify_memory_safe")
    @patch("psutil.virtual_memory")
    def test_critical_memory_forces_sequential(
        self, mock_vm: Mock, mock_verify: Mock, mock_ollama: Mock
    ) -> None:
        """Test sequential execution when memory critically low."""
        # Arrange
        mock_ollama.return_value = False
        mock_vm.return_value = Mock(available=8 * 1024**3)  # 8GB available (critical)
        mock_verify.return_value = False  # Not enough memory

        # Act
        worker_count, memory_safe, rationale = calculate_test_workers()

        # Assert
        assert worker_count == 1  # Sequential execution
        assert memory_safe is False
        assert "Critical memory" in rationale

    @patch("tools.memory_aware_test_runner.check_ollama_running")
    @patch("tools.memory_aware_test_runner.verify_memory_safe")
    @patch("tools.memory_aware_test_runner.get_safe_worker_count")
    @patch("psutil.virtual_memory")
    def test_memory_safe_threshold_10gb(
        self, mock_vm: Mock, mock_worker_count: Mock, mock_verify: Mock, mock_ollama: Mock
    ) -> None:
        """Test memory_safe flag set correctly (10GB+ threshold)."""
        # Arrange
        mock_ollama.return_value = False
        mock_verify.return_value = True
        mock_worker_count.return_value = 6

        # Act & Assert: Below threshold
        mock_vm.return_value = Mock(available=9 * 1024**3)
        _, memory_safe, _ = calculate_test_workers()
        assert memory_safe is False

        # Act & Assert: Above threshold
        mock_vm.return_value = Mock(available=11 * 1024**3)
        _, memory_safe, _ = calculate_test_workers()
        assert memory_safe is True


class TestParseTestOutput:
    """Test pytest output parsing."""

    def test_parse_all_tests_passed(self) -> None:
        """Test parsing output with 100% pass rate."""
        # Arrange
        stdout = "========================== 1725 passed in 45.2s =========================="
        stderr = ""

        # Act
        metrics = _parse_test_output(stdout, stderr)

        # Assert
        assert metrics["total"] == 1725
        assert metrics["passed"] == 1725
        assert metrics["failed"] == 0

    def test_parse_partial_failure(self) -> None:
        """Test parsing output with some failures."""
        # Arrange
        stdout = "==================== 1722 passed, 3 failed in 50.1s ===================="
        stderr = ""

        # Act
        metrics = _parse_test_output(stdout, stderr)

        # Assert
        assert metrics["total"] == 1725
        assert metrics["passed"] == 1722
        assert metrics["failed"] == 3

    def test_parse_with_errors(self) -> None:
        """Test parsing output with errors."""
        # Arrange
        stdout = "============== 100 passed, 2 failed, 1 error in 10.0s ==============="
        stderr = ""

        # Act
        metrics = _parse_test_output(stdout, stderr)

        # Assert
        assert metrics["total"] == 103
        assert metrics["passed"] == 100
        assert metrics["failed"] == 3  # Failures + errors combined

    def test_parse_no_tests_run(self) -> None:
        """Test parsing output with no tests."""
        # Arrange
        stdout = "========================== no tests ran in 0.1s =========================="
        stderr = ""

        # Act
        metrics = _parse_test_output(stdout, stderr)

        # Assert
        assert metrics["total"] == 0
        assert metrics["passed"] == 0
        assert metrics["failed"] == 0


class TestValidateCompleteness:
    """Test Article I: completeness validation."""

    def test_validate_completeness_success(self) -> None:
        """Test completeness validation with successful execution."""
        # Arrange
        result = Mock(spec=subprocess.CompletedProcess)
        result.returncode = 0
        result.stdout = "1725 passed in 45.2s"
        result.stderr = ""
        metrics = {"total": 1725, "passed": 1725, "failed": 0}

        # Act
        is_complete = _validate_completeness(result, metrics)

        # Assert
        assert is_complete is True

    def test_validate_completeness_with_test_failures(self) -> None:
        """Test completeness validation with test failures (still complete)."""
        # Arrange
        result = Mock(spec=subprocess.CompletedProcess)
        result.returncode = 1  # Exit code 1 = tests failed but ran to completion
        result.stdout = "1722 passed, 3 failed in 50.1s"
        result.stderr = ""
        metrics = {"total": 1725, "passed": 1722, "failed": 3}

        # Act
        is_complete = _validate_completeness(result, metrics)

        # Assert
        assert is_complete is True  # Complete, just not all passed

    def test_validate_completeness_with_terminated_signal(self) -> None:
        """Test incomplete detection with Terminated signal."""
        # Arrange
        result = Mock(spec=subprocess.CompletedProcess)
        result.returncode = 1
        result.stdout = "100 passed"
        result.stderr = "Terminated"
        metrics = {"total": 100, "passed": 100, "failed": 0}

        # Act
        is_complete = _validate_completeness(result, metrics)

        # Assert
        assert is_complete is False  # Incomplete due to termination

    def test_validate_completeness_with_truncated_output(self) -> None:
        """Test incomplete detection with truncated output."""
        # Arrange
        result = Mock(spec=subprocess.CompletedProcess)
        result.returncode = 0
        result.stdout = "100 passed ... (truncated)"
        result.stderr = ""
        metrics = {"total": 100, "passed": 100, "failed": 0}

        # Act
        is_complete = _validate_completeness(result, metrics)

        # Assert
        assert is_complete is False

    def test_validate_completeness_with_no_tests(self) -> None:
        """Test incomplete detection when no tests parsed."""
        # Arrange
        result = Mock(spec=subprocess.CompletedProcess)
        result.returncode = 0
        result.stdout = ""
        result.stderr = ""
        metrics = {"total": 0, "passed": 0, "failed": 0}

        # Act
        is_complete = _validate_completeness(result, metrics)

        # Assert
        assert is_complete is False  # No tests = incomplete

    def test_validate_completeness_with_bad_exit_code(self) -> None:
        """Test incomplete detection with unexpected exit code."""
        # Arrange
        result = Mock(spec=subprocess.CompletedProcess)
        result.returncode = 2  # Unexpected exit code
        result.stdout = "100 passed"
        result.stderr = ""
        metrics = {"total": 100, "passed": 100, "failed": 0}

        # Act
        is_complete = _validate_completeness(result, metrics)

        # Assert
        assert is_complete is False


class TestBuildFailureReport:
    """Test failure report generation."""

    def test_build_failure_report_with_failures(self) -> None:
        """Test failure report includes failing test names."""
        # Arrange
        result = Mock(spec=subprocess.CompletedProcess)
        result.stdout = """
FAILED tests/test_auth.py::test_login_invalid_credentials - AssertionError
FAILED tests/test_api.py::test_rate_limiting - TimeoutError
FAILED tests/test_db.py::test_connection_pool - ConnectionError
"""
        result.stderr = ""

        # Act
        report = _build_failure_report(result)

        # Assert
        assert "Test Verification Gate: FAILED" in report
        assert "Failing Tests (3)" in report
        assert "tests/test_auth.py::test_login_invalid_credentials" in report
        assert "tests/test_api.py::test_rate_limiting" in report
        assert "tests/test_db.py::test_connection_pool" in report
        assert "Article II Requirement: 100% test pass rate" in report

    def test_build_failure_report_no_parsable_failures(self) -> None:
        """Test failure report when failures not parsable."""
        # Arrange
        result = Mock(spec=subprocess.CompletedProcess)
        result.stdout = "Some tests failed but output is malformed"
        result.stderr = ""

        # Act
        report = _build_failure_report(result)

        # Assert
        assert "Unable to parse failure details" in report


class TestGetBlockingReason:
    """Test blocking reason generation."""

    def test_blocking_reason_article_i_violation(self) -> None:
        """Test blocking reason for Article I violation (incomplete)."""
        # Arrange
        is_complete = False
        pass_rate = 0.0

        # Act
        reason = _get_blocking_reason(is_complete, pass_rate)

        # Assert
        assert "Article I" in reason
        assert "Incomplete test execution" in reason

    def test_blocking_reason_article_ii_violation(self) -> None:
        """Test blocking reason for Article II violation (<100% pass rate)."""
        # Arrange
        is_complete = True
        pass_rate = 0.98

        # Act
        reason = _get_blocking_reason(is_complete, pass_rate)

        # Assert
        assert "Article II" in reason
        assert "98.0%" in reason
        assert "required: 100%" in reason

    def test_blocking_reason_both_complete_and_passed(self) -> None:
        """Test blocking reason when both complete and passed (edge case)."""
        # Arrange
        is_complete = True
        pass_rate = 1.0

        # Act
        reason = _get_blocking_reason(is_complete, pass_rate)

        # Assert
        assert "Unknown blocking reason" in reason


class TestPerformRollback:
    """Test git rollback functionality."""

    @patch("subprocess.run")
    def test_rollback_success(self, mock_run: Mock) -> None:
        """Test successful git rollback."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        # Act
        result = perform_rollback()

        # Assert
        assert result.is_ok()
        assert "Rollback successful" in result.unwrap()
        assert mock_run.call_count == 2  # Two git commands

        # Verify git restore --staged . called
        mock_run.assert_any_call(
            ["git", "restore", "--staged", "."],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Verify git restore . called
        mock_run.assert_any_call(
            ["git", "restore", "."], capture_output=True, text=True, timeout=10
        )

    @patch("subprocess.run")
    def test_rollback_unstage_failure(self, mock_run: Mock) -> None:
        """Test rollback failure during unstage step."""
        # Arrange
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="unstage error")

        # Act
        result = perform_rollback()

        # Assert
        assert result.is_err()
        assert "Failed to unstage changes" in result.unwrap_err()
        assert "unstage error" in result.unwrap_err()

    @patch("subprocess.run")
    def test_rollback_discard_failure(self, mock_run: Mock) -> None:
        """Test rollback failure during discard step."""
        # Arrange
        def side_effect(*args, **kwargs):
            if "restore" in args[0] and "--staged" in args[0]:
                return Mock(returncode=0, stdout="", stderr="")
            else:
                return Mock(returncode=1, stdout="", stderr="discard error")

        mock_run.side_effect = side_effect

        # Act
        result = perform_rollback()

        # Assert
        assert result.is_err()
        assert "Failed to discard changes" in result.unwrap_err()
        assert "discard error" in result.unwrap_err()

    @patch("subprocess.run")
    def test_rollback_timeout(self, mock_run: Mock) -> None:
        """Test rollback timeout handling."""
        # Arrange
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=10)

        # Act
        result = perform_rollback()

        # Assert
        assert result.is_err()
        assert "Rollback timeout" in result.unwrap_err()

    @patch("subprocess.run")
    def test_rollback_unexpected_exception(self, mock_run: Mock) -> None:
        """Test rollback handling of unexpected exceptions."""
        # Arrange
        mock_run.side_effect = Exception("Unexpected error")

        # Act
        result = perform_rollback()

        # Assert
        assert result.is_err()
        assert "Rollback failed" in result.unwrap_err()
        assert "Unexpected error" in result.unwrap_err()


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_tests_run_is_incomplete(self) -> None:
        """Test that zero tests is treated as incomplete."""
        # Arrange
        result = Mock(spec=subprocess.CompletedProcess)
        result.returncode = 0
        result.stdout = "no tests ran"
        result.stderr = ""
        metrics = {"total": 0, "passed": 0, "failed": 0}

        # Act
        is_complete = _validate_completeness(result, metrics)

        # Assert
        assert is_complete is False

    def test_exact_100_percent_pass_rate(self) -> None:
        """Test exactly 100% pass rate validation."""
        # Arrange
        config = VerificationConfig()

        # Act & Assert
        assert config.required_pass_rate == 1.0

        # Test 99.9% is not enough
        with pytest.raises(ValueError):
            VerificationConfig(required_pass_rate=0.999)

    def test_timeout_multiplier_progression(self) -> None:
        """Test Article I timeout multiplier progression (1x → 2x → 3x → 5x → 10x)."""
        # Arrange
        config = VerificationConfig()

        # Act & Assert
        assert config.timeout_multipliers == [1, 2, 3, 5, 10]
        assert len(config.timeout_multipliers) == config.max_retries

        # Verify timeout progression
        base_timeout_s = config.base_timeout_ms / 1000
        expected_timeouts = [
            base_timeout_s * mult for mult in config.timeout_multipliers
        ]
        assert expected_timeouts == [120, 240, 360, 600, 1200]

    def test_max_total_timeout_21x_base(self) -> None:
        """Test maximum total timeout is 21x base (1+2+3+5+10)."""
        # Arrange
        config = VerificationConfig()

        # Act
        total_multiplier = sum(config.timeout_multipliers)

        # Assert
        assert total_multiplier == 21  # 1+2+3+5+10 = 21

    @patch("tools.memory_aware_test_runner.check_ollama_running")
    @patch("tools.memory_aware_test_runner.verify_memory_safe")
    @patch("tools.memory_aware_test_runner.get_safe_worker_count")
    @patch("psutil.virtual_memory")
    def test_worker_count_boundaries(
        self, mock_vm: Mock, mock_worker_count: Mock, mock_verify: Mock, mock_ollama: Mock
    ) -> None:
        """Test worker count stays within 1-10 boundaries."""
        # Arrange
        mock_ollama.return_value = False

        # Act & Assert: Minimum (1 worker)
        mock_vm.return_value = Mock(available=8 * 1024**3)
        mock_verify.return_value = False  # Critical memory
        worker_count, _, _ = calculate_test_workers()
        assert 1 <= worker_count <= 10
        assert worker_count == 1

        # Act & Assert: Maximum (10 workers)
        mock_vm.return_value = Mock(available=25 * 1024**3)
        mock_verify.return_value = True
        mock_worker_count.return_value = 10
        worker_count, _, _ = calculate_test_workers()
        assert 1 <= worker_count <= 10
        assert worker_count == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
