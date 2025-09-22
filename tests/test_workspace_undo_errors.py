import json
import os
from pathlib import Path

from tools.undo_snapshot import WorkspaceSnapshot, WorkspaceUndo


def test_workspace_undo_missing_snapshot_id():
    tool = WorkspaceUndo(snapshot_id="does_not_exist", dry_run=False)
    out = tool.run()
    assert "Exit code: 1" in out
    assert "Snapshot not found" in out


def test_workspace_undo_corrupted_manifest(tmp_path, monkeypatch):
    # Create a fake snapshot directory with corrupted manifest
    repo_root = Path(os.getcwd())
    snaps = repo_root / "logs" / "snapshots"
    snaps.mkdir(parents=True, exist_ok=True)

    sid = "99990101_000000_000000"
    snap_dir = snaps / sid
    files_dir = snap_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    # Write corrupted manifest
    (snap_dir / "manifest.json").write_text("{not-json}")

    tool = WorkspaceUndo(snapshot_id=sid, dry_run=False)
    out = tool.run()
    assert "Exit code: 1" in out
    assert "Corrupted manifest" in out
