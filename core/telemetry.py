"""
SimpleTelemetry: Unified telemetry system with automatic retention.
Consolidates multiple telemetry systems into a single JSONL sink.
"""

import os
import json
import glob
import shutil
from datetime import datetime, timedelta
from typing import List, Optional
from shared.types.json import JSONValue
from shared.models.telemetry import TelemetryEvent, EventType, EventSeverity
from pathlib import Path


class SimpleTelemetry:
    """
    Unified telemetry system with automatic log rotation and retention.
    Single source of truth for all telemetry events.
    """

    def __init__(self, retention_runs: int = 10):
        """
        Initialize telemetry with configurable retention policy.

        Args:
            retention_runs: Number of recent runs to keep (default: 10)
        """
        # Anchor all paths under the current working directory (repo root during tests)
        self.allowed_root = Path.cwd().resolve()
        self.base_dir = self.allowed_root / "logs"
        self.events_dir = self.base_dir / "events"
        self.archive_dir = self.base_dir / "archive"
        self.retention_runs = retention_runs

        # Create directories (best-effort)
        self._ensure_dirs()

        # Current run file
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_file = self.events_dir / f"run_{self.run_id}.jsonl"

        # Apply retention on initialization
        self._apply_retention()

    def _ensure_dirs(self) -> None:
        """Ensure telemetry directories exist (best-effort)."""
        try:
            self.events_dir.mkdir(parents=True, exist_ok=True)
            self.archive_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Non-fatal; log() will attempt again and fallback gracefully
            pass

    def _is_safe_path(self, p: Path) -> bool:
        """Return True if path is within allowed_root (prevents traversal)."""
        try:
            rp = p.resolve()
            return self.allowed_root == rp or self.allowed_root in rp.parents
        except Exception:
            return False

    def log(self, event: str, data: dict[str, JSONValue], level: str = "info"):
        """
        Log a telemetry event to the unified sink.

        Args:
            event: Event name/type
            data: Event data dictionary
            level: Log level (info, warning, error, critical)
        """
        # Map string level to EventSeverity
        severity_map = {
            "debug": EventSeverity.DEBUG,
            "info": EventSeverity.INFO,
            "warning": EventSeverity.WARNING,
            "error": EventSeverity.ERROR,
            "critical": EventSeverity.CRITICAL
        }

        # Create Pydantic model for validation
        telemetry_event = TelemetryEvent(
            event_id=f"{self.run_id}_{datetime.now().timestamp()}",
            event_type=EventType.INFO,  # Default type, can be enhanced
            severity=severity_map.get(level, EventSeverity.INFO),
            metadata={"event_name": event, "run_id": self.run_id, **data}
        )

        # Convert to dict for backward compatibility
        entry = {
            "ts": telemetry_event.timestamp.isoformat() + "Z",
            "run_id": self.run_id,
            "level": level,
            "event": event,
            "data": data or {}
        }

        try:
            # Recreate directory on-demand (covers mid-run deletions)
            parent = self.current_file.parent
            if not self._is_safe_path(parent):
                raise PermissionError(f"Unsafe telemetry path outside project root: {parent}")
            parent.mkdir(parents=True, exist_ok=True)

            # Secure open with 0600 perms
            import os as _os
            fd = _os.open(str(self.current_file), _os.O_CREAT | _os.O_APPEND | _os.O_WRONLY, 0o600)
            try:
                with _os.fdopen(fd, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
                # Ensure file perms are correct (first creation enforces; chmod guards re-creation)
                try:
                    _os.chmod(self.current_file, 0o600)
                except Exception:
                    pass
            except Exception:
                # Ensure the descriptor is closed on failure
                try:
                    _os.close(fd)
                except Exception:
                    pass
                raise
        except Exception as e:
            # Fallback to stderr if file logging fails
            import sys
            print(f"Telemetry error: {e}", file=sys.stderr)

    def query(self,
              event_filter: Optional[str] = None,
              since: Optional[datetime] = None,
              limit: int = 100) -> List[dict[str, JSONValue]]:
        """
        Query recent telemetry events.

        Args:
            event_filter: Filter by event name (substring match)
            since: Only return events after this time
            limit: Maximum number of events to return

        Returns:
            List of matching events
        """
        events = []

        # Read from current and recent files
        files = sorted(self.events_dir.glob("run_*.jsonl"), reverse=True)[:3]

        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        if not line.strip():
                            continue

                        try:
                            event = json.loads(line)

                            # Apply filters
                            if event_filter and event_filter not in event.get("event", ""):
                                continue

                            if since:
                                event_time = datetime.fromisoformat(event["ts"].rstrip("Z"))
                                if event_time < since:
                                    continue

                            events.append(event)

                            if len(events) >= limit:
                                return events

                        except json.JSONDecodeError:
                            continue

            except Exception:
                continue

        return events

    def get_metrics(self) -> dict[str, JSONValue]:
        """
        Get aggregated metrics from recent telemetry.

        Returns:
            Dictionary with metrics like error rates, event counts, etc.
        """
        metrics = {
            "total_events": 0,
            "errors": 0,
            "warnings": 0,
            "event_types": {},
            "recent_errors": [],
            "health_score": 100.0
        }

        # Analyze last hour of events
        since = datetime.now() - timedelta(hours=1)
        events = self.query(since=since, limit=1000)

        for event in events:
            metrics["total_events"] += 1

            # Count by level
            level = event.get("level", "info")
            if level == "error":
                metrics["errors"] += 1
                metrics["recent_errors"].append({
                    "time": event["ts"],
                    "event": event["event"],
                    "message": event.get("data", {}).get("error", "Unknown error")
                })
            elif level == "warning":
                metrics["warnings"] += 1

            # Count by event type
            event_type = event.get("event", "unknown")
            metrics["event_types"][event_type] = metrics["event_types"].get(event_type, 0) + 1

        # Calculate health score (100 = perfect, 0 = critical)
        if metrics["total_events"] > 0:
            error_rate = metrics["errors"] / metrics["total_events"]
            metrics["health_score"] = max(0, 100 * (1 - error_rate * 2))

        # Keep only 5 most recent errors
        metrics["recent_errors"] = metrics["recent_errors"][-5:]

        return metrics

    def _apply_retention(self):
        """
        Apply retention policy by archiving old runs.
        Keeps only the most recent N runs in the events directory.
        """
        try:
            # Ensure archive dir exists before moving files
            self.archive_dir.mkdir(parents=True, exist_ok=True)

            # Get all run files sorted by name (which includes timestamp)
            run_files = sorted(self.events_dir.glob("run_*.jsonl"))

            if len(run_files) > self.retention_runs:
                # Archive older files
                files_to_archive = run_files[:-self.retention_runs]

                for file_path in files_to_archive:
                    archive_path = self.archive_dir / file_path.name
                    shutil.move(str(file_path), str(archive_path))

                self.log("retention_applied", {
                    "archived_count": len(files_to_archive),
                    "remaining_runs": self.retention_runs
                })

        except Exception as e:
            # Don't fail if retention fails
            self.log("retention_error", {"error": str(e)}, level="warning")

    def consolidate_legacy_logs(self):
        """
        One-time consolidation of legacy log files into unified format.
        Migrates logs from various directories into the unified sink.
        """
        legacy_dirs = [
            "logs/sessions",
            "logs/telemetry",
            "logs/auto_fixes",
            "logs/autonomous_healing"
        ]

        consolidated_count = 0

        for dir_path in legacy_dirs:
            if not os.path.exists(dir_path):
                continue

            # Process each legacy file
            for file_path in Path(dir_path).glob("*"):
                if file_path.suffix in ['.log', '.jsonl', '.json']:
                    try:
                        # Read and convert to unified format
                        with open(file_path, 'r') as f:
                            content = f.read()

                        # Log as legacy import event
                        self.log("legacy_import", {
                            "source": str(file_path),
                            "size": len(content),
                            "type": file_path.suffix
                        })

                        consolidated_count += 1

                        # Archive the original
                        archive_path = self.archive_dir / "legacy" / file_path.parent.name
                        archive_path.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(file_path), str(archive_path / file_path.name))

                    except Exception as e:
                        self.log("consolidation_error", {
                            "file": str(file_path),
                            "error": str(e)
                        }, level="warning")

        if consolidated_count > 0:
            self.log("consolidation_complete", {
                "files_processed": consolidated_count,
                "directories": legacy_dirs
            })

        return consolidated_count


# Global singleton instance
_telemetry_instance = None


def get_telemetry() -> SimpleTelemetry:
    """
    Get the global telemetry instance (singleton pattern).

    Returns:
        SimpleTelemetry: The global telemetry instance
    """
    global _telemetry_instance
    if _telemetry_instance is None:
        _telemetry_instance = SimpleTelemetry()
    return _telemetry_instance


def emit(event: str, data: dict[str, JSONValue] = None, level: str = "info"):
    """
    Convenience function to emit telemetry events.

    Args:
        event: Event name
        data: Event data (optional)
        level: Log level
    """
    telemetry = get_telemetry()
    telemetry.log(event, data or {}, level)