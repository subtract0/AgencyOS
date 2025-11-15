"""Focused checkpoint manager tests.

These tests were rewritten in 2025-11 to replace the legacy suite that hung
on macOS/Python 3.13. They cover the core functionality Night Shift relies on
without long-running threads or signal juggling.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import pytest

from shared.agent_context import create_agent_context
from shared.checkpoint_manager import CheckpointConfig, CheckpointManager
from shared.type_definitions.result import Ok


@pytest.fixture
def context() -> Any:
    return create_agent_context(session_id="checkpoint-test")


def test_trigger_checkpoint_writes_file(tmp_path, context):
    config = CheckpointConfig(base_path=str(tmp_path))
    manager = CheckpointManager(config)

    result = manager.trigger_checkpoint(context, reason="manual")

    checkpoint = result.unwrap()
    checkpoint_dir = (
        Path(config.base_path)
        / "sessions"
        / context.session_id
        / "checkpoints"
    )
    assert (checkpoint_dir / f"{checkpoint.checkpoint_id}.json").exists()
    assert manager._checkpoint_count == 1


def test_start_stop_auto_checkpoint_uses_timer_and_signal(monkeypatch, context, tmp_path):
    config = CheckpointConfig(
        base_path=str(tmp_path),
        checkpoint_interval_minutes=5,
        checkpoint_on_interrupt=True,
    )
    manager = CheckpointManager(config)

    calls = {"timer": 0, "signal": 0}

    def record_timer() -> None:
        calls["timer"] += 1

    def record_signal() -> None:
        calls["signal"] += 1

    monkeypatch.setattr(manager, "_start_interval_timer", record_timer)
    monkeypatch.setattr(manager, "_install_interrupt_handler", record_signal)

    assert manager.start_auto_checkpoint(context, task_id="demo").is_ok()
    assert calls == {"timer": 1, "signal": 1}
    assert manager._context is context

    assert manager.stop_auto_checkpoint().is_ok()
    assert manager._context is None


def test_on_task_complete_triggers_checkpoint(monkeypatch, tmp_path, context):
    config = CheckpointConfig(base_path=str(tmp_path), checkpoint_interval_tasks=2)
    manager = CheckpointManager(config)

    triggered = {"count": 0}

    def fake_trigger(*args, **kwargs):  # noqa: ANN001 - signature controlled
        triggered["count"] += 1
        return Ok(None)

    monkeypatch.setattr(manager, "trigger_checkpoint", fake_trigger)

    manager.on_task_complete(context)
    assert triggered["count"] == 0
    manager.on_task_complete(context)
    assert triggered["count"] == 1


def test_cleanup_old_checkpoints(tmp_path):
    base = Path(tmp_path)
    session_dir = base / "sessions" / "cleanup" / "checkpoints"
    session_dir.mkdir(parents=True)

    # Create three fake checkpoint files with staggered mtimes
    files = []
    for idx in range(3):
        file = session_dir / f"checkpoint_{idx}.json"
        file.write_text("{}")
        # Oldest file gets oldest timestamp
        os.utime(file, (time.time() - (idx + 1) * 3600, time.time() - (idx + 1) * 3600))
        files.append(file)

    config = CheckpointConfig(
        base_path=str(base),
        checkpoint_retention_count=1,
        checkpoint_retention_days=1,
    )
    manager = CheckpointManager(config)

    deleted = manager.cleanup_old_checkpoints("cleanup").unwrap()

    # Two of the three files should be removed (keep latest only)
    assert deleted == 2
    remaining = list(session_dir.glob("checkpoint_*.json"))
    assert len(remaining) == 1
