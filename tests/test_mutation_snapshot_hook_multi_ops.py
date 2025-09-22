import os
import json
from pathlib import Path
import asyncio

from shared.system_hooks import create_mutation_snapshot_hook


class DummyContext:
    def __init__(self):
        self._data = {}
        self.thread_manager = None
    def get(self, k, d=None):
        return self._data.get(k, d)
    def set(self, k, v):
        self._data[k] = v


class DummyWrapper:
    def __init__(self):
        self.context = DummyContext()


def test_snapshot_hook_multi_operations(tmp_path):
    root = Path(os.getcwd())
    f1 = root / "_tmp_multi_op_1.txt"
    f2 = root / "_tmp_multi_op_2.txt"
    f1.write_text("a")
    f2.write_text("b")

    try:
        hook = create_mutation_snapshot_hook()

        class MultiEditLike:
            name = "MultiEdit"
            def __init__(self, ops):
                self.operations = ops

        tool = MultiEditLike([
            {"file_path": str(f1)},
            {"file_path": str(f2)},
        ])
        wrapper = DummyWrapper()
        asyncio.get_event_loop().run_until_complete(hook.on_tool_start(wrapper, agent=None, tool=tool))

        snaps_dir = root / "logs" / "snapshots"
        assert snaps_dir.exists()
        subdirs = [p for p in snaps_dir.iterdir() if p.is_dir()]
        assert subdirs
        latest = sorted(subdirs, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        manifest = latest / "manifest.json"
        data = json.loads(manifest.read_text())
        paths = {x.get("path") for x in data.get("files", [])}
        assert "_tmp_multi_op_1.txt" in paths
        assert "_tmp_multi_op_2.txt" in paths
    finally:
        for p in (f1, f2):
            if p.exists():
                p.unlink()
