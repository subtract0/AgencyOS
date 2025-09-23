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


def test_aggregate_filters_by_run_id(tmp_path):
    base = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    dir_path = tmp_path / "telemetry"

    run_a = "runA"
    run_b = "runB"

    events = [
        {"ts": (base + timedelta(seconds=0)).isoformat().replace("+00:00", "Z"), "type": "orchestrator_started", "run_id": run_a, "max_concurrency": 2, "tasks": 1},
        {"ts": (base + timedelta(seconds=1)).isoformat().replace("+00:00", "Z"), "type": "task_started", "run_id": run_a, "id": "t1", "agent": "A", "attempt": 1},
        {"ts": (base + timedelta(seconds=2)).isoformat().replace("+00:00", "Z"), "type": "task_finished", "run_id": run_a, "id": "t1", "agent": "A", "attempt": 1, "status": "success"},
        {"ts": (base + timedelta(seconds=3)).isoformat().replace("+00:00", "Z"), "type": "orchestrator_finished", "run_id": run_a},
        # second run
        {"ts": (base + timedelta(seconds=4)).isoformat().replace("+00:00", "Z"), "type": "orchestrator_started", "run_id": run_b, "max_concurrency": 4, "tasks": 1},
        {"ts": (base + timedelta(seconds=5)).isoformat().replace("+00:00", "Z"), "type": "task_started", "run_id": run_b, "id": "t2", "agent": "B", "attempt": 1},
    ]

    _write_events(str(dir_path), base, events)

    # Aggregate for runA only
    summary_a = aggregate(since="2h", telemetry_dir=str(dir_path), now=base + timedelta(seconds=10), run_id=run_a)
    assert summary_a["metrics"]["total_events"] == 4
    assert summary_a["resources"]["max_concurrency"] == 2

    # Aggregate for runB only
    summary_b = aggregate(since="2h", telemetry_dir=str(dir_path), now=base + timedelta(seconds=10), run_id=run_b)
    # Only 2 events in runB window (start + task_started)
    assert summary_b["metrics"]["total_events"] == 2
    assert summary_b["resources"]["max_concurrency"] == 4
