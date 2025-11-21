"""Tests for TestVerificationGate (Article I & II enforcement).

Constitutional Coverage:
- Article I: Retry with 2x, 3x, 10x timeout on incomplete execution
- Article II: 100% pass requirement enforcement
- Article IV: Verification pattern storage
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shared.type_definitions.result import Err, Ok
from tools.orchestrator.test_verification_gate import (
    TestVerificationGate,
    VerificationError,
    VerificationResults,
    verify_tests,
)


class TestTestResults:
    """Test TestResults model validation."""

    def test_valid_results(self):
        """Test valid test results creation."""
        results = VerificationResults(
            passed=100,
            failed=0,
            skipped=5,
            errors=[],
            duration=45.67,
            coverage=95.5,
            timed_out=False,
            exit_code=0,
            worker_count=10,
            output="All tests passed",
        )

        assert results.passed == 100
        assert results.failed == 0
        assert results.skipped == 5
        assert results.duration == 45.67
        assert results.coverage == 95.5
        assert not results.timed_out
        assert results.exit_code == 0
        assert results.worker_count == 10

    def test_negative_values_rejected(self):
        """Test that negative test counts are rejected."""
        with pytest.raises(ValueError):
            VerificationResults(
                passed=-1,
                failed=0,
                skipped=0,
                duration=10.0,
                exit_code=0,
                worker_count=1,
            )

    def test_invalid_worker_count(self):
        """Test that worker count outside 1-12 range is rejected."""
        with pytest.raises(ValueError):
            VerificationResults(
                passed=10,
                failed=0,
                skipped=0,
                duration=10.0,
                exit_code=0,
                worker_count=0,  # Below minimum
            )

        with pytest.raises(ValueError):
            VerificationResults(
                passed=10,
                failed=0,
                skipped=0,
                duration=10.0,
                exit_code=0,
                worker_count=13,  # Above maximum
            )

    def test_is_constitutional_pass(self):
        """Test constitutional validation for passing tests."""
        results = VerificationResults(
            passed=100,
            failed=0,
            skipped=0,
            duration=10.0,
            exit_code=0,
            worker_count=5,
        )

        assert results.is_constitutional()

    def test_is_constitutional_fail_with_failures(self):
        """Test constitutional validation fails with test failures (Article II)."""
        results = VerificationResults(
            passed=99,
            failed=1,
            skipped=0,
            duration=10.0,
            exit_code=1,
            worker_count=5,
        )

        assert not results.is_constitutional()

    def test_is_constitutional_fail_with_timeout(self):
        """Test constitutional validation fails with timeout (Article I)."""
        results = VerificationResults(
            passed=0,
            failed=0,
            skipped=0,
            duration=10.0,
            timed_out=True,
            exit_code=124,
            worker_count=5,
        )

        assert not results.is_constitutional()

    def test_is_constitutional_fail_no_tests(self):
        """Test constitutional validation fails when no tests run (Article II)."""
        results = VerificationResults(
            passed=0,
            failed=0,
            skipped=0,
            duration=10.0,
            exit_code=0,
            worker_count=5,
        )

        assert not results.is_constitutional()

    def test_get_summary_pass(self):
        """Test summary generation for passing tests."""
        results = VerificationResults(
            passed=100,
            failed=0,
            skipped=5,
            duration=45.67,
            exit_code=0,
            worker_count=10,
        )

        summary = results.get_summary()
        assert "✅ PASS" in summary
        assert "105 tests" in summary
        assert "100 passed" in summary
        assert "5 skipped" in summary
        assert "45.67s" in summary
        assert "10 workers" in summary

    def test_get_summary_fail(self):
        """Test summary generation for failing tests."""
        results = VerificationResults(
            passed=99,
            failed=1,
            skipped=0,
            duration=30.0,
            exit_code=1,
            worker_count=5,
            errors=["FAILED tests/test_example.py::test_feature"],
        )

        summary = results.get_summary()
        assert "❌ FAIL" in summary
        assert "100 tests" in summary
        assert "99 passed" in summary
        assert "1 failed" in summary
        assert "30.00s" in summary

    def test_get_summary_timeout(self):
        """Test summary generation for timeout."""
        results = VerificationResults(
            passed=50,
            failed=0,
            skipped=0,
            duration=120.0,
            timed_out=True,
            exit_code=124,
            worker_count=5,
        )

        summary = results.get_summary()
        assert "[TIMEOUT]" in summary


class TestTestVerificationError:
    """Test TestVerificationError model."""

    def test_timeout_error(self):
        """Test timeout error creation."""
        error = VerificationError(
            reason="timeout",
            message="Execution timed out after 600s",
            exit_code=124,
        )

        assert error.reason == "timeout"
        assert "timed out" in error.message
        assert error.exit_code == 124

    def test_failures_error(self):
        """Test failures error with test list."""
        error = VerificationError(
            reason="failures",
            message="5 tests failed",
            exit_code=1,
            failed_tests=[
                "tests/test_example.py::test_feature1",
                "tests/test_example.py::test_feature2",
            ],
        )

        assert error.reason == "failures"
        assert len(error.failed_tests) == 2


class TestTestVerificationGate:
    """Test TestVerificationGate functionality."""

    @pytest.fixture
    def gate(self, tmp_path: Path):
        """Create test verification gate with temp project root."""
        return TestVerificationGate(project_root=tmp_path)

    def test_initialization_default_root(self):
        """Test gate initialization with default project root detection."""
        gate = TestVerificationGate()
        assert gate.project_root.exists()
        assert gate.base_timeout == 600
        assert gate.timeout_multipliers == [1, 2, 3, 10]

    def test_initialization_custom_root(self, tmp_path: Path):
        """Test gate initialization with custom project root."""
        gate = TestVerificationGate(project_root=tmp_path)
        assert gate.project_root == tmp_path

    @pytest.mark.asyncio
    async def test_parse_test_output_success(self, gate: TestVerificationGate):
        """Test parsing successful test output."""
        output = """
