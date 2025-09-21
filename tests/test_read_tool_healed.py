"""
NECESSARY-compliant tests for tools/read.py

This test suite addresses the critical violations identified in the audit:
- Q(T) Score: 0.43 (CRITICAL) -> targeting 0.85+
- Missing coverage for binary files, encoding, truncation, images, notebooks
- Error Conditions score: 0.30 -> targeting 0.80+
- Edge Cases score: 0.35 -> targeting 0.80+

Tests follow the NECESSARY pattern:
N - No Missing Behaviors
E - Edge Cases
C - Comprehensive
E - Error Conditions
S - State Validation
S - Side Effects
A - Async Operations
R - Regression Prevention
Y - Yielding Confidence
"""
import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tools import Read


class TestReadToolNecessary:
    """NECESSARY-compliant test suite for Read tool."""

    def test_read_nonexistent_file_error_condition(self):
        """Test error handling when file does not exist (ERROR CONDITIONS)."""
        tool = Read(file_path="/nonexistent/path/file.txt")
        result = tool.run()
        assert "Error: File does not exist:" in result
        assert "/nonexistent/path/file.txt" in result

    def test_read_directory_instead_of_file_error_condition(self, tmp_path: Path):
        """Test error handling when path is directory not file (ERROR CONDITIONS)."""
        directory = tmp_path / "test_dir"
        directory.mkdir()

        tool = Read(file_path=str(directory))
        result = tool.run()
        assert "Error: Path is not a file:" in result
        assert str(directory) in result

    def test_read_permission_denied_error_condition(self, tmp_path: Path):
        """Test error handling for permission denied scenarios (ERROR CONDITIONS)."""
        if os.name == 'nt':  # Windows
            pytest.skip("Permission tests not reliable on Windows")

        test_file = tmp_path / "restricted.txt"
        test_file.write_text("secret content")

        # Remove read permissions
        os.chmod(test_file, 0o000)

        try:
            tool = Read(file_path=str(test_file))
            result = tool.run()
            assert "Error: Permission denied reading file:" in result
        finally:
            # Restore permissions for cleanup
            os.chmod(test_file, 0o644)

    def test_read_binary_file_detection_and_encoding_fallback(self, tmp_path: Path):
        """Test binary file detection and encoding fallback mechanisms (NO MISSING BEHAVIORS)."""
        # Create a file with binary content that will cause UnicodeDecodeError in UTF-8
        # but can be read with latin-1 (which accepts all byte values)
        binary_file = tmp_path / "binary.bin"
        with open(binary_file, "wb") as f:
            f.write(b'\x80\x81\x82\x83\x84\x85')  # Invalid UTF-8 bytes

        tool = Read(file_path=str(binary_file))
        result = tool.run()

        # The tool should successfully read with latin-1 fallback OR detect as binary
        # Latin-1 can decode any byte sequence, so it will likely succeed
        assert ("Error: Unable to decode file" in result or
                "binary file" in result or
                "\t" in result)  # Successfully read with formatting

    def test_read_encoding_fallback_latin1_success(self, tmp_path: Path):
        """Test successful latin-1 encoding fallback (NO MISSING BEHAVIORS)."""
        # Create file with latin-1 content that's invalid UTF-8
        latin1_file = tmp_path / "latin1.txt"
        latin1_content = "Café\n".encode('latin-1')  # Contains special character
        with open(latin1_file, "wb") as f:
            f.write(latin1_content)

        tool = Read(file_path=str(latin1_file))
        result = tool.run()

        # Should successfully read with latin-1 fallback
        assert "Café" in result or "Error:" not in result

    def test_read_image_file_detection_png(self, tmp_path: Path):
        """Test image file detection for PNG files (NO MISSING BEHAVIORS)."""
        image_file = tmp_path / "test.png"
        # Create minimal PNG file header
        png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        image_file.write_bytes(png_header)

        tool = Read(file_path=str(image_file))
        result = tool.run()

        assert "[IMAGE FILE:" in result
        assert "image/" in result
        assert "multimodal environment" in result

    def test_read_image_file_detection_jpg(self, tmp_path: Path):
        """Test image file detection for JPG files (NO MISSING BEHAVIORS)."""
        image_file = tmp_path / "test.jpg"
        # Create minimal JPEG file header
        jpeg_header = b'\xff\xd8\xff\xe0'
        image_file.write_bytes(jpeg_header)

        tool = Read(file_path=str(image_file))
        result = tool.run()

        assert "[IMAGE FILE:" in result
        assert "image/" in result or "jpg" in result.lower()

    def test_read_jupyter_notebook_detection(self, tmp_path: Path):
        """Test Jupyter notebook detection and redirect (NO MISSING BEHAVIORS)."""
        notebook_file = tmp_path / "test.ipynb"
        notebook_content = '{"cells": [], "metadata": {}, "nbformat": 4}'
        notebook_file.write_text(notebook_content)

        tool = Read(file_path=str(notebook_file))
        result = tool.run()

        assert "Error: This is a Jupyter notebook file" in result
        assert "NotebookRead tool" in result

    def test_read_line_truncation_over_2000_chars(self, tmp_path: Path):
        """Test line truncation for lines over 2000 characters (EDGE CASES)."""
        long_line_file = tmp_path / "long_line.txt"
        # Create a line with 2500 characters
        long_line = "x" * 2500 + "\n"
        long_line_file.write_text(long_line)

        tool = Read(file_path=str(long_line_file))
        result = tool.run()

        # Line should be truncated to 1997 chars + "..."
        lines = result.split('\n')
        content_line = [line for line in lines if '\t' in line][0]
        line_content = content_line.split('\t', 1)[1]
        assert line_content.endswith("...")
        assert len(line_content) <= 2000

    def test_read_empty_file_warning(self, tmp_path: Path):
        """Test empty file handling with warning message (EDGE CASES)."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        tool = Read(file_path=str(empty_file))
        result = tool.run()

        assert "Warning: File exists but has empty contents" in result
        assert str(empty_file) in result

    def test_read_file_with_special_characters(self, tmp_path: Path):
        """Test reading files with special Unicode characters (EDGE CASES)."""
        special_file = tmp_path / "special.txt"
        special_content = "Hello 🌍\nLine with emoji 😀\n中文测试\n"
        special_file.write_text(special_content, encoding='utf-8')

        tool = Read(file_path=str(special_file))
        result = tool.run()

        assert "🌍" in result
        assert "😀" in result
        assert "中文测试" in result
        assert "\t" in result  # cat -n format

    def test_read_offset_beyond_file_length(self, tmp_path: Path):
        """Test offset parameter beyond file length (EDGE CASES)."""
        short_file = tmp_path / "short.txt"
        short_file.write_text("line1\nline2\nline3\n")

        tool = Read(file_path=str(short_file), offset=100)
        result = tool.run()

        # Should handle gracefully, return empty or appropriate message
        assert "Error:" not in result

    def test_read_negative_offset_handling(self, tmp_path: Path):
        """Test negative offset parameter handling (EDGE CASES)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("line1\nline2\nline3\n")

        tool = Read(file_path=str(test_file), offset=-5)
        result = tool.run()

        # Should start from beginning (offset clamped to 0)
        assert "\tline1" in result

    def test_read_context_tracking_state_validation(self, tmp_path: Path):
        """Test that read files are tracked in context (STATE VALIDATION)."""
        test_file = tmp_path / "tracked.txt"
        test_file.write_text("content")

        # Test that reading works with no context (falls back to global registry)
        tool = Read(file_path=str(test_file))
        result = tool.run()

        # Should complete successfully without context
        assert "content" in result
        assert "Error:" not in result

        # If context is None, the code should handle gracefully and use global registry

    def test_read_global_registry_side_effect(self, tmp_path: Path):
        """Test global registry side effect for persistence (SIDE EFFECTS)."""
        from tools.read import _global_read_files

        test_file = tmp_path / "global_test.txt"
        test_file.write_text("content")

        # Clear global registry
        _global_read_files.clear()

        tool = Read(file_path=str(test_file))
        tool.run()

        # Verify file was added to global registry
        abs_path = os.path.abspath(str(test_file))
        assert abs_path in _global_read_files

    def test_read_large_file_default_limit_2000_lines(self, tmp_path: Path):
        """Test default 2000 line limit for large files (COMPREHENSIVE)."""
        large_file = tmp_path / "large.txt"
        content = "".join(f"line {i}\n" for i in range(1, 3000))
        large_file.write_text(content)

        tool = Read(file_path=str(large_file))
        result = tool.run()

        # Should show truncation message
        assert "Truncated: showing first 2000 of 2999 total lines" in result

        # Count actual lines in output
        lines_with_content = [line for line in result.split('\n') if '\t' in line]
        assert len(lines_with_content) == 2000

    def test_read_symlink_handling(self, tmp_path: Path):
        """Test reading through symbolic links (EDGE CASES)."""
        if os.name == 'nt':  # Windows
            pytest.skip("Symlink tests not reliable on Windows")

        target_file = tmp_path / "target.txt"
        target_file.write_text("target content\n")

        symlink_file = tmp_path / "link.txt"
        symlink_file.symlink_to(target_file)

        tool = Read(file_path=str(symlink_file))
        result = tool.run()

        assert "target content" in result
        assert "Error:" not in result

    def test_read_file_with_various_line_endings(self, tmp_path: Path):
        """Test handling different line ending formats (COMPREHENSIVE)."""
        mixed_file = tmp_path / "mixed_endings.txt"
        # Mix of Unix (\n), Windows (\r\n), and old Mac (\r) line endings
        content = "unix\nwindows\r\nmac\rend"
        with open(mixed_file, 'wb') as f:
            f.write(content.encode('utf-8'))

        tool = Read(file_path=str(mixed_file))
        result = tool.run()

        # Should handle different line endings gracefully
        assert "unix" in result
        assert "windows" in result
        assert "mac" in result

    def test_read_exception_handling_comprehensive(self, tmp_path: Path):
        """Test comprehensive exception handling for unexpected errors (ERROR CONDITIONS)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        # Mock file operations to raise unexpected exception
        with patch('builtins.open', side_effect=OSError("Disk error")):
            tool = Read(file_path=str(test_file))
            result = tool.run()

            assert "Error reading file:" in result
            assert "Disk error" in result

    def test_read_cat_format_line_numbering_precision(self, tmp_path: Path):
        """Test precise cat -n format with right-aligned 6-width line numbers (COMPREHENSIVE)."""
        test_file = tmp_path / "numbering.txt"
        content = "".join(f"content line {i}\n" for i in range(1, 15))
        test_file.write_text(content)

        tool = Read(file_path=str(test_file))
        result = tool.run()

        lines = result.split('\n')
        content_lines = [line for line in lines if '\t' in line]

        # Check format: right-aligned 6-width number + tab + content
        assert content_lines[0].startswith("     1\t")  # 5 spaces + 1 + tab
        assert content_lines[9].startswith("    10\t")  # 4 spaces + 10 + tab

        # Verify tab separation
        for line in content_lines[:10]:
            parts = line.split('\t', 1)
            assert len(parts) == 2
            assert parts[0].strip().isdigit()

    def test_read_regression_prevention_offset_limit_combination(self, tmp_path: Path):
        """Test offset and limit combination edge cases (REGRESSION PREVENTION)."""
        test_file = tmp_path / "offset_limit.txt"
        content = "".join(f"line {i}\n" for i in range(1, 101))
        test_file.write_text(content)

        # Test various combinations
        tool1 = Read(file_path=str(test_file), offset=50, limit=10)
        result1 = tool1.run()

        tool2 = Read(file_path=str(test_file), offset=95, limit=20)
        result2 = tool2.run()

        # Verify offset 50, limit 10 shows lines 50-59
        assert "    50\tline 50" in result1
        assert "    59\tline 59" in result1
        assert "line 60" not in result1

        # Verify offset 95, limit 20 handles end-of-file gracefully
        assert "    95\tline 95" in result2
        assert "   100\tline 100" in result2
        # Should not error when requesting beyond file end

    def test_read_confidence_yielding_complete_workflow(self, tmp_path: Path):
        """Test complete read workflow yielding confidence in tool reliability (YIELDING CONFIDENCE)."""
        # Create a realistic file scenario
        realistic_file = tmp_path / "realistic.py"
        realistic_content = '''"""
A realistic Python file for testing read tool.
"""
import os
import sys
from pathlib import Path

def example_function():
    """Example function with docstring."""
    return "Hello, World!"

if __name__ == "__main__":
    print(example_function())
'''
        realistic_file.write_text(realistic_content)

        # Test complete read
        tool = Read(file_path=str(realistic_file))
        result = tool.run()

        # Verify all expected elements are present
        assert '"""' in result
        assert 'import os' in result
        assert 'def example_function' in result
        assert '__name__' in result

        # Verify formatting
        assert '\t' in result  # Tab separation
        lines_with_numbers = [line for line in result.split('\n') if '\t' in line]
        assert len(lines_with_numbers) > 10  # Reasonable number of lines

        # Verify line numbering starts at 1
        first_line = lines_with_numbers[0]
        assert first_line.split('\t')[0].strip() == "1"

        # No errors should occur
        assert "Error:" not in result
        assert "Warning:" not in result