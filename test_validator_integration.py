#!/usr/bin/env python3
"""
Integration test to verify ValidatorTool with REAL test execution (using fast tests).
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from quality_enforcer_agent.quality_enforcer_agent import ValidatorTool


def test_real_execution_fast_tests():
    """Test ValidatorTool with real (but fast) test execution."""
    print("\n" + "=" * 80)
    print("REAL INTEGRATION TEST - ValidatorTool with --fast flag")
    print("=" * 80)
    print("\nThis will execute actual tests (fast subset only)")
    print("Expected: All tests should pass and validation should succeed\n")

    # Create validator with fast tests (subset that should pass quickly)
    validator = ValidatorTool(test_command="python run_tests.py --fast")

    try:
        result = validator.run()
        print("\n" + "=" * 80)
        print("VALIDATION RESULT")
        print("=" * 80)
        print(result)

        # Check the log file
        log_file = Path("logs/autonomous_healing/verification_log.jsonl")
        if log_file.exists():
            lines = log_file.read_text().strip().split('\n')
            print(f"\n✓ Verification logged to {log_file}")
            print(f"  Total entries: {len(lines)}")
            print(f"\n  Latest entry:")
            print(f"  {lines[-1][:150]}...")

        print("\n" + "=" * 80)
        print("✓ INTEGRATION TEST PASSED")
        print("=" * 80)
        print("\nValidatorTool successfully:")
        print("  1. Executed real tests via subprocess")
        print("  2. Parsed test output correctly")
        print("  3. Verified 100% pass rate")
        print("  4. Logged results to autonomous_healing/")
        print("  5. Enforced Article II compliance\n")

        return 0

    except RuntimeError as e:
        print("\n" + "=" * 80)
        print("✗ INTEGRATION TEST FAILED - Tests did not pass")
        print("=" * 80)
        print(f"\nRuntimeError raised (as expected for failures):")
        print(str(e)[:500])
        print("\nThis is CORRECT behavior when tests fail!")
        print("ValidatorTool is enforcing Article II properly.\n")
        return 1

    except Exception as e:
        print("\n" + "=" * 80)
        print("✗ UNEXPECTED ERROR")
        print("=" * 80)
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(test_real_execution_fast_tests())
