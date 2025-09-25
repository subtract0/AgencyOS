import os
from pathlib import Path
import re
import json
import pytest

from core.telemetry import SimpleTelemetry


def test_events_dir_auto_created(tmp_path, monkeypatch):
    # Run in isolated working dir
    monkeypatch.chdir(tmp_path)

    tel = SimpleTelemetry()

    # Simulate mid-run cleanup of events dir
    events_dir = tmp_path / "logs" / "events"
    if events_dir.exists():
        for p in events_dir.glob("*"):
            try:
                p.unlink()
            except Exception:
                pass
        try:
            events_dir.rmdir()
        except Exception:
            pass

    # Should auto-recreate and write
    tel.log("test_event", {"k": "v"})
    run_files = sorted((tmp_path / "logs" / "events").glob("run_*.jsonl"))
    assert run_files, "expected telemetry run file to be created"

    # Validate entry is JSON line
    content = run_files[-1].read_text().strip()
    obj = json.loads(content)
    assert obj.get("event") == "test_event"


def test_secure_permissions(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tel = SimpleTelemetry()
    tel.log("perm_test", {})

    run_file = next((tmp_path / "logs" / "events").glob("run_*.jsonl"))
    mode = os.stat(run_file).st_mode & 0o777
    assert mode == 0o600, f"expected 0600 perms, got {oct(mode)}"


def test_reject_traversal(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    tel = SimpleTelemetry()

    # Force an unsafe path outside repo root
    tel.current_file = Path("..") / "evil" / "run_hack.jsonl"

    tel.log("should_not_write", {})
    err = capsys.readouterr().err
    assert "Unsafe telemetry path" in err
    assert not (tmp_path.parent / "evil").exists()


def test_fallback_on_open_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    tel = SimpleTelemetry()

    import os as _os

    def boom(*args, **kwargs):
        raise OSError("open failed")

    monkeypatch.setattr(_os, "open", boom)

    tel.log("boom", {})
    err = capsys.readouterr().err
    assert "Telemetry error" in err
