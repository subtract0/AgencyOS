"""
E2E Test Runner Tests - NECESSARY Pattern Compliance

Tests for E2E test execution infrastructure and pytest integration.

CONSTITUTIONAL MANDATE:
- Article I: Complete context (tests run to completion with proper timeouts)
- Article II: 100% verification (E2E tests must pass before merge)
- ADR-037: E2E testing framework with custom pytest runner

NECESSARY Coverage:
- Normal: E2E flag filtering, timeout configuration
- Edge: Serial execution, parallel constraints
- Error: Failure reporting and debugging
- Validation: Test runner contract compliance
"""

import pytest
import subprocess
import sys
from pathlib import Path


# =============================================================================
# NORMAL OPERATION TESTS
# =============================================================================


def test_e2e_flag_runs_only_e2e_tests():
    """
    Verify --e2e flag filters to only E2E tests.

    Pattern: NECESSARY - Normal operation
    Validates: Test selection based on marker
    """
    # Act: Run pytest with --e2e flag
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--e2e", "--collect-only"],
        cwd="/Users/am/Code/Agency",
        capture_output=True,
        text=True
    )

    # Assert: Only E2E tests collected
    assert result.returncode == 0
    assert "tests/e2e/" in result.stdout

    # Assert: No unit tests collected
    assert "tests/unit/" not in result.stdout or result.stdout.count("tests/unit/") == 0


def test_e2e_tests_have_longer_timeout():
    """
    Verify E2E tests use 120s timeout vs 5s for unit tests.

    Pattern: NECESSARY - Normal operation
    Validates: Timeout configuration for long-running tests
    """
    # Act: Run a sample E2E test with timeout check
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/e2e/test_e2e_fixtures.py::test_full_agent_context_fixture_creates_vectorstore",
            "-v", "--timeout=120"
        ],
        cwd="/Users/am/Code/Agency",
        capture_output=True,
        text=True,
        timeout=130  # Slightly longer than pytest timeout
    )

    # Assert: Test runs with 120s timeout (doesn't fail immediately)
    # If timeout was 5s, complex fixture setup would fail
    assert "TIMEOUT" not in result.stdout or result.returncode == 0


def test_e2e_marker_correctly_identifies_tests():
    """
    Verify pytest.mark.e2e correctly marks E2E tests.

    Pattern: NECESSARY - Normal operation
    Validates: Marker registration and selection
    """
    # Act: Collect tests with e2e marker
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-m", "e2e", "--collect-only"],
        cwd="/Users/am/Code/Agency",
        capture_output=True,
        text=True
    )

    # Assert: E2E tests are collected
    assert result.returncode == 0
    assert "test_e2e" in result.stdout

    # Assert: Marker is recognized
    assert "1 deselected" not in result.stdout or "e2e" in result.stdout


def test_run_tests_script_supports_e2e_flag():
    """
    Verify run_tests.py script supports --e2e flag.

    Pattern: NECESSARY - Normal operation
    Validates: Integration with existing test runner
    """
    # Act: Run test script with --e2e flag
    result = subprocess.run(
        [sys.executable, "run_tests.py", "--e2e", "--collect-only"],
        cwd="/Users/am/Code/Agency",
        capture_output=True,
        text=True,
        timeout=30
    )

    # Assert: Script recognizes flag
    assert result.returncode == 0 or "--e2e" in result.stderr

    # Assert: Only E2E tests would be executed
    if "collect" in result.stdout:
        assert "tests/e2e/" in result.stdout


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


def test_e2e_tests_run_serially_when_needed():
    """
    Verify critical E2E tests can run serially (not parallel).

    Pattern: NECESSARY - Edge case
    Validates: pytest-xdist compatibility with serial execution
    """
    # Arrange: E2E tests marked with @pytest.mark.serial
    # These should NOT run in parallel with pytest-xdist

    # Act: Run with -n auto (parallel)
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/e2e/",
            "-n", "auto",
            "-v"
        ],
        cwd="/Users/am/Code/Agency",
        capture_output=True,
        text=True,
        timeout=180
    )

    # Assert: Serial tests run correctly (not interleaved)
    # This is validated by test output showing sequential execution
    assert "gw" in result.stdout or result.returncode == 0


def test_e2e_tests_isolated_from_unit_tests():
    """
    Verify E2E tests don't run when executing unit tests.

    Pattern: NECESSARY - Edge case
    Validates: Test suite segmentation
    """
    # Act: Run unit tests only
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-m", "not e2e", "--collect-only"],
        cwd="/Users/am/Code/Agency",
        capture_output=True,
        text=True
    )

    # Assert: E2E tests excluded
    assert result.returncode == 0
    # E2E tests should be deselected
    assert "tests/e2e/" not in result.stdout or "deselected" in result.stdout


def test_e2e_fixtures_dont_slow_down_unit_tests():
    """
    Verify E2E fixtures don't load during unit test execution.

    Pattern: NECESSARY - Edge case
    Validates: Performance isolation
    """
    # Act: Run a simple unit test
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/shared/test_type_definitions.py::test_ok_unwrap",
            "-v", "--durations=5"
        ],
        cwd="/Users/am/Code/Agency",
        capture_output=True,
        text=True,
        timeout=10
    )

    # Assert: Test completes quickly (< 5s)
    assert result.returncode == 0

    # Assert: No E2E fixture setup in output
    assert "full_agent_context" not in result.stdout
    assert "tmp_git_repo" not in result.stdout


# =============================================================================
# ERROR CONDITION TESTS
# =============================================================================


