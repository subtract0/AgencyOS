import os
import json
from pathlib import Path

import pytest

from shared.system_hooks import create_intent_router_hook, create_tool_wrapper_hook, create_mutation_snapshot_hook


class DummyContext:
    def __init__(self):
        self._data = {}
        self.thread_manager = None

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value


class DummyWrapper:
    def __init__(self):
        self.context = DummyContext()


def test_intent_router_sets_route_flag():
    hook = create_intent_router_hook()
    wrapper = DummyWrapper()
    wrapper.context.set("latest_user_prompt", "Please give me a tts summary of the changes")

    # on_start should set route_to_agent
    import asyncio
    asyncio.get_event_loop().run_until_complete(hook.on_start(wrapper, agent=None))

    assert wrapper.context.get("route_to_agent") == "WorkCompletionSummaryAgent"


def test_tool_wrapper_retries_on_failure():
    hook = create_tool_wrapper_hook()
    wrapper = DummyWrapper()

    class FlakyTool:
        name = "Read"
        def __init__(self):
            self.calls = 0
        def run(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise Exception("transient error")
            return "ok"

    tool = FlakyTool()

    import asyncio
    asyncio.get_event_loop().run_until_complete(hook.on_tool_start(wrapper, agent=None, tool=tool))

    # First call will be retried by wrapper, resulting in success
    result = tool.run()
    assert result == "ok"
    assert tool.calls == 2


def test_mutation_snapshot_hook_creates_snapshot(tmp_path, monkeypatch):
    # Create a real file in repo root so snapshot paths are valid
    repo_root = Path(os.getcwd())
    test_file = repo_root / "_tmp_snapshot_test.txt"
    test_file.write_text("data")

    try:
        hook = create_mutation_snapshot_hook()
        wrapper = DummyWrapper()

        class WriteLike:
            name = "Write"
            def __init__(self, file_path):
                self.file_path = file_path

        tool = WriteLike(str(test_file))

        import asyncio
        asyncio.get_event_loop().run_until_complete(hook.on_tool_start(wrapper, agent=None, tool=tool))

        # Verify a snapshot was created
        snaps_dir = repo_root / "logs" / "snapshots"
        assert snaps_dir.exists()
        # Find most recent snapshot
        subdirs = [p for p in snaps_dir.iterdir() if p.is_dir()]
        assert subdirs, "No snapshot directories found"
        latest = sorted(subdirs, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        manifest = latest / "manifest.json"
        assert manifest.exists()
        data = json.loads(manifest.read_text())
        assert any(entry.get("path") == "_tmp_snapshot_test.txt" for entry in data.get("files", []))
    finally:
        if test_file.exists():
            test_file.unlink()
