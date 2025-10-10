"""
Session garbage collection for automatic TTL-based cleanup.

Implements automatic garbage collection for expired session states with
configurable retention policies and metrics logging.

Constitutional Compliance:
- Article I: Complete context - full session evaluation before deletion
- Article II: 100% verification - dry-run mode for testing
- Article IV: Learning integration - metrics logged for optimization
- Article V: Follows spec: specs/leap_2_session_state_optimization.md (Section 3)

Performance Target:
- <100ms to scan 1000 sessions
- 100% expired sessions cleaned within 24 hours

Usage:
    >>> from pathlib import Path
    >>> from shared.session_gc import SessionGarbageCollector
    >>> from shared.models.session import RetentionPolicy
    >>>
    >>> # Create collector with default retention policy
    >>> collector = SessionGarbageCollector(
    ...     session_dir=Path("~/.agency/memories/sessions").expanduser(),
    ...     archive_dir=Path("~/.agency/memories/archives").expanduser()
    ... )
    >>>
    >>> # Dry-run to see what would be deleted
    >>> result = collector.collect_expired_sessions(dry_run=True)
    >>> if result.is_ok():
    ...     gc_result = result.unwrap()
    ...     print(f"Would delete {gc_result.sessions_deleted} sessions")
    >>>
    >>> # Execute cleanup
    >>> result = collector.collect_expired_sessions(dry_run=False)
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from shared.models.session import (
    GCResult,
    RetentionPolicy,
    SessionState,
    SessionStatus,
)
from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)


class SessionGarbageCollector:
    """
    Automatic garbage collection for expired session states.

    Scans session directory and deletes/archives sessions based on:
    - TTL expiration (default 30 days)
    - Retention policies (90 days for completed, 30 for abandoned)
    - Session status (never delete RUNNING/CHECKPOINTED)

    Attributes:
        session_dir: Directory containing session state files
        archive_dir: Optional directory for archiving completed sessions
        retention_policy: Configurable retention rules
    """

    def __init__(
        self,
        session_dir: Path,
        archive_dir: Path | None = None,
        retention_policy: RetentionPolicy | None = None,
    ):
        """
        Initialize garbage collector.

        Args:
            session_dir: Directory containing session state files
            archive_dir: Optional directory for archiving completed sessions
            retention_policy: Custom retention policy (uses defaults if None)
        """
        self.session_dir = Path(session_dir)
        self.archive_dir = Path(archive_dir) if archive_dir else None
        self.retention_policy = retention_policy or RetentionPolicy()

        # Ensure session directory exists
        if not self.session_dir.exists():
            logger.warning(f"Session directory does not exist: {self.session_dir}")

    def collect_expired_sessions(
        self, dry_run: bool = False
    ) -> Result[GCResult, str]:
        """
        Run garbage collection on all session files.

        Scans all session files in session_dir, evaluates retention policy,
        and deletes/archives eligible sessions.

        Args:
            dry_run: If True, report what would be deleted without deleting

        Returns:
            Result with GCResult containing metrics or error message

        Example:
            >>> collector = SessionGarbageCollector(Path("~/.agency/sessions"))
            >>> result = collector.collect_expired_sessions(dry_run=True)
            >>> if result.is_ok():
            ...     metrics = result.unwrap()
            ...     print(f"Would delete: {metrics.sessions_deleted}")
            ...     print(f"Would archive: {metrics.sessions_archived}")
            ...     print(f"Space reclaimed: {metrics.disk_space_reclaimed_mb:.2f}MB")
        """
        start_time = time.perf_counter()
        gc_result = GCResult()

        try:
            # Validate session directory exists
            if not self.session_dir.exists():
                return Err(f"Session directory not found: {self.session_dir}")

            # Scan all session files (compressed and uncompressed)
            session_files = list(self.session_dir.glob("*.json.zlib"))
            session_files.extend(self.session_dir.glob("*.json"))

            logger.info(
                f"GC started: {len(session_files)} session files found "
                f"(dry_run={dry_run})"
            )

            for session_file in session_files:
                gc_result.sessions_scanned += 1

                # Load session state
                load_result = self._load_session(session_file)
                if load_result.is_err():
                    error_msg = (
                        f"{session_file.name}: {load_result.unwrap_err()}"
                    )
                    gc_result.errors.append(error_msg)
                    logger.warning(f"Failed to load session: {error_msg}")
                    continue

                session = load_result.unwrap()

                # Evaluate retention policy
                should_collect, reason = self._should_collect(session)

                if should_collect:
                    file_size_mb = session_file.stat().st_size / (1024 * 1024)

                    if (
                        session.is_completed()
                        and self.retention_policy.archive_completed
                        and self.archive_dir
                    ):
                        # Archive completed sessions
                        if not dry_run:
                            archive_result = self._archive_session(session_file)
                            if archive_result.is_err():
                                gc_result.errors.append(
                                    f"Archive failed: {session_file.name}: "
                                    f"{archive_result.unwrap_err()}"
                                )
                                continue

                        gc_result.sessions_archived += 1
                        logger.info(
                            f"{'Would archive' if dry_run else 'Archived'}: "
                            f"{session_file.name} ({reason})"
                        )
                    else:
                        # Delete non-completed or non-archived sessions
                        if not dry_run:
                            try:
                                session_file.unlink()
                            except Exception as e:
                                gc_result.errors.append(
                                    f"Delete failed: {session_file.name}: {str(e)}"
                                )
                                continue

                        gc_result.sessions_deleted += 1
                        gc_result.disk_space_reclaimed_mb += file_size_mb
                        logger.info(
                            f"{'Would delete' if dry_run else 'Deleted'}: "
                            f"{session_file.name} ({reason})"
                        )

            # Calculate total execution time
            gc_result.collection_time_ms = (time.perf_counter() - start_time) * 1000

            # Log summary
            logger.info(
                f"GC completed: {gc_result.sessions_scanned} scanned, "
                f"{gc_result.sessions_deleted} deleted, "
                f"{gc_result.sessions_archived} archived, "
                f"{gc_result.disk_space_reclaimed_mb:.2f}MB reclaimed, "
                f"{len(gc_result.errors)} errors "
                f"({gc_result.collection_time_ms:.2f}ms)"
            )

            return Ok(gc_result)

        except Exception as e:
            return Err(f"Garbage collection failed: {str(e)}")

    def _load_session(self, session_file: Path) -> Result[SessionState, str]:
        """
        Load session state from file (compressed or uncompressed).

        Args:
            session_file: Path to session file

        Returns:
            Result with SessionState or error message
        """
        try:
            if session_file.suffix == ".zlib":
                # Compressed session - defer decompression to future compression module
                # For now, treat as error since compression module not yet implemented
                return Err("Compressed sessions not yet supported (zlib decompression pending)")

            # Uncompressed JSON session
            json_content = session_file.read_text(encoding="utf-8")
            session_dict = json.loads(json_content)
            session = SessionState(**session_dict)
            return Ok(session)

        except json.JSONDecodeError as e:
            return Err(f"JSON parsing error: {str(e)}")
        except Exception as e:
            return Err(f"Load error: {str(e)}")

    def _should_collect(self, session: SessionState) -> tuple[bool, str]:
        """
        Evaluate retention policy for a session.

        Implements decision tree:
        1. Never collect RUNNING or CHECKPOINTED sessions
        2. Completed sessions: retain for 90 days (overrides TTL)
        3. Abandoned sessions: retain for 30 days (overrides TTL)
        4. TTL expired: collect if not covered by status-specific retention

        Retention policy takes precedence over TTL to allow completed sessions
        to be retained longer than the default 30-day TTL.

        Args:
            session: Session state to evaluate

        Returns:
            Tuple of (should_collect: bool, reason: str)
        """
        # Never collect active sessions (Constitutional safety check)
        if session.status in [SessionStatus.RUNNING, SessionStatus.CHECKPOINTED]:
            return (False, "Active session (RUNNING or CHECKPOINTED)")

        # Completed sessions: 90-day retention (overrides TTL)
        if session.is_completed():
            retention_days = self.retention_policy.completed_retention_days
            age_days = (datetime.now() - session.updated_at).days

            if age_days > retention_days:
                return (
                    True,
                    f"Completed session older than {retention_days} days "
                    f"(age: {age_days} days)",
                )
            return (
                False,
                f"Completed session within {retention_days}-day retention "
                f"(age: {age_days} days)",
            )

        # Abandoned sessions: 30-day retention (overrides TTL)
        if session.is_abandoned():
            retention_days = self.retention_policy.abandoned_retention_days
            age_days = (datetime.now() - session.updated_at).days

            if age_days > retention_days:
                return (
                    True,
                    f"Abandoned session older than {retention_days} days "
                    f"(age: {age_days} days)",
                )
            return (
                False,
                f"Abandoned session within {retention_days}-day retention "
                f"(age: {age_days} days)",
            )

        # TTL expired for non-completed, non-abandoned sessions
        if self.retention_policy.respect_ttl and session.is_expired():
            return (True, "TTL expired")

        # Default: do not collect
        return (False, "No collection criteria met")

    def _archive_session(self, session_file: Path) -> Result[None, str]:
        """
        Archive session to archive directory.

        Moves session file from session_dir to archive_dir, preserving filename.

        Args:
            session_file: Session file to archive

        Returns:
            Result with None on success or error message
        """
        try:
            if not self.archive_dir:
                return Err("Archive directory not configured")

            # Create archive directory if it doesn't exist
            self.archive_dir.mkdir(parents=True, exist_ok=True)

            # Move file to archive
            archive_path = self.archive_dir / session_file.name
            session_file.rename(archive_path)

            return Ok(None)

        except Exception as e:
            return Err(f"Archive operation failed: {str(e)}")


def schedule_daily_gc(
    session_dir: Path,
    archive_dir: Path | None = None,
    hour: int = 2,
    retention_policy: RetentionPolicy | None = None,
) -> Result[str, str]:
    """
    Schedule daily garbage collection at specified hour.

    This is a placeholder function for future background task integration.
    Actual implementation would use:
    - APScheduler for Python-based scheduling
    - Cron job for system-level scheduling
    - Background thread with asyncio.sleep for simple approach

    Args:
        session_dir: Directory containing session files
        archive_dir: Optional archive directory for completed sessions
        hour: Hour of day to run (0-23, default 2am)
        retention_policy: Custom retention policy (uses defaults if None)

    Returns:
        Result with schedule description or error message

    Example:
        >>> result = schedule_daily_gc(
        ...     session_dir=Path("~/.agency/sessions"),
        ...     hour=2
        ... )
        >>> if result.is_ok():
        ...     print(result.unwrap())
        "Daily GC scheduled at 02:00 for ~/.agency/sessions"
    """
    if not 0 <= hour <= 23:
        return Err(f"Invalid hour: {hour} (must be 0-23)")

    if not session_dir.exists():
        return Err(f"Session directory not found: {session_dir}")

    schedule_msg = (
        f"Daily GC scheduled at {hour:02d}:00 for {session_dir} "
        f"(Implementation pending: cron/APScheduler integration)"
    )

    logger.info(schedule_msg)

    # TODO: Phase 4 Code task - Implement actual scheduling
    # Options:
    # 1. APScheduler: from apscheduler.schedulers.background import BackgroundScheduler
    # 2. Cron job: 0 2 * * * python -m shared.session_gc
    # 3. asyncio: while True: await asyncio.sleep(seconds_until_next_run)

    return Ok(schedule_msg)
