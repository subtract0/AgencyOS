"""Security Tests for Anthropic Memory Tool

Tests path traversal prevention, access control, and other security features.

Test Coverage:
- Path traversal attack prevention (../, ../../, etc.)
- URL-encoded traversal prevention (%2e%2e%2f, %252e%252e)
- Root directory protection
- File size limits
- Path validation edge cases
"""

import os
import tempfile
from pathlib import Path

import pytest

from tools.anthropic_memory_tool import AgencyMemoryTool, create_memory_tool


class TestPathTraversalSecurity:
    """Test suite for path traversal attack prevention"""

    @pytest.fixture
    def memory_tool(self, tmp_path):
        """Create memory tool with temporary base directory"""
        return AgencyMemoryTool(base_dir=str(tmp_path / "memories"))

    def test_valid_path_accepted(self, memory_tool):
        """Valid paths within /memories should be accepted"""
        # These should not raise
        memory_tool._validate_path("/memories/notes.txt")
        memory_tool._validate_path("/memories/subdir/file.txt")
        memory_tool._validate_path("/memories/deep/nested/path/file.txt")

    def test_parent_directory_blocked(self, memory_tool):
        """Parent directory traversal should be blocked"""
        with pytest.raises(ValueError, match="traversal"):
            memory_tool._validate_path("/memories/../etc/passwd")

    def test_double_parent_directory_blocked(self, memory_tool):
        """Multiple parent directory traversals should be blocked"""
        with pytest.raises(ValueError, match="traversal"):
            memory_tool._validate_path("/memories/../../etc/passwd")

    def test_url_encoded_traversal_blocked(self, memory_tool):
        """URL-encoded traversal should be blocked"""
        with pytest.raises(ValueError, match="traversal"):
            memory_tool._validate_path("/memories/%2e%2e/etc/passwd")

    def test_double_encoded_traversal_blocked(self, memory_tool):
        """Double URL-encoded traversal should be blocked"""
        with pytest.raises(ValueError, match="traversal"):
            memory_tool._validate_path("/memories/%252e%252e/etc/passwd")

    def test_mixed_encoding_traversal_blocked(self, memory_tool):
        """Mixed encoding traversal should be blocked"""
        with pytest.raises(ValueError, match="traversal"):
            memory_tool._validate_path("/memories/.%2e/etc/passwd")

    def test_path_without_memories_prefix_blocked(self, memory_tool):
        """Paths not starting with /memories should be rejected"""
        with pytest.raises(ValueError, match="must start with /memories"):
            memory_tool._validate_path("/etc/passwd")

        with pytest.raises(ValueError, match="must start with /memories"):
            memory_tool._validate_path("notes.txt")

    def test_symlink_escape_prevented(self, memory_tool, tmp_path):
        """Symlinks pointing outside base_dir should be blocked"""
        # Create symlink pointing outside
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("secret")

        symlink_path = memory_tool.base_dir / "link"
        memory_tool.base_dir.mkdir(parents=True, exist_ok=True)

        # This test requires actual symlink creation
        # Skip on Windows if symlinks not supported
        try:
            os.symlink(str(outside_file), str(symlink_path))
        except OSError:
            pytest.skip("Symlinks not supported")

        # Attempting to access via symlink should fail validation
        with pytest.raises(ValueError, match="escapes memory directory"):
            validated = memory_tool._validate_path("/memories/link")
            # Force resolution to detect escape
            validated.resolve().relative_to(memory_tool.base_dir)


class TestFileOperationSecurity:
    """Test suite for file operation security"""

    @pytest.fixture
    def memory_tool(self, tmp_path):
        """Create memory tool with temporary base directory"""
        tool = AgencyMemoryTool(base_dir=str(tmp_path / "memories"), max_file_size=100)
        tool.base_dir.mkdir(parents=True, exist_ok=True)
        return tool

    def test_file_size_limit_enforced_on_create(self, memory_tool):
        """File creation should respect size limits"""
        large_content = "x" * 1000  # Exceeds 100 byte limit
        result = memory_tool.create("/memories/large.txt", large_content)
        assert "exceeds size limit" in result

    def test_file_size_limit_enforced_on_replace(self, memory_tool):
        """Text replacement should respect size limits"""
        # Create small file
        memory_tool.create("/memories/test.txt", "small")

        # Try to replace with large content
        large_replacement = "x" * 1000
        result = memory_tool.str_replace("/memories/test.txt", "small", large_replacement)
        assert "exceeds size limit" in result

    def test_file_size_limit_enforced_on_insert(self, memory_tool):
        """Text insertion should respect size limits"""
        # Create small file
        memory_tool.create("/memories/test.txt", "small")

        # Try to insert large content
        large_insertion = "x" * 1000
        result = memory_tool.insert("/memories/test.txt", 1, large_insertion)
        assert "exceeds size limit" in result

    def test_cannot_overwrite_directory(self, memory_tool):
        """Creating file should not overwrite existing directory"""
        # Create directory
        (memory_tool.base_dir / "testdir").mkdir()

        # Try to create file with same name
        result = memory_tool.create("/memories/testdir", "content")
        assert "Cannot overwrite directory" in result

    def test_cannot_delete_root_directory(self, memory_tool):
        """Root /memories directory should not be deletable"""
        result = memory_tool.delete("/memories")
        assert "Cannot delete root" in result

    def test_cannot_rename_root_directory(self, memory_tool):
        """Root /memories directory should not be renameable"""
        result = memory_tool.rename("/memories", "/memories_new")
        assert "Cannot rename root" in result


