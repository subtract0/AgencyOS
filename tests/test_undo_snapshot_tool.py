import os
from pathlib import Path

from tools.undo_snapshot import WorkspaceSnapshot, WorkspaceUndo


def test_snapshot_and_undo_roundtrip(tmp_path, monkeypatch):
    # Prepare a temp file inside repo root (cwd)
    repo_root = Path(os.getcwd())
    test_file = repo_root / "_tmp_unit_test_file.txt"
    test_file.write_text("hello")

    try:
        # Create snapshot
        snap_tool = WorkspaceSnapshot(files=[str(test_file)])
        out = snap_tool.run()
        assert "Snapshot created:" in out
        snap_id = out.split(":")[1].strip().split(" ")[0]

        # Modify file
        test_file.write_text("world")
        assert test_file.read_text() == "world"

        # Dry-run undo
        undo_dry = WorkspaceUndo(snapshot_id=snap_id, dry_run=True)
        out_dry = undo_dry.run()
        assert "Planned restore" in out_dry
        assert snap_id in out_dry

        # Perform undo
        undo = WorkspaceUndo(snapshot_id=snap_id, dry_run=False)
        out_real = undo.run()
        assert "Restored 1 file" in out_real
        assert test_file.read_text() == "hello"
    finally:
        if test_file.exists():
            test_file.unlink()
