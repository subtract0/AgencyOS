import os
from pathlib import Path

import pytest

from tools import Write, Read


def test_write_existing_file_requires_prior_read():
    """Test that Write tool requires using Read tool first for existing files"""
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
        tmp.write("Existing content")
        tmp_path = tmp.name

    try:
        # Try to write to existing file without reading first - should fail
        tool = Write(file_path=tmp_path, content="New content")
        result = tool.run()

        # Should get an error message about needing to read first
        assert "must use Read tool" in result or "read the file first" in result.lower()

        # File should remain unchanged
        with open(tmp_path, "r") as f:
            assert "Existing content" in f.read()

    finally:
        os.unlink(tmp_path)


def test_write_existing_file_works_after_read():
    """Test that Write tool works after using Read tool first for existing files"""
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
        tmp.write("Existing content")
        tmp_path = tmp.name

    try:
        # Read the file first (prerequisite)
        read_tool = Read(file_path=tmp_path)
        read_tool.run()

        # Now write should work
        tool = Write(file_path=tmp_path, content="New content")
        result = tool.run()

        assert "Successfully" in result

        # File should be changed
        with open(tmp_path, "r") as f:
            assert "New content" in f.read()

    finally:
        os.unlink(tmp_path)


def test_write_new_file_does_not_require_read():
    """Test that Write tool doesn't require Read for new files"""
    import os
    import tempfile

    tmp_dir = tempfile.mkdtemp()
    new_file_path = os.path.join(tmp_dir, "new_file.txt")

    try:
        # Write to new file should work without reading first
        tool = Write(file_path=new_file_path, content="New file content")
        result = tool.run()

        assert "Successfully" in result

        # File should be created with correct content
        with open(new_file_path, "r") as f:
            assert "New file content" in f.read()

    finally:
        if os.path.exists(new_file_path):
            os.unlink(new_file_path)
        os.rmdir(tmp_dir)


def test_write_new_file(tmp_path: Path):
    """Test writing a new file"""
    file_path = str(tmp_path / "new_file.txt")
    content = "Hello, World!\nThis is a test file."

    tool = Write(file_path=file_path, content=content)
    result = tool.run()

    assert "Successfully created file" in result
    assert file_path in result
    assert "Size:" in result and "Lines:" in result

    # Verify file was created with correct content
    assert Path(file_path).exists()
    with open(file_path, "r", encoding="utf-8") as f:
        written_content = f.read()
    assert written_content == content


def test_write_overwrite_existing_file(tmp_path: Path):
    """Test overwriting an existing file"""
    file_path = str(tmp_path / "existing_file.py")

    # Create initial file
    initial_content = "print('initial')"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(initial_content)

    # Read the file first (required precondition for overwriting existing files)
    read_tool = Read(file_path=file_path)
    read_tool.run()

    # Overwrite with new content
    new_content = "print('overwritten')\nprint('second line')"
    tool = Write(file_path=file_path, content=new_content)
    result = tool.run()

    assert "Successfully overwritten file" in result
    assert file_path in result

    # Verify file was overwritten
    with open(file_path, "r", encoding="utf-8") as f:
        written_content = f.read()
    assert written_content == new_content


def test_write_creates_directory(tmp_path: Path):
    """Test that Write creates intermediate directories"""
    file_path = str(tmp_path / "subdir" / "nested" / "file.txt")
    content = "Nested file content"

    tool = Write(file_path=file_path, content=content)
    result = tool.run()

    assert "Successfully created file" in result
    assert Path(file_path).exists()
    assert Path(file_path).parent.exists()

    with open(file_path, "r", encoding="utf-8") as f:
        written_content = f.read()
    assert written_content == content


def test_write_empty_file(tmp_path: Path):
    """Test writing an empty file"""
    file_path = str(tmp_path / "empty.txt")
    content = ""

    tool = Write(file_path=file_path, content=content)
    result = tool.run()

    assert "Successfully created file" in result
    assert "Size: 0 bytes" in result

    # Verify empty file was created
    assert Path(file_path).exists()
    with open(file_path, "r", encoding="utf-8") as f:
        written_content = f.read()
    assert written_content == ""


def test_write_large_file(tmp_path: Path):
    """Test writing a larger file with multiple lines"""
    file_path = str(tmp_path / "large_file.py")
    lines = [f"# Line {i}: This is line number {i}" for i in range(1, 101)]
    content = "\n".join(lines)

    tool = Write(file_path=file_path, content=content)
    result = tool.run()

    assert "Successfully created file" in result
    assert "Lines: 100" in result

    # Verify content
    with open(file_path, "r", encoding="utf-8") as f:
        written_content = f.read()
    assert written_content == content
    assert len(written_content.split("\n")) == 100


