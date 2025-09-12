from pathlib import Path

from tools import Glob


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


def test_glob_respects_gitignore_patterns(tmp_path: Path):
    # Create files and directories
    (tmp_path / "keep.txt").write_text("ok\n", encoding="utf-8")
    (tmp_path / "ignore.py").write_text("print()\n", encoding="utf-8")

    ignored_dir = tmp_path / "ignored_dir"
    ignored_dir.mkdir()
    (ignored_dir / "inside.txt").write_text("nope\n", encoding="utf-8")

    # .gitignore to exclude *.py and the whole directory
    (tmp_path / ".gitignore").write_text("""\n*.py\nignored_dir/\n""", encoding="utf-8")

    # Search everything recursively
    tool = Glob(pattern="**/*", path=str(tmp_path))
    out = tool.run()

    # Should list keep.txt but not ignore.py or anything under ignored_dir
    assert "keep.txt" in out
    assert "ignore.py" not in out
    assert "ignored_dir" not in out
    assert "inside.txt" not in out
