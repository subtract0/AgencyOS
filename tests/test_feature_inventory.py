"""
Comprehensive test coverage for tools.feature_inventory module.
Tests feature extraction, inventory generation, and file parsing functionality.
"""

import re
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

from tools.feature_inventory import (
    extract_features_from_md,
    check_test_files,
    main
)


class TestExtractFeaturesFromMd:
    """Test feature extraction from FEATURES.md file."""

    @pytest.fixture
    def sample_features_md(self):
        """Create a sample FEATURES.md file for testing."""
        content = '''# Features Documentation

## Core Authentication
User authentication and authorization system.

**Test Coverage**: `tests/test_auth.py`

### Login System
Standard email/password login.

**Test Coverage**: `tests/test_login.py`

## Data Processing
Advanced data processing capabilities.

**Test Coverage**: `tests/test_data_processing.py`

### Batch Processing
Process large datasets efficiently.

## Reporting
Generate comprehensive reports.

**Test Coverage**: `tests/test_reporting.py`

### Export Features
Export data in multiple formats.

**Test Coverage**: `tests/test_export.py`
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_file_path = f.name

        yield Path(temp_file_path)

        # Cleanup
        os.unlink(temp_file_path)

    def test_extract_features_basic(self, sample_features_md):
        """Test basic feature extraction from FEATURES.md."""
        features, test_files = extract_features_from_md(sample_features_md)

        # Check extracted features (## and ### headings)
        expected_features = [
            "Core Authentication",
            "Data Processing",
            "Reporting",
            "Login System",
            "Batch Processing",
            "Export Features"
        ]

        assert len(features) == len(expected_features)
        for expected_feature in expected_features:
            assert expected_feature in features

        # Check extracted test files
        expected_test_files = [
            "tests/test_auth.py",
            "tests/test_login.py",
            "tests/test_data_processing.py",
            "tests/test_reporting.py",
            "tests/test_export.py"
        ]

        assert len(test_files) == len(expected_test_files)
        for expected_test_file in expected_test_files:
            assert expected_test_file in test_files

    def test_extract_features_empty_file(self):
        """Test extraction from empty FEATURES.md file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("")
            temp_file_path = f.name

        try:
            features, test_files = extract_features_from_md(Path(temp_file_path))
            assert features == []
            assert test_files == []
        finally:
            os.unlink(temp_file_path)

    def test_extract_features_no_test_coverage(self):
        """Test extraction from file without test coverage sections."""
        content = '''# Features

## Feature One
Description without test coverage.

## Feature Two
Another feature without tests.
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_file_path = f.name

        try:
            features, test_files = extract_features_from_md(Path(temp_file_path))
            assert len(features) == 2
            assert "Feature One" in features
            assert "Feature Two" in features
            assert test_files == []
        finally:
            os.unlink(temp_file_path)

    def test_extract_features_various_heading_levels(self):
        """Test extraction with various heading levels."""
        content = '''# Main Title

## Level 2 Feature
Description

### Level 3 Feature
Description

#### Level 4 Feature (should be ignored)
Description

##### Level 5 Feature (should be ignored)
Description

## Another Level 2
Description

### Another Level 3
Description
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_file_path = f.name

        try:
            features, test_files = extract_features_from_md(Path(temp_file_path))

            # Should only capture ## and ### level headings
            expected_features = [
                "Level 2 Feature",
                "Level 3 Feature",
                "Another Level 2",
                "Another Level 3"
            ]

            assert len(features) == len(expected_features)
            for expected_feature in expected_features:
                assert expected_feature in features

            # Should not capture level 4 or 5 headings
            assert "Level 4 Feature (should be ignored)" not in features
            assert "Level 5 Feature (should be ignored)" not in features
        finally:
            os.unlink(temp_file_path)

    def test_extract_features_test_coverage_variations(self):
        """Test extraction with various test coverage format variations."""
        content = '''# Features

