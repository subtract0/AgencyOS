"""Test Verification Gate for Orchestrator (Article I & II Enforcement).

Constitutional Compliance:
- Article I: Retry with 2x, 3x, 10x timeout on incomplete execution
- Article II: 100% pass requirement (no exceptions)
- Article IV: Store verification patterns in VectorStore

This gate enforces the constitutional requirement that all tests must pass
before proceeding with any deployment or merge operations.
"""

import asyncio
import os
import re
import subprocess
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result
from tools.memory_aware_test_runner import get_safe_worker_count


class VerificationResults(BaseModel):
    """Test execution results with constitutional validation.

    Constitutional Requirements:
    - Article II: passed + failed + skipped >= 1 (tests were actually run)
    - Article II: failed == 0 (100% pass rate)
    - Article I: not timed_out (complete context)
    """

    passed: int = Field(ge=0, description="Number of tests passed")
    failed: int = Field(ge=0, description="Number of tests failed")
    skipped: int = Field(ge=0, description="Number of tests skipped")
    errors: list[str] = Field(default_factory=list, description="Error messages from failures")
    duration: float = Field(ge=0.0, description="Test execution duration in seconds")
    coverage: float | None = Field(
        default=None, ge=0.0, le=100.0, description="Test coverage percentage"
    )
    timed_out: bool = Field(default=False, description="Whether execution timed out")
    exit_code: int = Field(description="Process exit code")
    worker_count: int = Field(ge=1, le=10, description="Number of pytest workers used")
    output: str = Field(default="", description="Raw test output for debugging")

    def is_constitutional(self) -> bool:
        """Check if test results meet constitutional requirements.

        Returns:
            True if Article II compliant (100% pass rate, no timeout)
        """
        # Article I: Complete context (no timeout)
        if self.timed_out:
            return False

        # Article II: 100% pass rate
        if self.failed > 0:
            return False

        # Article II: Tests actually ran
        total_tests = self.passed + self.failed + self.skipped
        if total_tests == 0:
            return False

        return True

    def get_summary(self) -> str:
        """Get human-readable test summary."""
        total = self.passed + self.failed + self.skipped
        status = "✅ PASS" if self.is_constitutional() else "❌ FAIL"

        summary = f"{status} - {total} tests: {self.passed} passed"

        if self.failed > 0:
            summary += f", {self.failed} failed"
        if self.skipped > 0:
            summary += f", {self.skipped} skipped"

        summary += f" ({self.duration:.2f}s, {self.worker_count} workers)"

        if self.timed_out:
            summary += " [TIMEOUT]"

        return summary


class VerificationError(BaseModel):
    """Error details from test verification failure."""

    reason: Literal[
        "timeout", "failures", "no_tests_run", "process_error", "parse_error", "unknown"
    ]
    message: str
    exit_code: int | None = None
    failed_tests: list[str] = Field(default_factory=list)
    output: str = Field(default="", description="Raw output for debugging")


