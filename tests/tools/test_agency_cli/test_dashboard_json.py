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


def test_dashboard_json_outputs_summary(tmp_path):
    now = datetime.now(timezone.utc)
    dir_path = tmp_path / "telemetry"

    events = [
        {
            "ts": (now - timedelta(seconds=2)).isoformat().replace("+00:00", "Z"),
            "type": "task_started",
            "id": "tX",
            "agent": "AgentZ",
            "attempt": 1,
            "started_at": (now - timedelta(seconds=2)).timestamp(),
        },
        {
            "ts": (now - timedelta(seconds=1)).isoformat().replace("+00:00", "Z"),
            "type": "task_finished",
            "id": "tX",
            "agent": "AgentZ",
            "attempt": 1,
            "status": "success",
            "finished_at": (now - timedelta(seconds=1)).timestamp(),
            "duration_s": 1.0,
        },
    ]

    _write_events(str(dir_path), now, events)

    env = os.environ.copy()
    env["AGENCY_TELEMETRY_DIR"] = str(dir_path)

    proc = subprocess.run(
        [sys.executable, "-m", "tools.agency_cli.dashboard", "--since", "100h", "--format", "json"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0
    out = proc.stdout.strip()
    data = json.loads(out)

    # Basic keys present
    assert "metrics" in data
    assert "agents_active" in data
    assert data["metrics"]["total_events"] >= 2
    assert "AgentZ" in data["agents_active"]
