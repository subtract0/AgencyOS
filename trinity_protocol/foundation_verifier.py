"""
Foundation Verifier for Trinity Protocol

Ensures "Green Main" before autonomous operation begins.

Constitutional Compliance:
- Article I: Complete context (all tests must run to completion)
- Article II: 100% verification (all tests must pass)
- Article III: Automated enforcement (no manual overrides)

Core Principle:
EXECUTOR must NEVER start work on a broken foundation.
"""

import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class FoundationStatus(Enum):
    """Foundation health status."""

    HEALTHY = "healthy"  # All tests pass, ready for work
    BROKEN = "broken"    # Tests failing, work blocked
    TIMEOUT = "timeout"  # Tests timed out (Article I violation)
    ERROR = "error"      # Unable to verify (infrastructure issue)


class BrokenFoundationError(Exception):
    """
    Raised when foundation verification fails.

    This is a BLOCKER - EXECUTOR must not proceed.
    """
    pass


@dataclass
class VerificationResult:
    """Result of foundation verification check."""

    status: FoundationStatus
    all_tests_passed: bool
    exit_code: int
    output: str
    error: Optional[str]
    duration_seconds: float
    timestamp: str
    skipped_tests: int = 0
    failed_tests: int = 0
    passed_tests: int = 0
    constitutional_violations: Optional[List[str]] = None

    def to_compliance_report(self) -> Dict[str, Any]:
        """
        Generate constitutional compliance report.

        Returns:
            Dict with compliance status and violations
        """
        violations = []

        # Article II: 100% test success
        if not self.all_tests_passed:
            violations.append({
                "article": "Article II",
                "requirement": "100% test success",
                "violation": f"{self.failed_tests} tests failed"
            })

        # Article I: Complete context (no timeouts)
        if self.status == FoundationStatus.TIMEOUT:
            violations.append({
                "article": "Article I",
                "requirement": "Complete context",
                "violation": "Test suite timed out - incomplete results"
            })

        # Skipped tests (potential violation)
        if self.skipped_tests > 0:
            violations.append({
                "article": "Article II",
                "requirement": "All tests executed",
                "violation": f"{self.skipped_tests} tests skipped"
            })

        return {
            "article_ii_compliance": self.all_tests_passed,
            "article_i_compliance": self.status != FoundationStatus.TIMEOUT,
            "test_success_rate": self._calculate_success_rate(),
            "violations": violations,
            "status": self.status.value,
            "timestamp": self.timestamp
        }

    def _calculate_success_rate(self) -> float:
        """Calculate test success rate."""
        total = self.passed_tests + self.failed_tests
        if total == 0:
            return 1.0 if self.all_tests_passed else 0.0
        return self.passed_tests / total