===== test session starts =====
tests/test_example.py::test_feature1 PASSED
tests/test_example.py::test_feature2 PASSED
tests/test_example.py::test_feature3 SKIPPED

===== 2 passed, 1 skipped in 10.50s =====
"""

        result = gate._parse_test_output(output, exit_code=0, worker_count=5)

        assert result.is_ok()
        test_results = result.unwrap()
        assert test_results.passed == 2
        assert test_results.failed == 0
        assert test_results.skipped == 1
        assert test_results.duration == 10.50
        assert test_results.exit_code == 0
        assert test_results.worker_count == 5
        assert test_results.is_constitutional()

    @pytest.mark.asyncio
    async def test_parse_test_output_failures(self, gate: TestVerificationGate):
        """Test parsing output with test failures."""
        output = """
===== test session starts =====
tests/test_example.py::test_feature1 PASSED
tests/test_example.py::test_feature2 FAILED
tests/test_example.py::test_feature3 PASSED

FAILED tests/test_example.py::test_feature2 - AssertionError: expected 1, got 2

===== 2 passed, 1 failed in 15.25s =====
"""

        result = gate._parse_test_output(output, exit_code=1, worker_count=3)

        assert result.is_err()  # Article II: failures cause Err
        error = result.unwrap_err()
        assert error.reason == "failures"
        assert "Article II violation" in error.message
        assert "1 tests failed" in error.message
        assert len(error.failed_tests) == 1
        assert "test_feature2" in error.failed_tests[0]

    @pytest.mark.asyncio
    async def test_parse_test_output_no_tests(self, gate: TestVerificationGate):
        """Test parsing output when no tests run."""
        output = """
===== test session starts =====
===== no tests ran in 0.01s =====
"""

        result = gate._parse_test_output(output, exit_code=5, worker_count=1)

        assert result.is_err()
        error = result.unwrap_err()
        assert error.reason == "no_tests_run"
        assert "No tests were executed" in error.message

    @pytest.mark.asyncio
    async def test_execute_tests_success(self, gate: TestVerificationGate):
        """Test successful test execution."""
        mock_output = b"""
