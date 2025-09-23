from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

from tools.telemetry.aggregator import aggregate


def _write_events(dir_path: str, date: datetime, events: list[dict]) -> None:
    os.makedirs(dir_path, exist_ok=True)
    fname = os.path.join(dir_path, f"events-{date:%Y%m%d}.jsonl")
    with open(fname, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")


def test_bottlenecks_long_running_and_error_spike(tmp_path, monkeypatch):
    now = datetime(2025, 1, 1, 0, 1, 0, tzinfo=timezone.utc)
    base = now - timedelta(minutes=1)
    dir_path = tmp_path / "telemetry"

    # Two tasks: t1 running for 60s, t2 failed quickly
    events = [
        {"ts": (base + timedelta(seconds=0)).isoformat().replace("+00:00", "Z"), "type": "task_started", "id": "t1", "agent": "A", "attempt": 1},
        {"ts": (base + timedelta(seconds=1)).isoformat().replace("+00:00", "Z"), "type": "task_started", "id": "t2", "agent": "B", "attempt": 2},
        {"ts": (base + timedelta(seconds=2)).isoformat().replace("+00:00", "Z"), "type": "task_finished", "id": "t2", "agent": "B", "attempt": 2, "status": "failed"},
    ]

    _write_events(str(dir_path), now, events)

    # Set thresholds: long-running if >= 30s; error rate spike if >= 0.5
    monkeypatch.setenv("AGENCY_BOTTLENECK_AGE_S", "30")
    monkeypatch.setenv("AGENCY_ERROR_RATE_WARN", "0.5")

    summary = aggregate(since="2h", telemetry_dir=str(dir_path), now=now)

    b = summary["bottlenecks"]
    # One long-running task
    assert any(t["id"] == "t1" for t in b["slow_tasks"]) or any(t.get("id") == "t1" for t in b["slow_tasks"])
    # Error rate = 1 failed / 1 finished = 1.0 >= 0.5
    assert b["spike"] is True
    assert b["error_rate"] >= 0.5
