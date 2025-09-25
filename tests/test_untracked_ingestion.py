import os
from pathlib import Path
from tools.kanban.untracked import discover_untracked_cards, REPO_ROOT


def test_untracked_ingestion_respects_flags_and_globs(tmp_path, monkeypatch):
    # Create a fake repo structure under a temp root by monkeypatching REPO_ROOT? Not trivial since it's imported constant.
    # Instead, create actual files under the real repo in a safe temp subdir and point globs to them.
    test_dir = REPO_ROOT / "scratch" / "_tmp_untracked_test_"
    test_dir.mkdir(parents=True, exist_ok=True)
    try:
        p = test_dir / "note.txt"
        p.write_text("This is a test note with no secrets.")
        monkeypatch.setenv("LEARNING_UNTRACKED", "true")
        monkeypatch.setenv("LEARNING_UNTRACKED_GLOBS", f"scratch/_tmp_untracked_test_/note.txt")
        cards = discover_untracked_cards()
        assert any(c.get("source_ref", "").endswith("note.txt") for c in cards)
    finally:
        try:
            p.unlink(missing_ok=True)
            test_dir.rmdir()
        except Exception:
            pass


def test_untracked_ingestion_denies_dotgit(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNING_UNTRACKED", "true")
    monkeypatch.setenv("LEARNING_UNTRACKED_GLOBS", f".git/**/*")
    cards = discover_untracked_cards()
    assert cards == []
