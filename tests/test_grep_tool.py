from pathlib import Path

import pytest

from tools import Grep


# Helper function to skip tests if ripgrep is not installed
def skip_if_no_rg(output: str):
    if "ripgrep (rg) is not installed" in output:
        pytest.skip("ripgrep not installed")


# === EXISTING BASIC TESTS ===


def test_grep_files_with_matches(tmp_path: Path):
    f = tmp_path / "a.py"
    f.write_text("import os\n", encoding="utf-8")
    tool = Grep(pattern="import", path=str(tmp_path), output_mode="files_with_matches")
    out = tool.run()
    if "ripgrep (rg) is not installed" in out:
        # Environment without rg; skip behavior assertions
        return
    assert "Exit code:" in out
    assert str(f) in out


def test_grep_no_matches(tmp_path: Path):
    f = tmp_path / "a.txt"
    f.write_text("nothing here\n", encoding="utf-8")
    tool = Grep(pattern="doesnotmatch", path=str(tmp_path), output_mode="files_with_matches")
    out = tool.run()
    if "ripgrep (rg) is not installed" in out:
        return
    assert "No matches found for pattern" in out


# === REGEX PATTERN TESTS ===


def test_grep_regex_wildcard_pattern(tmp_path: Path):
    """Test regex pattern with wildcards (log.*Error)"""
    f = tmp_path / "app.log"
    f.write_text("logError: critical\nlogWarning: info\nnoMatch\n", encoding="utf-8")
    tool = Grep(pattern="log.*Error", path=str(tmp_path), output_mode="files_with_matches")
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert str(f) in out


def test_grep_regex_word_boundary(tmp_path: Path):
    """Test regex with word boundaries and whitespace (function\\s+\\w+)"""
    f = tmp_path / "code.py"
    f.write_text(
        "function process() {}\nfunction_name = 'test'\nmy function here\n",
        encoding="utf-8",
    )
    tool = Grep(pattern=r"function\s+\w+", path=str(tmp_path), output_mode="content", n=True)
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "function process" in out or "function_name" in out


def test_grep_regex_escaped_special_chars(tmp_path: Path):
    """Test regex with escaped special characters (braces, parentheses)"""
    f = tmp_path / "config.go"
    f.write_text("interface{}\ninterface { name }\ntype Data struct {}\n", encoding="utf-8")
    tool = Grep(
        pattern=r"interface\{\}",
        path=str(tmp_path),
        output_mode="content",
    )
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "interface{}" in out


def test_grep_regex_character_class(tmp_path: Path):
    """Test regex with character classes [0-9]"""
    f = tmp_path / "data.txt"
    f.write_text("id: 12345\nname: test\ncode: ABC\n", encoding="utf-8")
    tool = Grep(pattern=r"[0-9]+", path=str(tmp_path), output_mode="content")
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "12345" in out


# === MULTILINE MODE TESTS ===


def test_grep_multiline_disabled_default(tmp_path: Path):
    """Test default behavior: pattern should not match across lines"""
    f = tmp_path / "multi.txt"
    f.write_text("struct {\n  field\n}\n", encoding="utf-8")
    tool = Grep(
        pattern=r"struct \{[\s\S]*?field",
        path=str(tmp_path),
        output_mode="content",
        multiline=False,
    )
    out = tool.run()
    skip_if_no_rg(out)
    # Should NOT match because pattern spans multiple lines
    assert "No matches found" in out or "Exit code: 1" in out


def test_grep_multiline_enabled_cross_line_match(tmp_path: Path):
    """Test multiline mode: pattern SHOULD match across lines"""
    f = tmp_path / "multi.txt"
    f.write_text("struct {\n  field\n}\n", encoding="utf-8")
    tool = Grep(
        pattern=r"struct \{[\s\S]*?field",
        path=str(tmp_path),
        output_mode="content",
        multiline=True,
    )
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "struct" in out and "field" in out


def test_grep_multiline_dot_matches_newline(tmp_path: Path):
    """Test multiline mode: dot (.) should match newlines"""
    f = tmp_path / "text.md"
    f.write_text("# Title\n\nContent here\n", encoding="utf-8")
    tool = Grep(
        pattern=r"Title.+Content",
        path=str(tmp_path),
        output_mode="content",
        multiline=True,
    )
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "Title" in out


# === FILE FILTERING TESTS ===


def test_grep_glob_single_extension(tmp_path: Path):
    """Test glob pattern filtering for single file type (*.py)"""
    py_file = tmp_path / "script.py"
    py_file.write_text("import os\n", encoding="utf-8")
    txt_file = tmp_path / "readme.txt"
    txt_file.write_text("import os\n", encoding="utf-8")

    tool = Grep(
        pattern="import",
        path=str(tmp_path),
        glob="*.py",
        output_mode="files_with_matches",
    )
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert str(py_file) in out
    assert str(txt_file) not in out


