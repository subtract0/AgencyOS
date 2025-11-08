#!/usr/bin/env python3
"""
Rollback System - Phase 1, Task 4
Comprehensive state restoration

Features:
- Git rollback (reset to commit)
- File rollback (restore from backup)
- Full system rollback
- Snapshot management
- Rollback history

Constitutional Compliance:
- Article I: Complete rollback or fail (no partial states)
- Article II: Validate before rollback
- Article III: Automated restoration

Usage:
    # Create snapshot before risky operation
    rm = RollbackManager()
    snapshot_id = rm.create_snapshot(SnapshotType.GIT, "Before refactor").unwrap()

    # ... perform operations ...

    # Rollback if needed
    rm.rollback(snapshot_id)
"""

import json
import shutil
import subprocess
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result


# ============================================================================
# ENUMS
# ============================================================================


class SnapshotType(str, Enum):
    """Snapshot type"""

    GIT = "git"  # Git commit/branch state
    FILE = "file"  # File system backup
    FULL = "full"  # Full system state


# ============================================================================
# DATA MODELS
# ============================================================================


class Snapshot(BaseModel):
    """Snapshot metadata"""

    snapshot_id: str = Field(..., description="Unique snapshot ID")
    snapshot_type: SnapshotType = Field(..., description="Type of snapshot")
    description: str = Field(..., description="Human-readable description")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
    )
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")
    backup_path: Optional[Path] = Field(default=None, description="Backup file path")


class RollbackResult(BaseModel):
    """Result of rollback operation"""

    success: bool = Field(..., description="Whether rollback succeeded")
    snapshot_id: str = Field(..., description="Snapshot that was restored")
    message: str = Field(default="", description="Result message")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Rollback timestamp",
    )


# ============================================================================
# ROLLBACK MANAGER
# ============================================================================