class TestFileOperations:
    """Test suite for basic file operations"""

    @pytest.fixture
    def memory_tool(self, tmp_path):
        """Create memory tool with temporary base directory"""
        tool = AgencyMemoryTool(base_dir=str(tmp_path / "memories"))
        tool.base_dir.mkdir(parents=True, exist_ok=True)
        return tool

    def test_create_and_view_file(self, memory_tool):
        """Create file and view contents"""
        result = memory_tool.create("/memories/test.txt", "Hello, World!")
        assert "Successfully created" in result

        content = memory_tool.view("/memories/test.txt")
        assert content == "Hello, World!"

    def test_view_directory(self, memory_tool):
        """View directory listing"""
        # Create some files
        memory_tool.create("/memories/file1.txt", "content1")
        memory_tool.create("/memories/file2.txt", "content2")
        (memory_tool.base_dir / "subdir").mkdir()

        listing = memory_tool.view("/memories")
        assert "[DIR] subdir" in listing
        assert "[FILE] file1.txt" in listing
        assert "[FILE] file2.txt" in listing

    def test_str_replace(self, memory_tool):
        """Replace text in file"""
        memory_tool.create("/memories/test.txt", "Hello, World!")
        result = memory_tool.str_replace("/memories/test.txt", "World", "Claude")
        assert "Successfully replaced" in result

        content = memory_tool.view("/memories/test.txt")
        assert content == "Hello, Claude!"

    def test_insert_text(self, memory_tool):
        """Insert text at specific line"""
        memory_tool.create("/memories/test.txt", "Line 1\nLine 3\n")
        result = memory_tool.insert("/memories/test.txt", 2, "Line 2\n")
        assert "Successfully inserted" in result

        content = memory_tool.view("/memories/test.txt")
        assert content == "Line 1\nLine 2\nLine 3\n"

    def test_delete_file(self, memory_tool):
        """Delete file"""
        memory_tool.create("/memories/test.txt", "content")
        result = memory_tool.delete("/memories/test.txt")
        assert "Successfully deleted" in result

        # Verify deleted
        content = memory_tool.view("/memories/test.txt")
        assert "does not exist" in content

    def test_rename_file(self, memory_tool):
        """Rename file"""
        memory_tool.create("/memories/old.txt", "content")
        result = memory_tool.rename("/memories/old.txt", "/memories/new.txt")
        assert "Successfully renamed" in result

        # Verify renamed
        assert "does not exist" in memory_tool.view("/memories/old.txt")
        assert "content" == memory_tool.view("/memories/new.txt")

    def test_view_with_line_range(self, memory_tool):
        """View file with line range"""
        memory_tool.create("/memories/test.txt", "Line 1\nLine 2\nLine 3\nLine 4\n")

        # View lines 2-3
        content = memory_tool.view("/memories/test.txt", view_range=[2, 3])
        assert content == "Line 2\nLine 3\n"


class TestFactoryFunction:
    """Test suite for factory function"""

    def test_create_memory_tool_default(self, tmp_path, monkeypatch):
        """Factory should create tool with default directory"""
        monkeypatch.setenv("HOME", str(tmp_path))

        tool = create_memory_tool()
        expected_path = tmp_path / ".agency" / "memories"
        assert tool.base_dir == expected_path

    def test_create_memory_tool_with_session(self, tmp_path, monkeypatch):
        """Factory should create isolated session directory"""
        monkeypatch.setenv("HOME", str(tmp_path))

        tool = create_memory_tool(session_id="session_123")
        expected_path = tmp_path / ".agency" / "memories" / "session_123"
        assert tool.base_dir == expected_path

    def test_create_memory_tool_custom_base(self, tmp_path):
        """Factory should accept custom base directory"""
        custom_dir = tmp_path / "custom"

        tool = create_memory_tool(base_dir=str(custom_dir))
        assert tool.base_dir == custom_dir


class TestEdgeCases:
    """Test suite for edge cases"""

    @pytest.fixture
    def memory_tool(self, tmp_path):
        """Create memory tool with temporary base directory"""
        tool = AgencyMemoryTool(base_dir=str(tmp_path / "memories"))
        tool.base_dir.mkdir(parents=True, exist_ok=True)
        return tool

    def test_view_nonexistent_file(self, memory_tool):
        """Viewing non-existent file should return error"""
        result = memory_tool.view("/memories/nonexistent.txt")
        assert "does not exist" in result

    def test_replace_in_nonexistent_file(self, memory_tool):
        """Replacing in non-existent file should return error"""
        result = memory_tool.str_replace("/memories/nonexistent.txt", "old", "new")
        assert "does not exist" in result

    def test_replace_nonexistent_string(self, memory_tool):
        """Replacing non-existent string should return error"""
        memory_tool.create("/memories/test.txt", "content")
        result = memory_tool.str_replace("/memories/test.txt", "notfound", "new")
        assert "String not found" in result

    def test_empty_directory_view(self, memory_tool):
        """Viewing empty directory should return appropriate message"""
        (memory_tool.base_dir / "empty").mkdir()
        result = memory_tool.view("/memories/empty")
        assert "(empty directory)" in result

    def test_unicode_content(self, memory_tool):
        """Should handle Unicode content correctly"""
        unicode_content = "Hello, 世界! 🌍"
        memory_tool.create("/memories/unicode.txt", unicode_content)
        result = memory_tool.view("/memories/unicode.txt")
        assert result == unicode_content

    def test_rename_to_existing_path(self, memory_tool):
        """Renaming to existing path should fail"""
        memory_tool.create("/memories/file1.txt", "content1")
        memory_tool.create("/memories/file2.txt", "content2")

        result = memory_tool.rename("/memories/file1.txt", "/memories/file2.txt")
        assert "already exists" in result
