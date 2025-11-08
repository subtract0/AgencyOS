"""Shared helper to execute commands via the OpenEnv runner.

Falls back to ``subprocess.run`` when the spec/runner is unavailable or
when unsupported options are requested (e.g., shell pipelines or stdin).
"""
from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Mapping, Sequence

try:
    from envs.agency_env_runner import step as env_step  # type: ignore
except Exception:  # pragma: no cover - fallback when runner not installed
    env_step = None  # type: ignore

DEFAULT_SPEC_PATH = Path(__file__).with_name("agency_env_spec.json")


def _resolve_spec_path() -> str | None:
    spec = os.getenv("AGENCY_ENV_SPEC")
    if spec:
        return spec
    if DEFAULT_SPEC_PATH.exists():
        os.environ["AGENCY_ENV_SPEC"] = str(DEFAULT_SPEC_PATH)
        return str(DEFAULT_SPEC_PATH)
    return None


def _should_use_runner(shell: bool, input_data) -> bool:
    if shell or input_data is not None:
        return False
    if env_step is None:
        return False
    return _resolve_spec_path() is not None


def _normalize_command(cmd: Sequence[str] | str) -> list[str]:
    if isinstance(cmd, str):
        return shlex.split(cmd)
    return list(cmd)


def _build_completed_process(cmd, exit_code, stdout, stderr):
    return subprocess.CompletedProcess(cmd, exit_code, stdout, stderr)


def run_command(
    cmd: Sequence[str] | str,
    *,
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
    timeout: int | float | None = None,
    capture_output: bool = False,
    check: bool = False,
    text: bool = True,
    shell: bool = False,
    input=None,
) -> subprocess.CompletedProcess:
    """Execute ``cmd`` respecting the OpenEnv spec when available."""

    if not _should_use_runner(shell, input):
        return subprocess.run(  # type: ignore[arg-type]
            cmd,
            cwd=cwd,
            env=_merge_env(env),
            timeout=timeout,
            capture_output=capture_output,
            check=check,
            text=text,
            shell=shell,
            input=input,
        )

    command_list = _normalize_command(cmd)
    action = {
        "command": command_list,
        "timeout": timeout if timeout is not None else 600,
    }
    if cwd:
        action["cwd"] = cwd
    if env:
        action["env"] = dict(env)

    result = env_step(action)
    status = result.get("status")
    exit_code = result.get("exit_code")
    if exit_code is None:
        exit_code = 0 if status in {"ok", "completed"} else 1

    stdout_txt = result.get("stdout", "")
    stderr_txt = result.get("stderr", "")

    if not capture_output:
        if stdout_txt:
            sys.stdout.write(stdout_txt)
        if stderr_txt:
            sys.stderr.write(stderr_txt)

    if not text:
        stdout_payload = stdout_txt.encode()
        stderr_payload = stderr_txt.encode()
    else:
        stdout_payload = stdout_txt
        stderr_payload = stderr_txt

    completed = _build_completed_process(command_list, exit_code, stdout_payload, stderr_payload)

    if check and exit_code != 0:
        raise subprocess.CalledProcessError(exit_code, command_list, stdout_payload, stderr_payload)

    return completed


def _merge_env(overrides: Mapping[str, str] | None) -> dict[str, str] | None:
    if overrides is None:
        return None
    merged = os.environ.copy()
    merged.update(overrides)
    return merged


__all__ = ["run_command"]

