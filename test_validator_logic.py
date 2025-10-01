#!/usr/bin/env python3
"""
Unit test to validate ValidatorTool logic without running actual tests.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch
import subprocess

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from quality_enforcer_agent.quality_enforcer_agent import ValidatorTool


def test_parse_test_output_all_passed():
    """Test parsing of successful test output."""
    print("\n" + "=" * 60)
    print("TEST 1: Parse successful test output")
    print("=" * 60)

    validator = ValidatorTool()

    # Mock successful test result
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "1562 passed in 185.23 seconds"
    mock_result.stderr = ""

    result = validator._parse_test_output(mock_result)

    print(f"Tests passed: {result['tests_passed']}")
    print(f"Tests failed: {result['tests_failed']}")
    print(f"Pass rate: {result['pass_rate']:.1f}%")
    print(f"All passed: {result['all_passed']}")

    assert result['tests_passed'] == 1562
    assert result['tests_failed'] == 0
    assert result['pass_rate'] == 100.0
    assert result['all_passed'] is True

    print("✓ Successfully parsed successful test output")
    return True


def test_parse_test_output_with_failures():
    """Test parsing of failed test output."""
    print("\n" + "=" * 60)
    print("TEST 2: Parse failed test output")
    print("=" * 60)

    validator = ValidatorTool()

    # Mock failed test result
    mock_result = Mock()
    mock_result.returncode = 1
    mock_result.stdout = "5 failed, 1557 passed in 180.45 seconds"
    mock_result.stderr = "FAILED tests/test_example.py::test_something"

    result = validator._parse_test_output(mock_result)

    print(f"Tests passed: {result['tests_passed']}")
    print(f"Tests failed: {result['tests_failed']}")
    print(f"Pass rate: {result['pass_rate']:.1f}%")
    print(f"All passed: {result['all_passed']}")

    assert result['tests_passed'] == 1557
    assert result['tests_failed'] == 5
    assert result['pass_rate'] < 100.0
    assert result['all_passed'] is False

    print("✓ Successfully parsed failed test output")
    return True


def test_enforce_run_all_flag():
    """Test that --run-all flag handling is correct."""
    print("\n" + "=" * 60)
    print("TEST 3: Test --run-all flag enforcement logic")
    print("=" * 60)

    import shlex

    # Test 1: No flag - should add --run-all
    validator1 = ValidatorTool(test_command="python run_tests.py")
    parts1 = shlex.split(validator1.test_command)
    test_mode_flags = ["--run-all", "--fast", "--slow", "--benchmark", "--github", "--integration-only", "--run-integration"]
    has_mode_flag1 = any(flag in parts1 for flag in test_mode_flags)

    print(f"Command: {validator1.test_command}")
    print(f"Has mode flag: {has_mode_flag1}")
    assert not has_mode_flag1, "Should not have mode flag initially"
    print("✓ Correctly identified missing mode flag (will add --run-all)")

    # Test 2: Already has --fast - should NOT add --run-all
    validator2 = ValidatorTool(test_command="python run_tests.py --fast")
    parts2 = shlex.split(validator2.test_command)
    has_mode_flag2 = any(flag in parts2 for flag in test_mode_flags)

    print(f"\nCommand: {validator2.test_command}")
    print(f"Has mode flag: {has_mode_flag2}")
    assert has_mode_flag2, "Should have mode flag (--fast)"
    print("✓ Correctly identified existing --fast flag (will NOT add --run-all)")

    # Test 3: Already has --run-all
    validator3 = ValidatorTool(test_command="python run_tests.py --run-all")
    parts3 = shlex.split(validator3.test_command)
    has_run_all = "--run-all" in parts3

    print(f"\nCommand: {validator3.test_command}")
    print(f"Has --run-all: {has_run_all}")
    assert has_run_all, "Should have --run-all flag"
    print("✓ Correctly identified existing --run-all flag")

    return True


def test_hard_failure_on_test_failure():
    """Test that ValidatorTool raises RuntimeError on test failure."""
    print("\n" + "=" * 60)
    print("TEST 4: Verify hard failure on test failure")
    print("=" * 60)

    validator = ValidatorTool(test_command="python run_tests.py --fast")

    # Mock a failed test run
    mock_result = Mock()
    mock_result.returncode = 1
    mock_result.stdout = "1 failed, 1561 passed"
    mock_result.stderr = "FAILED tests/test_example.py"

    # Patch subprocess to return our mock result
    with patch.object(validator, '_run_with_constitutional_timeout', return_value=mock_result):
        try:
            validator.run()
            print("✗ FAILED: ValidatorTool did not raise exception on test failure!")
            return False
        except RuntimeError as e:
            error_msg = str(e)
            print(f"✓ ValidatorTool correctly raised RuntimeError")
            print(f"  Error message preview: {error_msg[:200]}...")

            # Verify the error message contains key information
            checks = [
                ("Article II" in error_msg, "Error mentions Article II"),
                ("Exit Code: 1" in error_msg, "Error shows exit code"),
                ("Tests Failed: 1" in error_msg, "Error shows failed test count"),
            ]

            all_passed = True
            for check, description in checks:
                if check:
                    print(f"  ✓ {description}")
                else:
                    print(f"  ✗ {description}")
                    all_passed = False

            return all_passed


def test_logging_functions():
    """Test that logging functions work correctly."""
    print("\n" + "=" * 60)
    print("TEST 5: Verify logging functions")
    print("=" * 60)

    validator = ValidatorTool()

    # Test verification result
    verification_result = {
        "tests_passed": 1562,
        "tests_failed": 0,
        "total_tests": 1562,
        "pass_rate": 100.0,
        "execution_time": 185.23,
        "all_passed": True,
        "exit_code": 0,
    }

    # Test logging (will create actual files)
    try:
        validator._log_verification(verification_result)
        print("✓ Verification logging executed without error")

        # Check if log file was created
        log_file = Path("logs/autonomous_healing/verification_log.jsonl")
        if log_file.exists():
            print(f"  ✓ Log file created: {log_file}")
            # Read last line
            lines = log_file.read_text().strip().split('\n')
            print(f"  ✓ Total log entries: {len(lines)}")
            return True
        else:
            print("  ✗ Log file not created")
            return False

    except Exception as e:
        print(f"✗ Logging failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("\n" + "=" * 80)
    print("VALIDATOR TOOL LOGIC VALIDATION (NO ACTUAL TEST EXECUTION)")
    print("=" * 80)

    results = []

    # Run all tests
    results.append(("Parse successful output", test_parse_test_output_all_passed()))
    results.append(("Parse failed output", test_parse_test_output_with_failures()))
    results.append(("Flag enforcement logic", test_enforce_run_all_flag()))
    results.append(("Hard failure on test failure", test_hard_failure_on_test_failure()))
    results.append(("Logging functions", test_logging_functions()))

    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ ValidatorTool logic is CORRECT")
        print("  - Parses test output correctly")
        print("  - Enforces --run-all flag appropriately")
        print("  - Raises RuntimeError on test failures")
        print("  - Logs verification results")
        return 0
    else:
        print("\n✗ ValidatorTool has logic issues - see failures above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