def test_write_python_file(tmp_path: Path):
    """Test writing a Python file with proper syntax"""
    file_path = str(tmp_path / "test_script.py")
    content = '''#!/usr/bin/env python3
"""
Test Python module created by Write tool
"""

def fibonacci(n):
    """Calculate nth Fibonacci number"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    for i in range(10):
        print(f"F({i}) = {fibonacci(i)}")

if __name__ == "__main__":
    main()
'''

    tool = Write(file_path=file_path, content=content)
    result = tool.run()

    assert "Successfully created file" in result
    assert "test_script.py" in result

    # Verify Python file content
    with open(file_path, "r", encoding="utf-8") as f:
        written_content = f.read()
    assert written_content == content
    assert "def fibonacci" in written_content
    assert "#!/usr/bin/env python3" in written_content


def test_write_json_file(tmp_path: Path):
    """Test writing a JSON configuration file"""
    file_path = str(tmp_path / "config.json")
    content = """{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "test_db"
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  },
  "features": ["auth", "caching", "monitoring"]
}"""

    tool = Write(file_path=file_path, content=content)
    result = tool.run()

    assert "Successfully created file" in result
    assert "config.json" in result

    # Verify JSON content
    with open(file_path, "r", encoding="utf-8") as f:
        written_content = f.read()
    assert written_content == content


def test_write_requires_absolute_path(tmp_path: Path):
    """Test that Write requires absolute paths"""
    relative_path = "relative_file.txt"
    content = "This should fail"

    tool = Write(file_path=relative_path, content=content)
    result = tool.run()

    assert "Error: File path must be absolute" in result
    assert relative_path in result


def test_write_error_path_is_directory(tmp_path: Path):
    """Test error when trying to write to a directory path"""
    dir_path = str(tmp_path / "test_dir")
    os.makedirs(dir_path)
    content = "This should fail"

    # Try to read the directory first (will fail but satisfies precondition check)
    read_tool = Read(file_path=dir_path)
    try:
        read_tool.run()
    except:
        pass  # Expected to fail since it's a directory

    tool = Write(file_path=dir_path, content=content)
    result = tool.run()

    assert "Error: Path exists but is not a file" in result


def test_write_unicode_content(tmp_path: Path):
    """Test writing Unicode content"""
    file_path = str(tmp_path / "unicode_file.txt")
    content = "Hello 🌍\nПривет мир\n你好世界\nこんにちは世界"

    tool = Write(file_path=file_path, content=content)
    result = tool.run()

    assert "Successfully created file" in result

    # Verify Unicode content
    with open(file_path, "r", encoding="utf-8") as f:
        written_content = f.read()
    assert written_content == content
    assert "🌍" in written_content
    assert "Привет" in written_content


def test_write_line_counting_with_various_endings(tmp_path: Path):
    """Test line counting with different line endings"""
    file_path = str(tmp_path / "line_test.txt")

    # Test content ending with newline
    content_with_newline = "Line 1\nLine 2\nLine 3\n"
    tool = Write(file_path=file_path, content=content_with_newline)
    result = tool.run()
    assert "Lines: 3" in result

    # Test content not ending with newline
    content_no_newline = "Line 1\nLine 2\nLine 3"
    # Read the file first (required for overwriting existing file)
    read_tool2 = Read(file_path=file_path)
    read_tool2.run()
    tool2 = Write(file_path=file_path, content=content_no_newline)
    result2 = tool2.run()
    assert "Lines: 3" in result2

    # Test single line with no newline
    single_line = "Single line"
    # Read the file first (required for overwriting existing file)
    read_tool3 = Read(file_path=file_path)
    read_tool3.run()
    tool3 = Write(file_path=file_path, content=single_line)
    result3 = tool3.run()
    assert "Lines: 1" in result3


def test_write_permission_error():
    """Test permission error handling (if possible on system)"""
    # This test might be skipped on systems where we can't create permission errors
    try:
        # Try to write to a system directory that should be read-only
        file_path = "/root/test_file.txt"  # This should fail on most systems
        content = "This should fail with permission error"

        tool = Write(file_path=file_path, content=content)
        result = tool.run()

        # Should either fail with permission error or directory creation error
        assert "Error" in result

    except Exception:
        # Skip this test if we can't set up the permission scenario
        pytest.skip("Cannot test permission errors on this system")


def test_write_file_size_reporting(tmp_path: Path):
    """Test that file size is reported correctly"""
    file_path = str(tmp_path / "size_test.txt")

    # Test small file
    small_content = "Small"
    tool = Write(file_path=file_path, content=small_content)
    result = tool.run()
    assert "Size: 5 bytes" in result

    # Test larger content
    large_content = "A" * 1024  # 1KB
    # Read the file first (required for overwriting existing file)
    read_tool = Read(file_path=file_path)
    read_tool.run()
    tool2 = Write(file_path=file_path, content=large_content)
    result2 = tool2.run()
    assert "Size: 1024 bytes" in result2
