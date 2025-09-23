"""
Tests for scaffolding module.
"""
import os
from tools.codegen.scaffold import scaffold_module


def test_scaffold_tool_module(tmp_path):
    """Test scaffolding a tool module."""
    out_dir = tmp_path / "tool_output"
    results = scaffold_module("tool", "test_tool", str(out_dir))

    # Should create multiple files
    assert len(results) > 0
    assert all(result.status == "created" for result in results)

    # Check that expected files exist
    expected_files = ["__init__.py", "test_tool.py", "cli.py"]
    created_paths = [os.path.basename(result.path) for result in results]

    for expected_file in expected_files:
        assert expected_file in created_paths

    # Verify file contents contain proper substitutions
    init_file = out_dir / "__init__.py"
    with open(init_file, 'r') as f:
        content = f.read()
        assert "test_tool" in content
        assert "TestTool" in content  # Class name should be converted to PascalCase

    tool_file = out_dir / "test_tool.py"
    with open(tool_file, 'r') as f:
        content = f.read()
        assert "class TestTool:" in content
        assert "test_tool" in content


def test_scaffold_tests_module(tmp_path):
    """Test scaffolding a tests module."""
    out_dir = tmp_path / "tests_output"
    results = scaffold_module("tests", "my_module", str(out_dir))

    assert len(results) > 0
    assert all(result.status == "created" for result in results)

    # Check for test files
    created_paths = [os.path.basename(result.path) for result in results]
    assert "__init__.py" in created_paths
    assert "test_my_module_basic.py" in created_paths

    # Verify test file content
    test_file = out_dir / "test_my_module_basic.py"
    with open(test_file, 'r') as f:
        content = f.read()
        assert "class TestMyModule:" in content
        assert "def test_" in content
        assert "pytest" in content


def test_scaffold_with_custom_params(tmp_path):
    """Test scaffolding with custom parameters."""
    params = {"module_path": "custom.path"}
    out_dir = tmp_path / "custom_output"
    results = scaffold_module("tests", "custom_tool", str(out_dir), params)

    assert len(results) > 0

    # Check that custom parameters were applied
    test_file = out_dir / "test_custom_tool_basic.py"
    with open(test_file, 'r') as f:
        content = f.read()
        assert "custom.path" in content


def test_scaffold_unknown_template(tmp_path):
    """Test handling of unknown template."""
    out_dir = tmp_path / "output"
    results = scaffold_module("unknown_template", "test", str(out_dir))

    assert len(results) == 1
    assert "error" in results[0].status
    assert "Unknown template" in results[0].status


def test_scaffold_class_name_conversion():
    """Test module name to class name conversion."""
    from tools.codegen.scaffold import _to_class_name

    assert _to_class_name("simple") == "Simple"
    assert _to_class_name("multi_word") == "MultiWord"
    assert _to_class_name("kebab-case") == "KebabCase"
    assert _to_class_name("mixed_case-example") == "MixedCaseExample"
    assert _to_class_name("") == ""


def test_scaffold_directory_creation_error():
    """Test handling of directory creation errors."""
    # Try to create in a location that should fail (non-existent parent)
    results = scaffold_module("tool", "test", "/nonexistent/deep/path")

    # Should handle the error gracefully
    assert len(results) >= 1
    # At least one result should indicate an error
    error_results = [r for r in results if "error" in r.status]
    assert len(error_results) > 0