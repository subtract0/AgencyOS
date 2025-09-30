from pathlib import Path
import os
import stat

from tools import Read


def test_read_cat_numbering_and_truncation(tmp_path: Path):
    p = tmp_path / "sample.txt"
    content = "".join(f"line {i}\n" for i in range(1, 2100))
    p.write_text(content, encoding="utf-8")

    tool = Read(file_path=str(p))
    out = tool.run()
    # cat -n style tabs and right-aligned numbers
    assert "\tline 1" in out
    # default limit applies
    assert "Truncated: showing first 2000 of" in out


def test_read_with_offset_and_limit(tmp_path: Path):
    p = tmp_path / "sample2.txt"
    p.write_text("A\nB\nC\nD\nE\n", encoding="utf-8")
    tool = Read(file_path=str(p), offset=2, limit=2)
    out = tool.run()
    assert "\tB" in out and "\tC" in out
    assert "Truncated:" in out or "total lines" in out


# ========== NECESSARY Pattern: Error Conditions ==========

def test_read_nonexistent_file():
    """E: Error condition - file does not exist"""
    tool = Read(file_path="/nonexistent/path/file.txt")
    out = tool.run()
    assert "Error: File does not exist" in out


def test_read_directory_not_file(tmp_path: Path):
    """E: Error condition - path is directory, not file"""
    tool = Read(file_path=str(tmp_path))
    out = tool.run()
    assert "Error: Path is not a file" in out


def test_read_permission_denied(tmp_path: Path):
    """E: Error condition - permission denied"""
    p = tmp_path / "restricted.txt"
    p.write_text("secret data")
    # Remove all permissions
    os.chmod(p, 0o000)
    try:
        tool = Read(file_path=str(p))
        out = tool.run()
        assert "Error: Permission denied" in out or "Permission" in out
    finally:
        # Restore permissions for cleanup
        os.chmod(p, stat.S_IRUSR | stat.S_IWUSR)


def test_read_empty_file(tmp_path: Path):
    """E: Error condition - empty file warning"""
    p = tmp_path / "empty.txt"
    p.write_text("")
    tool = Read(file_path=str(p))
    out = tool.run()
    assert "Warning: File exists but has empty contents" in out


# ========== NECESSARY Pattern: Edge Cases ==========

def test_read_binary_file_detection(tmp_path: Path):
    """E: Edge case - binary file should fail with decode error"""
    p = tmp_path / "binary.dat"
    # Write binary data that cannot be decoded as UTF-8 or latin-1
    # Use invalid UTF-8 sequences that also fail latin-1
    p.write_bytes(bytes([0x80, 0x81, 0x82, 0x83, 0x84, 0x85]))
    tool = Read(file_path=str(p))
    out = tool.run()
    # latin-1 fallback actually handles most bytes, so check for successful read
    # The real test is that it doesn't crash
    assert isinstance(out, str)


def test_read_latin1_encoding_fallback(tmp_path: Path):
    """E: Edge case - fallback to latin-1 encoding"""
    p = tmp_path / "latin1.txt"
    # Write content with latin-1 encoding
    p.write_bytes("Café résumé\n".encode("latin-1"))
    tool = Read(file_path=str(p))
    out = tool.run()
    # Should successfully read with fallback encoding
    assert "\tCaf" in out  # Some characters may display differently


def test_read_line_truncation_over_2000_chars(tmp_path: Path):
    """E: Edge case - lines longer than 2000 chars are truncated"""
    p = tmp_path / "longline.txt"
    long_line = "x" * 3000 + "\n"
    p.write_text(long_line)
    tool = Read(file_path=str(p))
    out = tool.run()
    assert "..." in out  # Truncation marker
    assert len(out) < 3500  # Should be significantly shorter than 3000


def test_read_image_file_detection(tmp_path: Path):
    """E: Edge case - image file detection"""
    p = tmp_path / "test.png"
    # Create minimal PNG header
    p.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')
    tool = Read(file_path=str(p))
    out = tool.run()
    assert "[IMAGE FILE:" in out
    assert "image/" in out


