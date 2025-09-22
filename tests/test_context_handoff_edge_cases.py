import os
import json
from pathlib import Path
import builtins

import pytest

from tools.context_handoff import ContextMessageHandoff


def test_context_handoff_permission_error_on_persist(monkeypatch):
    original_open = builtins.open

    def guarded_open(path, mode='r', *args, **kwargs):
        if isinstance(path, (str, os.PathLike)) and "logs/handoffs/" in str(path) and "w" in mode:
            raise PermissionError("permission denied")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)

    tool = ContextMessageHandoff(
        target_agent="PlannerAgent",
        prompt="Plan feature Z",
        context={"a": 1},
        persist=True,
    )
    out = tool.run()
    assert "Error: failed to persist handoff context" in out


def test_context_handoff_many_context_keys_summary_is_bounded():
    ctx = {f"k{i}": i for i in range(100)}
    tool = ContextMessageHandoff(
        target_agent="PlannerAgent",
        prompt="x" * 200,
        context=ctx,
        persist=False,
    )
    res = tool.run()
    # Only show first ~5 keys
    assert "keys=" in res
    keys_part = res.split("keys=")[-1]
    assert keys_part.count(",") <= 4
    assert len(res) < 500