## Feature 1
**Test Coverage**: `tests/test_feature1.py`

## Feature 2
**Test Coverage**: `tests/test_feature2.py`

## Feature 3
**Test Coverage** : `tests/test_feature3.py`

## Feature 4
**Test Coverage**:`tests/test_feature4.py`

## Feature 5
**test coverage**: `tests/test_feature5.py`

## Feature 6
No test coverage mentioned.
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_file_path = f.name

        try:
            features, test_files = extract_features_from_md(Path(temp_file_path))

            # All features should be extracted
            assert len(features) == 6

            # Only properly formatted test coverage should be extracted
            expected_test_files = [
                "tests/test_feature1.py",
                "tests/test_feature2.py",
                "tests/test_feature3.py",
                "tests/test_feature4.py"
            ]

            assert len(test_files) == len(expected_test_files)
            for expected_test_file in expected_test_files:
                assert expected_test_file in test_files

            # Lowercase version should not be captured
            assert "tests/test_feature5.py" not in test_files
        finally:
            os.unlink(temp_file_path)

    def test_extract_features_special_characters(self):
        """Test extraction with special characters in headings."""
        content = '''# Features

## Feature with (Parentheses)
Description

### Feature with "Quotes"
Description

## Feature with *Asterisks*
Description

### Feature with `Code`
Description

**Test Coverage**: `tests/test_special.py`
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_file_path = f.name

        try:
            features, test_files = extract_features_from_md(Path(temp_file_path))

            expected_features = [
                'Feature with (Parentheses)',
                'Feature with "Quotes"',
                'Feature with *Asterisks*',
                'Feature with `Code`'
            ]

            assert len(features) == len(expected_features)
            for expected_feature in expected_features:
                assert expected_feature in features

            assert "tests/test_special.py" in test_files
        finally:
            os.unlink(temp_file_path)

    def test_extract_features_multiline_sections(self):
        """Test extraction from file with multiline feature sections."""
        content = '''# Features

## Multi-line Feature
This feature has
multiple lines of description
and should still be captured.

**Test Coverage**: `tests/test_multiline.py`

### Another Feature
With more content
and line breaks.

