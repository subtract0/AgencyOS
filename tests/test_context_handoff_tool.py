import json
import os
from pathlib import Path

import pytest

from tools.context_handoff import ContextMessageHandoff


class TestContextMessageHandoff:
    def test_persist_true_writes_file_and_returns_path(self):
        tool = ContextMessageHandoff(
            target_agent="PlannerAgent",
            prompt="Plan feature X with constraints",
            context={"mission": "feature X", "priority": "high"},
            tags=["handoff", "mission"],
            persist=True,
        )
        result = tool.run()

        assert "Prepared handoff" in result
        assert "context saved" in result
        assert "logs/handoffs/" in result
        # Extract path=... substring
        start = result.find("path=")
        assert start != -1
        path = result[start + 5 :].split(" ")[0]
        assert os.path.exists(path)

        # Validate file content minimally
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["target_agent"] == "PlannerAgent"
        assert data["prompt"].startswith("Plan feature X")
        assert "mission" in data["context"]

    def test_non_persist_does_not_write_and_is_short(self):
        tool = ContextMessageHandoff(
            target_agent="MergerAgent",
            prompt="Verify tests and approve",
            context="a" * 5000,  # large raw context
            persist=False,
        )
        result = tool.run()
        assert "Prepared handoff" in result
        assert "not persisted" in result
        # Ensure summary is bounded
        assert len(result) < 1200

    def test_missing_required_fields(self):
        tool = ContextMessageHandoff(target_agent="", prompt="")
        out = tool.run()
        assert "Error" in out