class FoundationVerifier:
    """
    Verifies foundation health before autonomous operation.

    Usage:
        verifier = FoundationVerifier()

        # Check foundation health
        result = verifier.verify()
        if result.status != FoundationStatus.HEALTHY:
            # Foundation broken - cannot proceed

        # Or enforce in one step
        verifier.verify_and_enforce()  # Raises BrokenFoundationError if broken
    """

    def __init__(
        self,
        test_command: Optional[List[str]] = None,
        timeout_seconds: int = 600  # 10 minutes
    ):
        """
        Initialize foundation verifier.

        Args:
            test_command: Test command to run (default: python run_tests.py --run-all)
            timeout_seconds: Maximum time for test suite (Article I compliance)
        """
        self.test_command = test_command or ["python", "run_tests.py", "--run-all"]
        self.timeout_seconds = timeout_seconds
        self._cache: Optional[VerificationResult] = None
        self._cache_time: Optional[float] = None

    def verify(
        self,
        use_cache: bool = False,
        cache_ttl_seconds: int = 300  # 5 minutes
    ) -> VerificationResult:
        """
        Verify foundation health by running full test suite.

        Args:
            use_cache: Use cached result if available and fresh
            cache_ttl_seconds: Cache time-to-live in seconds

        Returns:
            VerificationResult with health status
        """
        # Check cache if enabled
        if use_cache and self._cache and self._cache_time:
            age = time.time() - self._cache_time
            if age < cache_ttl_seconds:
                return self._cache

        start_time = time.time()
        timestamp = datetime.now().isoformat()

        try:
            # Run full test suite (Article I: Complete context)
            result = subprocess.run(
                self.test_command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )

            duration = time.time() - start_time

            # Parse test results
            output = result.stdout + "\n" + result.stderr
            parsed = self._parse_test_output(output)

            # Check for incomplete run (no test summary found)
            has_test_summary = parsed["passed"] > 0 or parsed["failed"] > 0 or parsed["skipped"] > 0
            if result.returncode == 0 and not has_test_summary and output.strip():
                # Output exists but no test summary - incomplete run
                verification_result = VerificationResult(
                    status=FoundationStatus.ERROR,
                    all_tests_passed=False,
                    exit_code=result.returncode,
                    output=output,
                    error="Incomplete test run detected: no test summary found in output",
                    duration_seconds=duration,
                    timestamp=timestamp,
                    skipped_tests=0,
                    failed_tests=0,
                    passed_tests=0,
                    constitutional_violations=["Article I: Incomplete test execution"]
                )
            else:
                # Determine status
                all_tests_passed = result.returncode == 0 and parsed["failed"] == 0
                status = FoundationStatus.HEALTHY if all_tests_passed else FoundationStatus.BROKEN

                # Detect violations
                violations = []
                if parsed["skipped"] > 0:
                    violations.append(f"{parsed['skipped']} tests skipped")

                verification_result = VerificationResult(
                    status=status,
                    all_tests_passed=all_tests_passed,
                    exit_code=result.returncode,
                    output=output,
                    error=None if all_tests_passed else f"Test suite failed with exit code {result.returncode}",
                    duration_seconds=duration,
                    timestamp=timestamp,
                    skipped_tests=parsed["skipped"],
                    failed_tests=parsed["failed"],
                    passed_tests=parsed["passed"],
                    constitutional_violations=violations if violations else None
                )

        except subprocess.TimeoutExpired as e:
            # Article I violation: Incomplete context
            # Duration should be at least the timeout value
            duration = max(time.time() - start_time, self.timeout_seconds)
            verification_result = VerificationResult(
                status=FoundationStatus.TIMEOUT,
                all_tests_passed=False,
                exit_code=-1,
                output="",
                error=f"timeout: Test suite timed out after {self.timeout_seconds}s (Article I violation: incomplete context)",
                duration_seconds=duration,
                timestamp=timestamp,
                constitutional_violations=["Article I: Test suite timeout - incomplete results"]
            )

        except Exception as e:
            # Infrastructure error
            duration = time.time() - start_time
            verification_result = VerificationResult(
                status=FoundationStatus.ERROR,
                all_tests_passed=False,
                exit_code=-1,
                output="",
                error=f"Error executing test command: {str(e)}",
                duration_seconds=duration,
                timestamp=timestamp
            )

        # Update cache
        self._cache = verification_result
        self._cache_time = time.time()

        return verification_result

    def verify_and_enforce(self) -> VerificationResult:
        """
        Verify foundation and raise exception if broken.

        This is the enforcement mode for EXECUTOR startup.

        Returns:
            VerificationResult if foundation healthy

        Raises:
            BrokenFoundationError: If foundation is not healthy
        """
        result = self.verify()

        if result.status != FoundationStatus.HEALTHY:
            error_msg = self._format_enforcement_error(result)
            raise BrokenFoundationError(error_msg)

        return result

    def _parse_test_output(self, output: str) -> Dict[str, int]:
        """
        Parse test output to extract counts.

        Args:
            output: Test suite output

        Returns:
            Dict with passed, failed, skipped counts
        """
        passed = 0
        failed = 0
        skipped = 0

        # Parse pytest-style output
        # Examples:
        # "1562 passed"
        # "10 failed, 1552 passed"
        # "1560 passed, 2 skipped"
        # "1562 tests passed" (alternative format)

        output_lower = output.lower()

        # Extract numbers before keywords
        import re

        # Match "N passed" or "N tests passed"
        passed_match = re.search(r'(\d+)\s+(?:tests\s+)?passed', output_lower)
        if passed_match:
            passed = int(passed_match.group(1))

        # Match "N failed" or "N tests failed"
        failed_match = re.search(r'(\d+)\s+(?:tests\s+)?failed', output_lower)
        if failed_match:
            failed = int(failed_match.group(1))

        # Match "N skipped" or "N tests skipped"
        skipped_match = re.search(r'(\d+)\s+(?:tests\s+)?skipped', output_lower)
        if skipped_match:
            skipped = int(skipped_match.group(1))

        # Check for incomplete test run (no summary line)
        # If we have no test counts and non-empty output, it's incomplete
        if passed == 0 and failed == 0 and skipped == 0 and output.strip():
            # This is likely an incomplete run
            # We'll detect this by checking if output exists but no pytest summary
            if not re.search(r'\d+\s+(passed|failed|skipped)', output_lower):
                # Mark as having no valid results (will be caught by caller)
                pass

        return {
            "passed": passed,
            "failed": failed,
            "skipped": skipped
        }

    def _format_enforcement_error(self, result: VerificationResult) -> str:
        """
        Format enforcement error message.

        Args:
            result: Verification result

        Returns:
            Formatted error message
        """
        msg_parts = [
            "FOUNDATION IS BROKEN - EXECUTOR BLOCKED",
            "",
            f"Status: {result.status.value}",
            f"Exit Code: {result.exit_code}",
            f"Duration: {result.duration_seconds:.2f}s",
        ]

        if result.status == FoundationStatus.TIMEOUT:
            msg_parts.extend([
                "",
                "Constitutional Violation: Article I - Complete Context",
                f"Test suite timed out after {self.timeout_seconds}s",
                "All tests MUST run to completion before proceeding."
            ])
        elif result.status == FoundationStatus.BROKEN:
            msg_parts.extend([
                "",
                "Constitutional Violation: Article II - 100% Verification",
                f"Failed tests: {result.failed_tests}",
                f"Passed tests: {result.passed_tests}",
                "Main branch MUST maintain 100% test success."
            ])

        if result.constitutional_violations:
            msg_parts.extend([
                "",
                "Additional Violations:",
                *[f"  - {v}" for v in result.constitutional_violations]
            ])

        msg_parts.extend([
            "",
            "REQUIRED ACTION:",
            "1. Fix all failing tests",
            "2. Run full test suite locally: python run_tests.py --run-all",
            "3. Verify 100% pass rate",
            "4. Only then retry autonomous operation",
            "",
            "NO BYPASS PERMITTED (Article III: Automated Enforcement)"
        ])

        return "\n".join(msg_parts)
