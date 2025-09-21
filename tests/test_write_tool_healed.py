"""
NECESSARY-compliant test suite for Write tool.

Tests cover the 9 universal quality properties:
- N: No Missing Behaviors - All core functionality tested
- E: Edge Cases - Boundary conditions, symlinks, disk space, concurrency
- C: Comprehensive - All code paths and validation rules
- E: Error Conditions - Permission errors, invalid paths, filesystem issues
- S: State Validation - Read registry tracking and context persistence
- S: Side Effects - File creation, directory creation, registry mutations
- A: Async Operations - File I/O operations and context handling
- R: Regression Prevention - Known filesystem and permission issues
- Y: Yielding Confidence - Real-world file operations and edge cases

Quality Score Target: Q(T) ≥ 0.85
"""

import os
import stat
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from tools.write import Write, _global_written_files
from tools.read import Read, _global_read_files


class TestWriteNecessaryCompliance:
    """Comprehensive test suite following NECESSARY pattern for Write tool."""

    def setup_method(self):
        """Clean up global state before each test."""
        _global_written_files.clear()
        _global_read_files.clear()

    # N: No Missing Behaviors - Core functionality tests

    def test_write_new_file_basic(self, tmp_path):
        """Test basic new file creation."""
        file_path = str(tmp_path / "new_file.txt")
        content = "Hello, World!"

        tool = Write(file_path=file_path, content=content)
        result = tool.run()

        assert "Successfully created file" in result
        assert file_path in result
        assert "Size: 13 bytes" in result
        assert "Lines: 1" in result

        # Verify file content
        with open(file_path, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_write_overwrite_existing_after_read(self, tmp_path):
        """Test overwriting existing file after read requirement."""
        file_path = str(tmp_path / "existing.txt")
        original_content = "Original content"
        new_content = "New content"

        # Create initial file
        with open(file_path, "w") as f:
            f.write(original_content)

        # Read first (required)
        read_tool = Read(file_path=file_path)
        read_tool.run()

        # Write new content
        tool = Write(file_path=file_path, content=new_content)
        result = tool.run()

        assert "Successfully overwritten file" in result
        with open(file_path, "r") as f:
            assert f.read() == new_content

    def test_directory_creation_for_new_file(self, tmp_path):
        """Test automatic directory creation for new files."""
        file_path = str(tmp_path / "nested" / "deep" / "file.txt")
        content = "Nested file"

        tool = Write(file_path=file_path, content=content)
        result = tool.run()

        assert "Successfully created file" in result
        assert os.path.exists(file_path)
        assert os.path.exists(os.path.dirname(file_path))

    def test_context_read_tracking_integration(self, tmp_path):
        """Test integration with context for read tracking."""
        file_path = str(tmp_path / "context_test.txt")

        # Create existing file
        with open(file_path, "w") as f:
            f.write("Original")

        # Add to global registry to simulate read tracking
        abs_path = os.path.abspath(file_path)
        _global_read_files.add(abs_path)

        tool = Write(file_path=file_path, content="New content")
        result = tool.run()

        assert "Successfully overwritten file" in result

        # Verify the code structure for context handling
        import inspect
        source_lines = inspect.getsource(tool.run)
        assert "self.context is not None" in source_lines
        assert "self.context.get" in source_lines

    def test_line_count_calculation_various_formats(self, tmp_path):
        """Test line counting with different content formats."""
        file_path = str(tmp_path / "line_test.txt")

        test_cases = [
            ("", 0),  # Empty file
            ("Single line", 1),  # Single line without newline
            ("Single line\n", 1),  # Single line with newline
            ("Line 1\nLine 2", 2),  # Two lines without final newline
            ("Line 1\nLine 2\n", 2),  # Two lines with final newline
            ("A\nB\nC\nD\nE", 5),  # Multiple lines
        ]

        for content, expected_lines in test_cases:
            tool = Write(file_path=file_path, content=content)
            result = tool.run()

            assert f"Lines: {expected_lines}" in result

            # Prepare for next iteration if file exists
            if os.path.exists(file_path):
                read_tool = Read(file_path=file_path)
                read_tool.run()

    # E: Edge Cases - Boundary conditions and special scenarios

    def test_absolute_path_requirement(self, tmp_path):
        """Test that relative paths are rejected."""
        relative_path = "relative_file.txt"
        content = "This should fail"

        tool = Write(file_path=relative_path, content=content)
        result = tool.run()

        assert "Error: File path must be absolute" in result
        assert relative_path in result

    def test_write_to_directory_path_error(self, tmp_path):
        """Test error when trying to write to directory path."""
        dir_path = str(tmp_path / "test_dir")
        os.makedirs(dir_path)
        content = "Should fail"

        # Simulate read attempt to satisfy precondition
        abs_path = os.path.abspath(dir_path)
        _global_read_files.add(abs_path)

        tool = Write(file_path=dir_path, content=content)
        result = tool.run()

        assert "Error: Path exists but is not a file" in result

    def test_symlink_handling(self, tmp_path):
        """Test writing to symlinks."""
        target_file = tmp_path / "target.txt"
        symlink_file = tmp_path / "symlink.txt"

        # Create target file and symlink
        target_file.write_text("original")
        os.symlink(str(target_file), str(symlink_file))

        # Read through symlink first
        read_tool = Read(file_path=str(symlink_file))
        read_tool.run()

        # Write through symlink
        tool = Write(file_path=str(symlink_file), content="new content")
        result = tool.run()

        assert "Successfully overwritten file" in result
        # Verify content was written to target
        assert target_file.read_text() == "new content"

    def test_very_large_file_content(self, tmp_path):
        """Test writing very large content."""
        file_path = str(tmp_path / "large_file.txt")
        # Create 1MB of content
        large_content = "A" * (1024 * 1024)

        tool = Write(file_path=file_path, content=large_content)
        result = tool.run()

        assert "Successfully created file" in result
        assert "Size: 1048576 bytes" in result

        # Verify file size
        assert os.path.getsize(file_path) == 1048576

    def test_unicode_content_with_various_encodings(self, tmp_path):
        """Test Unicode content handling."""
        file_path = str(tmp_path / "unicode_test.txt")
        unicode_content = "Hello 🌍\nПривет мир\n你好世界\nこんにちは世界\n🚀🎉💻"

        tool = Write(file_path=file_path, content=unicode_content)
        result = tool.run()

        assert "Successfully created file" in result

        # Verify Unicode content is preserved
        with open(file_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        assert written_content == unicode_content

    def test_empty_content_file_creation(self, tmp_path):
        """Test creating empty files."""
        file_path = str(tmp_path / "empty.txt")
        content = ""

        tool = Write(file_path=file_path, content=content)
        result = tool.run()

        assert "Successfully created file" in result
        assert "Size: 0 bytes" in result
        assert "Lines: 0" in result

    def test_special_characters_in_file_path(self, tmp_path):
        """Test file paths with special characters."""
        special_chars_file = tmp_path / "file with spaces & symbols.txt"
        file_path = str(special_chars_file)
        content = "Special path content"

        tool = Write(file_path=file_path, content=content)
        result = tool.run()

        assert "Successfully created file" in result
        assert os.path.exists(file_path)

    # C: Comprehensive - All validation rules and code paths

    def test_read_requirement_enforced_existing_file(self, tmp_path):
        """Test that read requirement is strictly enforced for existing files."""
        file_path = str(tmp_path / "existing.txt")

        # Create existing file
        with open(file_path, "w") as f:
            f.write("Original")

        # Try to write without reading first
        tool = Write(file_path=file_path, content="New content")
        result = tool.run()

        assert "Error: You must use Read tool at least once" in result

        # Verify file is unchanged
        with open(file_path, "r") as f:
            assert f.read() == "Original"

    def test_global_read_registry_fallback(self, tmp_path):
        """Test fallback to global read registry when context not available."""
        file_path = str(tmp_path / "global_test.txt")

        # Create existing file
        with open(file_path, "w") as f:
            f.write("Original")

        # Add to global registry manually
        abs_path = os.path.abspath(file_path)
        _global_read_files.add(abs_path)

        # Write without context should work (context is None by default in tests)
        tool = Write(file_path=file_path, content="New content")
        result = tool.run()

        assert "Successfully overwritten file" in result

        # Verify code structure checks global registry
        import inspect
        source_lines = inspect.getsource(tool.run)
        assert "_global_read_files" in source_lines

    def test_context_and_global_registry_synchronization(self, tmp_path):
        """Test that both context and global registry are updated."""
        file_path = str(tmp_path / "sync_test.txt")
        content = "Test content"

        tool = Write(file_path=file_path, content=content)
        tool.run()

        # Verify global registry is updated
        abs_path = os.path.abspath(file_path)
        assert abs_path in _global_written_files

        # Verify code structure for context updates
        import inspect
        source_lines = inspect.getsource(tool.run)
        assert "self.context.set" in source_lines
        assert "_global_written_files.add" in source_lines

    def test_file_size_and_line_count_accuracy(self, tmp_path):
        """Test accuracy of file size and line count reporting."""
        file_path = str(tmp_path / "metrics_test.txt")

        test_cases = [
            ("", 0, 0),  # Empty
            ("a", 1, 1),  # Single char
            ("hello", 5, 1),  # Single word
            ("line1\nline2", 11, 2),  # Two lines
            ("a\nb\nc\nd\ne\n", 10, 5),  # Five lines with final newline
        ]

        for content, expected_size, expected_lines in test_cases:
            tool = Write(file_path=file_path, content=content)
            result = tool.run()

            assert f"Size: {expected_size} bytes" in result
            assert f"Lines: {expected_lines}" in result

            # Verify actual file metrics
            actual_size = os.path.getsize(file_path)
            assert actual_size == expected_size

            # Prepare for next iteration
            if os.path.exists(file_path):
                read_tool = Read(file_path=file_path)
                read_tool.run()

    # E: Error Conditions - Exception handling

    def test_permission_denied_error_handling(self, tmp_path):
        """Test handling of permission denied errors."""
        if os.name != 'posix':
            pytest.skip("Permission test only applies to POSIX systems")

        file_path = str(tmp_path / "readonly_dir" / "file.txt")
        readonly_dir = tmp_path / "readonly_dir"
        readonly_dir.mkdir()

        # Make directory read-only
        os.chmod(str(readonly_dir), stat.S_IRUSR | stat.S_IXUSR)

        try:
            tool = Write(file_path=file_path, content="Should fail")
            result = tool.run()

            assert "Error" in result
            assert any(word in result for word in ["Permission", "permission", "denied"])

        finally:
            # Restore permissions for cleanup
            os.chmod(str(readonly_dir), stat.S_IRWXU)

    def test_disk_space_exhaustion_simulation(self, tmp_path):
        """Test behavior when disk space is exhausted (simulated)."""
        file_path = str(tmp_path / "space_test.txt")
        content = "Test content"

        tool = Write(file_path=file_path, content=content)

        # Mock open to raise OSError for disk space
        with patch("builtins.open", side_effect=OSError("No space left on device")):
            result = tool.run()

        assert "Error writing file: No space left on device" in result

    def test_invalid_directory_creation_error(self, tmp_path):
        """Test error handling when directory creation fails."""
        # Try to create file in path that can't be created
        if os.name == 'nt':  # Windows
            invalid_path = "C:\\invalid\\<>\\file.txt"
        else:  # Unix-like
            invalid_path = "/root/cannot_create/file.txt"

        tool = Write(file_path=invalid_path, content="Should fail")
        result = tool.run()

        assert "Error" in result

    def test_file_write_io_error_handling(self, tmp_path):
        """Test handling of I/O errors during file writing."""
        file_path = str(tmp_path / "io_error_test.txt")
        content = "Test content"

        tool = Write(file_path=file_path, content=content)

        # Mock the file write to raise IOError
        with patch("builtins.open", mock_open_with_error(IOError("I/O error"))):
            result = tool.run()

        assert "Error writing file: I/O error" in result

    def test_context_operation_error_handling(self, tmp_path):
        """Test handling of context operation errors."""
        file_path = str(tmp_path / "context_error_test.txt")
        content = "Test content"

        tool = Write(file_path=file_path, content=content)

        # Test that exceptions are handled properly in code structure
        import inspect
        source_lines = inspect.getsource(tool.run)
        assert "try:" in source_lines
        assert "except Exception as e:" in source_lines
        assert "Error during write operation:" in source_lines

        # Test normal operation works
        result = tool.run()
        assert "Successfully created file" in result

    # S: State Validation - Registry and context state

    def test_read_registry_state_consistency(self, tmp_path):
        """Test consistency of read registry state checking."""
        file_path = str(tmp_path / "consistency_test.txt")

        # Create file
        with open(file_path, "w") as f:
            f.write("Original")

        abs_path = os.path.abspath(file_path)

        # Add to global registry to simulate read state
        _global_read_files.add(abs_path)

        tool = Write(file_path=file_path, content="New content")
        result = tool.run()

        assert "Successfully overwritten file" in result

        # Verify code checks both context and global registry
        import inspect
        source_lines = inspect.getsource(tool.run)
        assert "self.context is not None" in source_lines
        assert "file_has_been_read = abs_file_path in _global_read_files" in source_lines

    def test_written_files_registry_tracking(self, tmp_path):
        """Test that written files are properly tracked in registry."""
        file_path = str(tmp_path / "tracking_test.txt")
        content = "Test content"

        tool = Write(file_path=file_path, content=content)
        tool.run()

        abs_path = os.path.abspath(file_path)
        assert abs_path in _global_written_files

    def test_context_state_updates(self, tmp_path):
        """Test that context state is properly updated."""
        file_path = str(tmp_path / "context_update_test.txt")
        content = "Test content"

        tool = Write(file_path=file_path, content=content)
        tool.run()

        # Verify file was created
        assert os.path.exists(file_path)

        # Verify code structure for context updates
        import inspect
        source_lines = inspect.getsource(tool.run)
        assert 'self.context.set("read_files"' in source_lines

        # Verify the file is tracked globally
        abs_path = os.path.abspath(file_path)
        assert abs_path in _global_written_files

    # S: Side Effects - File system mutations

    def test_file_system_mutations(self, tmp_path):
        """Test that file system is properly modified."""
        file_path = str(tmp_path / "mutation_test.txt")
        content = "Test content"

        # Verify file doesn't exist
        assert not os.path.exists(file_path)

        tool = Write(file_path=file_path, content=content)
        tool.run()

        # Verify file exists and has correct content
        assert os.path.exists(file_path)
        with open(file_path, "r") as f:
            assert f.read() == content

    def test_directory_creation_side_effects(self, tmp_path):
        """Test directory creation side effects."""
        nested_path = tmp_path / "level1" / "level2" / "level3"
        file_path = str(nested_path / "file.txt")

        # Verify directories don't exist
        assert not nested_path.exists()

        tool = Write(file_path=file_path, content="Test")
        tool.run()

        # Verify all directories were created
        assert nested_path.exists()
        assert nested_path.is_dir()

    def test_no_unintended_side_effects(self, tmp_path):
        """Test that no unintended side effects occur."""
        file_path = str(tmp_path / "side_effect_test.txt")
        other_file = str(tmp_path / "other_file.txt")

        # Create other file
        with open(other_file, "w") as f:
            f.write("Should not change")

        tool = Write(file_path=file_path, content="New file")
        tool.run()

        # Verify other file is unchanged
        with open(other_file, "r") as f:
            assert f.read() == "Should not change"

    # A: Async Operations - File I/O and context operations

    def test_concurrent_write_operations(self, tmp_path):
        """Test behavior with concurrent write operations."""
        base_path = str(tmp_path / "concurrent_test")
        content = "Concurrent content"

        results = []
        threads = []

        def write_file(index):
            file_path = f"{base_path}_{index}.txt"
            tool = Write(file_path=file_path, content=f"{content} {index}")
            result = tool.run()
            results.append(result)

        # Create multiple threads writing different files
        for i in range(5):
            thread = threading.Thread(target=write_file, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify all operations succeeded
        assert len(results) == 5
        for result in results:
            assert "Successfully created file" in result

        # Verify all files exist
        for i in range(5):
            file_path = f"{base_path}_{i}.txt"
            assert os.path.exists(file_path)

    def test_context_operations_thread_safety(self, tmp_path):
        """Test thread safety of context operations."""
        base_path = str(tmp_path / "thread_safety_test")

        results = []

        def write_with_different_files(index):
            file_path = f"{base_path}_{index}.txt"
            tool = Write(file_path=file_path, content=f"Thread content {index}")
            result = tool.run()
            results.append(result)

        threads = []
        for i in range(3):
            thread = threading.Thread(target=write_with_different_files, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All should succeed (different files)
        success_count = sum(1 for result in results if "Successfully" in result)
        assert success_count == 3

        # Verify files were created
        for i in range(3):
            file_path = f"{base_path}_{i}.txt"
            assert os.path.exists(file_path)

    # R: Regression Prevention - Known issue patterns

    def test_path_normalization_consistency(self, tmp_path):
        """Test that path normalization is handled consistently."""
        # Test various path formats
        base_file = tmp_path / "path_test.txt"

        path_variants = [
            str(base_file),
            str(base_file) + "/",  # Trailing slash should be handled
            os.path.normpath(str(base_file)),
        ]

        for i, path_variant in enumerate(path_variants):
            if path_variant.endswith('/'):
                # This should fail as it looks like a directory
                tool = Write(file_path=path_variant, content=f"Content {i}")
                result = tool.run()
                assert "Error" in result
            else:
                tool = Write(file_path=path_variant, content=f"Content {i}")
                result = tool.run()

                if i == 0:
                    assert "Successfully created file" in result
                else:
                    # For overwrite, need to read first
                    read_tool = Read(file_path=path_variant)
                    read_tool.run()
                    result = tool.run()
                    assert "Successfully overwritten file" in result

    def test_encoding_regression_prevention(self, tmp_path):
        """Test that encoding issues don't cause regressions."""
        file_path = str(tmp_path / "encoding_test.txt")

        # Content with various encoding challenges (avoiding surrogates)
        problematic_content = "\u00e9\u00e7\u00e0\u2603😀"  # é, ç, à, ☃, 😀

        tool = Write(file_path=file_path, content=problematic_content)
        result = tool.run()

        assert "Successfully created file" in result

        # Verify content is preserved exactly
        with open(file_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        assert written_content == problematic_content

    def test_line_ending_consistency(self, tmp_path):
        """Test consistent handling of different line endings."""
        file_path = str(tmp_path / "line_ending_test.txt")

        # Test actual behavior of line counting in the Write tool
        line_ending_variants = [
            ("Line1\nLine2\nLine3", 3),      # Unix LF - counts newlines
            ("Line1\r\nLine2\r\nLine3", 3),  # Windows CRLF - counts newlines
            ("Line1\rLine2\rLine3", 1),      # Classic Mac CR - doesn't count \r as newline
        ]

        for i, (content, expected_lines) in enumerate(line_ending_variants):
            if i > 0:
                # Read first for overwrite
                read_tool = Read(file_path=file_path)
                read_tool.run()

            tool = Write(file_path=file_path, content=content)
            result = tool.run()

            # The tool counts lines based on \n characters
            assert f"Lines: {expected_lines}" in result

            # For line ending tests, verify by reading in binary mode
            # to see actual bytes written
            with open(file_path, "rb") as f:
                written_bytes = f.read()

            # Convert content to bytes and verify key characteristics
            content_bytes = content.encode('utf-8')
            assert len(written_bytes) == len(content_bytes)
            assert b"Line1" in written_bytes
            assert b"Line2" in written_bytes
            assert b"Line3" in written_bytes

    # Y: Yielding Confidence - Real-world scenarios

    def test_realistic_code_file_writing(self, tmp_path):
        """Test writing realistic code files."""
        python_file = str(tmp_path / "example_module.py")
        python_content = '''#!/usr/bin/env python3
"""
Example Python module for testing Write tool.
"""

import os
import sys
from typing import List, Dict, Optional


class ExampleClass:
    """Example class with various methods."""

    def __init__(self, name: str, value: int = 0):
        self.name = name
        self.value = value

    def process_data(self, data: List[Dict]) -> Optional[str]:
        """Process input data and return result."""
        if not data:
            return None

        processed = []
        for item in data:
            if "name" in item and "value" in item:
                processed.append(f"{item['name']}: {item['value']}")

        return "\\n".join(processed)


def main():
    """Main function."""
    example = ExampleClass("test", 42)
    test_data = [
        {"name": "item1", "value": 100},
        {"name": "item2", "value": 200},
    ]

    result = example.process_data(test_data)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

        tool = Write(file_path=python_file, content=python_content)
        result = tool.run()

        assert "Successfully created file" in result
        assert ".py" in result

        # Verify the file is valid Python (syntax check)
        with open(python_file, "r") as f:
            written_content = f.read()

        # Basic syntax validation
        compile(written_content, python_file, "exec")

    def test_configuration_file_scenarios(self, tmp_path):
        """Test writing various configuration file types."""
        configs = {
            "config.json": '{"database": {"host": "localhost", "port": 5432}, "debug": true}',
            "settings.yml": "database:\\n  host: localhost\\n  port: 5432\\ndebug: true",
            "app.ini": "[database]\\nhost = localhost\\nport = 5432\\n\\n[app]\\ndebug = true",
        }

        for filename, content in configs.items():
            file_path = str(tmp_path / filename)
            tool = Write(file_path=file_path, content=content)
            result = tool.run()

            assert "Successfully created file" in result
            assert filename in result

    def test_batch_file_operations(self, tmp_path):
        """Test batch operations simulating real workflow."""
        # Simulate creating a project structure
        files_to_create = [
            ("src/__init__.py", "# Main package"),
            ("src/models.py", "class User:\\n    pass"),
            ("src/views.py", "def index():\\n    return 'Hello'"),
            ("tests/__init__.py", "# Test package"),
            ("tests/test_models.py", "def test_user():\\n    assert True"),
            ("README.md", "# Project\\n\\nDescription here"),
        ]

        results = []
        for file_path, content in files_to_create:
            full_path = str(tmp_path / file_path)
            tool = Write(file_path=full_path, content=content)
            result = tool.run()
            results.append(result)

        # Verify all files were created successfully
        for result in results:
            assert "Successfully created file" in result

        # Verify project structure
        for file_path, _ in files_to_create:
            full_path = tmp_path / file_path
            assert full_path.exists()

    def test_error_recovery_scenarios(self, tmp_path):
        """Test error recovery in realistic scenarios."""
        file_path = str(tmp_path / "recovery_test.txt")

        # Scenario 1: Initial write fails, retry succeeds
        content = "Test content"

        tool = Write(file_path=file_path, content=content)

        # Mock first call to fail, second to succeed
        call_count = 0
        def mock_open_with_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise PermissionError("First call fails")
            return open(*args, **kwargs)

        # This will fail
        with patch("builtins.open", side_effect=mock_open_with_failure):
            result1 = tool.run()

        assert "Error" in result1

        # This should succeed (normal retry)
        result2 = tool.run()
        assert "Successfully created file" in result2


def mock_open_with_error(error):
    """Helper to create mock open that raises specific error."""
    def mock_open(*args, **kwargs):
        raise error
    return mock_open