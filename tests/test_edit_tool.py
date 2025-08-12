from pathlib import Path
from claude_code.tools.edit import Edit


def test_edit_unique_replacement_and_preview(tmp_path: Path):
    p = tmp_path / "file.txt"
    p.write_text("hello world\nbye\n", encoding="utf-8")
    tool = Edit(file_path=str(p), old_string="hello", new_string="hi", replace_all=False)
    out = tool.run()
    assert "Successfully replaced 1 occurrence" in out
    assert "Preview:" in out


def test_edit_multiple_occurrences_error_with_previews(tmp_path: Path):
    p = tmp_path / "multi.txt"
    p.write_text("a test a test a\n", encoding="utf-8")
    tool = Edit(file_path=str(p), old_string="a", new_string="b", replace_all=False)
    out = tool.run()
    assert "Error: String appears" in out
    assert "First matches:" in out