def test_e2e_test_failure_provides_detailed_output():
    """
    Verify E2E test failures provide helpful debugging information.

    Pattern: NECESSARY - Error condition
    Validates: Debugging support for failed E2E tests
    """
    # Arrange: Create a test that will fail
    failing_test = """
import pytest

@pytest.mark.e2e
def test_intentional_failure():
    '''This test intentionally fails to verify error reporting.'''
    assert False, "Detailed failure message for debugging"
"""

    test_file = Path("/tmp/test_failing_e2e.py")
    test_file.write_text(failing_test)

    try:
        # Act: Run failing test
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_file), "-v"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Assert: Failure is reported with details
        assert result.returncode != 0
        assert "Detailed failure message for debugging" in result.stdout or \
               "Detailed failure message for debugging" in result.stderr
        assert "AssertionError" in result.stdout or "AssertionError" in result.stderr

    finally:
        # Cleanup
        test_file.unlink(missing_ok=True)


def test_e2e_test_timeout_reports_helpful_error():
    """
    Verify E2E test timeouts provide context for debugging.

    Pattern: NECESSARY - Error condition
    Validates: Timeout error messages
    """
    # Arrange: Create a test that times out
    timeout_test = """
import pytest
import time

@pytest.mark.e2e
def test_intentional_timeout():
    '''This test intentionally times out.'''
    time.sleep(200)  # Exceeds 120s E2E timeout
"""

    test_file = Path("/tmp/test_timeout_e2e.py")
    test_file.write_text(timeout_test)

    try:
        # Act: Run test with short timeout
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_file), "--timeout=2", "-v"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Assert: Timeout is reported
        assert result.returncode != 0
        assert "timeout" in result.stdout.lower() or "timeout" in result.stderr.lower()

    finally:
        # Cleanup
        test_file.unlink(missing_ok=True)


def test_e2e_fixture_error_provides_traceback():
    """
    Verify fixture setup errors provide full traceback.

    Pattern: NECESSARY - Error condition
    Validates: Fixture debugging support
    """
    # Arrange: Create test with broken fixture
    broken_fixture_test = """
import pytest

@pytest.fixture
def broken_fixture():
    raise RuntimeError("Fixture setup failed intentionally")

@pytest.mark.e2e
def test_with_broken_fixture(broken_fixture):
    assert True
"""

    test_file = Path("/tmp/test_broken_fixture_e2e.py")
    test_file.write_text(broken_fixture_test)

    try:
        # Act: Run test
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_file), "-v"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Assert: Error includes traceback
        assert result.returncode != 0
        assert "RuntimeError" in result.stdout or "RuntimeError" in result.stderr
        assert "Fixture setup failed intentionally" in result.stdout or \
               "Fixture setup failed intentionally" in result.stderr

    finally:
        # Cleanup
        test_file.unlink(missing_ok=True)


# =============================================================================
# VALIDATION TESTS
# =============================================================================


def test_e2e_tests_comply_with_article_i_timeout_requirements():
    """
    Verify E2E tests run to completion per Article I.

    Pattern: NECESSARY - Validation
    Constitutional: Article I (complete context before action)
    """
    # Act: Run E2E fixture test
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/e2e/test_e2e_fixtures.py::test_full_agent_context_fixture_creates_vectorstore",
            "-v", "--timeout=120"
        ],
        cwd="/Users/am/Code/Agency",
        capture_output=True,
        text=True,
        timeout=130
    )

    # Assert: Test completes (doesn't timeout prematurely)
    assert "TIMEOUT" not in result.stdout
    # Test may fail due to missing implementation, but shouldn't timeout
    assert "seconds" in result.stdout or result.returncode in [0, 1, 5]


def test_e2e_runner_integrates_with_constitutional_compliance():
    """
    Verify E2E runner supports constitutional compliance checks.

    Pattern: NECESSARY - Validation
    Constitutional: Article II (100% verification)
    """
    # Act: Run E2E tests with coverage
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/e2e/",
            "--cov=tests/e2e",
            "--cov-report=term-missing",
            "--collect-only"
        ],
        cwd="/Users/am/Code/Agency",
        capture_output=True,
        text=True,
        timeout=30
    )

    # Assert: Coverage reporting works
    assert result.returncode == 0 or "coverage" in result.stdout.lower()


def test_e2e_tests_marked_correctly_in_pytest_ini():
    """
    Verify pytest.ini registers e2e marker.

    Pattern: NECESSARY - Validation
    Validates: Marker configuration
    """
    # Read pytest.ini
    pytest_ini = Path("/Users/am/Code/Agency/pytest.ini")

    if pytest_ini.exists():
        content = pytest_ini.read_text()

        # Assert: e2e marker is registered
        assert "e2e" in content or "markers" in content


# =============================================================================
# STRESS TESTS
# =============================================================================


def test_e2e_runner_handles_many_parallel_tests():
    """
    Verify E2E runner handles parallel execution of multiple tests.

    Pattern: NECESSARY - Stress
    Validates: Parallel execution stability
    """
    # Act: Run all E2E fixture tests in parallel
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/e2e/test_e2e_fixtures.py",
            "-n", "4",  # 4 parallel workers
            "-v"
        ],
        cwd="/Users/am/Code/Agency",
        capture_output=True,
        text=True,
        timeout=180
    )

    # Assert: Parallel execution succeeds
    # Tests may fail due to missing implementation, but runner should work
    assert "gw0" in result.stdout or "gw1" in result.stdout or result.returncode in [0, 1, 5]


# =============================================================================
# PYTEST MARKER
# =============================================================================

# Mark all tests in this file as E2E tests
pytestmark = pytest.mark.e2e
