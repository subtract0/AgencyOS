"""
Tests for NECESSARYValidator - AST-based test quality validation.

Constitutional Compliance:
- Article I: Complete context validation (full AST required)
- Article II: Test quality enforcement before acceptance
- Article IV: VectorStore integration for proven fix patterns

Test Structure: NECESSARY pattern compliant
"""

import ast
import tempfile
from pathlib import Path

import pytest

from shared.type_definitions.result import Err, Ok
from tools.orchestrator.necessary_validator import (
    NECESSARYValidator,
    SuggestedFix,
    ValidationReport,
    Violation,
)


class TestNECESSARYValidator:
    """Test suite for NECESSARY pattern validator."""

    def test_validate_when_compliant_test_then_returns_ok_with_no_violations(self):
        """Test validation with fully compliant NECESSARY test."""
        # Arrange
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
        validator = NECESSARYValidator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(compliant_test)
            test_file = f.name

        # Act
        result = validator.validate(test_file)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert isinstance(report, ValidationReport)
        assert report.passed is True
        assert len(report.violations) == 0
        assert report.file_path == test_file

        # Cleanup
        Path(test_file).unlink()

    def test_validate_when_generic_test_name_then_detects_naming_violation(self):
        """Test detection of generic test names."""
        # Arrange
        generic_test = '''
def test_1():
    """Test validation."""
    result = validate_email("test@example.com")
    assert result.is_ok()
'''
        validator = NECESSARYValidator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(generic_test)
            test_file = f.name

        # Act
        result = validator.validate(test_file)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert report.passed is False
        assert len(report.violations) > 0

        naming_violations = [v for v in report.violations if v.type == "naming"]
        assert len(naming_violations) == 1
        assert "test_1" in naming_violations[0].description
        assert len(naming_violations[0].suggested_fixes) > 0

        # Cleanup
        Path(test_file).unlink()

    def test_validate_when_missing_aaa_comments_then_detects_structure_violation(self):
        """Test detection of missing AAA structure."""
        # Arrange
        no_aaa_test = '''
def test_user_creation_when_valid_data_then_returns_user():
    """Test user creation with valid data."""
    user_data = {"email": "test@example.com", "name": "Test"}
    result = create_user(user_data)
    assert result.is_ok()
'''
        validator = NECESSARYValidator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(no_aaa_test)
            test_file = f.name

        # Act
        result = validator.validate(test_file)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert report.passed is False

        aaa_violations = [v for v in report.violations if v.type == "aaa_structure"]
        assert len(aaa_violations) == 1
        assert "AAA" in aaa_violations[0].description or "Arrange" in aaa_violations[0].description

        # Cleanup
        Path(test_file).unlink()

    def test_validate_when_missing_docstring_then_detects_docstring_violation(self):
        """Test detection of missing docstrings."""
        # Arrange
        no_docstring_test = """
def test_validate_email_when_invalid_format_then_returns_error():
    # Arrange
    invalid_email = "not-an-email"

    # Act
    result = validate_email(invalid_email)

    # Assert
    assert result.is_err()
"""
        validator = NECESSARYValidator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(no_docstring_test)
            test_file = f.name

        # Act
        result = validator.validate(test_file)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert report.passed is False

        docstring_violations = [v for v in report.violations if v.type == "docstring"]
        assert len(docstring_violations) == 1
        assert "docstring" in docstring_violations[0].description.lower()

        # Cleanup
        Path(test_file).unlink()

    def test_validate_when_syntax_error_then_returns_error(self):
        """Test handling of syntax errors in test files."""
        # Arrange
        syntax_error_test = """
def test_invalid_syntax()
    # Missing colon causes syntax error
    assert True
"""
        validator = NECESSARYValidator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(syntax_error_test)
            test_file = f.name

        # Act
        result = validator.validate(test_file)

        # Assert
        assert result.is_err()
        error_msg = result.unwrap_err()
        assert "syntax" in error_msg.lower() or "parse" in error_msg.lower()

        # Cleanup
        Path(test_file).unlink()

    def test_validate_when_multiple_violations_then_all_detected(self):
        """Test detection of multiple violation types."""
        # Arrange
        multiple_violations_test = """
def test_1():
    user_data = {"email": "test@example.com"}
    result = create_user(user_data)
    assert result
"""
        validator = NECESSARYValidator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(multiple_violations_test)
            test_file = f.name

        # Act
        result = validator.validate(test_file)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert report.passed is False

        # Should detect: naming, AAA structure, docstring
        violation_types = {v.type for v in report.violations}
        assert "naming" in violation_types
        assert "aaa_structure" in violation_types
        assert "docstring" in violation_types

        # Cleanup
        Path(test_file).unlink()

    def test_suggested_fix_when_naming_violation_then_has_confidence_score(self):
        """Test auto-fix suggestions include confidence scores."""
        # Arrange
        generic_test = '''
def test_basic():
    """Test."""
    # Arrange
    value = 42

    # Act
    result = process(value)

    # Assert
    assert result == 84
'''
        validator = NECESSARYValidator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(generic_test)
            test_file = f.name

        # Act
        result = validator.validate(test_file)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        naming_violations = [v for v in report.violations if v.type == "naming"]
        assert len(naming_violations) > 0

        fix = naming_violations[0].suggested_fixes[0]
        assert isinstance(fix, SuggestedFix)
        assert 0.0 <= fix.confidence <= 1.0
        assert fix.description
        assert fix.code_snippet

        # Cleanup
        Path(test_file).unlink()

    def test_validate_when_file_not_exists_then_returns_error(self):
        """Test handling of non-existent files."""
        # Arrange
        validator = NECESSARYValidator()
        non_existent_file = "/tmp/does_not_exist_12345.py"

        # Act
        result = validator.validate(non_existent_file)

        # Assert
        assert result.is_err()
        assert "not found" in result.unwrap_err().lower() or "exist" in result.unwrap_err().lower()

    def test_validate_when_empty_file_then_returns_ok_with_no_tests(self):
        """Test handling of empty test files."""
        # Arrange
        validator = NECESSARYValidator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("")  # Empty file
            test_file = f.name

        # Act
        result = validator.validate(test_file)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert report.passed is True  # No tests = no violations
        assert len(report.violations) == 0

        # Cleanup
        Path(test_file).unlink()

    def test_violation_severity_when_naming_violation_then_marked_high(self):
        """Test violation severity levels."""
        # Arrange
        generic_test = '''
def test_1():
    """Test."""
    # Arrange
    x = 1

    # Act
    y = x + 1

    # Assert
    assert y == 2
'''
        validator = NECESSARYValidator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(generic_test)
            test_file = f.name

        # Act
        result = validator.validate(test_file)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        naming_violations = [v for v in report.violations if v.type == "naming"]
        assert len(naming_violations) > 0
        assert naming_violations[0].severity in ["critical", "high", "medium", "low"]

        # Cleanup
        Path(test_file).unlink()

    def test_validate_when_class_based_test_then_analyzes_methods(self):
        """Test analysis of class-based test structures."""
        # Arrange
        class_test = '''
class TestUserValidation:
    """Test user validation functionality."""

    def test_1(self):
        """Test validation."""
        result = validate_user({"email": "test@example.com"})
        assert result.is_ok()
'''
        validator = NECESSARYValidator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(class_test)
            test_file = f.name

        # Act
        result = validator.validate(test_file)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert report.passed is False

        # Should detect violations in class methods
        naming_violations = [v for v in report.violations if v.type == "naming"]
        assert len(naming_violations) > 0

        # Cleanup
        Path(test_file).unlink()

    def test_suggested_fix_when_aaa_violation_then_high_confidence(self):
        """Test AAA structure fixes have high confidence (>0.9)."""
        # Arrange
        no_aaa_test = '''
def test_process_when_valid_input_then_returns_result():
    """Test processing with valid input."""
    value = 42
    result = process(value)
    assert result == 84
'''
        validator = NECESSARYValidator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(no_aaa_test)
            test_file = f.name

        # Act
        result = validator.validate(test_file)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        aaa_violations = [v for v in report.violations if v.type == "aaa_structure"]
        assert len(aaa_violations) > 0

        fix = aaa_violations[0].suggested_fixes[0]
        assert fix.confidence >= 0.9  # High confidence for structural fixes

        # Cleanup
        Path(test_file).unlink()

    def test_validate_when_pytest_fixture_used_then_not_flagged_as_violation(self):
        """Test that pytest fixtures are handled correctly."""
        # Arrange
        fixture_test = '''
def test_user_creation_when_valid_data_then_creates_user(db_session):
    """Test user creation with database session fixture."""
    # Arrange
    user_data = {"email": "test@example.com", "name": "Test"}

    # Act
    result = create_user(db_session, user_data)

    # Assert
    assert result.is_ok()
    assert result.unwrap().email == "test@example.com"
'''
        validator = NECESSARYValidator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(fixture_test)
            test_file = f.name

        # Act
        result = validator.validate(test_file)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        # Should pass - fixtures are valid pytest patterns
        assert report.passed is True or len(report.violations) == 0

        # Cleanup
        Path(test_file).unlink()

    def test_validation_report_structure_when_violations_exist_then_all_fields_populated(self):
        """Test ValidationReport structure completeness."""
        # Arrange
        test_with_violations = """
def test_1():
    x = 1
    assert x
"""
        validator = NECESSARYValidator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_with_violations)
            test_file = f.name

        # Act
        result = validator.validate(test_file)

        # Assert
        assert result.is_ok()
        report = result.unwrap()

        # Verify all fields are populated
        assert report.file_path == test_file
        assert isinstance(report.passed, bool)
        assert isinstance(report.violations, list)
        assert isinstance(report.fixes, list)

        # Check Violation structure
        violation = report.violations[0]
        assert hasattr(violation, "type")
        assert hasattr(violation, "severity")
        assert hasattr(violation, "line_number")
        assert hasattr(violation, "description")
        assert hasattr(violation, "suggested_fixes")

        # Cleanup
        Path(test_file).unlink()
