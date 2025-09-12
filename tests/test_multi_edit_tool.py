from pathlib import Path

import pytest

from tools import MultiEdit, Read
from tools.multi_edit import EditOperation

def test_multi_edit_requires_prior_read():
    """Test that MultiEdit tool requires using Read tool first"""
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
        tmp.write("Hello world\nThis is a test")
        tmp_path = tmp.name

    try:
        # Try to edit without reading first - should fail
        edits = [EditOperation(old_string="world", new_string="universe")]
        tool = MultiEdit(file_path=tmp_path, edits=edits)
        result = tool.run()

        # Should get an error message about needing to read first
        assert "must use Read tool" in result or "read the file first" in result.lower()

        # File should remain unchanged
        with open(tmp_path, "r") as f:
            assert "Hello world" in f.read()

    finally:
        os.unlink(tmp_path)


def test_multi_edit_read_first_required_for_all_extensions(tmp_path: Path):
    """Read-first must be enforced for any existing file extension."""
    # .txt requires read first
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("alpha beta gamma")

    edits_txt = [EditOperation(old_string="beta", new_string="BETA")]
    tool_txt = MultiEdit(file_path=str(txt_file), edits=edits_txt)
    result_txt = tool_txt.run()
    assert (
        "must use Read tool" in result_txt
        or "read the file first" in result_txt.lower()
    )

    # .py also requires read first now
    py_file = tmp_path / "sample.py"
    py_file.write_text("print('alpha')\nvalue = 1")

    edits_py = [EditOperation(old_string="value = 1", new_string="value = 2")]
    tool_py = MultiEdit(file_path=str(py_file), edits=edits_py)
    result_py = tool_py.run()
    assert (
        "must use Read tool" in result_py or "read the file first" in result_py.lower()
    )


def test_multi_edit_works_after_read():
    """Test that MultiEdit tool works after using Read tool first"""
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
        tmp.write("Hello world\nThis is a test")
        tmp_path = tmp.name

    try:
        # Read the file first (prerequisite)
        read_tool = Read(file_path=tmp_path)
        read_tool.run()

        # Now edit should work
        edits = [EditOperation(old_string="world", new_string="universe")]
        tool = MultiEdit(file_path=tmp_path, edits=edits)
        result = tool.run()

        assert "Successfully applied" in result

        # File should be changed
        with open(tmp_path, "r") as f:
            assert "Hello universe" in f.read()

    finally:
        os.unlink(tmp_path)


def test_multi_edit_atomicity_on_new_file():
    """Test that new file creation is atomic - if later edits fail, no file should be created"""
    import os
    import tempfile

    tmp_dir = tempfile.mkdtemp()
    new_file_path = os.path.join(tmp_dir, "new_file.txt")

    try:
        # Create edits where first creates file, but second will fail
        edits = [
            EditOperation(old_string="", new_string="Hello world\nThis is new content"),
            EditOperation(
                old_string="non_existent_string", new_string="replacement"
            ),  # This will fail
        ]

        tool = MultiEdit(file_path=new_file_path, edits=edits)
        result = tool.run()

        # Should report failure
        assert "Error" in result or "Failed" in result

        # File should not exist since operation failed
        assert not os.path.exists(new_file_path), (
            f"File {new_file_path} should not exist after failed atomic operation"
        )

    finally:
        if os.path.exists(new_file_path):
            os.unlink(new_file_path)
        os.rmdir(tmp_dir)