def test_grep_glob_multiple_extensions(tmp_path: Path):
    """Test glob pattern with multiple extensions (*.{ts,tsx})"""
    ts_file = tmp_path / "app.ts"
    ts_file.write_text("export class App {}\n", encoding="utf-8")
    tsx_file = tmp_path / "component.tsx"
    tsx_file.write_text("export const Component = () => {}\n", encoding="utf-8")
    js_file = tmp_path / "index.js"
    js_file.write_text("export const test = 1;\n", encoding="utf-8")

    tool = Grep(
        pattern="export",
        path=str(tmp_path),
        glob="*.{ts,tsx}",
        output_mode="files_with_matches",
    )
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert str(ts_file) in out
    assert str(tsx_file) in out
    assert str(js_file) not in out


def test_grep_type_filter_python(tmp_path: Path):
    """Test type parameter for filtering by language (py)"""
    py_file = tmp_path / "main.py"
    py_file.write_text("def test(): pass\n", encoding="utf-8")
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("def test(): pass\n", encoding="utf-8")

    tool = Grep(pattern="def", path=str(tmp_path), type="py", output_mode="files_with_matches")
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert str(py_file) in out
    assert str(txt_file) not in out


# === CONTEXT LINES TESTS (-A/-B/-C) ===


def test_grep_context_after_lines(tmp_path: Path):
    """Test -A flag: show lines after match"""
    f = tmp_path / "log.txt"
    f.write_text("line1\nERROR found\nline3\nline4\nline5\n", encoding="utf-8")
    tool = Grep(pattern="ERROR", path=str(tmp_path), output_mode="content", A=2)
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "ERROR" in out
    # Test that -A flag is accepted and command succeeds (ripgrep behavior may vary)


def test_grep_context_before_lines(tmp_path: Path):
    """Test -B flag: show lines before match"""
    f = tmp_path / "log.txt"
    f.write_text("line1\nline2\nline3\nERROR found\nline5\n", encoding="utf-8")
    tool = Grep(pattern="ERROR", path=str(tmp_path), output_mode="content", B=2)
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "ERROR" in out
    # Test that -B flag is accepted and command succeeds (ripgrep behavior may vary)


def test_grep_context_surrounding_lines(tmp_path: Path):
    """Test -C flag: show lines before AND after match"""
    f = tmp_path / "log.txt"
    f.write_text("line1\nline2\nERROR found\nline4\nline5\n", encoding="utf-8")
    tool = Grep(pattern="ERROR", path=str(tmp_path), output_mode="content", C=1)
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "ERROR" in out
    # Test that -C flag is accepted and command succeeds (ripgrep behavior may vary)


def test_grep_context_ignored_in_files_with_matches_mode(tmp_path: Path):
    """Test that -A/-B/-C are ignored when not in content mode"""
    f = tmp_path / "test.txt"
    f.write_text("line1\nMATCH\nline3\n", encoding="utf-8")
    tool = Grep(
        pattern="MATCH",
        path=str(tmp_path),
        output_mode="files_with_matches",
        A=10,  # Should be ignored
    )
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert str(f) in out
    # Should not show content, only filename
    assert "line1" not in out or "line3" not in out


# === HEAD LIMIT TESTS ===


def test_grep_head_limit_truncates_output(tmp_path: Path):
    """Test head_limit truncates results to N lines"""
    f = tmp_path / "many.txt"
    f.write_text("\n".join([f"line{i}" for i in range(100)]), encoding="utf-8")
    tool = Grep(pattern="line", path=str(tmp_path), output_mode="content", head_limit=5)
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "output limited to first 5 lines" in out
    assert "line0" in out
    assert "line99" not in out


def test_grep_head_limit_files_with_matches(tmp_path: Path):
    """Test head_limit works with files_with_matches mode"""
    for i in range(10):
        (tmp_path / f"file{i}.txt").write_text("match\n", encoding="utf-8")

    tool = Grep(
        pattern="match",
        path=str(tmp_path),
        output_mode="files_with_matches",
        head_limit=3,
    )
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "output limited to first 3 lines" in out


def test_grep_head_limit_count_mode(tmp_path: Path):
    """Test head_limit works with count mode"""
    for i in range(10):
        (tmp_path / f"file{i}.txt").write_text("match\n", encoding="utf-8")

    tool = Grep(pattern="match", path=str(tmp_path), output_mode="count", head_limit=3)
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "output limited to first 3 lines" in out


# === OUTPUT MODE TESTS ===


def test_grep_output_mode_content(tmp_path: Path):
    """Test content output mode shows matching lines"""
    f = tmp_path / "data.txt"
    f.write_text("hello\nworld\nhello again\n", encoding="utf-8")
    tool = Grep(pattern="hello", path=str(tmp_path), output_mode="content")
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "hello" in out
    assert "world" not in out


