import json
import tempfile
import time

import pytest

from tools.context_handoff import ContextMessageHandoff
from tools.handoff_context_read import HandoffContextRead


@pytest.fixture
def isolated_handoff_dir(monkeypatch):
    """Create an isolated temporary directory for handoff tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to temp directory to isolate file operations
        monkeypatch.chdir(tmpdir)
        yield tmpdir


def test_handoff_context_read_returns_latest_record(isolated_handoff_dir):
    # Create two handoffs for the same target
    t1 = ContextMessageHandoff(
        target_agent="PlannerAgent",
        prompt="Plan A",
        context={"k": 1},
        persist=True,
    ).run()

    # Small delay to ensure different modification times
    time.sleep(0.1)

    t2 = ContextMessageHandoff(
        target_agent="PlannerAgent",
        prompt="Plan B",
        context={"k": 2},
        persist=True,
    ).run()

    reader = HandoffContextRead(target_agent="PlannerAgent", limit=1)
    out = reader.run()

    assert out.startswith("Exit code: 0\n")
    lines = out.splitlines()[1:]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["data"]["prompt"].startswith("Plan B")


def test_handoff_context_read_handles_missing_dir(tmp_path, monkeypatch):
    # Point CWD to a fresh temp directory where logs/handoffs doesn't exist
    monkeypatch.chdir(tmp_path)
    reader = HandoffContextRead(target_agent="PlannerAgent", limit=1)
    out = reader.run()
    assert "No handoffs directory" in out
