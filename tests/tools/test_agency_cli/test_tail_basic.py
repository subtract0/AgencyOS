from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone


def _write_events(dir_path: str, date: datetime, events: list[dict]) -> None:
    os.makedirs(dir_path, exist_ok=True)
    fname = os.path.join(dir_path, f"events-{date:%Y%m%d}.jsonl")
    with open(fname, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")


def test_tail_filters_by_run_and_grep(tmp_path, monkeypatch):
    base = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    dir_path = tmp_path / "telemetry"

    run_a = "runA"
    run_b = "runB"

    events = [
        {"ts": (base + timedelta(seconds=0)).isoformat().replace("+00:00", "Z"), "type": "task_started", "run_id": run_a, "id": "t1", "agent": "A"},
        {"ts": (base + timedelta(seconds=1)).isoformat().replace("+00:00", "Z"), "type": "task_finished", "run_id": run_a, "id": "t1", "agent": "A", "status": "success"},
        {"ts": (base + timedelta(seconds=2)).isoformat().replace("+00:00", "Z"), "type": "task_started", "run_id": run_b, "id": "t2", "agent": "B"},
    ]

    _write_events(str(dir_path), base, events)

    env = os.environ.copy()
    env["AGENCY_TELEMETRY_DIR"] = str(dir_path)

    # Filter by runA
    now_time = (base + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    proc = subprocess.run(
        [sys.executable, "-m", "tools.agency_cli.tail", "--since", "2h", "--run", run_a, "--format", "json", "--now", now_time],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0
    arr = json.loads(proc.stdout)
    assert len(arr) == 2

    # Grep success within runA
    proc2 = subprocess.run(
        [sys.executable, "-m", "tools.agency_cli.tail", "--since", "2h", "--run", run_a, "--grep", "success", "--format", "json", "--now", now_time],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    arr2 = json.loads(proc2.stdout)
    assert len(arr2) == 1
    assert arr2[0]["status"] == "success"
