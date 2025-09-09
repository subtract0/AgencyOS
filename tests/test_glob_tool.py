from pathlib import Path

from agency_code_agent.tools.glob import Glob


def test_glob_simple_pattern(tmp_path: Path):
    (tmp_path / "x.py").write_text("# py\n", encoding="utf-8")
    (tmp_path / "y.txt").write_text("text\n", encoding="utf-8")
    tool = Glob(pattern="*.py", path=str(tmp_path))
    out = tool.run()
    assert "Found 1 files" in out
    assert str(tmp_path / "x.py") in out


def test_glob_recursive_pattern(tmp_path: Path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "a.py").write_text("# python\n", encoding="utf-8")
    tool = Glob(pattern="**/*.py", path=str(tmp_path))
    out = tool.run()
    assert str(sub / "a.py") in out
