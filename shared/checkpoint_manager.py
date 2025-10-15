"""
CheckpointManager - Automated checkpoint management for multi-day task persistence.

Provides auto-checkpoint triggers (interval, task count, interrupt, phase),
resume logic with integrity validation, and retention policy enforcement.

Constitutional Compliance:
- Article I: Complete context (all checkpoints validated)
- Article II: Result pattern for all operations
- Article III: Automated triggers (no manual intervention)
- Article IV: Telemetry logging for learning
- Article V: Spec-driven design (specs/checkpoint_manager_spec.md)

Specification: specs/checkpoint_manager_spec.md (Milestone M2)
Phase: Leap 3 - CheckpointManager Service
"""

from __future__ import annotations

import json
import logging
import signal
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from shared.session_checkpoint import (
    SessionCheckpoint,
    load_checkpoint,
    save_checkpoint,
)
from shared.type_definitions.result import Err, Ok, Result

if TYPE_CHECKING:
    from shared.agent_context import AgentContext

logger = logging.getLogger(__name__)


class CheckpointConfig(BaseModel):
    """
    Configuration for CheckpointManager auto-checkpoint behavior.

    Constitutional Compliance:
    - Article II (Law #2): Strict typing with Pydantic, no Dict[Any, Any]
    """

    # Auto-checkpoint triggers
    auto_checkpoint_enabled: bool = Field(
        default=True, description="Enable/disable all auto-checkpoint triggers"
    )
    checkpoint_interval_tasks: int = Field(
        default=5, ge=1, description="Checkpoint after every N completed tasks"
    )
    checkpoint_interval_minutes: int = Field(
        default=30, ge=1, description="Checkpoint every N minutes (background timer)"
    )
    checkpoint_on_interrupt: bool = Field(default=True, description="Checkpoint on SIGINT (Ctrl+C)")
    checkpoint_on_phase_complete: bool = Field(
        default=True, description="Checkpoint on explicit phase completion"
    )

    # Retention policy
    checkpoint_retention_count: int = Field(
        default=5,
        ge=-1,
        description="Keep last N checkpoints (-1 = keep all, for debugging)",
    )
    checkpoint_retention_days: int = Field(
        default=7, ge=1, description="Delete checkpoints older than N days"
    )

    # Performance tuning
    checkpoint_compression_level: int = Field(
        default=6, ge=1, le=9, description="zlib compression level (1-9)"
    )
    checkpoint_max_retries: int = Field(
        default=3, ge=1, description="Max fallback attempts on corruption"
    )

    # Storage
    base_path: str = Field(default="~/.agency", description="Base directory for checkpoints")


