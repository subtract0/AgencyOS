from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _run_hook(payload: dict, project_dir: Path) -> subprocess.CompletedProcess[str]:
    hook_path = project_dir / ".claude" / "hooks" / "damage-control" / "bash-tool-damage-control.py"
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    return subprocess.run(
        ["python3", str(hook_path)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def _decision(stdout: str) -> str | None:
    if not stdout.strip():
        return None
    data = json.loads(stdout)
    return data.get("hookSpecificOutput", {}).get("permissionDecision")


def test_allows_non_bash_tools() -> None:
    project_dir = Path(__file__).resolve().parents[1]
    payload = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}
    result = _run_hook(payload, project_dir)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_denies_recursive_delete_of_root() -> None:
    project_dir = Path(__file__).resolve().parents[1]
    payload = {
        "tool_name": "Bash",
        "cwd": str(project_dir),
        "tool_input": {"command": "rm -rf /"},
    }
    result = _run_hook(payload, project_dir)
    assert _decision(result.stdout) == "deny"


def test_requires_confirmation_for_recursive_delete_in_project() -> None:
    project_dir = Path(__file__).resolve().parents[1]
    payload = {
        "tool_name": "Bash",
        "cwd": str(project_dir),
        "tool_input": {"command": "rm -rf tmp"},
    }
    result = _run_hook(payload, project_dir)
    assert _decision(result.stdout) == "ask"


def test_allows_non_recursive_delete_in_project() -> None:
    project_dir = Path(__file__).resolve().parents[1]
    payload = {
        "tool_name": "Bash",
        "cwd": str(project_dir),
        "tool_input": {"command": "rm tmp.txt"},
    }
    result = _run_hook(payload, project_dir)
    assert result.returncode == 0
    assert result.stdout.strip() == ""