**Test Coverage**: `tests/test_another.py`
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_file_path = f.name

        try:
            features, test_files = extract_features_from_md(Path(temp_file_path))

            assert "Multi-line Feature" in features
            assert "Another Feature" in features
            assert "tests/test_multiline.py" in test_files
            assert "tests/test_another.py" in test_files
        finally:
            os.unlink(temp_file_path)

    def test_extract_features_file_not_found(self):
        """Test extraction from non-existent file."""
        with pytest.raises(FileNotFoundError):
            extract_features_from_md(Path("/nonexistent/file.md"))

    def test_extract_features_permission_error(self):
        """Test extraction when file cannot be read due to permissions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test")
            temp_file_path = f.name

        try:
            # Mock permission error
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                with pytest.raises(PermissionError):
                    extract_features_from_md(Path(temp_file_path))
        finally:
            os.unlink(temp_file_path)


class TestCheckTestFiles:
    """Test test file checking functionality."""

    @pytest.fixture
    def temp_project_structure(self, tmp_path):
        """Create a temporary project structure for testing."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        # Create tests directory
        tests_dir = project_root / "tests"
        tests_dir.mkdir()

        # Create some test files
        (tests_dir / "test_existing.py").write_text('''
def test_function_one():
    assert True

def test_function_two():
    assert False

def helper_function():
    pass

def test_function_three():
    pass
''')

        (tests_dir / "test_empty.py").write_text('')

        (tests_dir / "test_no_tests.py").write_text('''
def helper_function():
    pass

class HelperClass:
    pass
''')

        return project_root

    def test_check_test_files_existing(self, temp_project_structure):
        """Test checking existing test files."""
        test_files = [
            "tests/test_existing.py",
            "tests/test_missing.py",
            "tests/test_empty.py",
            "tests/test_no_tests.py"
        ]

        coverage_report = check_test_files(test_files, temp_project_structure)

        # Check test_existing.py
        assert coverage_report["tests/test_existing.py"]["exists"] is True
        assert coverage_report["tests/test_existing.py"]["test_count"] == 3  # 3 test_ functions

        # Check test_missing.py
        assert coverage_report["tests/test_missing.py"]["exists"] is False
        assert coverage_report["tests/test_missing.py"]["test_count"] == 0

        # Check test_empty.py
        assert coverage_report["tests/test_empty.py"]["exists"] is True
        assert coverage_report["tests/test_empty.py"]["test_count"] == 0

        # Check test_no_tests.py
        assert coverage_report["tests/test_no_tests.py"]["exists"] is True
        assert coverage_report["tests/test_no_tests.py"]["test_count"] == 0

    def test_check_test_files_empty_list(self, temp_project_structure):
        """Test checking empty list of test files."""
        coverage_report = check_test_files([], temp_project_structure)
        assert coverage_report == {}

    def test_check_test_files_absolute_paths(self, temp_project_structure):
        """Test checking test files with absolute paths."""
        # Create absolute path test file
        absolute_test_file = temp_project_structure / "tests" / "test_absolute.py"
        absolute_test_file.write_text("def test_absolute(): pass")

        test_files = [str(absolute_test_file)]
        coverage_report = check_test_files(test_files, temp_project_structure)

        assert str(absolute_test_file) in coverage_report
        assert coverage_report[str(absolute_test_file)]["exists"] is True
        assert coverage_report[str(absolute_test_file)]["test_count"] == 1

    def test_check_test_files_various_test_patterns(self, temp_project_structure):
        """Test counting various test function patterns."""
        test_file = temp_project_structure / "tests" / "test_patterns.py"
        test_file.write_text('''
def test_simple():
    pass

def test_with_underscores_and_numbers_123():
    pass

def test_():  # Edge case: just test_
    pass

def not_a_test():
    pass

def TEST_UPPERCASE():  # Should not match
    pass

def test_multiline():
    """
    Multiline test function
    """
    pass

class TestClass:
    def test_method(self):
        pass

    def test_another_method(self):
        pass

    def not_test_method(self):
        pass

def test_complex_function():
    # Complex test with nested structures
    if True:
        for i in range(10):
            pass
    return True
''')

        test_files = ["tests/test_patterns.py"]
        coverage_report = check_test_files(test_files, temp_project_structure)

        assert coverage_report["tests/test_patterns.py"]["exists"] is True
        # Should count: test_simple, test_with_underscores_and_numbers_123, test_,
        # test_multiline, test_method, test_another_method, test_complex_function
        assert coverage_report["tests/test_patterns.py"]["test_count"] == 7

    def test_check_test_files_read_error(self, temp_project_structure):
        """Test handling read errors for test files."""
        # Create a file that will cause read issues
        problematic_file = temp_project_structure / "tests" / "test_problematic.py"
        problematic_file.write_text("def test_function(): pass")

        test_files = ["tests/test_problematic.py"]

        # Mock file reading to raise an exception
        with patch('builtins.open', side_effect=UnicodeDecodeError("utf-8", b'', 0, 1, "invalid")):
            coverage_report = check_test_files(test_files, temp_project_structure)

            assert coverage_report["tests/test_problematic.py"]["exists"] is True
            assert coverage_report["tests/test_problematic.py"]["test_count"] == -1  # Error indicator

    def test_check_test_files_nested_directories(self, temp_project_structure):
        """Test checking test files in nested directories."""
        # Create nested directory structure
        nested_dir = temp_project_structure / "tests" / "unit" / "core"
        nested_dir.mkdir(parents=True)

        nested_test_file = nested_dir / "test_nested.py"
        nested_test_file.write_text("def test_nested_function(): pass")

        test_files = ["tests/unit/core/test_nested.py"]
        coverage_report = check_test_files(test_files, temp_project_structure)

        assert coverage_report["tests/unit/core/test_nested.py"]["exists"] is True
        assert coverage_report["tests/unit/core/test_nested.py"]["test_count"] == 1

    def test_check_test_files_binary_file(self, temp_project_structure):
        """Test handling binary files mistaken for test files."""
        # Create a binary file with .py extension
        binary_file = temp_project_structure / "tests" / "test_binary.py"
        binary_file.write_bytes(b'\x00\x01\x02\x03\x04')

        test_files = ["tests/test_binary.py"]
        coverage_report = check_test_files(test_files, temp_project_structure)

        assert coverage_report["tests/test_binary.py"]["exists"] is True
        assert coverage_report["tests/test_binary.py"]["test_count"] == -1  # Error due to binary content


