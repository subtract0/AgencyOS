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


def test_cost_aggregation_with_pricing(tmp_path, monkeypatch):
    now = datetime(2025, 1, 1, 0, 0, 5, tzinfo=timezone.utc)
    dir_path = tmp_path / "telemetry"

    events = [
        {"ts": (now - timedelta(seconds=4)).isoformat().replace("+00:00", "Z"), "type": "task_started", "id": "t1", "agent": "A", "attempt": 1},
        {
            "ts": (now - timedelta(seconds=2)).isoformat().replace("+00:00", "Z"),
            "type": "task_finished", "id": "t1", "agent": "A", "attempt": 1, "status": "success",
            "usage": {"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500},
            "model": "gpt-x"
        }
    ]

    _write_events(str(dir_path), now, events)

    # Pricing: $3/1k prompt, $6/1k completion
    pricing = {"gpt-x": {"prompt": 3.0, "completion": 6.0}}
    monkeypatch.setenv("AGENCY_PRICING_JSON", json.dumps(pricing))

    summary = aggregate(since="1h", telemetry_dir=str(dir_path), now=now)

    costs = summary["costs"]
    assert costs["total_tokens"] == 1500
    # expected cost = 1000/1k*3 + 500/1k*6 = 3 + 3 = 6
    assert abs(costs["total_usd"] - 6.0) < 1e-6
    assert abs(costs["by_agent"]["A"]["usd"] - 6.0) < 1e-6
    assert abs(costs["by_model"]["gpt-x"]["usd"] - 6.0) < 1e-6
