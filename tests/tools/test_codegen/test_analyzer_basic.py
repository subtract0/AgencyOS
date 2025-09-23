"""
Tests for analyzer module.
"""
import tempfile
import os
from tools.codegen.analyzer import suggest_refactors


def test_suggest_refactors_basic(tmp_path):
    """Test basic refactor suggestions."""
    # Create test Python file with various issues
    test_file = tmp_path / "test_code.py"
    test_file.write_text("""
def public_function(x, y):  # Missing type hints
    try:
        result = x / y
        return result
    except Exception:  # Broad exception
        return None

def _private_function(a: int, b: int) -> int:
    return a + b

def very_long_function():
    # This function has many lines to trigger long-function rule
    line1 = 1
    line2 = 2
    line3 = 3
    line4 = 4
    line5 = 5
    line6 = 6
    line7 = 7
    line8 = 8
    line9 = 9
    line10 = 10
    line11 = 11
    line12 = 12
    line13 = 13
    line14 = 14
    line15 = 15
    line16 = 16
    line17 = 17
    line18 = 18
    line19 = 19
    line20 = 20
    line21 = 21
    line22 = 22
    line23 = 23
    line24 = 24
    line25 = 25
    line26 = 26
    line27 = 27
    line28 = 28
    line29 = 29
    line30 = 30
    line31 = 31
    line32 = 32
    line33 = 33
    line34 = 34
    line35 = 35
    line36 = 36
    line37 = 37
    line38 = 38
    line39 = 39
    line40 = 40
    line41 = 41
    line42 = 42
    line43 = 43
    line44 = 44
    line45 = 45
    line46 = 46
    line47 = 47
    line48 = 48
    line49 = 49
    line50 = 50
    line51 = 51  # This makes it > 50 lines
    return line51

# TODO: Fix this later
# XXX: This is a hack
""")

    suggestions = suggest_refactors([str(test_file)])

    # Should detect multiple issues
    assert len(suggestions) > 0

    # Check for specific rule types
    rule_ids = [s.rule_id for s in suggestions]
    assert "broad-except" in rule_ids
    assert "missing-type-hints" in rule_ids
    assert "long-function" in rule_ids
    assert "dead-code-markers" in rule_ids

    # Verify suggestion structure
    for suggestion in suggestions:
        assert suggestion.path == str(test_file)
        assert suggestion.line > 0
        assert suggestion.severity in ["info", "warning", "error"]
        assert suggestion.rule_id
        assert suggestion.message


def test_suggest_refactors_empty_list():
    """Test with empty file list."""
    suggestions = suggest_refactors([])
    assert suggestions == []


def test_suggest_refactors_specific_rules(tmp_path):
    """Test with specific rule selection."""
    test_file = tmp_path / "test_code.py"
    test_file.write_text("""
def func():
    try:
        pass
    except Exception:
        pass
""")

    # Only check for broad exceptions
    suggestions = suggest_refactors([str(test_file)], rules=["broad-except"])
    assert len(suggestions) == 1
    assert suggestions[0].rule_id == "broad-except"


def test_suggest_refactors_syntax_error(tmp_path):
    """Test handling of syntax errors."""
    test_file = tmp_path / "bad_syntax.py"
    test_file.write_text("def broken_syntax(\n  # missing closing paren")

    suggestions = suggest_refactors([str(test_file)])
    assert len(suggestions) == 1
    assert suggestions[0].rule_id == "parse-error"
    assert suggestions[0].severity == "error"


def test_suggest_refactors_non_python_files(tmp_path):
    """Test that non-Python files are skipped."""
    txt_file = tmp_path / "readme.txt"
    txt_file.write_text("This is not Python code.")

    suggestions = suggest_refactors([str(txt_file)])
    assert suggestions == []