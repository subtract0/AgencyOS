"""
Tests for focused NoneType auto-fix functionality.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, mock_open

from tools.auto_fix_nonetype import (
    NoneTypeErrorDetector,
    LLMNoneTypeFixer,
    AutoNoneTypeFixer,
    SimpleNoneTypeMonitor
)


class TestNoneTypeErrorDetector:
    """Test NoneType error detection."""

    def test_detects_attribute_error(self):
        """Should detect AttributeError NoneType issues."""
        log_content = """
        File "/path/to/file.py", line 42, in function
            result = obj.attribute
        AttributeError: 'NoneType' object has no attribute 'attribute'
        """

        detector = NoneTypeErrorDetector(log_content=log_content)
        result = detector.run()

        data = json.loads(result)
        assert data["status"] == "errors_detected"
        assert data["count"] == 1
        assert data["errors"][0]["error_type"] == "NoneType"
        assert data["errors"][0]["attribute"] == "attribute"
        assert data["errors"][0]["line_number"] == "42"

    def test_detects_type_error(self):
        """Should detect TypeError NoneType issues."""
        log_content = """
        TypeError: 'NoneType' object is not iterable
        """

        detector = NoneTypeErrorDetector(log_content=log_content)
        result = detector.run()

        data = json.loads(result)
        assert data["status"] == "errors_detected"
        assert data["count"] == 1

    def test_no_errors_found(self):
        """Should handle cases with no NoneType errors."""
        log_content = "Everything is working fine"

        detector = NoneTypeErrorDetector(log_content=log_content)
        result = detector.run()

        data = json.loads(result)
        assert data["status"] == "no_nonetype_errors"

    def test_multiple_errors(self):
        """Should detect multiple NoneType errors."""
        log_content = """
        AttributeError: 'NoneType' object has no attribute 'method1'
        TypeError: 'NoneType' object is not callable
        AttributeError: 'NoneType' object has no attribute 'method2'
        """

        detector = NoneTypeErrorDetector(log_content=log_content)
        result = detector.run()

        data = json.loads(result)
        assert data["status"] == "errors_detected"
        assert data["count"] >= 2  # Should find multiple errors


class TestLLMNoneTypeFixer:
    """Test LLM-based fix generation."""

    def test_generates_attribute_fix(self):
        """Should generate appropriate fix for attribute access."""
        error_info = json.dumps({
            "status": "errors_detected",
            "count": 1,
            "errors": [{
                "error_type": "NoneType",
                "pattern": "AttributeError: 'NoneType' object has no attribute 'value'",
                "file_path": "test.py",
                "line_number": "10",
                "attribute": "value"
            }]
        })

        fixer = LLMNoneTypeFixer(
            error_info=error_info,
            code_context="variable = get_data()\nresult = variable.value"
        )
        result = fixer.run()

        data = json.loads(result)
        assert data["status"] == "fixes_generated"
        assert len(data["fixes"]) == 1
        assert "null check" in data["fixes"][0]["fix_suggestion"].lower()
        assert "GPT-5 PROMPT" in data["fixes"][0]["fix_suggestion"]

    def test_generates_iteration_fix(self):
        """Should generate appropriate fix for iteration errors."""
        error_info = json.dumps({
            "status": "errors_detected",
            "count": 1,
            "errors": [{
                "error_type": "NoneType",
                "pattern": "TypeError: argument of type 'NoneType' is not iterable",
                "file_path": "test.py",
                "line_number": "15",
                "attribute": None
            }]
        })

        fixer = LLMNoneTypeFixer(error_info=error_info)
        result = fixer.run()

        data = json.loads(result)
        assert data["status"] == "fixes_generated"
        assert "iterable" in data["fixes"][0]["fix_suggestion"].lower()

    def test_handles_no_errors(self):
        """Should handle case with no errors to fix."""
        error_info = json.dumps({"status": "no_nonetype_errors"})

        fixer = LLMNoneTypeFixer(error_info=error_info)
        result = fixer.run()

        assert "No NoneType errors to fix" in result


class TestAutoNoneTypeFixer:
    """Test complete auto-fix workflow."""

    @patch('tools.auto_fix_nonetype.Read')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    def test_complete_workflow(self, mock_makedirs, mock_file, mock_read):
        """Should complete full auto-fix workflow."""
        # Mock file reading
        mock_read.return_value.run.return_value = "def function():\n    return obj.value"

        error_message = "AttributeError: 'NoneType' object has no attribute 'value'"

        fixer = AutoNoneTypeFixer(
            file_path="/test/file.py",
            error_message=error_message
        )
        result = fixer.run()

        assert "AUTO-FIX ANALYSIS COMPLETE" in result
        assert "FIXES GENERATED" in result
        assert "GPT-5 prompts" in result
        mock_makedirs.assert_called_with("logs/auto_fixes", exist_ok=True)

    @patch('tools.auto_fix_nonetype.Read')
    def test_handles_file_read_error(self, mock_read):
        """Should handle file reading errors gracefully."""
        mock_read.side_effect = Exception("File not found")

        # Use an error message that will be detected
        error_message = "AttributeError: 'NoneType' object has no attribute 'value'"

        fixer = AutoNoneTypeFixer(
            file_path="/nonexistent/file.py",
            error_message=error_message
        )
        result = fixer.run()

        assert "Failed to read file" in result


class TestSimpleNoneTypeMonitor:
    """Test simple monitoring functionality."""

    @patch('os.path.exists')
    @patch('os.listdir')
    def test_no_logs_directory(self, mock_listdir, mock_exists):
        """Should handle missing log directories."""
        mock_exists.return_value = False

        monitor = SimpleNoneTypeMonitor()
        result = monitor.run()

        assert "No NoneType errors detected" in result

    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('os.path.getmtime')
    @patch('builtins.open', new_callable=mock_open)
    def test_finds_errors_in_logs(self, mock_file, mock_getmtime, mock_listdir, mock_exists):
        """Should find errors in log files."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["test.log"]
        mock_getmtime.return_value = 9999999999  # Recent timestamp
        mock_file.return_value.read.return_value = "AttributeError: 'NoneType' object has no attribute 'test'"

        monitor = SimpleNoneTypeMonitor()
        result = monitor.run()

        assert "NONETYPE ERRORS DETECTED" in result

    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('os.path.getmtime')
    @patch('builtins.open', new_callable=mock_open)
    def test_skips_old_files(self, mock_file, mock_getmtime, mock_listdir, mock_exists):
        """Should skip old log files."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["old.log"]
        mock_getmtime.return_value = 0  # Very old timestamp

        monitor = SimpleNoneTypeMonitor()
        result = monitor.run()

        assert "No NoneType errors detected" in result


class TestIntegration:
    """Integration tests for the complete auto-fix system."""

    def test_end_to_end_workflow(self):
        """Test the complete workflow from detection to fix suggestion."""
        # Simulate an error message
        error_message = """
        File "/app/test.py", line 25, in process_data
            return data.value
        AttributeError: 'NoneType' object has no attribute 'value'
        """

        # Step 1: Detect error
        detector = NoneTypeErrorDetector(log_content=error_message)
        detection_result = detector.run()

        data = json.loads(detection_result)
        assert data["status"] == "errors_detected"

        # Step 2: Generate fix
        fixer = LLMNoneTypeFixer(
            error_info=detection_result,
            code_context="def process_data(data):\n    return data.value"
        )
        fix_result = fixer.run()

        fix_data = json.loads(fix_result)
        assert fix_data["status"] == "fixes_generated"
        assert len(fix_data["fixes"]) > 0
        assert "GPT-5 PROMPT" in fix_data["fixes"][0]["fix_suggestion"]

        # Verify the fix contains practical guidance
        fix_suggestion = fix_data["fixes"][0]["fix_suggestion"]
        assert "null check" in fix_suggestion.lower()
        assert "if" in fix_suggestion  # Should suggest conditional logic


if __name__ == "__main__":
    # Skip nested pytest execution to prevent recursion
    import os
    if os.environ.get("AGENCY_NESTED_TEST") != "1":
        pytest.main([__file__])