from pathlib import Path

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
