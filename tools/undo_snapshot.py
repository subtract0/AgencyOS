import json
import os
import shutil
from pathlib import Path

from agency_swarm.tools import BaseTool
from pydantic import BaseModel, Field


class FileEntry(BaseModel):
    """Represents a file entry in the snapshot manifest."""

    path: str


class SnapshotManifest(BaseModel):
    """Represents the snapshot manifest structure."""

    snapshot_id: str
    repo_root: str
    files: list[FileEntry]
    note: str


class WorkspaceSnapshot(BaseTool):  # type: ignore[misc]
    """
    Create a reversible snapshot of one or more files within the repository root.
    Stores copies under logs/snapshots/<snapshot_id>/ with a manifest for undo.
    """

    files: list[str] = Field(
        ..., description="Absolute paths of files to snapshot (must reside under repo root)"
    )
    note: str | None = Field(None, description="Optional note to include in manifest")

    def run(self) -> str:
        repo_root = Path(os.getcwd())
        snapshot_dir = repo_root / "logs" / "snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        # Validate and normalize files
        norm_files: list[Path] = []
        for file_path in self.files:
            p = Path(file_path).resolve()
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

        manifest = SnapshotManifest(
            snapshot_id=snapshot_id, repo_root=str(repo_root), files=[], note=self.note or ""
        )

        for p in norm_files:
            rel = p.relative_to(repo_root)
            dst = files_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
            manifest.files.append(FileEntry(path=str(rel)))

        with open(target / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest.model_dump(), f, indent=2)

        return f"Snapshot created: {snapshot_id} (files={len(norm_files)})"


class WorkspaceUndo(BaseTool):  # type: ignore[misc]
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
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as e:
            return f"Exit code: 1\nError: Corrupted manifest: {e}"

        restored: list[str] = []
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
        return (
            f"{action} {len(restored)} file(s) from snapshot {self.snapshot_id}: "
            + ", ".join(restored[:10])
            + ("..." if len(restored) > 10 else "")
        )


workspace_snapshot = WorkspaceSnapshot
workspace_undo = WorkspaceUndo
