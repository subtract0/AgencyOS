from tools.kanban import adapters


def test_smoke_build_cards_handles_empty(monkeypatch):
    monkeypatch.setattr(adapters, "list_events", lambda since, grep=None, limit=None, telemetry_dir=None: [])
    cards = adapters.build_cards(window="1h")
    assert isinstance(cards, list)
    assert cards == []


def test_smoke_build_cards_handles_errors(monkeypatch):
    # malformed events should be ignored gracefully
    def _events(since, grep=None, limit=None, telemetry_dir=None):
        return [
            {"type": "task_finished", "status": "failed", "agent": "Coder", "error": "NoneType error"},
            {"bad": "event"},
        ]
    monkeypatch.setattr(adapters, "list_events", _events)
    cards = adapters.build_cards(window="1h")
    # One error card expected
    assert any(c["type"] == "error" for c in cards)