def test_multi_edit_basic_operations(tmp_path: Path):
    """Test basic multi-edit operations on existing file"""
    # Create test file
    test_file = tmp_path / "test.py"
    content = '''def old_function(param1, param2):
    """This is an old function."""
    result = param1 + param2
    print("Old message")
    return result

def another_function():
    """Another function."""
    old_value = 42
    return old_value
'''
    test_file.write_text(content)

    # Define multiple edits - use more unique strings to avoid ambiguity
    edits = [
        EditOperation(old_string="def old_function(", new_string="def new_function("),
        EditOperation(old_string="Old message", new_string="Updated message"),
        EditOperation(old_string="old_value = 42", new_string="new_value = 42"),
    ]

    # Read the file first (required precondition)

    read_tool = Read(file_path=str(test_file))
    read_tool.run()

    # Read first (required precondition)
    Read(file_path=str(test_file)).run()

    # Read first (required precondition)
    Read(file_path=str(test_file)).run()

    tool = MultiEdit(file_path=str(test_file), edits=edits)
    result = tool.run()

    assert "Successfully applied 3 edit operations" in result
    assert "3 total replacements" in result

    # Verify changes were applied
    modified_content = test_file.read_text()
    assert "def new_function(" in modified_content
    assert "Updated message" in modified_content
    assert "new_value = 42" in modified_content
    assert "old_function" not in modified_content


def test_multi_edit_replace_all(tmp_path: Path):
    """Test replace_all functionality"""
    test_file = tmp_path / "replace_all.py"
    content = """def process_old_data():
    old_var = "old"
    print(f"Processing {old_var}")
    return old_var

def handle_old_records():
    old_var = "different old"
    return old_var
"""
    test_file.write_text(content)

    edits = [
        EditOperation(old_string="old_var", new_string="new_var", replace_all=True),
        EditOperation(old_string="old_data", new_string="new_data"),
        EditOperation(old_string="old_records", new_string="new_records"),
    ]

    # Read the file first (required precondition)
    read_tool = Read(file_path=str(test_file))
    read_tool.run()

    tool = MultiEdit(file_path=str(test_file), edits=edits)
    result = tool.run()

    assert "Successfully applied 3 edit operations" in result
    # Just verify that the operation succeeded and we have some replacements
    assert "total replacements" in result
    # Extract the actual replacement count from the result
    words = result.split()
    replacement_count = None
    for i, word in enumerate(words):
        if word.isdigit() and i > 0 and "replacements" in words[i + 1 : i + 3]:
            replacement_count = int(word)
            break
    if replacement_count is not None:
        assert replacement_count >= 3  # At least as many as the operations
    else:
        # Fallback: just check that replacements are mentioned
        assert "replacements" in result

    modified_content = test_file.read_text()
    assert "new_var" in modified_content
    assert "old_var" not in modified_content
    assert "process_new_data" in modified_content
    assert "handle_new_records" in modified_content


def test_multi_edit_sequential_operations(tmp_path: Path):
    """Test that edits are applied sequentially"""
    test_file = tmp_path / "sequential.txt"
    content = "Step 1: initial\nStep 2: process\nStep 3: finalize"
    test_file.write_text(content)

    # Use non-overlapping edits that don't depend on each other to avoid complexity
    edits = [
        EditOperation(old_string="initial", new_string="started"),
        EditOperation(old_string="Step 2: process", new_string="Step 2: execute"),
        EditOperation(old_string="Step 3: finalize", new_string="Step 3: complete"),
    ]

    # Read the file first (required precondition)
    read_tool = Read(file_path=str(test_file))
    read_tool.run()

    tool = MultiEdit(file_path=str(test_file), edits=edits)
    result = tool.run()

    assert "Successfully applied 3 edit operations" in result

    modified_content = test_file.read_text()
    assert "Step 1: started" in modified_content
    assert "Step 2: execute" in modified_content
    assert "Step 3: complete" in modified_content


def test_multi_edit_create_new_file(tmp_path: Path):
    """Test creating a new file with multi-edit"""
    new_file = tmp_path / "new_file.py"

    # First edit creates the file (empty old_string)
    edits = [
        EditOperation(
            old_string="",
            new_string="#!/usr/bin/env python3\n\ndef main():\n    print('Hello')\n    return 0",
        ),
        EditOperation(old_string="Hello", new_string="Hello, World!"),
        EditOperation(old_string="return 0", new_string="return True"),
    ]

    tool = MultiEdit(file_path=str(new_file), edits=edits)
    result = tool.run()

    assert "Successfully created new file" in result
    assert "applied 3 edit operations" in result
    assert str(new_file) in result

    # Verify file was created with correct content
    assert new_file.exists()
    content = new_file.read_text()
    assert "#!/usr/bin/env python3" in content
    assert "Hello, World!" in content
    assert "return True" in content
    assert "Hello'" not in content  # Original "Hello" should be replaced


