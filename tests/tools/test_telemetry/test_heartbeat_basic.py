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


def test_heartbeat_running_detection(tmp_path, monkeypatch):
    now = datetime(2025, 1, 1, 0, 0, 20, tzinfo=timezone.utc)
    base = now - timedelta(seconds=20)
    dir_path = tmp_path / "telemetry"

    # Task started at t=0, heartbeat at t=10, unfinished
    events = [
        {"ts": (base + timedelta(seconds=0)).isoformat().replace("+00:00", "Z"), "type": "task_started", "id": "t1", "agent": "A", "attempt": 1},
        {"ts": (base + timedelta(seconds=10)).isoformat().replace("+00:00", "Z"), "type": "heartbeat", "id": "t1", "agent": "A", "attempt": 1},
    ]

    _write_events(str(dir_path), base, events)

    # Aggregate with now=20s later
    summary = aggregate(since="1h", telemetry_dir=str(dir_path), now=now)

    running = summary["running_tasks"]
    assert len(running) == 1
    r = running[0]
    assert r["id"] == "t1"
    # last heartbeat age should be ~10s (from t=10 to t=20)
    assert 9.9 <= r["last_heartbeat_age_s"] <= 10.1

    resources = summary["resources"]
    assert resources["heartbeats"]["count"] == 1
