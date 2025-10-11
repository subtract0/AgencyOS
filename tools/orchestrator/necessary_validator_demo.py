"""
Demo script for NECESSARYValidator.

Shows validation of test files with various NECESSARY pattern violations
and auto-fix suggestions with confidence scores.

Usage:
    python tools/orchestrator/necessary_validator_demo.py
"""

import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.orchestrator.necessary_validator import NECESSARYValidator


def demo_compliant_test():
    """Demonstrate validation of compliant test."""
    print("\n" + "=" * 70)
    print("DEMO 1: Compliant NECESSARY Test")
    print("=" * 70)

    compliant_test = '''
def test_validate_email_when_valid_format_then_returns_ok():
    """Test email validation with valid format."""
    # Arrange
    email = "test@example.com"

    # Act
    result = validate_email(email)

    # Assert
    assert result.is_ok()
    assert result.unwrap() == email
'''

    print("\nTest Code:")
    print(compliant_test)

    validator = NECESSARYValidator()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(compliant_test)
        test_file = f.name

    result = validator.validate(test_file)

    if result.is_ok():
        report = result.unwrap()
        if report.passed:
            print("\n✅ PASSED: Test is NECESSARY compliant!")
        else:
            print(f"\n❌ FAILED: {len(report.violations)} violations detected")
    else:
        print(f"\n❌ ERROR: {result.unwrap_err()}")

    Path(test_file).unlink()


def demo_naming_violation():
    """Demonstrate detection of naming violation."""
    print("\n" + "=" * 70)
    print("DEMO 2: Naming Violation Detection")
    print("=" * 70)

    bad_naming_test = '''
def test_1():
    """Test validation."""
    # Arrange
    email = "test@example.com"

    # Act
    result = validate_email(email)

    # Assert
    assert result.is_ok()
'''

    print("\nTest Code:")
    print(bad_naming_test)

    validator = NECESSARYValidator()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(bad_naming_test)
        test_file = f.name

    result = validator.validate(test_file)

    if result.is_ok():
        report = result.unwrap()
        print(f"\n❌ FAILED: {len(report.violations)} violations detected\n")

        for violation in report.violations:
            print(f"Violation Type: {violation.type}")
            print(f"Severity: {violation.severity}")
            print(f"Line: {violation.line_number}")
            print(f"Description: {violation.description}")

            if violation.suggested_fixes:
                print("\nAuto-Fix Suggestions:")
                for fix in violation.suggested_fixes:
                    print(f"  - {fix.description}")
                    print(f"    Confidence: {fix.confidence:.2f}")
                    print(f"    Code: {fix.code_snippet}")

    Path(test_file).unlink()


def demo_multiple_violations():
    """Demonstrate detection of multiple violations."""
    print("\n" + "=" * 70)
    print("DEMO 3: Multiple Violations")
    print("=" * 70)

    multiple_violations_test = """
def test_basic():
    user_data = {"email": "test@example.com"}
    result = create_user(user_data)
    assert result
"""

    print("\nTest Code:")
    print(multiple_violations_test)

    validator = NECESSARYValidator()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(multiple_violations_test)
        test_file = f.name

    result = validator.validate(test_file)

    if result.is_ok():
        report = result.unwrap()
        print(f"\n❌ FAILED: {len(report.violations)} violations detected\n")

        violation_types = [v.type for v in report.violations]
        print(f"Violation Types: {', '.join(violation_types)}")

        for i, violation in enumerate(report.violations, 1):
            print(f"\n{i}. {violation.type.upper()} ({violation.severity} severity)")
            print(f"   {violation.description}")

            if violation.suggested_fixes:
                best_fix = violation.suggested_fixes[0]
                print(f"   Best Fix (confidence {best_fix.confidence:.2f}):")
                print(f"   {best_fix.description}")

    Path(test_file).unlink()


def demo_aaa_structure_violation():
    """Demonstrate detection of missing AAA structure."""
    print("\n" + "=" * 70)
    print("DEMO 4: AAA Structure Violation")
    print("=" * 70)

    no_aaa_test = '''
def test_user_creation_when_valid_data_then_creates_user():
    """Test user creation with valid data."""
    user_data = {"email": "test@example.com", "name": "Test"}
    result = create_user(user_data)
    assert result.is_ok()
    assert result.unwrap().email == "test@example.com"
'''

    print("\nTest Code:")
    print(no_aaa_test)

    validator = NECESSARYValidator()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(no_aaa_test)
        test_file = f.name

    result = validator.validate(test_file)

    if result.is_ok():
        report = result.unwrap()
        aaa_violations = [v for v in report.violations if v.type == "aaa_structure"]

        if aaa_violations:
            violation = aaa_violations[0]
            print("\n❌ AAA Structure Missing")
            print(f"Description: {violation.description}")

            if violation.suggested_fixes:
                fix = violation.suggested_fixes[0]
                print(f"\nAuto-Fix (confidence {fix.confidence:.2f}):")
                print(f"{fix.description}")
                print("\nSuggested Code:")
                print(fix.code_snippet)

    Path(test_file).unlink()


if __name__ == "__main__":
    print("\n" + "🚀" * 35)
    print("NECESSARY Pattern Validator - Demo")
    print("🚀" * 35)

    demo_compliant_test()
    demo_naming_violation()
    demo_multiple_violations()
    demo_aaa_structure_violation()

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
