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


def test_dashboard_text_includes_resources_and_costs(tmp_path, monkeypatch):
    now = datetime.now(timezone.utc)
    dir_path = tmp_path / "telemetry"

    events = [
        {"ts": (now - timedelta(seconds=5)).isoformat().replace("+00:00", "Z"), "type": "orchestrator_started", "max_concurrency": 4, "tasks": 1},
        {"ts": (now - timedelta(seconds=4)).isoformat().replace("+00:00", "Z"), "type": "task_started", "id": "t1", "agent": "AgentZ", "attempt": 1},
        {"ts": (now - timedelta(seconds=3)).isoformat().replace("+00:00", "Z"), "type": "heartbeat", "id": "t1", "agent": "AgentZ", "attempt": 1},
        {
            "ts": (now - timedelta(seconds=2)).isoformat().replace("+00:00", "Z"),
            "type": "task_finished", "id": "t1", "agent": "AgentZ", "attempt": 1, "status": "success",
            "usage": {"prompt_tokens": 1000, "completion_tokens": 0, "total_tokens": 1000},
            "model": "gpt-x"
        },
    ]

    _write_events(str(dir_path), now, events)

    monkeypatch.setenv("AGENCY_TELEMETRY_DIR", str(dir_path))
    monkeypatch.setenv("AGENCY_PRICING_JSON", json.dumps({"gpt-x": {"prompt": 3.0, "completion": 6.0}}))

    proc = subprocess.run(
        [sys.executable, "-m", "tools.agency_cli.dashboard", "--since", "1h", "--format", "text"],
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),
    )

    out = proc.stdout
    assert "Agents Active:" in out
    assert "Running Tasks" in out or "Running Tasks" in out
    assert "Resources:" in out
    assert "Costs:" in out
