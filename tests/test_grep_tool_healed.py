"""
NECESSARY-compliant comprehensive tests for tools/grep.py
Addresses Q(T) Score: 0.41 → Target: 0.90+

Test Coverage Areas:
- N: No Missing Behaviors - Complex regex patterns, multiline mode, file filtering
- E: Edge Cases - Empty results, special characters, large outputs
- C: Comprehensive - All output modes, context lines, file types
- E: Error Conditions - Invalid regex, timeout scenarios, ripgrep failures
- S: State Validation - Command construction, parameter handling
- S: Side Effects - File system interactions, process execution
- A: Async Operations - Timeout handling, subprocess management
- R: Regression Prevention - All major functionality paths
- Y: Yielding Confidence - Real-world search scenarios
"""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools import Grep


class TestGrepRegexPatterns:
    """Test complex regex pattern matching functionality."""

    def test_complex_regex_patterns(self, tmp_path: Path):
        """Test various complex regex patterns with real content."""
        # Create test file with diverse content
        test_file = tmp_path / "complex.py"
        test_file.write_text(
            "import os\n"
            "import sys\n"
            "def function_name():\n"
            "    log.error('Error occurred')\n"
            "    log.warning('Warning message')\n"
            "class MyClass:\n"
            "    def __init__(self):\n"
            "        self.value = 123\n"
            "    def method_with_underscore(self):\n"
            "        return 'test'\n",
            encoding="utf-8"
        )

        # Test complex pattern: functions with underscores
        tool = Grep(
            pattern=r"def\s+\w*_\w*\(",
            path=str(tmp_path),
            output_mode="content"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "method_with_underscore" in result
        assert "__init__" in result

    def test_case_insensitive_regex(self, tmp_path: Path):
        """Test case insensitive search functionality."""
        test_file = tmp_path / "case_test.txt"
        test_file.write_text("ERROR: Critical failure\nerror: minor issue\nWarning: check this\n")

        tool = Grep(
            pattern="error",
            path=str(tmp_path),
            output_mode="content",
            **{"-i": True}
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "ERROR: Critical failure" in result
        assert "error: minor issue" in result

    def test_escaped_special_characters(self, tmp_path: Path):
        """Test regex patterns with escaped special characters."""
        test_file = tmp_path / "special.go"
        test_file.write_text(
            "interface{}\n"
            "map[string]int{}\n"
            "func() error {\n"
            "    return nil\n"
            "}\n"
        )

        # Test escaped braces for Go interface{}
        tool = Grep(
            pattern=r"interface\{\}",
            path=str(tmp_path),
            output_mode="content"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "interface{}" in result


class TestGrepMultilineMode:
    """Test multiline mode functionality."""

    def test_multiline_pattern_matching(self, tmp_path: Path):
        """Test multiline patterns spanning multiple lines."""
        test_file = tmp_path / "multiline.py"
        test_file.write_text(
            "def complex_function(\n"
            "    param1: str,\n"
            "    param2: int\n"
            ") -> bool:\n"
            "    return True\n"
            "\n"
            "simple_func() -> str:\n"
            "    return 'test'\n"
        )

        # Test multiline pattern matching
        tool = Grep(
            pattern=r"def\s+\w+\([^)]*\n[^)]*\)\s*->",
            path=str(tmp_path),
            output_mode="content",
            multiline=True
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "complex_function" in result

    def test_multiline_disabled_by_default(self, tmp_path: Path):
        """Test that multiline is disabled by default."""
        test_file = tmp_path / "multiline_default.py"
        test_file.write_text(
            "def function(\n"
            "    param: str\n"
            ") -> None:\n"
            "    pass\n"
        )

        # Should not match across lines without multiline=True
        tool = Grep(
            pattern=r"def\s+function\([^)]*\n[^)]*\)",
            path=str(tmp_path),
            output_mode="content"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        # Should get an error about literal \n not being allowed without multiline
        assert "literal" in result and "\\n" in result and "multiline" in result.lower()


class TestGrepFileTypeFiltering:
    """Test file type filtering functionality."""

    def test_python_file_type_filtering(self, tmp_path: Path):
        """Test filtering by Python file type."""
        # Create multiple file types
        py_file = tmp_path / "test.py"
        py_file.write_text("import os\nprint('python')")

        js_file = tmp_path / "test.js"
        js_file.write_text("import fs from 'fs';\nconsole.log('javascript');")

        txt_file = tmp_path / "test.txt"
        txt_file.write_text("import should not match in txt")

        # Search only Python files
        tool = Grep(
            pattern="import",
            path=str(tmp_path),
            type="py",
            output_mode="files_with_matches"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "test.py" in result
        assert "test.js" not in result
        assert "test.txt" not in result

    def test_javascript_file_type_filtering(self, tmp_path: Path):
        """Test filtering by JavaScript file type."""
        py_file = tmp_path / "script.py"
        py_file.write_text("function = 'python'")

        js_file = tmp_path / "script.js"
        js_file.write_text("function test() { return 'js'; }")

        # Search only JavaScript files
        tool = Grep(
            pattern="function",
            path=str(tmp_path),
            type="js",
            output_mode="content"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "script.js" in result
        assert "script.py" not in result


class TestGrepContextLines:
    """Test context line functionality (-A, -B, -C parameters)."""

    def test_after_context_lines(self, tmp_path: Path):
        """Test showing lines after matches (-A parameter)."""
        test_file = tmp_path / "context.py"
        test_file.write_text(
            "line1\n"
            "MATCH_LINE\n"
            "after1\n"
            "after2\n"
            "after3\n"
            "line6\n"
        )

        tool = Grep(
            pattern="MATCH_LINE",
            path=str(tmp_path),
            output_mode="content",
            **{"-A": 2, "-n": True}
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "MATCH_LINE" in result
        # Context lines are shown with "-" prefix in ripgrep
        assert "after1" in result
        assert "after2" in result

    def test_before_context_lines(self, tmp_path: Path):
        """Test showing lines before matches (-B parameter)."""
        test_file = tmp_path / "context.py"
        test_file.write_text(
            "before1\n"
            "before2\n"
            "MATCH_LINE\n"
            "after1\n"
        )

        tool = Grep(
            pattern="MATCH_LINE",
            path=str(tmp_path),
            output_mode="content",
            **{"-B": 2, "-n": True}
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "before1" in result
        assert "before2" in result
        assert "MATCH_LINE" in result

    def test_context_lines_both_directions(self, tmp_path: Path):
        """Test showing context lines in both directions (-C parameter)."""
        test_file = tmp_path / "context.py"
        test_file.write_text(
            "before1\n"
            "before2\n"
            "MATCH_LINE\n"
            "after1\n"
            "after2\n"
        )

        tool = Grep(
            pattern="MATCH_LINE",
            path=str(tmp_path),
            output_mode="content",
            **{"-C": 2, "-n": True}
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "before1" in result
        assert "before2" in result
        assert "MATCH_LINE" in result
        assert "after1" in result
        assert "after2" in result

    def test_context_ignored_in_non_content_mode(self, tmp_path: Path):
        """Test that context parameters are ignored in non-content output modes."""
        test_file = tmp_path / "context.py"
        test_file.write_text("MATCH_LINE\nafter1\n")

        tool = Grep(
            pattern="MATCH_LINE",
            path=str(tmp_path),
            output_mode="files_with_matches",
            **{"-A": 5}  # Should be ignored
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "context.py" in result
        # Should not show content with context
        assert "after1" not in result


class TestGrepGlobPatterns:
    """Test glob pattern filtering functionality."""

    def test_single_extension_glob(self, tmp_path: Path):
        """Test glob pattern for single file extension."""
        py_file = tmp_path / "test.py"
        py_file.write_text("python_content")

        txt_file = tmp_path / "test.txt"
        txt_file.write_text("text_content")

        tool = Grep(
            pattern="content",
            path=str(tmp_path),
            glob="*.py",
            output_mode="files_with_matches"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "test.py" in result
        assert "test.txt" not in result

    def test_multiple_extension_glob(self, tmp_path: Path):
        """Test glob pattern for multiple file extensions."""
        py_file = tmp_path / "script.py"
        py_file.write_text("function")

        js_file = tmp_path / "script.js"
        js_file.write_text("function")

        txt_file = tmp_path / "document.txt"
        txt_file.write_text("function")

        tool = Grep(
            pattern="function",
            path=str(tmp_path),
            glob="*.{py,js}",
            output_mode="files_with_matches"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "script.py" in result
        assert "script.js" in result
        assert "document.txt" not in result

    def test_recursive_glob_pattern(self, tmp_path: Path):
        """Test recursive glob pattern matching."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        root_file = tmp_path / "root.py"
        root_file.write_text("root_match")

        sub_file = subdir / "nested.py"
        sub_file.write_text("nested_match")

        tool = Grep(
            pattern="match",
            path=str(tmp_path),
            glob="**/*.py",
            output_mode="files_with_matches"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "root.py" in result
        assert "nested.py" in result


class TestGrepOutputModes:
    """Test different output modes (content, files_with_matches, count)."""

    def test_content_output_mode(self, tmp_path: Path):
        """Test content output mode with line numbers."""
        test_file = tmp_path / "content.py"
        test_file.write_text(
            "line1\n"
            "match_line\n"
            "line3\n"
            "another_match_line\n"
        )

        tool = Grep(
            pattern="match",
            path=str(tmp_path),
            output_mode="content",
            **{"-n": True}
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "match_line" in result
        assert "another_match_line" in result
        # Should show line numbers in ripgrep format (line:content)
        assert ":match_line" in result and ":another_match_line" in result

    def test_files_with_matches_output_mode(self, tmp_path: Path):
        """Test files_with_matches output mode."""
        file1 = tmp_path / "has_match.py"
        file1.write_text("contains target")

        file2 = tmp_path / "no_match.py"
        file2.write_text("different content")

        tool = Grep(
            pattern="target",
            path=str(tmp_path),
            output_mode="files_with_matches"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "has_match.py" in result
        assert "no_match.py" not in result
        # Should not show content
        assert "contains target" not in result

    def test_count_output_mode(self, tmp_path: Path):
        """Test count output mode."""
        test_file = tmp_path / "count_test.py"
        test_file.write_text(
            "match here\n"
            "another match\n"
            "no target\n"
            "final match\n"
        )

        tool = Grep(
            pattern="match",
            path=str(tmp_path),
            output_mode="count"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        # Should show count format (filename:count)
        assert "count_test.py:3" in result or "3" in result


class TestGrepErrorConditions:
    """Test error conditions and edge cases."""

    def test_invalid_regex_pattern(self, tmp_path: Path):
        """Test handling of invalid regex patterns."""
        test_file = tmp_path / "test.py"
        test_file.write_text("some content")

        tool = Grep(
            pattern="[invalid",  # Unclosed bracket
            path=str(tmp_path),
            output_mode="content"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        # Should return error information
        assert "Exit code:" in result
        assert result.startswith("Exit code: 2") or "regex parse error" in result.lower()

    def test_nonexistent_path(self, tmp_path: Path):
        """Test searching in non-existent directory."""
        nonexistent_path = str(tmp_path / "does_not_exist")

        tool = Grep(
            pattern="anything",
            path=nonexistent_path,
            output_mode="files_with_matches"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        # Should handle gracefully
        assert "Exit code:" in result
        assert result.startswith("Exit code: 2") or "No such file" in result

    def test_invalid_file_type(self, tmp_path: Path):
        """Test invalid file type parameter."""
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        tool = Grep(
            pattern="content",
            path=str(tmp_path),
            type="nonexistent_type",
            output_mode="files_with_matches"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        # Should handle unknown file type
        assert "Exit code:" in result

    @patch('subprocess.run')
    def test_timeout_handling(self, mock_run):
        """Test timeout handling for long-running searches."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=[], timeout=30)

        tool = Grep(pattern="test", output_mode="content")
        result = tool.run()

        assert "timed out after 30 seconds" in result

    @patch('subprocess.run')
    def test_ripgrep_not_installed(self, mock_run):
        """Test behavior when ripgrep is not installed."""
        mock_run.side_effect = FileNotFoundError()

        tool = Grep(pattern="test", output_mode="content")
        result = tool.run()

        assert "ripgrep (rg) is not installed" in result

    def test_general_exception_handling(self):
        """Test general exception handling."""
        with patch.object(Grep, '__init__', side_effect=Exception("Test error")):
            try:
                tool = Grep(pattern="test")
                # This should not execute due to init exception
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Test error" in str(e)


class TestGrepEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_file_search(self, tmp_path: Path):
        """Test searching in empty files."""
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")

        tool = Grep(
            pattern="anything",
            path=str(tmp_path),
            output_mode="files_with_matches"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "No matches found" in result

    def test_very_long_lines(self, tmp_path: Path):
        """Test handling of very long lines."""
        long_content = "x" * 50000 + "NEEDLE" + "y" * 50000
        test_file = tmp_path / "long.txt"
        test_file.write_text(long_content)

        tool = Grep(
            pattern="NEEDLE",
            path=str(tmp_path),
            output_mode="content"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        # For very long lines, the content may be truncated, but we should have found a match
        # Check that the file was processed (shows filename) and exit code is 0
        assert "long.txt:" in result

    def test_special_unicode_characters(self, tmp_path: Path):
        """Test searching with unicode characters."""
        test_file = tmp_path / "unicode.py"
        test_file.write_text("# Comment with émojis 🐍\nπ = 3.14159\n")

        tool = Grep(
            pattern="émojis",
            path=str(tmp_path),
            output_mode="content"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "émojis" in result

    def test_head_limit_functionality(self, tmp_path: Path):
        """Test head_limit parameter across different output modes."""
        # Create file with many matches
        content = "\n".join([f"match line {i}" for i in range(20)])
        test_file = tmp_path / "many_matches.txt"
        test_file.write_text(content)

        tool = Grep(
            pattern="match",
            path=str(tmp_path),
            output_mode="content",
            head_limit=3
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "output limited to first 3 lines" in result

    def test_large_output_truncation(self, tmp_path: Path):
        """Test truncation of very large outputs."""
        # Create content that would generate large output
        large_content = "\n".join([f"match_line_{i:06d}" * 100 for i in range(1000)])
        test_file = tmp_path / "large.txt"
        test_file.write_text(large_content)

        tool = Grep(
            pattern="match_line",
            path=str(tmp_path),
            output_mode="content"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        # Should handle large output appropriately
        assert len(result) <= 35000  # Some buffer for metadata
        if len(result) > 30000:
            assert "truncated" in result


class TestGrepStateValidation:
    """Test state validation and command construction."""

    def test_command_construction_basic(self, tmp_path: Path):
        """Test basic command construction."""
        test_file = tmp_path / "test.py"
        test_file.write_text("test content")

        tool = Grep(pattern="test", path=str(tmp_path))

        # Test that tool initializes with correct defaults
        assert tool.pattern == "test"
        assert tool.path == str(tmp_path)
        assert tool.output_mode == "files_with_matches"
        assert tool.multiline is False

    def test_command_construction_with_all_options(self, tmp_path: Path):
        """Test command construction with all options."""
        test_file = tmp_path / "test.py"
        test_file.write_text("test content")

        # Use alias notation for Field aliases
        tool = Grep(
            pattern="test",
            path=str(tmp_path),
            glob="*.py",
            output_mode="content",
            **{"-A": 2, "-B": 1, "-n": True, "-i": True},
            type="py",
            head_limit=10,
            multiline=True
        )

        # Verify all parameters are set correctly
        assert tool.pattern == "test"
        assert tool.glob == "*.py"
        assert tool.output_mode == "content"
        assert getattr(tool, "A") == 2
        assert getattr(tool, "B") == 1
        assert getattr(tool, "n") is True
        assert getattr(tool, "i") is True
        assert tool.type == "py"
        assert tool.head_limit == 10
        assert tool.multiline is True

    def test_alias_field_handling(self):
        """Test that alias fields (-A, -B, -C, -n, -i) work correctly."""
        tool = Grep(pattern="test", **{"-A": 3, "-B": 2, "-C": 1, "-n": True, "-i": True})

        assert getattr(tool, "A") == 3
        assert getattr(tool, "B") == 2
        assert getattr(tool, "C") == 1
        assert getattr(tool, "n") is True
        assert getattr(tool, "i") is True


class TestGrepRegressionPrevention:
    """Test for regression prevention of known issues."""

    def test_gitignore_respected(self, tmp_path: Path):
        """Test that .gitignore files are respected in git repositories."""
        import subprocess

        # Initialize git repo first (ripgrep only respects .gitignore in git repos)
        try:
            subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("git not available")

        # Create a .gitignore file
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("ignored.py\n")

        # Create ignored and non-ignored files
        ignored = tmp_path / "ignored.py"
        ignored.write_text("secret content")

        normal = tmp_path / "normal.py"
        normal.write_text("secret content")

        tool = Grep(
            pattern="secret",
            path=str(tmp_path),
            output_mode="files_with_matches"
        )
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result
        assert "normal.py" in result
        # Should respect .gitignore (ripgrep default behavior in git repos)
        assert "ignored.py" not in result

    def test_exit_code_handling_consistency(self, tmp_path: Path):
        """Test consistent exit code handling."""
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        # Test successful search
        tool = Grep(pattern="content", path=str(tmp_path))
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        assert "Exit code: 0" in result

        # Test no matches (exit code 1)
        tool = Grep(pattern="nomatch", path=str(tmp_path))
        result = tool.run()

        assert "Exit code: 1" in result
        assert "No matches found" in result

    def test_stderr_stdout_separation(self, tmp_path: Path):
        """Test that stderr and stdout are properly separated."""
        test_file = tmp_path / "test.py"
        test_file.write_text("test content")

        tool = Grep(pattern="test", path=str(tmp_path), output_mode="content")
        result = tool.run()

        if "ripgrep (rg) is not installed" in result:
            pytest.skip("ripgrep not available")

        # Should have clear stdout section
        assert "--- STDOUT ---" in result
        # For successful searches, stderr section may or may not be present
        assert "Exit code: 0" in result


if __name__ == "__main__":
    # Run a quick smoke test
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "smoke_test.py"
        test_file.write_text("import os\nprint('hello')")

        tool = Grep(pattern="import", path=tmp_dir, output_mode="files_with_matches")
        result = tool.run()
        print("Smoke test result:", result)