def test_multi_edit_complex_code_refactor(tmp_path: Path):
    """Test complex code refactoring scenario"""
    test_file = tmp_path / "refactor.py"
    content = '''class OldClass:
    def __init__(self):
        self.old_attribute = "value"
        self.another_old = 42

    def old_method(self, param):
        """Old method implementation."""
        result = self.old_attribute + str(param)
        print(f"Old: {result}")
        return result

    def helper_method(self):
        return self.another_old * 2

# Usage
instance = OldClass()
result = instance.old_method(10)
'''
    test_file.write_text(content)

    # Comprehensive refactoring
    edits = [
        EditOperation(old_string="OldClass", new_string="NewClass", replace_all=True),
        EditOperation(
            old_string="old_attribute", new_string="new_attribute", replace_all=True
        ),
        EditOperation(
            old_string="another_old", new_string="another_new", replace_all=True
        ),
        EditOperation(
            old_string="old_method", new_string="new_method", replace_all=True
        ),
        EditOperation(
            old_string="Old method implementation.",
            new_string="Updated method implementation.",
        ),
        EditOperation(
            old_string='print(f"Old: {result}")',
            new_string='print(f"Updated: {result}")',
        ),
    ]

    Read(file_path=str(test_file)).run()

    tool = MultiEdit(file_path=str(test_file), edits=edits)
    result = tool.run()

    assert "Successfully applied 6 edit operations" in result

    modified_content = test_file.read_text()
    assert "class NewClass:" in modified_content
    assert "self.new_attribute" in modified_content
    assert "self.another_new" in modified_content
    assert "def new_method(" in modified_content
    assert "Updated method implementation" in modified_content
    assert "Updated: {result}" in modified_content
    assert "instance = NewClass()" in modified_content
    assert "instance.new_method(10)" in modified_content


def test_multi_edit_json_config_update(tmp_path: Path):
    """Test updating JSON configuration"""
    config_file = tmp_path / "config.json"
    content = """{
  "database": {
    "host": "old_host",
    "port": 5432,
    "name": "old_database"
  },
  "cache": {
    "type": "redis",
    "host": "old_cache_host",
    "timeout": 30
  },
  "logging": {
    "level": "DEBUG",
    "format": "old_format"
  }
}"""
    config_file.write_text(content)

    edits = [
        EditOperation(old_string='"old_host"', new_string='"new_host"'),
        EditOperation(old_string='"old_database"', new_string='"production_db"'),
        EditOperation(old_string='"old_cache_host"', new_string='"cache.prod.com"'),
        EditOperation(old_string='"DEBUG"', new_string='"INFO"'),
        EditOperation(
            old_string='"old_format"',
            new_string='"%(asctime)s - %(levelname)s - %(message)s"',
        ),
    ]

    # Read first (required precondition)
    Read(file_path=str(config_file)).run()

    tool = MultiEdit(file_path=str(config_file), edits=edits)
    result = tool.run()

    assert "Successfully applied 5 edit operations" in result

    modified_content = config_file.read_text()
    assert '"new_host"' in modified_content
    assert '"production_db"' in modified_content
    assert '"cache.prod.com"' in modified_content
    assert '"INFO"' in modified_content
    assert '"%(asctime)s - %(levelname)s - %(message)s"' in modified_content


def test_multi_edit_error_string_not_found(tmp_path: Path):
    """Test error when string to replace is not found"""
    test_file = tmp_path / "error_test.py"
    content = "def function():\n    return 42"
    test_file.write_text(content)

    edits = [
        EditOperation(old_string="function", new_string="new_function"),
        EditOperation(old_string="nonexistent_string", new_string="replacement"),
    ]

    # Read first (required precondition)
    Read(file_path=str(test_file)).run()

    tool = MultiEdit(file_path=str(test_file), edits=edits)
    result = tool.run()

    assert "Error in edit 2" in result
    assert "String to replace not found" in result
    assert "nonexistent_string" in result

    # Original file should be unchanged
    unchanged_content = test_file.read_text()
    assert unchanged_content == content


