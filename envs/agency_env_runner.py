"""Skeleton OpenEnv-style runner for AgencyOS missions."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

SPEC_PATH = Path(__file__).with_name("agency_env_spec.json")


def load_spec() -> Dict[str, Any]:
    return json.loads(SPEC_PATH.read_text())


def reset() -> Dict[str, Any]:
    """Reset environment state (placeholder)."""
    return {"status": "reset", "cwd": "/workspace"}


def step(action: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single agent action (placeholder)."""
    command = action.get("command")
    return {"status": "ok", "command": command}


def close() -> Dict[str, Any]:
    return {"status": "closed"}


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: agency_env_runner.py [reset|step|close]")

    op = sys.argv[1]
    if op == "reset":
        print(load_spec())
        print(reset())
    elif op == "step":
        print(step({"command": "noop"}))
    elif op == "close":
        print(close())
    else:
        raise SystemExit(f"Unknown op: {op}")
