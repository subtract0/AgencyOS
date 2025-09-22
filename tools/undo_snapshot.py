import os
import json
import shutil
from pathlib import Path
from typing import List, Optional

from agency_swarm.tools import BaseTool
from pydantic import Field


class WorkspaceSnapshot(BaseTool):
    """
    Create a reversible snapshot of one or more files within the repository root.
    Stores copies under logs/snapshots/<snapshot_id>/ with a manifest for undo.
    """

    files: List[str] = Field(
        ..., description="Absolute paths of files to snapshot (must reside under repo root)"
    )
    note: Optional[str] = Field(None, description="Optional note to include in manifest")

    def run(self) -> str:
        repo_root = Path(os.getcwd())
        snapshot_dir = repo_root / "logs" / "snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        # Validate and normalize files
        norm_files: List[Path] = []
        for f in self.files:
            p = Path(f).resolve()
            try:
                p.relative_to(repo_root)
            except Exception:
                return f"Exit code: 1\nError: File is outside repo root: {p}"
            if not p.exists() or not p.is_file():
                return f"Exit code: 1\nError: File not found or not a file: {p}"
            norm_files.append(p)

        # Create unique snapshot id
        from datetime import datetime

        snapshot_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        target = snapshot_dir / snapshot_id
        files_dir = target / "files"
        files_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "snapshot_id": snapshot_id,
            "repo_root": str(repo_root),
            "files": [],
            "note": self.note or "",
        }

        for p in norm_files:
            rel = p.relative_to(repo_root)
            dst = files_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
            manifest["files"].append({"path": str(rel)})

        with open(target / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return f"Snapshot created: {snapshot_id} (files={len(norm_files)})"


class WorkspaceUndo(BaseTool):
    """
    Restore files from a previously created snapshot.
    """

    snapshot_id: str = Field(..., description="Snapshot identifier to restore")
    dry_run: bool = Field(False, description="If true, list intended changes without writing")

    def run(self) -> str:
        repo_root = Path(os.getcwd())
        target = repo_root / "logs" / "snapshots" / self.snapshot_id
        manifest_path = target / "manifest.json"
        files_dir = target / "files"

        if not manifest_path.exists():
            return f"Exit code: 1\nError: Snapshot not found: {self.snapshot_id}"

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as e:
            return f"Exit code: 1\nError: Corrupted manifest: {e}"

        restored = []
        for entry in manifest.get("files", []):
            rel = Path(entry.get("path", ""))
            src = files_dir / rel
            dst = repo_root / rel
            if not src.exists():
                return f"Exit code: 1\nError: Snapshot missing file: {src}"
            if not self.dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(src, dst)
                except Exception as e:
                    return f"Exit code: 1\nError: Failed to restore file '{rel}': {e}"
            restored.append(str(rel))

        action = "Planned restore" if self.dry_run else "Restored"
        return f"{action} {len(restored)} file(s) from snapshot {self.snapshot_id}: " + \
               ", ".join(restored[:10]) + ("..." if len(restored) > 10 else "")


workspace_snapshot = WorkspaceSnapshot
workspace_undo = WorkspaceUndo
