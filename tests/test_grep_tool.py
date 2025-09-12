from pathlib import Path

from tools import Grep


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
    tool = Grep(
        pattern="doesnotmatch", path=str(tmp_path), output_mode="files_with_matches"
    )
    out = tool.run()
    if "ripgrep (rg) is not installed" in out:
        return
    assert "No matches found for pattern" in out
