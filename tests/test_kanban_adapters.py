import json
from typing import List, Dict, Any
from shared.types.json import JSONValue

from tools.kanban import adapters


def _fake_events() -> List[Dict[str, JSONValue]]:
    return [
        {"type": "task_started", "agent": "Coder", "id": "t1", "ts": "2025-09-25T00:00:00Z"},
        {"type": "task_finished", "agent": "Coder", "id": "t1", "status": "success", "ts": "2025-09-25T00:05:00Z"},
        {"type": "task_finished", "agent": "Coder", "id": "t2", "status": "failed", "error": "ImportError: foo", "ts": "2025-09-25T00:10:00Z"},
        {"type": "pattern_extracted", "id": "p1", "context": {"trigger": {"type": "error"}}, "ts": "2025-09-25T00:15:00Z"},
        {"type": "heartbeat", "agent": "Auditor", "id": "hb1", "ts": "2025-09-25T00:20:00Z"},
        {"type": "misc_event", "agent": "Planner", "id": "m1", "error": "AttributeError: 'NoneType'", "ts": "2025-09-25T00:25:00Z"},
    ]


def test_build_cards_maps_events(monkeypatch):
    monkeypatch.setattr(adapters, "list_events", lambda since, grep=None, limit=None, telemetry_dir=None: _fake_events())

    cards = adapters.build_cards(window="4h")
    # Ensure we got expected cardinality (heartbeat ignored)
    types = [c["type"] for c in cards]
    statuses = [c["status"] for c in cards]

    # Expect at least: task, task, error, pattern, error
    assert any(t == "task" and s == "Resolved" for t, s in zip(types, statuses))
    assert any(t == "task" and s == "In Progress" for t, s in zip(types, statuses))
    assert any(t == "error" and s == "To Investigate" for t, s in zip(types, statuses))
    assert any(t == "pattern" and s == "Learned" for t, s in zip(types, statuses))

    # Summaries should be short and safe
    for c in cards:
        assert len(c.get("summary", "")) <= 200 + 1  # allow truncation suffix


def test_build_feed_structure(monkeypatch):
    monkeypatch.setattr(adapters, "list_events", lambda since, grep=None, limit=None, telemetry_dir=None: _fake_events())
    feed = adapters.build_feed(window="1h")
    assert "generated_at" in feed
    assert isinstance(feed.get("cards"), list)