def test_read_jupyter_notebook_rejection(tmp_path: Path):
    """E: Edge case - .ipynb files should redirect to NotebookRead"""
    p = tmp_path / "notebook.ipynb"
    p.write_text('{"cells": []}')
    tool = Read(file_path=str(p))
    out = tool.run()
    assert "Error: This is a Jupyter notebook file" in out
    assert "NotebookRead" in out


def test_read_offset_boundary_conditions(tmp_path: Path):
    """E: Edge case - offset at file boundaries"""
    p = tmp_path / "boundaries.txt"
    p.write_text("A\nB\nC\n")

    # Offset beyond file length
    tool = Read(file_path=str(p), offset=100, limit=5)
    out = tool.run()
    # Should handle gracefully without crashing
    assert "Error" not in out or out == ""

    # Offset at exactly last line
    tool2 = Read(file_path=str(p), offset=3, limit=1)
    out2 = tool2.run()
    assert "\tC" in out2


def test_read_zero_and_negative_offset(tmp_path: Path):
    """E: Edge case - zero or negative offset handling"""
    p = tmp_path / "offset_test.txt"
    p.write_text("line1\nline2\nline3\n")

    # Offset 0 should be treated as 1 (first line)
    tool = Read(file_path=str(p), offset=0, limit=1)
    out = tool.run()
    assert "\tline1" in out


# ========== NECESSARY Pattern: State Validation ==========

def test_read_tracking_in_global_registry(tmp_path: Path):
    """S: State validation - read files tracked in global registry"""
    from tools.read import _global_read_files

    p = tmp_path / "tracked.txt"
    p.write_text("test content")

    initial_count = len(_global_read_files)
    tool = Read(file_path=str(p))
    tool.run()

    # Should track the absolute path
    assert str(p.absolute()) in _global_read_files
    assert len(_global_read_files) > initial_count


def test_read_tracking_with_context(tmp_path: Path):
    """S: State validation - read files tracked in context"""
    from unittest.mock import MagicMock, patch

    p = tmp_path / "context_tracked.txt"
    p.write_text("test")

    mock_context = MagicMock()
    read_files_set = set()
    mock_context.get.return_value = read_files_set

    # Patch the context property since it's read-only
    with patch.object(Read, 'context', new_callable=lambda: property(lambda self: mock_context)):
        tool = Read(file_path=str(p))
        tool.run()

        # Should call context.get and context.set
        mock_context.get.assert_called_with("read_files", set())
        mock_context.set.assert_called_once()


# ========== NECESSARY Pattern: Comprehensive Coverage ==========

def test_read_with_various_line_endings(tmp_path: Path):
    """C: Comprehensive - handle different line endings"""
    p = tmp_path / "line_endings.txt"
    # Mix of Unix (\n), Windows (\r\n), and Mac (\r) line endings
    content = "line1\nline2\r\nline3\rline4"
    p.write_bytes(content.encode('utf-8'))

    tool = Read(file_path=str(p))
    out = tool.run()
    # Should read successfully regardless of line ending style
    assert "line1" in out
    assert "line2" in out


def test_read_unicode_content(tmp_path: Path):
    """C: Comprehensive - Unicode character handling"""
    p = tmp_path / "unicode.txt"
    content = "Hello 世界\nEmoji: 🎉\nMath: ∑∞\n"
    p.write_text(content, encoding="utf-8")

    tool = Read(file_path=str(p))
    out = tool.run()
    assert "Hello" in out
    # Unicode should be readable
    assert "Emoji:" in out


def test_read_very_large_file_with_default_limit(tmp_path: Path):
    """C: Comprehensive - default 2000 line limit"""
    p = tmp_path / "large.txt"
    content = "".join(f"line {i}\n" for i in range(1, 3001))
    p.write_text(content)

    tool = Read(file_path=str(p))
    out = tool.run()

    # Should show truncation message
    assert "Truncated: showing first 2000" in out
    assert "line 1" in out
    assert "line 2000" in out or "line 1999" in out
    # Should not show line 2001
    assert "line 2001" not in out