class TestMainFunction:
    """Test main function functionality."""

    @pytest.fixture
    def mock_project_with_features(self, tmp_path):
        """Create a mock project with FEATURES.md and test files."""
        project_root = tmp_path / "mock_project"
        project_root.mkdir()

        # Create FEATURES.md
        features_md = project_root / "FEATURES.md"
        features_md.write_text('''# Project Features

## Authentication System
User login and registration functionality.

**Test Coverage**: `tests/test_auth.py`

## Data Processing
Process and analyze data efficiently.

**Test Coverage**: `tests/test_data.py`

### Export Functionality
Export data in various formats.

**Test Coverage**: `tests/test_export.py`

## Reporting
Generate comprehensive reports.

**Test Coverage**: `tests/test_reports.py`
''')

        # Create tests directory
        tests_dir = project_root / "tests"
        tests_dir.mkdir()

        # Create some test files
        (tests_dir / "test_auth.py").write_text('''
def test_login():
    pass

def test_register():
    pass

def test_logout():
    pass
''')

        (tests_dir / "test_data.py").write_text('''
def test_process_data():
    pass
''')

        # test_export.py is missing
        # test_reports.py exists but empty
        (tests_dir / "test_reports.py").write_text('')

        return project_root

    @patch('tools.feature_inventory.Path.__file__')
    def test_main_function_success(self, mock_file, mock_project_with_features, capsys):
        """Test main function with successful execution."""
        # Mock the __file__ path to point to our test project
        mock_file.parent.parent = mock_project_with_features

        # Change working directory to the mock project
        original_cwd = os.getcwd()
        try:
            os.chdir(mock_project_with_features)
            main()
        finally:
            os.chdir(original_cwd)

        captured = capsys.readouterr()
        output = captured.out

        # Check that output contains expected elements
        assert "🔍 Agency Code Feature Inventory" in output
        assert "📊 Summary:" in output
        assert "Features documented:" in output
        assert "Test files referenced:" in output
        assert "Test files found:" in output
        assert "Total test functions:" in output
        assert "📋 Test Coverage Details:" in output
        assert "🎯 Overall Coverage:" in output

        # Check specific file results
        assert "✅ tests/test_auth.py (3 tests)" in output
        assert "✅ tests/test_data.py (1 tests)" in output
        assert "❌ tests/test_export.py" in output
        assert "✅ tests/test_reports.py ()" in output or "✅ tests/test_reports.py (0 tests)" in output

    @patch('tools.feature_inventory.Path.__file__')
    def test_main_function_missing_features_md(self, mock_file, tmp_path, capsys):
        """Test main function when FEATURES.md is missing."""
        # Create empty project directory
        empty_project = tmp_path / "empty_project"
        empty_project.mkdir()

        mock_file.parent.parent = empty_project

        original_cwd = os.getcwd()
        try:
            os.chdir(empty_project)
            main()
        finally:
            os.chdir(original_cwd)

        captured = capsys.readouterr()
        output = captured.out

        assert "❌ FEATURES.md not found" in output

    @patch('tools.feature_inventory.extract_features_from_md')
    @patch('tools.feature_inventory.Path.__file__')
    def test_main_function_extraction_error(self, mock_file, mock_extract, tmp_path, capsys):
        """Test main function when feature extraction fails."""
        # Create project with FEATURES.md
        project_root = tmp_path / "error_project"
        project_root.mkdir()
        (project_root / "FEATURES.md").write_text("# Features")

        mock_file.parent.parent = project_root
        mock_extract.side_effect = Exception("Extraction failed")

        original_cwd = os.getcwd()
        try:
            os.chdir(project_root)
            with pytest.raises(Exception, match="Extraction failed"):
                main()
        finally:
            os.chdir(original_cwd)

    @patch('tools.feature_inventory.Path.__file__')
    def test_main_function_zero_coverage(self, mock_file, tmp_path, capsys):
        """Test main function with zero test coverage."""
        # Create project with features but no test files
        project_root = tmp_path / "no_tests_project"
        project_root.mkdir()

        features_md = project_root / "FEATURES.md"
        features_md.write_text('''# Features

## Feature One
Description

**Test Coverage**: `tests/test_one.py`

## Feature Two
Description

**Test Coverage**: `tests/test_two.py`
''')

        mock_file.parent.parent = project_root

        original_cwd = os.getcwd()
        try:
            os.chdir(project_root)
            main()
        finally:
            os.chdir(original_cwd)

        captured = capsys.readouterr()
        output = captured.out

        assert "Features documented: 2" in output
        assert "Test files referenced: 2" in output
        assert "Test files found: 0/2" in output
        assert "Total test functions: 0" in output
        assert "🎯 Overall Coverage: 0.0%" in output

    @patch('tools.feature_inventory.Path.__file__')
    def test_main_function_perfect_coverage(self, mock_file, tmp_path, capsys):
        """Test main function with perfect test coverage."""
        # Create project with complete test coverage
        project_root = tmp_path / "perfect_project"
        project_root.mkdir()

        features_md = project_root / "FEATURES.md"
        features_md.write_text('''# Features

## Feature One
**Test Coverage**: `tests/test_one.py`

## Feature Two
**Test Coverage**: `tests/test_two.py`
''')

        tests_dir = project_root / "tests"
        tests_dir.mkdir()

        (tests_dir / "test_one.py").write_text("def test_one(): pass")
        (tests_dir / "test_two.py").write_text("def test_two(): pass")

        mock_file.parent.parent = project_root

        original_cwd = os.getcwd()
        try:
            os.chdir(project_root)
            main()
        finally:
            os.chdir(original_cwd)

        captured = capsys.readouterr()
        output = captured.out

        assert "Test files found: 2/2" in output
        assert "🎯 Overall Coverage: 100.0%" in output


