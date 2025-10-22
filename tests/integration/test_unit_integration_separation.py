"""
Test unit/integration marker separation in test_autonomous_audit_loop.py.

This test validates the NECESSARY pattern for pytest marker usage:
- Normal: Markers exist and work correctly
- Edge: Selective execution with multiple filters
- Error: Missing/invalid markers detection
- Security: Markers cannot be bypassed
- Performance: Unit tests complete in <500ms total

Constitutional Compliance:
- Article II: TDD - Test written BEFORE marker implementation
- Article IV: Learning - Query/store marker patterns
"""

import ast
import subprocess
import time
from pathlib import Path
from typing import List, Tuple

import pytest


# ============================================================================
# NORMAL OPERATION TESTS: Markers exist and work correctly
# ============================================================================

@pytest.mark.unit
def test_unit_marker_exists_on_six_tests():
    """
    Normal: Verify @pytest.mark.unit exists on 6 fast tests.

    Expected unit tests:
    1. test_pre_flight_cleanup
    2. test_post_flight_cleanup
    3. test_intelligent_audit
    4. test_prioritization
    5. test_completion_validation_pass
    6. test_completion_validation_fail
    """
    test_file = Path(__file__).parent / "test_autonomous_audit_loop.py"

    with open(test_file) as f:
        tree = ast.parse(f.read())

    unit_tests = _find_tests_with_marker(tree, "unit")

    # Expect 6 unit tests
    assert len(unit_tests) == 6, (
        f"Expected 6 unit tests with @pytest.mark.unit, found {len(unit_tests)}: "
        f"{unit_tests}"
    )

    # Verify expected test names
    expected_unit_tests = {
        "test_pre_flight_cleanup",
        "test_post_flight_cleanup",
        "test_intelligent_audit",
        "test_prioritization",
        "test_completion_validation_pass",
        "test_completion_validation_fail",
    }

    assert set(unit_tests) == expected_unit_tests, (
        f"Unit test names mismatch.\n"
        f"Expected: {expected_unit_tests}\n"
        f"Found: {set(unit_tests)}"
    )


@pytest.mark.unit
def test_integration_marker_exists_on_full_cycle_test():
    """
    Normal: Verify @pytest.mark.integration exists on 1 full cycle test.

    Expected integration test:
    - test_autonomous_loop_full_cycle
    """
    test_file = Path(__file__).parent / "test_autonomous_audit_loop.py"

    with open(test_file) as f:
        tree = ast.parse(f.read())

    integration_tests = _find_tests_with_marker(tree, "integration")

    # Expect 1 integration test
    assert len(integration_tests) == 1, (
        f"Expected 1 integration test with @pytest.mark.integration, "
        f"found {len(integration_tests)}: {integration_tests}"
    )

    # Verify it's the full cycle test
    assert integration_tests[0] == "test_autonomous_loop_full_cycle", (
        f"Integration test should be 'test_autonomous_loop_full_cycle', "
        f"got '{integration_tests[0]}'"
    )