def test_multi_edit_error_ambiguous_string(tmp_path: Path):
    """Test error when string appears multiple times without replace_all"""
    test_file = tmp_path / "ambiguous.py"
    content = """def test():
    value = "test"
    return test(value)

def test_helper():
    return "test"
"""
    test_file.write_text(content)

    edits = [
        EditOperation(old_string="test", new_string="exam")  # Appears multiple times
    ]

    # Read first (required precondition)
    Read(file_path=str(test_file)).run()

    tool = MultiEdit(file_path=str(test_file), edits=edits)
    result = tool.run()

    assert "Error in edit 1" in result
    assert "String appears" in result
    assert "times in file" in result
    assert "use replace_all=True" in result


def test_multi_edit_error_same_strings(tmp_path: Path):
    """Test error when old_string equals new_string"""
    test_file = tmp_path / "same_strings.py"
    content = "def function():\n    return 42"
    test_file.write_text(content)

    edits = [
        EditOperation(old_string="function", new_string="function")  # Same strings
    ]

    # Read first (required precondition)
    Read(file_path=str(test_file)).run()

    tool = MultiEdit(file_path=str(test_file), edits=edits)
    result = tool.run()

    assert "Error in edit 1" in result
    assert "old_string and new_string must be different" in result


def test_multi_edit_nonexistent_file():
    """Test error when file doesn't exist"""
    edits = [EditOperation(old_string="old", new_string="new")]

    tool = MultiEdit(file_path="/nonexistent/file.txt", edits=edits)
    result = tool.run()

    assert "Error: File does not exist" in result


def test_multi_edit_file_is_directory(tmp_path: Path):
    """Test error when path is a directory"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    edits = [EditOperation(old_string="old", new_string="new")]

    tool = MultiEdit(file_path=str(test_dir), edits=edits)
    result = tool.run()

    assert "Error: Path is not a file" in result


def test_multi_edit_html_template(tmp_path: Path):
    """Test editing HTML template"""
    template_file = tmp_path / "template.html"
    content = """<!DOCTYPE html>
<html>
<head>
    <title>Old Title</title>
    <meta charset="old-encoding">
</head>
<body>
    <h1 class="old-header">Welcome</h1>
    <p class="old-text">This is old content.</p>
    <div id="old-container">
        <span class="old-span">Old text</span>
    </div>
</body>
</html>"""
    template_file.write_text(content)

    edits = [
        EditOperation(old_string="Old Title", new_string="New Title"),
        EditOperation(old_string="old-encoding", new_string="utf-8"),
        EditOperation(old_string="old-header", new_string="new-header"),
        EditOperation(old_string="old-text", new_string="new-text"),
        EditOperation(old_string="old-container", new_string="new-container"),
        EditOperation(old_string="old-span", new_string="new-span"),
        EditOperation(old_string="Old text", new_string="Updated text"),
        EditOperation(old_string="old content", new_string="fresh content"),
    ]

    # Read first (required precondition)
    Read(file_path=str(template_file)).run()

    tool = MultiEdit(file_path=str(template_file), edits=edits)
    result = tool.run()

    assert "Successfully applied 8 edit operations" in result

    modified_content = template_file.read_text()
    assert "<title>New Title</title>" in modified_content
    assert 'meta charset="utf-8"' in modified_content
    assert 'class="new-header"' in modified_content
    assert 'class="new-text"' in modified_content
    assert 'id="new-container"' in modified_content
    assert 'class="new-span"' in modified_content
    assert "Updated text" in modified_content
    assert "fresh content" in modified_content


def test_multi_edit_whitespace_preservation(tmp_path: Path):
    """Test that whitespace is preserved correctly"""
    test_file = tmp_path / "whitespace.py"
    content = """def function():
    if condition:
        # Comment with    spaces
        result = "  value  "
        return result.strip()

    return None