===== test session starts =====
tests/test_example.py::test_feature PASSED
===== 1 passed in 5.00s =====
"""

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (mock_output, b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await gate._execute_tests(mode="unit", timeout=120, worker_count=3)

        assert result.is_ok()
        test_results = result.unwrap()
        assert test_results.passed == 1
        assert test_results.failed == 0
        assert test_results.is_constitutional()

    @pytest.mark.asyncio
    async def test_execute_tests_timeout(self, gate: TestVerificationGate):
        """Test test execution timeout (Article I)."""
        mock_process = AsyncMock()
        mock_process.communicate.side_effect = TimeoutError()
        mock_process.kill = AsyncMock()
        mock_process.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await gate._execute_tests(mode="unit", timeout=10, worker_count=3)

        assert result.is_err()
        error = result.unwrap_err()
        assert error.reason == "timeout"
        assert "timed out" in error.message
        assert error.exit_code == 124

    @pytest.mark.asyncio
    async def test_execute_tests_file_not_found(self, gate: TestVerificationGate):
        """Test handling when run_tests.py not found."""
        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError("run_tests.py not found"),
        ):
            result = await gate._execute_tests(mode="unit", timeout=120, worker_count=3)

        assert result.is_err()
        error = result.unwrap_err()
        assert error.reason == "process_error"
        assert "not found" in error.message

    @pytest.mark.asyncio
    async def test_verify_success_first_try(self, gate: TestVerificationGate):
        """Test verification succeeds on first try."""
        # Mock successful execution
        mock_results = VerificationResults(
            passed=100,
            failed=0,
            skipped=0,
            duration=30.0,
            exit_code=0,
            worker_count=3,
        )

        async def mock_execute(*args, **kwargs):
            return Ok(mock_results)

        with patch.object(gate, "_execute_tests", side_effect=mock_execute):
            result = await gate.verify(mode="unit")

        assert result.is_ok()
        test_results = result.unwrap()
        assert test_results.passed == 100
        assert test_results.is_constitutional()

    @pytest.mark.asyncio
    async def test_verify_retry_on_timeout(self, gate: TestVerificationGate):
        """Test Article I retry logic: retry on timeout with exponential backoff."""
        # First attempt: timeout
        timeout_error = VerificationError(reason="timeout", message="Timed out", exit_code=124)

        # Second attempt: success
        success_results = VerificationResults(
            passed=50,
            failed=0,
            skipped=0,
            duration=60.0,
            exit_code=0,
            worker_count=3,
        )

        call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return Err(timeout_error)
            return Ok(success_results)

        with patch.object(gate, "_execute_tests", side_effect=mock_execute):
            result = await gate.verify(mode="unit")

        # Should succeed on second try
        assert result.is_ok()
        test_results = result.unwrap()
        assert test_results.passed == 50
        assert call_count == 2  # First timeout, then success

    @pytest.mark.asyncio
    async def test_verify_no_retry_on_failures(self, gate: TestVerificationGate):
        """Test that failures don't trigger retry (only timeout does)."""
        failure_error = VerificationError(
            reason="failures",
            message="5 tests failed",
            exit_code=1,
            failed_tests=["test1", "test2"],
        )

        call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return Err(failure_error)

        with patch.object(gate, "_execute_tests", side_effect=mock_execute):
            result = await gate.verify(mode="unit")

        # Should fail immediately without retry
        assert result.is_err()
        error = result.unwrap_err()
        assert error.reason == "failures"
        assert call_count == 1  # No retry

    @pytest.mark.asyncio
    async def test_verify_exhausts_all_retries(self, gate: TestVerificationGate):
        """Test that all retry attempts are exhausted on persistent timeout."""
        timeout_error = VerificationError(reason="timeout", message="Timed out", exit_code=124)

        call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return Err(timeout_error)

        with patch.object(gate, "_execute_tests", side_effect=mock_execute):
            result = await gate.verify(mode="unit")

        # Should fail after all retries
        assert result.is_err()
        error = result.unwrap_err()
        assert error.reason == "timeout"
        assert call_count == 4  # All multipliers: [1, 2, 3, 10]

    @pytest.mark.asyncio
    async def test_verify_passes_correct_mode(self, gate: TestVerificationGate):
        """Test that verify passes correct mode to execute_tests."""
        captured_mode = None

        async def mock_execute(mode, timeout, worker_count, retry_attempt):
            nonlocal captured_mode
            captured_mode = mode
            return Ok(
                VerificationResults(
                    passed=10,
                    failed=0,
                    skipped=0,
                    duration=5.0,
                    exit_code=0,
                    worker_count=worker_count,
                )
            )

        with patch.object(gate, "_execute_tests", side_effect=mock_execute):
            await gate.verify(mode="fast")

        assert captured_mode == "fast"

    @pytest.mark.asyncio
    async def test_verify_uses_memory_aware_worker_count(self, gate: TestVerificationGate):
        """Test that verify uses memory-aware worker count."""
        captured_worker_count = None

        async def mock_execute(mode, timeout, worker_count, retry_attempt):
            nonlocal captured_worker_count
            captured_worker_count = worker_count
            return Ok(
                VerificationResults(
                    passed=10,
                    failed=0,
                    skipped=0,
                    duration=5.0,
                    exit_code=0,
                    worker_count=worker_count,
                )
            )

        with patch.object(gate, "_execute_tests", side_effect=mock_execute):
            with patch(
                "tools.orchestrator.test_verification_gate.get_safe_worker_count",
                return_value=5,
            ):
                await gate.verify(mode="unit")

        assert captured_worker_count == 5