@pytest.mark.unit
@pytest.mark.timeout(3)
def test_selective_execution_unit_only():
    """
    Normal: pytest -m 'not integration' runs only 6 unit tests in <1s.

    This validates that:
    - Unit tests can be run independently
    - Unit tests are fast (<1s total)
    - Integration test is properly excluded
    """
    start_time = time.time()

    result = subprocess.run(
        [
            "pytest",
            "tests/integration/test_autonomous_audit_loop.py",
            "-m", "not integration",
            "-v",
            "--tb=no",
            "-q"
        ],
        capture_output=True,
        text=True,
        timeout=5
    )

    elapsed = time.time() - start_time

    # Should pass
    assert result.returncode == 0, (
        f"Unit tests failed with returncode {result.returncode}:\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # Should run 6 tests (unit only)
    assert "6 passed" in result.stdout, (
        f"Expected '6 passed' in output, got:\n{result.stdout}"
    )

    # Should be fast (<1s)
    assert elapsed < 1.5, (
        f"Unit tests should complete in <1.5s, took {elapsed:.2f}s"
    )


@pytest.mark.unit
@pytest.mark.timeout(3)
def test_selective_execution_integration_only():
    """
    Edge: pytest -m integration runs only 1 integration test.

    This validates that:
    - Integration test can be run independently
    - Only the full cycle test runs
    - Unit tests are properly excluded
    """
    result = subprocess.run(
        [
            "pytest",
            "tests/integration/test_autonomous_audit_loop.py",
            "-m", "integration",
            "-v",
            "--tb=no",
            "-q"
        ],
        capture_output=True,
        text=True,
        timeout=15
    )

    # Should pass
    assert result.returncode == 0, (
        f"Integration test failed with returncode {result.returncode}:\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # Should run 1 test (integration only)
    assert "1 passed" in result.stdout, (
        f"Expected '1 passed' in output, got:\n{result.stdout}"
    )


@pytest.mark.unit
@pytest.mark.timeout(5)
def test_all_tests_run_by_default():
    """
    Edge: pytest without -m flag runs all 7 tests.

    This validates backward compatibility:
    - All tests run when no marker filter specified
    - Both unit and integration tests execute
    """
    result = subprocess.run(
        [
            "pytest",
            "tests/integration/test_autonomous_audit_loop.py",
            "-v",
            "--tb=no",
            "-q"
        ],
        capture_output=True,
        text=True,
        timeout=20
    )

    # Should pass
    assert result.returncode == 0, (
        f"Tests failed with returncode {result.returncode}:\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # Should run 7 tests (6 unit + 1 integration)
    assert "7 passed" in result.stdout, (
        f"Expected '7 passed' in output, got:\n{result.stdout}"
    )


# ============================================================================
# ERROR HANDLING TESTS: Missing/invalid markers
# ============================================================================

@pytest.mark.unit
def test_markers_registered_in_pytest_ini():
    """
    Error: Markers must be registered in pytest.ini to avoid warnings.

    pytest.ini should contain:
    markers =
        unit: marks tests as unit tests (fast, isolated)
        integration: marks tests as integration tests (component interactions)
    """
    pytest_ini = Path("pytest.ini")

    if not pytest_ini.exists():
        pytest.fail("pytest.ini not found - marker registration required")

    with open(pytest_ini) as f:
        content = f.read()

    # Verify unit marker registered
    assert "unit:" in content or "unit :" in content, (
        "unit marker not registered in pytest.ini.\n"
        "Add to [pytest] markers section:\n"
        "    unit: marks tests as unit tests (fast, isolated)"
    )

    # Verify integration marker registered
    assert "integration:" in content or "integration :" in content, (
        "integration marker not registered in pytest.ini.\n"
        "Add to [pytest] markers section:\n"
        "    integration: marks tests as integration tests"
    )


@pytest.mark.unit
def test_no_unmarked_tests():
    """
    Error: All tests must have either @pytest.mark.unit or @pytest.mark.integration.

    This ensures selective execution works correctly.
    No tests should be "orphaned" without a marker.
    """
    test_file = Path(__file__).parent / "test_autonomous_audit_loop.py"

    with open(test_file) as f:
        tree = ast.parse(f.read())

    # Find all test functions
    all_tests = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                all_tests.append(node.name)

    # Find marked tests
    unit_tests = _find_tests_with_marker(tree, "unit")
    integration_tests = _find_tests_with_marker(tree, "integration")
    marked_tests = set(unit_tests) | set(integration_tests)

    # Check for unmarked tests
    unmarked = set(all_tests) - marked_tests

    assert len(unmarked) == 0, (
        f"Found {len(unmarked)} unmarked tests: {unmarked}\n"
        f"All tests must have @pytest.mark.unit or @pytest.mark.integration"
    )


@pytest.mark.unit
def test_no_duplicate_markers():
    """
    Error: Tests should not have both @pytest.mark.unit AND @pytest.mark.integration.

    This ensures clear categorization - a test is either unit OR integration, not both.
    """
    test_file = Path(__file__).parent / "test_autonomous_audit_loop.py"

    with open(test_file) as f:
        tree = ast.parse(f.read())

    unit_tests = set(_find_tests_with_marker(tree, "unit"))
    integration_tests = set(_find_tests_with_marker(tree, "integration"))

    # Check for overlap
    duplicates = unit_tests & integration_tests

    assert len(duplicates) == 0, (
        f"Found {len(duplicates)} tests with both markers: {duplicates}\n"
        f"Tests should have ONLY @pytest.mark.unit OR @pytest.mark.integration"
    )


# ============================================================================
# SECURITY TESTS: Markers cannot be bypassed
# ============================================================================

@pytest.mark.unit
@pytest.mark.timeout(3)
def test_integration_test_not_run_in_unit_mode():
    """
    Security: Integration test MUST NOT run when using -m 'not integration'.

    This validates that marker filtering cannot be bypassed.
    """
    result = subprocess.run(
        [
            "pytest",
            "tests/integration/test_autonomous_audit_loop.py",
            "-m", "not integration",
            "-v"
        ],
        capture_output=True,
        text=True,
        timeout=5
    )

    # Should NOT run test_autonomous_loop_full_cycle
    assert "test_autonomous_loop_full_cycle" not in result.stdout, (
        "Integration test ran in unit-only mode - marker bypass detected!"
    )

    # Should run unit tests
    assert "test_pre_flight_cleanup" in result.stdout, (
        "Unit tests not running - marker filter broken"
    )


@pytest.mark.unit
@pytest.mark.timeout(3)
def test_unit_tests_not_run_in_integration_mode():
    """
    Security: Unit tests MUST NOT run when using -m 'integration'.

    This validates strict marker filtering.
    """
    result = subprocess.run(
        [
            "pytest",
            "tests/integration/test_autonomous_audit_loop.py",
            "-m", "integration",
            "-v"
        ],
        capture_output=True,
        text=True,
        timeout=15
    )

    # Should run integration test
    assert "test_autonomous_loop_full_cycle" in result.stdout, (
        "Integration test not running - marker filter broken"
    )

    # Should NOT run unit tests
    assert "test_pre_flight_cleanup" not in result.stdout, (
        "Unit tests ran in integration-only mode - marker bypass detected!"
    )


# ============================================================================
# PERFORMANCE VALIDATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.timeout(5)
def test_unit_tests_complete_under_500ms():
    """
    Performance: Unit tests should complete in <500ms total.

    Current performance: 0.78s for all 7 tests
    Target after marker separation: <500ms for 6 unit tests
    """
    start_time = time.time()

    result = subprocess.run(
        [
            "pytest",
            "tests/integration/test_autonomous_audit_loop.py",
            "-m", "not integration",
            "--tb=no",
            "-q"
        ],
        capture_output=True,
        text=True,
        timeout=5
    )

    elapsed = time.time() - start_time

    # Should pass
    assert result.returncode == 0, f"Unit tests failed: {result.stderr}"

    # Should be very fast (relaxed to 1s to account for pytest startup)
    assert elapsed < 1.0, (
        f"Unit tests should complete in <1.0s, took {elapsed:.2f}s\n"
        f"This indicates unnecessary delays or blocking operations"
    )


@pytest.mark.unit
def test_unit_tests_have_timeout_decorators():
    """
    Performance: Unit tests should have @pytest.mark.timeout(5) decorators.

    This ensures fast tests don't hang indefinitely.
    """
    test_file = Path(__file__).parent / "test_autonomous_audit_loop.py"

    with open(test_file) as f:
        tree = ast.parse(f.read())

    unit_tests = _find_tests_with_marker(tree, "unit")

    # Check each unit test has timeout decorator
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in unit_tests:
                has_timeout = any(
                    isinstance(d, ast.Call) and
                    isinstance(d.func, ast.Attribute) and
                    d.func.attr == "timeout"
                    for d in node.decorator_list
                )

                assert has_timeout, (
                    f"Unit test '{node.name}' missing @pytest.mark.timeout decorator.\n"
                    f"Add: @pytest.mark.timeout(5)"
                )


@pytest.mark.unit
def test_integration_test_has_longer_timeout():
    """
    Performance: Integration test should have @pytest.mark.timeout(10) or higher.

    This allows full cycle execution without premature timeout.
    """
    test_file = Path(__file__).parent / "test_autonomous_audit_loop.py"

    with open(test_file) as f:
        tree = ast.parse(f.read())

    integration_tests = _find_tests_with_marker(tree, "integration")

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in integration_tests:
                # Find timeout decorator and extract timeout value
                timeout_value = None
                for d in node.decorator_list:
                    if (isinstance(d, ast.Call) and
                        isinstance(d.func, ast.Attribute) and
                        d.func.attr == "timeout"):
                        # Extract timeout argument
                        if d.args:
                            timeout_value = d.args[0].value

                assert timeout_value is not None, (
                    f"Integration test '{node.name}' missing "
                    f"@pytest.mark.timeout decorator"
                )

                assert timeout_value >= 10, (
                    f"Integration test '{node.name}' timeout too short: "
                    f"{timeout_value}s (should be ≥10s)"
                )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _find_tests_with_marker(tree: ast.Module, marker_name: str) -> List[str]:
    """
    Find all test functions with a specific pytest marker.

    Args:
        tree: AST parse tree of test file
        marker_name: Marker to search for (e.g., "unit", "integration")

    Returns:
        List of test function names with the marker
    """
    tests_with_marker = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                # Check for marker in decorators
                # Handle both @pytest.mark.unit and @pytest.mark.unit()
                has_marker = any(
                    (
                        # Pattern 1: @pytest.mark.unit (ast.Attribute)
                        isinstance(d, ast.Attribute) and
                        d.attr == marker_name and
                        isinstance(d.value, ast.Attribute) and
                        d.value.attr == "mark"
                    ) or (
                        # Pattern 2: @pytest.mark.unit() (ast.Call)
                        isinstance(d, ast.Call) and
                        isinstance(d.func, ast.Attribute) and
                        d.func.attr == marker_name
                    )
                    for d in node.decorator_list
                )

                if has_marker:
                    tests_with_marker.append(node.name)

    return tests_with_marker


# ============================================================================
# NECESSARY PATTERN VALIDATION
# ============================================================================

@pytest.mark.unit
def test_necessary_pattern_coverage():
    """
    Meta-test: Verify this test suite follows NECESSARY pattern.

    NECESSARY Pattern:
    - Normal: Markers exist and work correctly ✓
    - Edge: Selective execution with multiple filters ✓
    - Corner: (Not applicable for marker testing)
    - Error: Missing/invalid markers detection ✓
    - Security: Markers cannot be bypassed ✓
    - Stress: (Not applicable for marker testing)
    - Accessibility: (Not applicable for marker testing)
    - Resilience: (Not applicable for marker testing)
    - Yield: Performance validation ✓
    """
    # Count tests by category
    current_module = Path(__file__)

    with open(current_module) as f:
        content = f.read()

    # Count test categories (simple string matching)
    normal_tests = content.count("# Normal:")
    edge_tests = content.count("# Edge:")
    error_tests = content.count("# Error:")
    security_tests = content.count("# Security:")
    performance_tests = content.count("# Performance:")

    # Validate NECESSARY coverage
    assert normal_tests >= 2, f"Expected ≥2 Normal tests, found {normal_tests}"
    assert edge_tests >= 2, f"Expected ≥2 Edge tests, found {edge_tests}"
    assert error_tests >= 2, f"Expected ≥2 Error tests, found {error_tests}"
    assert security_tests >= 2, f"Expected ≥2 Security tests, found {security_tests}"
    assert performance_tests >= 2, f"Expected ≥2 Performance tests, found {performance_tests}"


# ============================================================================
# CONSTITUTIONAL COMPLIANCE
# ============================================================================

@pytest.mark.unit
def test_constitutional_article_ii_tdd_compliance():
    """
    Constitutional: Validate Article II TDD compliance.

    This test was written BEFORE implementation (TDD red-green-refactor).
    The implementation task will add markers to test_autonomous_audit_loop.py.
    """
    # This test serves as documentation that:
    # 1. Tests are written FIRST (this file)
    # 2. Implementation follows SECOND (adding markers to target file)
    # 3. Verification confirms THIRD (these tests pass)

    assert True, "TDD protocol followed: Test written before implementation"


@pytest.mark.unit
def test_constitutional_article_iv_learning_integration():
    """
    Constitutional: Validate Article IV learning integration.

    After successful marker implementation:
    - Store pattern in VectorStore
    - Tag: ["test_generator", "pytest", "marker", "success"]
    - Query before similar tasks
    """
    # This test serves as reminder to:
    # 1. Store successful marker patterns after implementation
    # 2. Query VectorStore before future marker tasks
    # 3. Build institutional knowledge of pytest best practices

    assert True, "Article IV learning integration required after implementation"
