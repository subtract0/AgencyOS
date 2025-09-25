"""
Tests for autonomous healing patch application and verification.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open

from tools.apply_and_verify_patch import ApplyAndVerifyPatch


class TestApplyAndVerifyPatch:
    """Test the complete patch application and verification workflow."""

    @patch('tools.apply_and_verify_patch.Read')
    @patch('tools.apply_and_verify_patch.Edit')
    @patch('tools.apply_and_verify_patch.Bash')
    @patch('subprocess.run')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    def test_successful_healing_cycle(self, mock_makedirs, mock_file, mock_subprocess, mock_bash, mock_edit, mock_read):
        """Test complete successful autonomous healing cycle."""

        # Mock file reading
        mock_read.return_value.run.return_value = "original content"

        # Mock successful edit
        mock_edit.return_value.run.return_value = "File has been updated successfully"

        # Mock successful test run
        mock_bash.return_value.run.return_value = "✅ All tests passed!\ncollected 689 items\nTEST EXECUTION COMPLETE"

        # Mock successful git operations
        mock_subprocess.side_effect = [
            MagicMock(returncode=0, stderr=""),  # git add
            MagicMock(returncode=0, stderr=""),  # git commit
            MagicMock(returncode=0, stdout="abc123def456", stderr="")  # git rev-parse
        ]

        tool = ApplyAndVerifyPatch(
            file_path="/test/file.py",
            original_code="obj.attribute",
            fixed_code="if obj is not None:\n    obj.attribute",
            error_description="AttributeError: 'NoneType' object has no attribute 'attribute'"
        )

        result = tool.run()

        assert "🎉 AUTONOMOUS HEALING COMPLETE!" in result
        assert "✅ PATCH: Applied successfully" in result
        assert "✅ TESTS: All tests passing" in result
        assert "✅ COMMIT:" in result

    @patch('tools.apply_and_verify_patch.Read')
    def test_file_read_failure(self, mock_read):
        """Test handling of file read failures."""

        mock_read.side_effect = Exception("File not found")

        tool = ApplyAndVerifyPatch(
            file_path="/nonexistent/file.py",
            original_code="test",
            fixed_code="fixed test",
            error_description="Test error"
        )

        result = tool.run()

        assert "❌ FAILED: Cannot read file" in result

    @patch('tools.apply_and_verify_patch.Read')
    @patch('tools.apply_and_verify_patch.Edit')
    @patch('tools.apply_and_verify_patch.Bash')
    @patch('builtins.open', new_callable=mock_open)
    def test_test_failure_reverts_changes(self, mock_file, mock_bash, mock_edit, mock_read):
        """Test that test failures cause changes to be reverted."""

        original_content = "original content"
        mock_read.return_value.run.return_value = original_content
        mock_edit.return_value.run.return_value = "File has been updated successfully"

        # Mock test failure
        mock_bash.return_value.run.return_value = "FAILED tests/test_something.py"

        tool = ApplyAndVerifyPatch(
            file_path="/test/file.py",
            original_code="obj.attribute",
            fixed_code="if obj is not None:\n    obj.attribute",
            error_description="Test error"
        )

        result = tool.run()

        assert "❌ HEALING FAILED: Tests failed after applying patch" in result
        assert "The file has been restored to its original state" in result


if __name__ == "__main__":
    # Skip nested pytest execution to prevent recursion
    import os
    if os.environ.get("AGENCY_NESTED_TEST") != "1":
        pytest.main([__file__])