"""
Test Verification Gate E2E Tests - NECESSARY Pattern Compliance

End-to-end tests for test verification gate tool (Article VI TDD enforcement).

CONSTITUTIONAL MANDATE:
- Article VI: TDD (tests before code, verification gate enforces)
- Article II: 100% verification (gate prevents merge on test failure)
- ADR-037: E2E testing for constitutional enforcement tools

NECESSARY Coverage:
- Normal: Test gate validates passing tests
- Error: Test gate blocks failing tests
- Validation: Rollback on failure
- Security: No bypass mechanisms
"""

import pytest
import subprocess
from pathlib import Path


# =============================================================================
# NORMAL OPERATION TESTS
# =============================================================================


@pytest.mark.e2e
def test_verification_gate_runs_real_pytest(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify test verification gate runs actual pytest (not mocked).

    Pattern: NECESSARY - Normal operation
    Validates: Real test execution
    """
    from tools.test_verification_gate import TestVerificationGate

    # Arrange: Create passing test
    test_file = tmp_git_repo / "tests" / "test_sample.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("""
import pytest

def test_passing():
    assert 1 + 1 == 2

def test_also_passing():
    assert "hello" == "hello"
""")

    # Act: Run verification gate
    gate = TestVerificationGate(agent_context=full_agent_context)

    result = gate.verify_tests(
        working_dir=str(tmp_git_repo),
        test_path="tests/test_sample.py"
    )

    # Assert: Tests ran successfully
    assert result.is_ok()
    verification_result = result.unwrap()

    assert verification_result.get("all_passed") is True
    assert verification_result.get("total_tests") == 2
    assert verification_result.get("passed") == 2
    assert verification_result.get("failed") == 0


@pytest.mark.e2e
def test_verification_gate_detects_failing_tests(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify test verification gate detects failing tests.

    Pattern: NECESSARY - Normal operation
    Validates: Failure detection
    """
    from tools.test_verification_gate import TestVerificationGate

    # Arrange: Create failing test
    test_file = tmp_git_repo / "tests" / "test_failing.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("""
import pytest

def test_failing():
    assert 1 + 1 == 3  # This will fail
""")

    # Act: Run verification gate
    gate = TestVerificationGate(agent_context=full_agent_context)

    result = gate.verify_tests(
        working_dir=str(tmp_git_repo),
        test_path="tests/test_failing.py"
    )

    # Assert: Failure detected
    assert result.is_err()
    error = result.error

    assert "test failed" in str(error).lower()
    assert error.get("total_tests") == 1
    assert error.get("failed") == 1


@pytest.mark.e2e
def test_verification_gate_provides_detailed_failure_output(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify test verification gate provides detailed failure information.

    Pattern: NECESSARY - Normal operation
    Validates: Debugging support
    """
    from tools.test_verification_gate import TestVerificationGate

    # Arrange: Create test with assertion error
    test_file = tmp_git_repo / "tests" / "test_detailed_failure.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("""
def test_with_clear_error():
    expected = {"key": "value"}
    actual = {"key": "wrong_value"}
    assert expected == actual, f"Expected {expected}, got {actual}"
""")

    # Act: Run verification gate
    gate = TestVerificationGate(agent_context=full_agent_context)

    result = gate.verify_tests(
        working_dir=str(tmp_git_repo),
        test_path="tests/test_detailed_failure.py"
    )

    # Assert: Detailed error provided
    assert result.is_err()
    error = result.error

    assert "Expected" in str(error) or "wrong_value" in str(error)
    assert error.get("failure_details") is not None


# =============================================================================
# VALIDATION TESTS (ARTICLE VI - TDD ENFORCEMENT)
# =============================================================================


@pytest.mark.e2e
def test_verification_gate_enforces_tdd_workflow(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify verification gate enforces TDD: tests BEFORE code (Article VI).

    Pattern: NECESSARY - Validation
    Constitutional: Article VI (TDD mandatory)
    """
    from tools.test_verification_gate import TestVerificationGate

    # Arrange: Create test file (RED phase - no implementation yet)
    test_file = tmp_git_repo / "tests" / "test_tdd_workflow.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("""
from module_under_test import calculate_total

def test_calculate_total():
    assert calculate_total([1, 2, 3]) == 6
""")

    # Act: Run verification gate (should fail - no implementation)
    gate = TestVerificationGate(agent_context=full_agent_context)

    result = gate.verify_tests(
        working_dir=str(tmp_git_repo),
        test_path="tests/test_tdd_workflow.py"
    )

    # Assert: Tests fail (RED phase validated)
    assert result.is_err()
    error = result.error
    assert "import" in str(error).lower() or "module" in str(error).lower()

    # Arrange: Now create implementation
    impl_file = tmp_git_repo / "module_under_test.py"
    impl_file.write_text("""
def calculate_total(numbers):
    return sum(numbers)
""")

    # Act: Run verification gate again (should pass - GREEN phase)
    result2 = gate.verify_tests(
        working_dir=str(tmp_git_repo),
        test_path="tests/test_tdd_workflow.py"
    )

    # Assert: Tests now pass (GREEN phase validated)
    assert result2.is_ok()
    verification_result = result2.unwrap()
    assert verification_result.get("all_passed") is True


@pytest.mark.e2e
def test_verification_gate_blocks_merge_on_failure(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify verification gate prevents merge when tests fail (Article II).

    Pattern: NECESSARY - Validation
    Constitutional: Article II (100% verification)
    """
    from tools.test_verification_gate import TestVerificationGate

    # Arrange: Create failing test
    test_file = tmp_git_repo / "tests" / "test_blocking.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("""
def test_blocking():
    assert False, "This blocks merge"
""")

    # Act: Run verification gate with merge_check=True
    gate = TestVerificationGate(agent_context=full_agent_context)

    result = gate.verify_tests(
        working_dir=str(tmp_git_repo),
        test_path="tests/test_blocking.py",
        merge_check=True
    )

    # Assert: Merge blocked
    assert result.is_err()
    error = result.error

    assert error.get("merge_blocked") is True
    assert "cannot merge" in str(error).lower() or "blocked" in str(error).lower()


# =============================================================================
# ERROR CONDITION TESTS
# =============================================================================


@pytest.mark.e2e
def test_verification_gate_rollback_on_failure(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify verification gate triggers rollback when tests fail.

    Pattern: NECESSARY - Error condition
    Validates: Failure recovery
    """
    from tools.test_verification_gate import TestVerificationGate
    import subprocess

    # Arrange: Create initial working state
    impl_file = tmp_git_repo / "calculator.py"
    impl_file.write_text("""
def add(a, b):
    return a + b
""")

    test_file = tmp_git_repo / "tests" / "test_calculator.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("""
from calculator import add

def test_add():
    assert add(2, 3) == 5
""")

    # Commit initial state
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo)
    subprocess.run(["git", "commit", "-m", "Initial state"], cwd=tmp_git_repo)

    # Act: Break implementation
    impl_file.write_text("""
def add(a, b):
    return a - b  # BROKEN: subtracts instead of adds
""")

    # Act: Run verification gate with rollback enabled
    gate = TestVerificationGate(agent_context=full_agent_context)

    result = gate.verify_tests(
        working_dir=str(tmp_git_repo),
        test_path="tests/test_calculator.py",
        rollback_on_failure=True
    )

    # Assert: Tests failed and rollback triggered
    assert result.is_err()
    error = result.error
    assert error.get("rollback_completed") is True

    # Assert: Implementation restored to working state
    restored_content = impl_file.read_text()
    assert "return a + b" in restored_content
    assert "return a - b" not in restored_content


@pytest.mark.e2e
def test_verification_gate_handles_pytest_crash(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify verification gate handles pytest crashes gracefully.

    Pattern: NECESSARY - Error condition
    Validates: Crash handling
    """
    from tools.test_verification_gate import TestVerificationGate

    # Arrange: Create test that crashes pytest
    test_file = tmp_git_repo / "tests" / "test_crash.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("""
import sys

def test_crash():
    sys.exit(1)  # Force crash
""")

    # Act: Run verification gate
    gate = TestVerificationGate(agent_context=full_agent_context)

    result = gate.verify_tests(
        working_dir=str(tmp_git_repo),
        test_path="tests/test_crash.py"
    )

    # Assert: Crash detected and reported
    assert result.is_err()
    error = result.error
    assert "crash" in str(error).lower() or "exit" in str(error).lower()


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


@pytest.mark.e2e
def test_verification_gate_handles_empty_test_suite(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify verification gate handles empty test directory.

    Pattern: NECESSARY - Edge case
    Validates: Empty input handling
    """
    from tools.test_verification_gate import TestVerificationGate

    # Arrange: Create empty test directory
    test_dir = tmp_git_repo / "tests"
    test_dir.mkdir(exist_ok=True)

    # Act: Run verification gate
    gate = TestVerificationGate(agent_context=full_agent_context)

    result = gate.verify_tests(
        working_dir=str(tmp_git_repo),
        test_path="tests/"
    )

    # Assert: Empty test suite handled
    # Could either error (no tests found) or succeed (nothing to fail)
    if result.is_err():
        error = result.error
        assert "no tests" in str(error).lower() or "empty" in str(error).lower()
    else:
        verification_result = result.unwrap()
        assert verification_result.get("total_tests") == 0


@pytest.mark.e2e
def test_verification_gate_handles_skipped_tests(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify verification gate handles skipped tests correctly.

    Pattern: NECESSARY - Edge case
    Validates: Skip handling
    """
    from tools.test_verification_gate import TestVerificationGate

    # Arrange: Create test with skips
    test_file = tmp_git_repo / "tests" / "test_skipped.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("""
import pytest

def test_passing():
    assert True

@pytest.mark.skip(reason="Not implemented yet")
def test_skipped():
    assert False
""")

    # Act: Run verification gate
    gate = TestVerificationGate(agent_context=full_agent_context)

    result = gate.verify_tests(
        working_dir=str(tmp_git_repo),
        test_path="tests/test_skipped.py"
    )

    # Assert: Skipped tests don't cause failure
    assert result.is_ok()
    verification_result = result.unwrap()

    assert verification_result.get("passed") >= 1
    assert verification_result.get("skipped") >= 1


# =============================================================================
# SECURITY TESTS
# =============================================================================


@pytest.mark.e2e
def test_verification_gate_no_bypass_mechanism(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify verification gate cannot be bypassed (Article III).

    Pattern: NECESSARY - Security
    Constitutional: Article III (no manual overrides)
    """
    from tools.test_verification_gate import TestVerificationGate

    # Arrange: Failing test
    test_file = tmp_git_repo / "tests" / "test_no_bypass.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("""
def test_must_fail():
    assert False
""")

    # Act: Try to run with bypass flags (should be ignored)
    gate = TestVerificationGate(agent_context=full_agent_context)

    result = gate.verify_tests(
        working_dir=str(tmp_git_repo),
        test_path="tests/test_no_bypass.py",
        allow_bypass=True  # This flag should NOT exist or be ignored
    )

    # Assert: Bypass not allowed, test still fails
    assert result.is_err()


# =============================================================================
# STRESS TESTS
# =============================================================================


@pytest.mark.e2e
@pytest.mark.slow
def test_verification_gate_handles_large_test_suite(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify verification gate handles large test suites efficiently.

    Pattern: NECESSARY - Stress
    Validates: Performance with realistic test counts
    """
    from tools.test_verification_gate import TestVerificationGate

    # Arrange: Create 100 test files
    for i in range(100):
        test_file = tmp_git_repo / "tests" / f"test_large_{i}.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(f"""
def test_{i}_a():
    assert True

def test_{i}_b():
    assert True
""")

    # Act: Run verification gate on all tests
    gate = TestVerificationGate(agent_context=full_agent_context)

    result = gate.verify_tests(
        working_dir=str(tmp_git_repo),
        test_path="tests/"
    )

    # Assert: All tests executed
    assert result.is_ok()
    verification_result = result.unwrap()

    assert verification_result.get("total_tests") == 200  # 100 files * 2 tests
    assert verification_result.get("all_passed") is True


# =============================================================================
# REGRESSION TESTS
# =============================================================================


@pytest.mark.e2e
def test_verification_gate_maintains_git_state(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify verification gate doesn't modify git state unexpectedly.

    Pattern: NECESSARY - Regression
    Validates: Git state preservation
    """
    from tools.test_verification_gate import TestVerificationGate
    import subprocess

    # Arrange: Create clean git state
    test_file = tmp_git_repo / "tests" / "test_git_state.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("""
def test_example():
    assert True
""")

    subprocess.run(["git", "add", "."], cwd=tmp_git_repo)
    subprocess.run(["git", "commit", "-m", "Test commit"], cwd=tmp_git_repo)

    # Get current git hash
    git_hash_before = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True
    ).stdout.strip()

    # Act: Run verification gate
    gate = TestVerificationGate(agent_context=full_agent_context)

    result = gate.verify_tests(
        working_dir=str(tmp_git_repo),
        test_path="tests/test_git_state.py"
    )

    # Assert: Git state unchanged
    git_hash_after = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True
    ).stdout.strip()

    assert git_hash_before == git_hash_after