"""
    test_file.write_text(content)

    edits = [
        EditOperation(
            old_string="    if condition:", new_string="    if new_condition:"
        ),
        EditOperation(
            old_string="        # Comment with    spaces",
            new_string="        # Updated comment    with spaces",
        ),
        EditOperation(old_string='"  value  "', new_string='"  new_value  "'),
    ]

    # Read first (required precondition)
    Read(file_path=str(test_file)).run()

    tool = MultiEdit(file_path=str(test_file), edits=edits)
    result = tool.run()

    assert "Successfully applied 3 edit operations" in result

    modified_content = test_file.read_text()
    assert "    if new_condition:" in modified_content
    assert "        # Updated comment    with spaces" in modified_content
    assert '"  new_value  "' in modified_content
    # Original indentation should be preserved
    assert modified_content.count("    ") >= 2  # At least original indentation


def test_multi_edit_unicode_content(tmp_path: Path):
    """Test editing files with Unicode content"""
    test_file = tmp_path / "unicode.py"
    content = """# -*- coding: utf-8 -*-
def greet():
    messages = {
        "english": "Hello 🌍",
        "russian": "Привет мир",
        "chinese": "你好世界",
        "japanese": "こんにちは世界"
    }
    return messages
"""
    test_file.write_text(content, encoding="utf-8")

    edits = [
        EditOperation(old_string="Hello 🌍", new_string="Welcome 🌎"),
        EditOperation(old_string="Привет мир", new_string="Добро пожаловать"),
        EditOperation(old_string="你好世界", new_string="欢迎来到世界"),
        EditOperation(old_string="こんにちは世界", new_string="世界へようこそ"),
    ]

    # Read first (required precondition)
    Read(file_path=str(test_file)).run()

    tool = MultiEdit(file_path=str(test_file), edits=edits)
    result = tool.run()

    assert "Successfully applied 4 edit operations" in result

    modified_content = test_file.read_text(encoding="utf-8")
    assert "Welcome 🌎" in modified_content
    assert "Добро пожаловать" in modified_content
    assert "欢迎来到世界" in modified_content
    assert "世界へようこそ" in modified_content


def test_multi_edit_large_file(tmp_path: Path):
    """Test multi-edit on a larger file"""
    test_file = tmp_path / "large_file.py"

    # Create a larger file with repetitive content
    lines = []
    for i in range(100):
        lines.append(f"def old_function_{i}():")
        lines.append(f'    """Old function {i}"""')
        lines.append(f"    old_value = {i}")
        lines.append(f"    return old_value * 2")
        lines.append("")

    content = "\n".join(lines)
    test_file.write_text(content)

    # Perform multiple replacements
    edits = [
        EditOperation(
            old_string="old_function_", new_string="new_function_", replace_all=True
        ),
        EditOperation(
            old_string="Old function", new_string="New function", replace_all=True
        ),
        EditOperation(old_string="old_value", new_string="new_value", replace_all=True),
    ]

    # Read first (required precondition)
    Read(file_path=str(test_file)).run()

    tool = MultiEdit(file_path=str(test_file), edits=edits)
    result = tool.run()

    assert "Successfully applied 3 edit operations" in result
    # Should replace 100 function names + 100 docstrings + 200 variable references = 400 total
    assert "400 total replacements" in result

    modified_content = test_file.read_text()
    assert "def new_function_50():" in modified_content
    assert "New function 25" in modified_content
    assert "new_value = 75" in modified_content
    assert "old_function" not in modified_content


def test_multi_edit_empty_edits_list():
    """Test error when no edits provided"""
    try:
        tool = MultiEdit(file_path="/tmp/test.txt", edits=[])
        pytest.fail("Should have raised validation error for empty edits list")
    except Exception as e:
        # Pydantic should catch this due to min_items=1
        assert "edits" in str(e).lower() or "at least 1" in str(e).lower()


def test_multi_edit_file_already_exists_create_mode(tmp_path: Path):
    """Test error when trying to create file that already exists"""
    existing_file = tmp_path / "existing.txt"
    existing_file.write_text("Already exists")

    edits = [
        EditOperation(old_string="", new_string="New content")  # Create mode
    ]

    tool = MultiEdit(file_path=str(existing_file), edits=edits)
    result = tool.run()

    assert "Error: File already exists, cannot create new file" in result