class TestRegexPatterns:
    """Test the regex patterns used in the module."""

    def test_test_pattern_regex(self):
        """Test the test coverage regex pattern."""
        pattern = r'\*\*Test Coverage\*\*:\s*`([^`]+)`'

        # Valid patterns
        valid_cases = [
            "**Test Coverage**: `tests/test_file.py`",
            "**Test Coverage**:`tests/test_file.py`",
            "**Test Coverage**: `tests/nested/test_file.py`",
            "**Test Coverage**:   `tests/test_file_with_underscores.py`",
        ]

        for case in valid_cases:
            match = re.search(pattern, case)
            assert match is not None, f"Pattern should match: {case}"
            assert "tests/" in match.group(1)

        # Invalid patterns
        invalid_cases = [
            "**test coverage**: `tests/test_file.py`",  # lowercase
            "**Test Coverage** `tests/test_file.py`",   # missing colon
            "**Test Coverage**: tests/test_file.py",    # missing backticks
            "Test Coverage: `tests/test_file.py`",      # missing bold formatting
        ]

        for case in invalid_cases:
            match = re.search(pattern, case)
            assert match is None, f"Pattern should not match: {case}"

    def test_feature_pattern_regex(self):
        """Test the feature heading regex pattern."""
        pattern = r'^#{2,3}\s+(.+)$'

        # Valid patterns
        valid_cases = [
            "## Feature Name",
            "### Sub Feature",
            "##  Feature with Extra Spaces",
            "### Feature with (Special) Characters!",
            "## Feature with *formatting*",
        ]

        for case in valid_cases:
            match = re.search(pattern, case, re.MULTILINE)
            assert match is not None, f"Pattern should match: {case}"
            assert len(match.group(1)) > 0

        # Invalid patterns
        invalid_cases = [
            "# Single Hash",          # Only one hash
            "#### Four Hashes",       # More than 3 hashes
            " ## Indented",           # Leading space
            "##No Space",             # No space after hashes
            "Normal text",            # No hashes
        ]

        for case in invalid_cases:
            match = re.search(pattern, case, re.MULTILINE)
            assert match is None, f"Pattern should not match: {case}"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_extract_features_unicode_content(self):
        """Test extraction with unicode content."""
        content = '''# Features 🚀

## Internationalization 🌍
Support for múltiple languages and émojis.

**Test Coverage**: `tests/test_i18n.py`

### Encoding Support
Handle UTF-8, UTF-16, and other encodings.

**Test Coverage**: `tests/tëst_encoding.py`
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_file_path = f.name

        try:
            features, test_files = extract_features_from_md(Path(temp_file_path))

            assert "Internationalization 🌍" in features
            assert "Encoding Support" in features
            assert "tests/test_i18n.py" in test_files
            assert "tests/tëst_encoding.py" in test_files
        finally:
            os.unlink(temp_file_path)

    def test_check_test_files_very_large_file(self, tmp_path):
        """Test checking very large test file."""
        project_root = tmp_path / "large_file_project"
        project_root.mkdir()

        tests_dir = project_root / "tests"
        tests_dir.mkdir()

        # Create large test file
        large_test_file = tests_dir / "test_large.py"
        large_content = "def test_function_{}(): pass\n" * 10000  # 10k test functions
        large_test_file.write_text(large_content)

        test_files = ["tests/test_large.py"]
        coverage_report = check_test_files(test_files, project_root)

        assert coverage_report["tests/test_large.py"]["exists"] is True
        assert coverage_report["tests/test_large.py"]["test_count"] == 10000

    def test_main_function_path_handling(self, tmp_path):
        """Test main function path handling edge cases."""
        # Test with symbolic links, if supported by the OS
        if hasattr(os, 'symlink'):
            project_root = tmp_path / "symlink_project"
            project_root.mkdir()

            # Create FEATURES.md
            features_md = project_root / "FEATURES.md"
            features_md.write_text("# Features\n## Test Feature\n**Test Coverage**: `tests/test.py`")

            # Create tests directory and file
            tests_dir = project_root / "tests"
            tests_dir.mkdir()
            (tests_dir / "test.py").write_text("def test_function(): pass")

            # Test that main function works with the real path
            with patch('tools.feature_inventory.Path') as mock_path:
                mock_path.__file__.parent.parent = project_root
                mock_path.return_value.exists.return_value = True

                # This should not raise an exception
                try:
                    original_cwd = os.getcwd()
                    os.chdir(project_root)
                    main()
                finally:
                    os.chdir(original_cwd)

    def test_check_test_files_concurrent_access(self, tmp_path):
        """Test check_test_files with concurrent file access scenarios."""
        project_root = tmp_path / "concurrent_project"
        project_root.mkdir()

        tests_dir = project_root / "tests"
        tests_dir.mkdir()

        test_file = tests_dir / "test_concurrent.py"
        test_file.write_text("def test_function(): pass")

        test_files = ["tests/test_concurrent.py"]

        # Simulate concurrent access by having multiple calls
        results = []
        for _ in range(5):
            result = check_test_files(test_files, project_root)
            results.append(result)

        # All results should be identical
        for result in results[1:]:
            assert result == results[0]