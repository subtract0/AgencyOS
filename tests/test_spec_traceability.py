"""
Tests for Spec Traceability Validation Tool

Constitutional Compliance: Article V - Spec-Driven Development
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from tools.spec_traceability import (
    SpecTraceabilityValidator,
    SpecTraceabilityReport,
)


class TestSpecTraceabilityValidator:
    """Test suite for SpecTraceabilityValidator."""

    @pytest.fixture
    def temp_codebase(self):
        """Create a temporary codebase directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def validator(self):
        """Create a validator instance with default settings."""
        return SpecTraceabilityValidator(min_coverage=0.80)

    def test_validate_file_with_comment_ref(self, validator, temp_codebase):
        """Test file with comment-based spec reference."""
        # Arrange
        file_path = temp_codebase / "feature.py"
        file_path.write_text(
            """# Spec: specs/feature-name.md

def my_feature():
    '''Implement feature.'''
    pass
"""
        )

        # Act
        result = validator.validate_file(file_path)

        # Assert
        assert result is True

    def test_validate_file_with_specification_comment(self, validator, temp_codebase):
        """Test file with 'Specification:' comment reference."""
        # Arrange
        file_path = temp_codebase / "feature.py"
        file_path.write_text(
            """# Specification: specs/my-feature.md

def my_feature():
    '''Implement feature.'''
    pass
"""
        )

        # Act
        result = validator.validate_file(file_path)

        # Assert
        assert result is True

    def test_validate_file_with_see_comment(self, validator, temp_codebase):
        """Test file with 'See:' comment reference."""
        # Arrange
        file_path = temp_codebase / "feature.py"
        file_path.write_text(
            """# See: specs/feature-spec.md

def my_feature():
    '''Implement feature.'''
    pass
"""
        )

        # Act
        result = validator.validate_file(file_path)

        # Assert
        assert result is True

    def test_validate_file_with_docstring_ref(self, validator, temp_codebase):
        """Test file with docstring spec reference."""
        # Arrange
        file_path = temp_codebase / "feature.py"
        file_path.write_text(
            '''"""
Feature Implementation

Specification: specs/feature-name.md

This module implements the feature according to the specification.
"""

def my_feature():
    """Implement feature."""
    pass
'''
        )

        # Act
        result = validator.validate_file(file_path)

        # Assert
        assert result is True

    def test_validate_file_without_ref(self, validator, temp_codebase):
        """Test file without spec reference fails."""
        # Arrange
        file_path = temp_codebase / "feature.py"
        file_path.write_text(
            """def my_feature():
    '''Implement feature.'''
    pass
"""
        )

        # Act
        result = validator.validate_file(file_path)

        # Assert
        assert result is False

    def test_validate_file_case_insensitive(self, validator, temp_codebase):
        """Test spec reference detection is case-insensitive."""
        # Arrange
        file_path = temp_codebase / "feature.py"
        file_path.write_text(
            """# SPEC: specs/feature-name.md

def my_feature():
    '''Implement feature.'''
    pass
"""
        )

        # Act
        result = validator.validate_file(file_path)

        # Assert
        assert result is True

    def test_should_exclude_test_files(self, validator):
        """Test that test files are excluded."""
        # Arrange
        test_file = Path("test_feature.py")
        feature_test = Path("feature_test.py")
        init_file = Path("__init__.py")

        # Act & Assert
        assert validator.should_exclude(test_file) is True
        assert validator.should_exclude(feature_test) is True
        assert validator.should_exclude(init_file) is True

    def test_should_not_exclude_regular_files(self, validator):
        """Test that regular files are not excluded."""
        # Arrange
        regular_file = Path("feature.py")

        # Act & Assert
        assert validator.should_exclude(regular_file) is False

    def test_validate_codebase_full_coverage(self, validator, temp_codebase):
        """Test codebase with 100% spec coverage."""
        # Arrange - create 3 files with spec references
        for i in range(3):
            file_path = temp_codebase / f"feature_{i}.py"
            file_path.write_text(f"# Spec: specs/feature-{i}.md\n\ndef feature():\n    pass\n")

        # Act
        result = validator.validate_codebase(temp_codebase)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert report.total_files == 3
        assert report.files_with_spec_refs == 3
        assert report.files_without_spec_refs == 0
        assert report.spec_coverage == 100.0
        assert report.compliant is True
        assert len(report.violations) == 0

    def test_validate_codebase_partial_coverage(self, validator, temp_codebase):
        """Test codebase with partial spec coverage."""
        # Arrange - create 2 files with refs, 2 without
        for i in range(2):
            file_path = temp_codebase / f"feature_{i}.py"
            file_path.write_text(f"# Spec: specs/feature-{i}.md\n\ndef feature():\n    pass\n")

        for i in range(2, 4):
            file_path = temp_codebase / f"feature_{i}.py"
            file_path.write_text(f"def feature():\n    pass\n")

        # Act
        result = validator.validate_codebase(temp_codebase)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert report.total_files == 4
        assert report.files_with_spec_refs == 2
        assert report.files_without_spec_refs == 2
        assert report.spec_coverage == 50.0
        assert report.compliant is False  # Below 80% threshold
        assert len(report.violations) == 2

    def test_validate_codebase_excludes_test_files(self, validator, temp_codebase):
        """Test that test files are excluded from coverage calculation."""
        # Arrange - create 1 feature file with ref, 1 test file without ref
        feature_file = temp_codebase / "feature.py"
        feature_file.write_text("# Spec: specs/feature.md\n\ndef feature():\n    pass\n")

        test_file = temp_codebase / "test_feature.py"
        test_file.write_text("def test_feature():\n    assert True\n")

        # Act
        result = validator.validate_codebase(temp_codebase)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert report.total_files == 1  # Test file excluded
        assert report.files_with_spec_refs == 1
        assert report.spec_coverage == 100.0
        assert report.compliant is True

    def test_validate_codebase_with_init_files(self, validator, temp_codebase):
        """Test that __init__.py files are excluded."""
        # Arrange
        init_file = temp_codebase / "__init__.py"
        init_file.write_text("# Empty init\n")

        feature_file = temp_codebase / "feature.py"
        feature_file.write_text("# Spec: specs/feature.md\n\ndef feature():\n    pass\n")

        # Act
        result = validator.validate_codebase(temp_codebase)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert report.total_files == 1  # __init__.py excluded
        assert report.spec_coverage == 100.0

    def test_validate_codebase_empty_directory(self, validator, temp_codebase):
        """Test validation of empty codebase."""
        # Act
        result = validator.validate_codebase(temp_codebase)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert report.total_files == 0
        assert report.spec_coverage == 0.0
        # Empty codebase has 0% coverage, which is below threshold
        assert report.compliant is False

    def test_validate_codebase_with_subdirectories(self, validator, temp_codebase):
        """Test validation across subdirectories."""
        # Arrange - create nested structure
        subdir = temp_codebase / "module"
        subdir.mkdir()

        (temp_codebase / "root.py").write_text(
            "# Spec: specs/root.md\n\ndef root():\n    pass\n"
        )
        (subdir / "feature.py").write_text(
            "# Spec: specs/feature.md\n\ndef feature():\n    pass\n"
        )

        # Act
        result = validator.validate_codebase(temp_codebase)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert report.total_files == 2
        assert report.files_with_spec_refs == 2
        assert report.spec_coverage == 100.0

    def test_spec_coverage_calculation(self, validator, temp_codebase):
        """Test coverage percentage calculation is accurate."""
        # Arrange - create 5 files: 4 with refs, 1 without
        for i in range(4):
            file_path = temp_codebase / f"feature_{i}.py"
            file_path.write_text(f"# Spec: specs/feature-{i}.md\n\ndef feature():\n    pass\n")

        no_ref_file = temp_codebase / "no_ref.py"
        no_ref_file.write_text("def feature():\n    pass\n")

        # Act
        result = validator.validate_codebase(temp_codebase)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert report.total_files == 5
        assert report.files_with_spec_refs == 4
        assert report.files_without_spec_refs == 1
        # 4/5 = 80%
        assert report.spec_coverage == 80.0
        assert report.compliant is True  # Exactly at threshold

    def test_validator_with_lower_threshold(self, temp_codebase):
        """Test validator with lower minimum coverage threshold."""
        # Arrange
        validator = SpecTraceabilityValidator(min_coverage=0.50)  # 50% threshold

        # Create 1 file with ref, 1 without
        (temp_codebase / "with_ref.py").write_text(
            "# Spec: specs/feature.md\n\ndef feature():\n    pass\n"
        )
        (temp_codebase / "without_ref.py").write_text("def feature():\n    pass\n")

        # Act
        result = validator.validate_codebase(temp_codebase)

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert report.spec_coverage == 50.0
        assert report.compliant is True  # Meets 50% threshold

    def test_validate_file_with_invalid_path(self, validator):
        """Test validation handles invalid file paths gracefully."""
        # Arrange
        invalid_path = Path("/nonexistent/file.py")

        # Act
        result = validator.validate_file(invalid_path)

        # Assert
        assert result is False  # Should return False, not raise exception


class TestSpecTraceabilityReport:
    """Test suite for SpecTraceabilityReport model."""

    def test_report_model_creation(self):
        """Test SpecTraceabilityReport model can be created."""
        # Arrange & Act
        report = SpecTraceabilityReport(
            total_files=10,
            files_with_spec_refs=8,
            files_without_spec_refs=2,
            spec_coverage=80.0,
            violations=["file1.py", "file2.py"],
            compliant=True
        )

        # Assert
        assert report.total_files == 10
        assert report.files_with_spec_refs == 8
        assert report.files_without_spec_refs == 2
        assert report.spec_coverage == 80.0
        assert len(report.violations) == 2
        assert report.compliant is True

    def test_report_violations_default(self):
        """Test violations field defaults to empty list."""
        # Arrange & Act
        report = SpecTraceabilityReport(
            total_files=5,
            files_with_spec_refs=5,
            files_without_spec_refs=0,
            spec_coverage=100.0,
            compliant=True
        )

        # Assert
        assert report.violations == []