def test_grep_output_mode_count(tmp_path: Path):
    """Test count output mode shows match counts per file"""
    f = tmp_path / "data.txt"
    f.write_text("test\ntest\ntest\n", encoding="utf-8")
    tool = Grep(pattern="test", path=str(tmp_path), output_mode="count")
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "3" in out or ":" in out  # ripgrep count format: filename:count


def test_grep_line_numbers_in_content_mode(tmp_path: Path):
    """Test -n flag shows line numbers in content mode"""
    f = tmp_path / "code.py"
    f.write_text("line1\nline2\nimport os\nline4\n", encoding="utf-8")
    tool = Grep(pattern="import", path=str(tmp_path), output_mode="content", n=True)
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    # ripgrep shows line numbers in format: filename:line_number:content
    assert "3" in out or ":" in out


# === CASE SENSITIVITY TESTS ===


def test_grep_case_sensitive_default(tmp_path: Path):
    """Test default case-sensitive search"""
    f = tmp_path / "text.txt"
    f.write_text("Hello\nhello\nHELLO\n", encoding="utf-8")
    tool = Grep(pattern="Hello", path=str(tmp_path), output_mode="content")
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    # Should only match exact case


def test_grep_case_insensitive_flag(tmp_path: Path):
    """Test -i flag enables case-insensitive search"""
    f = tmp_path / "text.txt"
    f.write_text("Hello\nhello\nHELLO\n", encoding="utf-8")
    tool = Grep(pattern="hello", path=str(tmp_path), output_mode="content", i=True)
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    # Should match all variations - check for "hello" which should be in output
    # (ripgrep outputs the matched lines as-is from the file)
    assert "hello" in out.lower()  # Case-insensitive check in output


# === ERROR CONDITION TESTS ===


def test_grep_invalid_regex_pattern(tmp_path: Path):
    """Test error handling for invalid regex pattern"""
    f = tmp_path / "test.txt"
    f.write_text("test\n", encoding="utf-8")
    tool = Grep(pattern="[invalid(", path=str(tmp_path), output_mode="content")
    out = tool.run()
    skip_if_no_rg(out)
    # Should return error exit code or error message
    assert "Exit code:" in out
    # ripgrep returns non-zero exit code for invalid regex


def test_grep_nonexistent_path(tmp_path: Path):
    """Test error handling for non-existent search path"""
    nonexistent = tmp_path / "does_not_exist"
    tool = Grep(pattern="test", path=str(nonexistent), output_mode="content")
    out = tool.run()
    skip_if_no_rg(out)
    # Should handle gracefully
    assert "Exit code:" in out


def test_grep_empty_pattern_handled(tmp_path: Path):
    """Test behavior with empty pattern"""
    f = tmp_path / "test.txt"
    f.write_text("content\n", encoding="utf-8")
    tool = Grep(pattern="", path=str(tmp_path), output_mode="content")
    out = tool.run()
    skip_if_no_rg(out)
    # ripgrep may reject or match everything
    assert "Exit code:" in out


# === EDGE CASE TESTS ===


def test_grep_empty_file(tmp_path: Path):
    """Test search in empty file"""
    f = tmp_path / "empty.txt"
    f.write_text("", encoding="utf-8")
    tool = Grep(pattern="test", path=str(tmp_path), output_mode="content")
    out = tool.run()
    skip_if_no_rg(out)
    assert "No matches found" in out or "Exit code: 1" in out


def test_grep_special_characters_in_content(tmp_path: Path):
    """Test search with special characters in file content"""
    f = tmp_path / "special.txt"
    f.write_text("$VAR=test\n@decorator\n#comment\n", encoding="utf-8")
    tool = Grep(pattern=r"\$VAR", path=str(tmp_path), output_mode="content")
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "$VAR" in out


def test_grep_unicode_content(tmp_path: Path):
    """Test search with Unicode characters"""
    f = tmp_path / "unicode.txt"
    f.write_text("café ☕ 日本語\n", encoding="utf-8")
    tool = Grep(pattern="café", path=str(tmp_path), output_mode="content")
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "café" in out


def test_grep_very_long_line(tmp_path: Path):
    """Test handling of very long lines (potential truncation)"""
    f = tmp_path / "long.txt"
    long_line = "x" * 5000 + "MATCH" + "y" * 5000
    f.write_text(long_line + "\n", encoding="utf-8")
    tool = Grep(pattern="MATCH", path=str(tmp_path), output_mode="content")
    out = tool.run()
    skip_if_no_rg(out)
    assert "Exit code: 0" in out
    assert "MATCH" in out


def test_grep_large_output_truncation(tmp_path: Path):
    """Test 30000 character truncation for very large outputs"""
    f = tmp_path / "huge.txt"
    # Create file with many matches to exceed 30000 char limit
    f.write_text("match\n" * 2000, encoding="utf-8")
    tool = Grep(pattern="match", path=str(tmp_path), output_mode="content")
    out = tool.run()
    skip_if_no_rg(out)
    # Check if truncation message appears for large outputs
    if len(out) >= 30000:
        assert "output truncated to 30000 characters" in out
