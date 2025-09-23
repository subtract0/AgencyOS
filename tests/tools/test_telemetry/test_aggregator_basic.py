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


def test_aggregate_basic_running_and_counts(tmp_path):
    base_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    dir_path = tmp_path / "telemetry"

    # Events: one running task (started only), one success finished
    events = [
        {
            "ts": (base_dt + timedelta(seconds=0)).isoformat().replace("+00:00", "Z"),
            "type": "task_started",
            "id": "t1",
            "agent": "AgentA",
            "attempt": 1,
            "started_at": (base_dt.timestamp()),
        },
        {
            "ts": (base_dt + timedelta(seconds=1)).isoformat().replace("+00:00", "Z"),
            "type": "task_started",
            "id": "t2",
            "agent": "AgentB",
            "attempt": 1,
            "started_at": (base_dt.timestamp()),
        },
        {
            "ts": (base_dt + timedelta(seconds=2)).isoformat().replace("+00:00", "Z"),
            "type": "task_finished",
            "id": "t2",
            "agent": "AgentB",
            "attempt": 1,
            "status": "success",
            "finished_at": (base_dt + timedelta(seconds=2)).timestamp(),
            "duration_s": 2.0,
        },
    ]

    _write_events(str(dir_path), base_dt, events)

    # Aggregate with now=base_dt+10s and since spanning 1h
    summary = aggregate(since="1h", telemetry_dir=str(dir_path), now=base_dt + timedelta(seconds=10))

    assert summary["metrics"]["total_events"] == 3
    assert summary["metrics"]["tasks_started"] == 2
    assert summary["metrics"]["tasks_finished"] == 1

    recent = summary["recent_results"]
    assert recent["success"] == 1
    assert recent["failed"] == 0
    assert recent["timeout"] == 0

    running = summary["running_tasks"]
    assert any(r["id"] == "t1" for r in running)
    t1 = next(r for r in running if r["id"] == "t1")
    # Age should be ~10s
    assert 9.9 <= t1["age_s"] <= 10.1

    agents = summary["agents_active"]
    assert agents == ["AgentA", "AgentB"]