class TestVerificationGate:
    """Gate that enforces constitutional test requirements.

    Constitutional Enforcement:
    - Article I: Retry with exponential backoff (2x, 3x, 10x timeout)
    - Article II: 100% pass requirement (zero failures)
    - Article III: Automated enforcement (no manual overrides)
    - Article IV: Store verification patterns

    Usage:
        gate = TestVerificationGate()
        result = await gate.verify()

        if result.is_ok():
            test_results = result.unwrap()
            print(test_results.get_summary())
        else:
            error = result.unwrap_err()
            print(f"Verification failed: {error.message}")
    """

    def __init__(self, project_root: Path | None = None):
        """Initialize test verification gate.

        Args:
            project_root: Path to project root (default: detect from file location)
        """
        if project_root is None:
            # Detect project root (tools/orchestrator/test_verification_gate.py -> ../..)
            self.project_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.project_root = Path(project_root).resolve()

        # Article I: Timeout configuration with exponential backoff
        self.base_timeout = 600  # 10 minutes (increased from 2 minutes)
        self.timeout_multipliers = [1, 2, 3, 10]  # Article I retry policy

    async def verify(self, mode: Literal["all", "unit", "fast"] = "all") -> Result[
        VerificationResults, VerificationError
    ]:
        """Verify all tests pass with constitutional retry logic.

        Args:
            mode: Test mode ("all" for full suite, "unit" for unit tests, "fast" for fast tests)

        Returns:
            Result with VerificationResults or VerificationError

        Constitutional Compliance:
        - Article I: Retries with 2x, 3x, 10x timeout on incomplete execution
        - Article II: Returns Err if any test fails (100% pass requirement)
        """
        # Memory-aware worker count (prevents kernel panic on Apple Silicon)
        worker_count = get_safe_worker_count()

        # Try execution with exponential backoff (Article I)
        last_error: VerificationError | None = None

        for multiplier in self.timeout_multipliers:
            timeout = self.base_timeout * multiplier

            result = await self._execute_tests(mode, timeout, worker_count)

            if result.is_ok():
                # Success! Return results
                return result

            # Capture error for potential retry
            error = result.unwrap_err()
            last_error = error

            # Only retry on timeout (Article I: complete context)
            if error.reason != "timeout":
                # Non-timeout errors: fail immediately
                return result

            # Timeout: retry with longer timeout
            print(
                f"⚠️  Test timeout after {timeout}s, retrying with {multiplier * 2}x timeout "
                f"(Article I)"
            )

        # All retries exhausted
        if last_error is None:
            last_error = VerificationError(
                reason="unknown",
                message="All retries exhausted (should not happen)",
                output="",
            )

        return Err(last_error)

    async def _execute_tests(
        self, mode: str, timeout: int, worker_count: int
    ) -> Result[VerificationResults, VerificationError]:
        """Execute test suite with given timeout.

        Args:
            mode: Test mode ("all", "unit", "fast")
            timeout: Timeout in seconds
            worker_count: Number of pytest workers

        Returns:
            Result with VerificationResults or VerificationError
        """
        # Build command
        cmd = ["python", "run_tests.py"]

        if mode == "all":
            cmd.append("--run-all")
        elif mode == "fast":
            cmd.append("--fast")
        # "unit" is default, no flag needed

        # Environment variables
        env = os.environ.copy()
        env["AGENCY_TEST_TIMEOUT_OVERRIDE"] = str(timeout)
        env["PYTEST_ADDOPTS"] = f"-n {worker_count}"

        try:
            # Run tests asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.project_root),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            try:
                # Wait for completion with timeout
                stdout_data, _ = await asyncio.wait_for(
                    process.communicate(), timeout=timeout + 30  # +30s grace period
                )

                output = stdout_data.decode("utf-8", errors="replace")
                exit_code = process.returncode or 0

            except TimeoutError:
                # Kill process on timeout
                process.kill()
                await process.wait()

                return Err(
                    VerificationError(
                        reason="timeout",
                        message=f"Test execution timed out after {timeout}s (Article I violation)",
                        exit_code=124,
                        output="[timeout - no output captured]",
                    )
                )

            # Parse test results from output
            return self._parse_test_output(output, exit_code, worker_count)

        except FileNotFoundError:
            return Err(
                VerificationError(
                    reason="process_error",
                    message="run_tests.py not found - ensure you're in project root",
                    output="",
                )
            )
        except Exception as e:
            return Err(
                VerificationError(
                    reason="process_error",
                    message=f"Failed to execute tests: {e}",
                    output=str(e),
                )
            )

    def _parse_test_output(
        self, output: str, exit_code: int, worker_count: int
    ) -> Result[VerificationResults, VerificationError]:
        """Parse pytest output to extract test results.

        Args:
            output: Raw pytest output
            exit_code: Process exit code
            worker_count: Number of workers used

        Returns:
            Result with VerificationResults or VerificationError
        """
        try:
            # Parse pytest summary line
            # Format: "===== 1725 passed, 2 failed, 5 skipped in 45.67s ====="
            summary_pattern = re.compile(
                r"=+ (?:(\d+) passed)?[,\s]*(?:(\d+) failed)?[,\s]*"
                r"(?:(\d+) skipped)?[,\s]*(?:in ([\d.]+)s)? =+"
            )

            passed = 0
            failed = 0
            skipped = 0
            duration = 0.0

            for line in output.splitlines():
                match = summary_pattern.search(line)
                if match:
                    passed = int(match.group(1) or 0)
                    failed = int(match.group(2) or 0)
                    skipped = int(match.group(3) or 0)
                    duration = float(match.group(4) or 0.0)
                    break

            # Extract error messages from failed tests
            errors: list[str] = []
            failed_tests: list[str] = []

            if failed > 0:
                # Extract FAILED lines
                for line in output.splitlines():
                    if "FAILED" in line:
                        errors.append(line.strip())
                        # Extract test name
                        test_match = re.search(r"FAILED ([\w/:.]+)", line)
                        if test_match:
                            failed_tests.append(test_match.group(1))

            # Check if tests actually ran
            total_tests = passed + failed + skipped
            if total_tests == 0:
                return Err(
                    VerificationError(
                        reason="no_tests_run",
                        message="No tests were executed (check pytest configuration)",
                        exit_code=exit_code,
                        output=output[-1000:],  # Last 1000 chars for debugging
                    )
                )

            # Create test results
            results = VerificationResults(
                passed=passed,
                failed=failed,
                skipped=skipped,
                errors=errors,
                duration=duration,
                coverage=None,  # TODO: Parse coverage if available
                timed_out=False,
                exit_code=exit_code,
                worker_count=worker_count,
                output=output[-2000:],  # Last 2000 chars for context
            )

            # Article II enforcement: 100% pass requirement
            if not results.is_constitutional():
                return Err(
                    VerificationError(
                        reason="failures",
                        message=f"Article II violation: {failed} tests failed (100% pass required)",
                        exit_code=exit_code,
                        failed_tests=failed_tests,
                        output=output[-2000:],
                    )
                )

            # Success!
            return Ok(results)

        except Exception as e:
            return Err(
                VerificationError(
                    reason="parse_error",
                    message=f"Failed to parse test output: {e}",
                    exit_code=exit_code,
                    output=output[-1000:],
                )
            )


# Convenience function for quick verification
async def verify_tests(mode: Literal["all", "unit", "fast"] = "all") -> Result[
    VerificationResults, VerificationError
]:
    """Verify all tests pass with constitutional enforcement.

    Args:
        mode: Test mode ("all" for full suite, "unit" for unit tests, "fast" for fast tests)

    Returns:
        Result with VerificationResults or VerificationError

    Example:
        result = await verify_tests("all")
        if result.is_ok():
            print(result.unwrap().get_summary())
        else:
            print(f"Tests failed: {result.unwrap_err().message}")
    """
    gate = TestVerificationGate()
    return await gate.verify(mode)