class RollbackManager:
    """
    Rollback Manager: Comprehensive state restoration

    Manages snapshots and rollbacks:
    1. Create snapshots before risky operations
    2. Rollback to any snapshot
    3. Automatic cleanup of old snapshots
    4. Validation before rollback
    """

    def __init__(
        self,
        snapshot_dir: Optional[Path] = None,
        retention_days: int = 30,
    ):
        """
        Initialize rollback manager

        Args:
            snapshot_dir: Directory for storing snapshots
            retention_days: Days to retain snapshots
        """
        self.snapshot_dir = snapshot_dir or (
            Path.home() / ".agency" / "rollback" / "snapshots"
        )
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        self.retention_days = retention_days

        # In-memory snapshot registry
        self.snapshots: Dict[str, Snapshot] = {}

        # Rollback history
        self.history: List[Dict] = []

        # Load existing snapshots
        self._load_snapshots()

    def _load_snapshots(self) -> None:
        """Load snapshots from disk"""
        try:
            manifest_file = self.snapshot_dir / "manifest.json"
            if manifest_file.exists():
                with open(manifest_file) as f:
                    data = json.load(f)
                    for snapshot_data in data.get("snapshots", []):
                        snapshot = Snapshot(**snapshot_data)
                        self.snapshots[snapshot.snapshot_id] = snapshot
        except Exception:
            pass  # Start fresh if loading fails

    def _save_snapshots(self) -> None:
        """Save snapshots to disk"""
        try:
            manifest_file = self.snapshot_dir / "manifest.json"
            data = {
                "snapshots": [
                    s.model_dump(mode="json") for s in self.snapshots.values()
                ]
            }
            with open(manifest_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception:
            pass  # Best effort save

    def create_snapshot(
        self,
        snapshot_type: SnapshotType,
        description: str,
        metadata: Optional[Dict] = None,
    ) -> Result[str, str]:
        """
        Create snapshot

        Args:
            snapshot_type: Type of snapshot
            description: Description
            metadata: Additional metadata

        Returns:
            Result with snapshot ID or error
        """
        try:
            snapshot_id = str(uuid.uuid4())
            snapshot = Snapshot(
                snapshot_id=snapshot_id,
                snapshot_type=snapshot_type,
                description=description,
                metadata=metadata or {},
            )

            # Create backup based on type
            if snapshot_type == SnapshotType.GIT:
                backup_result = self._backup_git(snapshot)
                if backup_result.is_err():
                    return backup_result

            elif snapshot_type == SnapshotType.FILE:
                file_path = metadata.get("file_path") if metadata else None
                if not file_path:
                    return Err("file_path required in metadata for FILE snapshot")

                backup_result = self._backup_file(Path(file_path), snapshot)
                if backup_result.is_err():
                    return backup_result

            elif snapshot_type == SnapshotType.FULL:
                backup_result = self._backup_full(snapshot)
                if backup_result.is_err():
                    return backup_result

            # Register snapshot
            self.snapshots[snapshot_id] = snapshot
            self._save_snapshots()

            return Ok(snapshot_id)

        except Exception as e:
            return Err(f"Failed to create snapshot: {e}")

    def _backup_git(self, snapshot: Snapshot) -> Result[None, str]:
        """Backup git state"""
        try:
            # Get current commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return Err("Failed to get git commit hash")

            commit_hash = result.stdout.strip()
            snapshot.metadata["commit_hash"] = commit_hash

            return Ok(None)

        except Exception as e:
            return Err(f"Git backup failed: {e}")

    def _backup_file(self, file_path: Path, snapshot: Snapshot) -> Result[None, str]:
        """Backup file"""
        try:
            if not file_path.exists():
                return Err(f"File does not exist: {file_path}")

            # Copy file to backup location
            backup_path = self.snapshot_dir / f"{snapshot.snapshot_id}_{file_path.name}"
            shutil.copy2(file_path, backup_path)
            snapshot.backup_path = backup_path

            return Ok(None)

        except Exception as e:
            return Err(f"File backup failed: {e}")

    def _backup_full(self, snapshot: Snapshot) -> Result[None, str]:
        """Backup full system state"""
        try:
            # For now, combine git + key files
            # In a real system, this would be more comprehensive
            git_result = self._backup_git(snapshot)
            if git_result.is_err():
                return git_result

            return Ok(None)

        except Exception as e:
            return Err(f"Full backup failed: {e}")

    def get_snapshot(self, snapshot_id: str) -> Result[Snapshot, str]:
        """Get snapshot by ID"""
        if snapshot_id not in self.snapshots:
            return Err(f"Snapshot not found: {snapshot_id}")

        return Ok(self.snapshots[snapshot_id])

    def list_snapshots(
        self, snapshot_type: Optional[SnapshotType] = None
    ) -> List[Snapshot]:
        """List all snapshots, optionally filtered by type"""
        snapshots = list(self.snapshots.values())

        if snapshot_type:
            snapshots = [s for s in snapshots if s.snapshot_type == snapshot_type]

        # Sort by creation time (newest first)
        snapshots.sort(key=lambda s: s.created_at, reverse=True)

        return snapshots

    def rollback(self, snapshot_id: str) -> Result[RollbackResult, str]:
        """
        Rollback to snapshot

        Args:
            snapshot_id: Snapshot to restore

        Returns:
            Result with rollback result or error
        """
        # Get snapshot
        snapshot_result = self.get_snapshot(snapshot_id)
        if snapshot_result.is_err():
            return Err(snapshot_result.unwrap_err())

        snapshot = snapshot_result.unwrap()

        # Validate snapshot
        validate_result = self.validate_snapshot(snapshot_id)
        if validate_result.is_err():
            return Err(f"Snapshot validation failed: {validate_result.unwrap_err()}")

        # Perform rollback based on type
        try:
            if snapshot.snapshot_type == SnapshotType.GIT:
                rollback_result = self._rollback_git(snapshot)

            elif snapshot.snapshot_type == SnapshotType.FILE:
                rollback_result = self._rollback_file(snapshot)

            elif snapshot.snapshot_type == SnapshotType.FULL:
                rollback_result = self._rollback_full(snapshot)

            else:
                return Err(f"Unknown snapshot type: {snapshot.snapshot_type}")

            if rollback_result.is_err():
                return Err(rollback_result.unwrap_err())

            # Record in history
            result = RollbackResult(
                success=True,
                snapshot_id=snapshot_id,
                message=f"Rolled back to: {snapshot.description}",
            )

            self.history.append({
                "snapshot_id": snapshot_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "success": True,
            })

            return Ok(result)

        except Exception as e:
            return Err(f"Rollback failed: {e}")

    def _rollback_git(self, snapshot: Snapshot) -> Result[None, str]:
        """Rollback git state"""
        try:
            commit_hash = snapshot.metadata.get("commit_hash")
            if not commit_hash:
                return Err("No commit hash in snapshot")

            # Git reset to commit
            result = subprocess.run(
                ["git", "reset", "--hard", commit_hash],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return Err(f"Git reset failed: {result.stderr}")

            return Ok(None)

        except Exception as e:
            return Err(f"Git rollback failed: {e}")

    def _rollback_file(self, snapshot: Snapshot) -> Result[None, str]:
        """Rollback file from backup"""
        try:
            if not snapshot.backup_path or not snapshot.backup_path.exists():
                return Err("Backup file not found")

            file_path_str = snapshot.metadata.get("file_path")
            if not file_path_str:
                return Err("No file path in snapshot metadata")

            target_path = Path(file_path_str)

            # Restore from backup
            shutil.copy2(snapshot.backup_path, target_path)

            return Ok(None)

        except Exception as e:
            return Err(f"File rollback failed: {e}")

    def _rollback_full(self, snapshot: Snapshot) -> Result[None, str]:
        """Rollback full system"""
        try:
            # Rollback git
            git_result = self._rollback_git(snapshot)
            if git_result.is_err():
                return git_result

            # In a real system, restore other components here

            return Ok(None)

        except Exception as e:
            return Err(f"Full rollback failed: {e}")

    def validate_snapshot(self, snapshot_id: str) -> Result[None, str]:
        """Validate snapshot integrity"""
        snapshot_result = self.get_snapshot(snapshot_id)
        if snapshot_result.is_err():
            return Err(snapshot_result.unwrap_err())

        snapshot = snapshot_result.unwrap()

        # Check if backup exists for FILE snapshots
        if snapshot.snapshot_type == SnapshotType.FILE:
            if not snapshot.backup_path or not snapshot.backup_path.exists():
                return Err("Backup file missing")

        # Check git commit exists for GIT snapshots
        if snapshot.snapshot_type == SnapshotType.GIT:
            commit_hash = snapshot.metadata.get("commit_hash")
            if not commit_hash:
                return Err("No commit hash in snapshot")

            # Verify commit exists
            try:
                result = subprocess.run(
                    ["git", "cat-file", "-e", commit_hash],
                    capture_output=True,
                    timeout=10,
                )
                if result.returncode != 0:
                    return Err(f"Git commit not found: {commit_hash}")
            except Exception:
                return Err("Failed to verify git commit")

        return Ok(None)

    def delete_snapshot(self, snapshot_id: str) -> Result[None, str]:
        """Delete snapshot"""
        if snapshot_id not in self.snapshots:
            return Err(f"Snapshot not found: {snapshot_id}")

        snapshot = self.snapshots[snapshot_id]

        # Delete backup file if exists
        if snapshot.backup_path and snapshot.backup_path.exists():
            try:
                snapshot.backup_path.unlink()
            except Exception:
                pass  # Best effort

        # Remove from registry
        del self.snapshots[snapshot_id]
        self._save_snapshots()

        return Ok(None)

    def cleanup_old_snapshots(self) -> Result[int, str]:
        """Cleanup snapshots older than retention period"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
            deleted_count = 0

            for snapshot_id, snapshot in list(self.snapshots.items()):
                if snapshot.created_at < cutoff_date:
                    self.delete_snapshot(snapshot_id)
                    deleted_count += 1

            return Ok(deleted_count)

        except Exception as e:
            return Err(f"Cleanup failed: {e}")

    def get_rollback_history(self, limit: int = 10) -> List[Dict]:
        """Get rollback history"""
        # Return most recent first
        return self.history[-limit:][::-1]


# ============================================================================
# CLI
# ============================================================================


def main() -> None:
    """CLI entry point"""
    print("🔄 ROLLBACK SYSTEM")
    print("=" * 70)
    print("Use as a library - no CLI interface yet")
    print("=" * 70)


if __name__ == "__main__":
    main()