class TestConvenienceFunction:
    """Test convenience function for quick verification."""

    @pytest.mark.asyncio
    async def test_verify_tests_convenience_function(self):
        """Test verify_tests convenience function."""
        mock_results = VerificationResults(
            passed=100,
            failed=0,
            skipped=0,
            duration=30.0,
            exit_code=0,
            worker_count=10,
        )

        async def mock_verify(*args, **kwargs):
            return Ok(mock_results)

        with patch.object(TestVerificationGate, "verify", side_effect=mock_verify):
            result = await verify_tests("all")

        assert result.is_ok()
        test_results = result.unwrap()
        assert test_results.passed == 100


class TestConstitutionalCompliance:
    """Test constitutional compliance scenarios."""

    @pytest.mark.asyncio
    async def test_article_i_complete_context_enforcement(self):
        """Test Article I: Complete context before action (retry on timeout)."""
        gate = TestVerificationGate()

        # Simulate timeout then success
        timeout_error = VerificationError(reason="timeout", message="Timed out", exit_code=124)
        success_results = VerificationResults(
            passed=100,
            failed=0,
            skipped=0,
            duration=60.0,
            exit_code=0,
            worker_count=3,
        )

        call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return Err(timeout_error)
            return Ok(success_results)

        with patch.object(gate, "_execute_tests", side_effect=mock_execute):
            result = await gate.verify()

        # Article I: Should retry and succeed
        assert result.is_ok()
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_article_ii_100_percent_pass_requirement(self):
        """Test Article II: 100% pass requirement (zero failures allowed)."""
        gate = TestVerificationGate()

        output = """
===== 99 passed, 1 failed in 30.00s =====
"""

        result = gate._parse_test_output(output, exit_code=1, worker_count=5)

        # Article II: Even 1 failure causes Err
        assert result.is_err()
        error = result.unwrap_err()
        assert "Article II violation" in error.message
        assert "1 tests failed" in error.message

    @pytest.mark.asyncio
    async def test_article_iv_verification_pattern_storage(self, tmp_path: Path):
        """Test Article IV: Store verification patterns (metadata captured)."""
        gate = TestVerificationGate(project_root=tmp_path)

        mock_results = VerificationResults(
            passed=100,
            failed=0,
            skipped=0,
            duration=30.0,
            exit_code=0,
            worker_count=10,
            output="All tests passed successfully",
        )

        async def mock_execute(*args, **kwargs):
            return Ok(mock_results)

        with patch.object(gate, "_execute_tests", side_effect=mock_execute):
            result = await gate.verify()

        # Article IV: Results contain pattern data for learning
        assert result.is_ok()
        test_results = result.unwrap()
        assert test_results.duration > 0
        assert test_results.worker_count > 0
        assert len(test_results.output) > 0  # Context for learning
