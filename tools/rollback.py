"""
Rollback system for autonomous operations.

Every fix creates a snapshot that can be restored.
Provides defense-in-depth with multiple restore mechanisms:
1. File content snapshots (fastest)
2. Git ref fallback (if file restore fails)

Constitutional Compliance:
- Article I: Complete context via snapshot metadata
- Article II: 100% verification via test-after-rollback
- Article III: Automated enforcement via auto-rollback on failure
"""

import json
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.type_definitions.result import Err, Ok, Result


SNAPSHOT_DIR = PROJECT_ROOT / "logs" / "snapshots"
MAX_SNAPSHOTS = 50


@dataclass
class Snapshot:
    """A restorable snapshot of file state."""

    id: str
    timestamp: datetime
    files: dict[str, str]  # path -> content
    git_ref: str
    description: str
    restored: bool = False


@dataclass
class RollbackResult:
    """Result of a rollback operation."""

    success: bool
    snapshot_id: str
    files_restored: list[str] = field(default_factory=list)
    git_fallback_used: bool = False
    error: Optional[str] = None


class RollbackManager:
    """Manages snapshots and rollbacks."""

    def __init__(self, snapshot_dir: Path | str | None = None):
        """Initialize rollback manager.

        Args:
            snapshot_dir: Directory to store snapshots
        """
        self.snapshot_dir = Path(snapshot_dir) if snapshot_dir else SNAPSHOT_DIR
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.current_snapshot: Optional[Snapshot] = None

    def create_snapshot(self, files: list[str], description: str) -> Result[Snapshot, str]:
        """Create snapshot before making changes.

        Args:
            files: List of file paths to snapshot
            description: Human-readable description

        Returns:
            Result containing Snapshot or error
        """
        snapshot_id = f"snap_{int(datetime.now().timestamp() * 1000)}"

        # Get current git ref
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
            )
            git_ref = result.stdout.strip()
        except Exception:
            git_ref = "unknown"

        # Capture file contents
        file_contents = {}
        for file_path in files:
            path = Path(file_path) if Path(file_path).is_absolute() else PROJECT_ROOT / file_path
            if path.exists():
                try:
                    file_contents[str(path)] = path.read_text()
                except Exception as e:
                    return Err(f"Failed to read {file_path}: {e}")
            else:
                # File doesn't exist yet - record as empty for deletion on rollback
                file_contents[str(path)] = ""

        snapshot = Snapshot(
            id=snapshot_id,
            timestamp=datetime.now(),
            files=file_contents,
            git_ref=git_ref,
            description=description,
        )

        # Save snapshot
        snapshot_path = self.snapshot_dir / f"{snapshot_id}.json"
        try:
            snapshot_path.write_text(
                json.dumps(
                    {
                        "id": snapshot.id,
                        "timestamp": snapshot.timestamp.isoformat(),
                        "files": snapshot.files,
                        "git_ref": snapshot.git_ref,
                        "description": snapshot.description,
                    },
                    indent=2,
                )
            )
        except Exception as e:
            return Err(f"Failed to save snapshot: {e}")

        self.current_snapshot = snapshot
        return Ok(snapshot)

    def load_snapshot(self, snapshot_id: str) -> Result[Snapshot, str]:
        """Load a snapshot from disk.

        Args:
            snapshot_id: ID of snapshot to load

        Returns:
            Result containing Snapshot or error
        """
        snapshot_path = self.snapshot_dir / f"{snapshot_id}.json"
        if not snapshot_path.exists():
            return Err(f"Snapshot not found: {snapshot_id}")

        try:
            data = json.loads(snapshot_path.read_text())
            return Ok(
                Snapshot(
                    id=data["id"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    files=data["files"],
                    git_ref=data["git_ref"],
                    description=data["description"],
                )
            )
        except Exception as e:
            return Err(f"Failed to load snapshot: {e}")

    def rollback(self, snapshot_id: Optional[str] = None) -> Result[RollbackResult, str]:
        """Rollback to a snapshot.

        Args:
            snapshot_id: ID of snapshot to rollback to (uses current if None)

        Returns:
            Result containing RollbackResult or error
        """
        # Get snapshot to restore
        if snapshot_id:
            result = self.load_snapshot(snapshot_id)
            if result.is_err():
                return Err(result.unwrap_err())
            snapshot = result.unwrap()
        elif self.current_snapshot:
            snapshot = self.current_snapshot
        else:
            return Err("No snapshot to rollback to")

        files_restored = []
        git_fallback_used = False

        # Restore files
        for file_path, content in snapshot.files.items():
            try:
                path = Path(file_path)
                if content:
                    path.write_text(content)
                    files_restored.append(file_path)
                elif path.exists():
                    # File was created after snapshot - delete it
                    path.unlink()
                    files_restored.append(f"{file_path} (deleted)")
            except Exception as e:
                # File restore failed - try git fallback
                try:
                    subprocess.run(
                        ["git", "checkout", snapshot.git_ref, "--", file_path],
                        capture_output=True,
                        cwd=str(PROJECT_ROOT),
                    )
                    git_fallback_used = True
                    files_restored.append(f"{file_path} (git)")
                except Exception:
                    return Err(f"Failed to restore {file_path}: {e}")

        # Mark snapshot as restored
        snapshot.restored = True

        return Ok(
            RollbackResult(
                success=True,
                snapshot_id=snapshot.id,
                files_restored=files_restored,
                git_fallback_used=git_fallback_used,
            )
        )

    def rollback_with_test_verify(
        self, snapshot_id: Optional[str] = None, test_path: str = "tests/unit/"
    ) -> Result[RollbackResult, str]:
        """Rollback and verify tests pass.

        Args:
            snapshot_id: ID of snapshot to rollback to
            test_path: Path to tests to run

        Returns:
            Result containing RollbackResult or error
        """
        # Perform rollback
        result = self.rollback(snapshot_id)
        if result.is_err():
            return result

        rollback_result = result.unwrap()

        # Verify tests pass
        test_result = subprocess.run(
            ["python", "-m", "pytest", test_path, "-x", "--tb=no", "-q"],
            capture_output=True,
            timeout=300,
            cwd=str(PROJECT_ROOT),
        )

        if test_result.returncode != 0:
            rollback_result.error = "Tests failed after rollback"
            rollback_result.success = False

        return Ok(rollback_result)

    def cleanup_old_snapshots(self, keep_last: int = MAX_SNAPSHOTS) -> int:
        """Remove old snapshots, keeping the most recent.

        Args:
            keep_last: Number of recent snapshots to keep

        Returns:
            Number of snapshots removed
        """
        snapshots = sorted(self.snapshot_dir.glob("snap_*.json"))
        removed = 0

        for old_snapshot in snapshots[:-keep_last]:
            try:
                old_snapshot.unlink()
                removed += 1
            except Exception:
                pass

        return removed

    def list_snapshots(self, limit: int = 10) -> list[dict]:
        """List recent snapshots.

        Args:
            limit: Maximum number to return

        Returns:
            List of snapshot metadata
        """
        snapshots = sorted(self.snapshot_dir.glob("snap_*.json"), reverse=True)
        result = []

        for snapshot_path in snapshots[:limit]:
            try:
                data = json.loads(snapshot_path.read_text())
                result.append(
                    {
                        "id": data["id"],
                        "timestamp": data["timestamp"],
                        "description": data["description"],
                        "files_count": len(data["files"]),
                    }
                )
            except Exception:
                pass

        return result


# Global rollback manager
_ROLLBACK = RollbackManager()


def get_rollback_manager() -> RollbackManager:
    """Get the global rollback manager."""
    return _ROLLBACK


@contextmanager
def with_rollback(files: list[str], description: str):
    """Context manager for operations with automatic rollback on failure.

    Args:
        files: List of file paths to snapshot
        description: Description for the snapshot

    Yields:
        The created snapshot

    Example:
        with with_rollback(["tools/foo.py"], "Adding feature X"):
            # Make changes...
            # If exception occurs, changes are rolled back automatically
    """
    manager = get_rollback_manager()
    result = manager.create_snapshot(files, description)

    if result.is_err():
        raise RuntimeError(f"Failed to create snapshot: {result.unwrap_err()}")

    snapshot = result.unwrap()

    try:
        yield snapshot
    except Exception as e:
        print(f"⚠️ Error occurred, rolling back: {e}")
        rollback_result = manager.rollback(snapshot.id)
        if rollback_result.is_ok():
            print(f"✅ Rolled back to {snapshot.id}")
        else:
            print(f"❌ Rollback failed: {rollback_result.unwrap_err()}")
        raise


def create_snapshot(files: list[str], description: str) -> Result[Snapshot, str]:
    """Convenience function to create a snapshot.

    Args:
        files: List of file paths
        description: Description

    Returns:
        Result containing Snapshot or error
    """
    return _ROLLBACK.create_snapshot(files, description)


def rollback(snapshot_id: Optional[str] = None) -> Result[RollbackResult, str]:
    """Convenience function to rollback.

    Args:
        snapshot_id: Snapshot ID (uses current if None)

    Returns:
        Result containing RollbackResult or error
    """
    return _ROLLBACK.rollback(snapshot_id)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Rollback management")
    parser.add_argument("--list", action="store_true", help="List recent snapshots")
    parser.add_argument("--rollback", type=str, help="Rollback to snapshot ID")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup old snapshots")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    args = parser.parse_args()

    manager = get_rollback_manager()

    if args.list:
        snapshots = manager.list_snapshots()
        print(f"\nRecent Snapshots ({len(snapshots)}):\n")
        for snap in snapshots:
            print(f"  {snap['id']}")
            print(f"    Created: {snap['timestamp']}")
            print(f"    Description: {snap['description']}")
            print(f"    Files: {snap['files_count']}")
            print()

    elif args.rollback:
        result = manager.rollback(args.rollback)
        if result.is_ok():
            r = result.unwrap()
            print(f"✅ Rolled back to {r.snapshot_id}")
            print(f"   Files restored: {len(r.files_restored)}")
            if r.git_fallback_used:
                print("   Note: Git fallback was used for some files")
        else:
            print(f"❌ Rollback failed: {result.unwrap_err()}")

    elif args.cleanup:
        removed = manager.cleanup_old_snapshots()
        print(f"Removed {removed} old snapshots")

    elif args.demo:
        print("=== Rollback Demo ===\n")

        # Create a test file
        test_file = PROJECT_ROOT / "logs" / "_rollback_test.tmp"
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text("original content")

        print(f"1. Created test file: {test_file}")
        print(f"   Content: {test_file.read_text()}")

        # Create snapshot
        result = manager.create_snapshot([str(test_file)], "Demo snapshot")
        if result.is_ok():
            snapshot = result.unwrap()
            print(f"\n2. Created snapshot: {snapshot.id}")

            # Modify file
            test_file.write_text("modified content")
            print(f"\n3. Modified file")
            print(f"   Content: {test_file.read_text()}")

            # Rollback
            rollback_result = manager.rollback(snapshot.id)
            if rollback_result.is_ok():
                r = rollback_result.unwrap()
                print(f"\n4. Rolled back")
                print(f"   Content: {test_file.read_text()}")
                print(f"   Success: {r.success}")

            # Cleanup
            test_file.unlink()
            print("\n5. Cleaned up test file")
        else:
            print(f"Error: {result.unwrap_err()}")

    else:
        parser.print_help()