class CheckpointManager:
    """
    Automated checkpoint management service for multi-day task persistence.

    Provides auto-checkpoint triggers (interval, task count, interrupt, phase),
    resume logic with integrity validation, and retention policy enforcement.

    Constitutional Compliance:
    - Article I: Complete context (all checkpoints validated)
    - Article II: Result pattern for all operations
    - Article III: Automated triggers (no manual intervention)
    - Article IV: Telemetry logging for learning
    - Article V: Spec-driven design (this specification)

    Example:
        >>> from shared.agent_context import create_agent_context
        >>> context = create_agent_context(session_id="task_123")
        >>> config = CheckpointConfig(checkpoint_interval_minutes=30)
        >>> manager = CheckpointManager(config)
        >>> manager.start_auto_checkpoint(context, task_id="feature_x")
        >>> # ... agent executes tasks ...
        >>> manager.stop_auto_checkpoint()
    """

    def __init__(self, config: CheckpointConfig):
        """Initialize CheckpointManager with configuration."""
        self.config = config
        self._lock = (
            threading.RLock()
        )  # Use RLock for reentrant locking (on_task_complete → trigger_checkpoint)
        self._timer_thread: threading.Thread | None = None
        self._stop_timer = threading.Event()
        self._task_count = 0
        self._context: AgentContext | None = None
        self._original_sigint_handler = None

        # Telemetry counters (Article IV)
        self._checkpoint_count = 0
        self._checkpoint_failures = 0
        self._resume_count = 0

        logger.debug(f"CheckpointManager initialized: {config}")

    def start_auto_checkpoint(self, context: AgentContext, task_id: str) -> Result[None, str]:
        """
        Start auto-checkpoint system for given context.

        Initializes interval timer, signal handlers, and task counter.

        Args:
            context: AgentContext to checkpoint
            task_id: Task identifier for checkpoint metadata

        Returns:
            Result[None, str] on success/failure

        Constitutional Compliance:
            - Article III: Automated trigger initialization
        """
        with self._lock:
            if not self.config.auto_checkpoint_enabled:
                return Ok(None)

            self._context = context
            self._task_count = 0

            # Start interval timer thread
            if self.config.checkpoint_interval_minutes > 0:
                self._start_interval_timer()

            # Install signal handler for interrupt checkpoint
            if self.config.checkpoint_on_interrupt:
                self._install_interrupt_handler()

            logger.info(
                f"Auto-checkpoint started: task={task_id}, "
                f"interval={self.config.checkpoint_interval_minutes}m"
            )
            return Ok(None)

    def stop_auto_checkpoint(self) -> Result[None, str]:
        """
        Stop auto-checkpoint system.

        Stops interval timer, restores signal handlers, and cleans up resources.

        Returns:
            Result[None, str] on success/failure

        Fix: Stop timer thread BEFORE acquiring lock to prevent deadlock
        (timer thread may call trigger_checkpoint which acquires lock)
        """
        # Stop timer thread FIRST without holding lock
        if self._timer_thread and self._timer_thread.is_alive():
            self._stop_timer.set()
            self._timer_thread.join(timeout=5)

        # Now acquire lock for cleanup
        with self._lock:
            self._timer_thread = None

            # Restore original signal handler
            if self._original_sigint_handler:
                signal.signal(signal.SIGINT, self._original_sigint_handler)
                self._original_sigint_handler = None

            self._context = None
            logger.info(f"Auto-checkpoint stopped: total_checkpoints={self._checkpoint_count}")
            return Ok(None)

    def trigger_checkpoint(
        self, context: AgentContext, reason: str
    ) -> Result[SessionCheckpoint, str]:
        """
        Manually trigger checkpoint creation.

        Args:
            context: AgentContext to checkpoint
            reason: Human-readable reason (e.g., "phase_complete", "task_complete")

        Returns:
            Result with SessionCheckpoint on success

        Constitutional Compliance:
            - Article I: Complete context (full state saved)
            - Article IV: Telemetry logging
        """
        with self._lock:
            try:
                # Get session state
                session_state = context.get_session_state(agent_name="checkpoint_manager")

                # Create checkpoint
                base_path = Path(self.config.base_path).expanduser()
                result = save_checkpoint(session_state, context.session_id, str(base_path))

                if result.is_err():
                    error = result.unwrap_err()
                    self._checkpoint_failures += 1
                    logger.error(f"Checkpoint failed: {error.error_type} - {error.message}")
                    return Err(f"{error.error_type}: {error.message}")

                checkpoint = result.unwrap()
                self._checkpoint_count += 1

                # Log telemetry (Article IV)
                logger.info(
                    f"Checkpoint triggered: reason={reason}, "
                    f"checkpoint_id={checkpoint.checkpoint_id}, "
                    f"total_checkpoints={self._checkpoint_count}"
                )

                return Ok(checkpoint)

            except Exception as e:
                self._checkpoint_failures += 1
                logger.error(f"Checkpoint trigger failed: {e}")
                return Err(f"unexpected_error: {str(e)}")

    def detect_paused_session(self, session_id: str) -> Result[SessionCheckpoint | None, str]:
        """
        Detect if session has paused with checkpoints available.

        Scans checkpoints directory for latest checkpoint by timestamp.

        Args:
            session_id: Session identifier to search

        Returns:
            Result with latest SessionCheckpoint or None if no checkpoints

        Constitutional Compliance:
            - Article I: Complete context (find all checkpoints)
        """
        try:
            base_path = Path(self.config.base_path).expanduser()
            checkpoints_dir = base_path / "sessions" / session_id / "checkpoints"

            if not checkpoints_dir.exists():
                logger.debug(f"No checkpoints directory for session: {session_id}")
                return Ok(None)

            # Find all checkpoint files
            checkpoint_files = sorted(
                checkpoints_dir.glob("checkpoint_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            if not checkpoint_files:
                logger.debug(f"No checkpoint files found for session: {session_id}")
                return Ok(None)

            # Try checkpoints in order (newest first) until we find a valid one
            for checkpoint_file in checkpoint_files:
                checkpoint_id = checkpoint_file.stem

                # Read checkpoint file to get checksum (lightweight validation)
                try:
                    with open(checkpoint_file) as f:
                        checkpoint_data = json.load(f)

                    # Validate checksum is valid hex (64 chars)
                    checksum = checkpoint_data.get("checksum", "")
                    if len(checksum) != 64 or not all(
                        c in "0123456789abcdef" for c in checksum.lower()
                    ):
                        # Corrupted checkpoint, try next
                        logger.warning(
                            f"Checkpoint {checkpoint_id} has invalid checksum, trying next..."
                        )
                        continue

                    # Valid checkpoint found
                    logger.info(
                        f"Paused session detected: {session_id}, latest_checkpoint={checkpoint_id}"
                    )

                    # Return checkpoint metadata (with valid checksum for Pydantic validation)
                    checkpoint_metadata = SessionCheckpoint(
                        checkpoint_id=checkpoint_id,
                        timestamp=datetime.fromtimestamp(checkpoint_file.stat().st_mtime),
                        session_state_json=checkpoint_data.get("session_state_json", ""),
                        checksum=checksum,
                    )

                    return Ok(checkpoint_metadata)

                except (OSError, json.JSONDecodeError) as e:
                    logger.warning(f"Cannot read checkpoint {checkpoint_id}: {e}, trying next...")
                    continue

            # No valid checkpoints found
            logger.debug(f"No valid checkpoints found for session: {session_id}")
            return Ok(None)

        except Exception as e:
            logger.error(f"Paused session detection failed: {e}")
            return Err(f"unexpected_error: {str(e)}")

    def resume_from_checkpoint(
        self, session_id: str, checkpoint_id: str | None = None
    ) -> Result[AgentContext, str]:
        """
        Resume session from checkpoint with integrity validation and fallback.

        Args:
            session_id: Session identifier
            checkpoint_id: Specific checkpoint ID (None = use latest)

        Returns:
            Result with restored AgentContext

        Constitutional Compliance:
            - Article I: Complete context restoration
            - Article II: Checksum validation
            - Article IV: Resume metrics logging
        """
        try:
            base_path = Path(self.config.base_path).expanduser()

            # If no checkpoint_id, find latest
            if checkpoint_id is None:
                detection_result = self.detect_paused_session(session_id)
                if detection_result.is_err():
                    return Err(detection_result.unwrap_err())

                checkpoint_meta = detection_result.unwrap()
                if checkpoint_meta is None:
                    return Err("no_checkpoints_found")

                checkpoint_id = checkpoint_meta.checkpoint_id

            # Attempt to load checkpoint with fallback
            max_retries = self.config.checkpoint_max_retries
            checkpoints_dir = base_path / "sessions" / session_id / "checkpoints"
            checkpoint_files = sorted(
                checkpoints_dir.glob("checkpoint_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            for attempt in range(max_retries):
                if attempt >= len(checkpoint_files):
                    break

                # Try current checkpoint
                current_file = checkpoint_files[attempt]
                current_id = current_file.stem

                logger.info(f"Resume attempt {attempt + 1}/{max_retries}: {current_id}")

                result = load_checkpoint(current_id, session_id, str(base_path))

                if result.is_ok():
                    # Success - restore AgentContext
                    session_state = result.unwrap()

                    # Create AgentContext from session state
                    from agency_memory import Memory

                    memory = Memory()
                    for snapshot in session_state.memory_snapshots:
                        key = snapshot.get("key", "unknown")
                        content = snapshot.get("content", {})
                        tags = snapshot.get("tags", [])
                        if isinstance(tags, list):
                            memory.store(str(key), content, tags)

                    from shared.agent_context import AgentContext

                    context = AgentContext(memory=memory, session_id=session_id)
                    context._metadata = session_state.metadata  # type: ignore

                    # Log resume metrics (Article IV)
                    checkpoint_age = (
                        datetime.now() - datetime.fromtimestamp(current_file.stat().st_mtime)
                    ).total_seconds()
                    self._resume_count += 1

                    logger.info(
                        f"Resume successful: checkpoint={current_id}, "
                        f"age={checkpoint_age:.1f}s, "
                        f"memories={len(session_state.memory_snapshots)}, "
                        f"total_resumes={self._resume_count}"
                    )

                    return Ok(context)

                else:
                    # Checksum mismatch or corruption - try next checkpoint
                    error = result.unwrap_err()
                    logger.warning(
                        f"Checkpoint {current_id} failed: {error.message}, trying fallback..."
                    )

            # All checkpoints failed
            return Err(f"all_checkpoints_corrupted: tried {max_retries} checkpoints")

        except Exception as e:
            logger.error(f"Resume from checkpoint failed: {e}")
            return Err(f"unexpected_error: {str(e)}")

    def cleanup_old_checkpoints(self, session_id: str) -> Result[int, str]:
        """
        Clean up old checkpoints based on retention policy.

        Keeps last N checkpoints and deletes those older than M days.

        Args:
            session_id: Session identifier to clean

        Returns:
            Result with number of checkpoints deleted

        Constitutional Compliance:
            - Article IV: Cleanup metrics logging
        """
        try:
            base_path = Path(self.config.base_path).expanduser()
            checkpoints_dir = base_path / "sessions" / session_id / "checkpoints"

            if not checkpoints_dir.exists():
                return Ok(0)

            # Get all checkpoints sorted by modification time (newest first)
            checkpoint_files = sorted(
                checkpoints_dir.glob("checkpoint_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            deleted_count = 0
            cutoff_time = datetime.now() - timedelta(days=self.config.checkpoint_retention_days)

            # Track which files to keep based on retention count
            files_to_keep = (
                set(checkpoint_files[: self.config.checkpoint_retention_count])
                if self.config.checkpoint_retention_count >= 0
                else set(checkpoint_files)
            )

            # Single pass: delete files that violate EITHER retention policy
            for checkpoint_file in checkpoint_files:
                should_delete = False

                # Retention policy 1: Beyond retention count
                if checkpoint_file not in files_to_keep:
                    should_delete = True
                    reason = "count"

                # Retention policy 2: Older than retention days (AND already marked for deletion OR within keep count)
                if checkpoint_file.exists():
                    file_mtime = datetime.fromtimestamp(checkpoint_file.stat().st_mtime)
                    if file_mtime < cutoff_time:
                        should_delete = True
                        reason = "age"

                # Delete if either policy says so
                if should_delete and checkpoint_file.exists():
                    checkpoint_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted checkpoint ({reason}): {checkpoint_file.name}")

            # Log telemetry (Article IV)
            logger.info(f"Checkpoint cleanup: session={session_id}, deleted={deleted_count}")

            return Ok(deleted_count)

        except Exception as e:
            logger.error(f"Checkpoint cleanup failed: {e}")
            return Err(f"unexpected_error: {str(e)}")

    # --- PRIVATE METHODS ---

    def _start_interval_timer(self) -> None:
        """Start background thread for interval-based checkpoints."""
        self._stop_timer.clear()

        def _timer_loop():
            # Sleep in small intervals to allow faster shutdown
            interval_seconds = self.config.checkpoint_interval_minutes * 60
            elapsed = 0

            while not self._stop_timer.is_set():
                # Sleep in 1-second intervals for responsive shutdown
                time.sleep(1)
                elapsed += 1

                if self._stop_timer.is_set():
                    break

                # Trigger checkpoint when interval reached
                if elapsed >= interval_seconds:
                    if self._context:
                        result = self.trigger_checkpoint(self._context, reason="interval_timer")
                        if result.is_err():
                            logger.error(f"Interval checkpoint failed: {result.unwrap_err()}")

                    # Reset elapsed time
                    elapsed = 0

        self._timer_thread = threading.Thread(target=_timer_loop, daemon=True)
        self._timer_thread.start()
        logger.debug(
            f"Checkpoint timer started: interval={self.config.checkpoint_interval_minutes}m"
        )

    def _install_interrupt_handler(self) -> None:
        """Install signal handler for interrupt checkpoint (Ctrl+C)."""
        self._original_sigint_handler = signal.getsignal(signal.SIGINT)

        def _interrupt_handler(signum, frame):
            logger.info("Interrupt signal received, creating emergency checkpoint...")

            if self._context:
                result = self.trigger_checkpoint(self._context, reason="user_interrupt")
                if result.is_ok():
                    logger.info("Emergency checkpoint created successfully")
                else:
                    logger.error(f"Emergency checkpoint failed: {result.unwrap_err()}")

            # Call original handler (or default behavior)
            if self._original_sigint_handler and callable(self._original_sigint_handler):
                self._original_sigint_handler(signum, frame)
            else:
                # Default: exit gracefully
                import sys

                sys.exit(0)

        signal.signal(signal.SIGINT, _interrupt_handler)
        logger.debug("Interrupt checkpoint handler installed (SIGINT)")

    def on_task_complete(self, context: AgentContext) -> Result[None, str]:
        """
        Callback for task completion checkpoint trigger.

        Called by orchestrator after task execution completes.

        Args:
            context: AgentContext to checkpoint

        Returns:
            Result[None, str] on success/failure

        Constitutional Compliance:
            - Article III: Automated trigger (orchestrator calls this)
        """
        with self._lock:
            self._task_count += 1

            if self._task_count % self.config.checkpoint_interval_tasks == 0:
                result = self.trigger_checkpoint(context, reason="task_complete")
                if result.is_err():
                    return Err(result.unwrap_err())

            return Ok(None)
