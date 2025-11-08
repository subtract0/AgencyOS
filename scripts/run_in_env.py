#!/usr/bin/env python3
"""Helper CLI to execute commands via agency_env_runner step API."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Allow direct import when running from root
sys.path.append(str(Path(__file__).resolve().parents[1]))

from envs.agency_env_runner import step  # type: ignore  # pylint: disable=import-error


def parse_env_overrides(values: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for entry in values:
        if "=" not in entry:
            raise SystemExit(f"Invalid env override '{entry}' (expected KEY=VALUE)")
        key, value = entry.split("=", 1)
        overrides[key] = value
    return overrides


def main() -> int:
    parser = argparse.ArgumentParser(description="Run commands via OpenEnv runner")
    parser.add_argument(
        "--spec",
        default=os.environ.get("AGENCY_ENV_SPEC"),
        help="Path to environment spec (defaults to AGENCY_ENV_SPEC env var)",
    )
    parser.add_argument("--cwd", help="Working directory for the command")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout in seconds (default: 600)")
    parser.add_argument(
        "--env",
        action="append",
        default=[],
        help="Environment override KEY=VALUE (can be provided multiple times)",
    )
    parser.add_argument(
        "--log-file",
        help="Optional path to write the runner response JSON (for CI artifacts)",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to execute (pass after --)",
    )

    args = parser.parse_args()

    if not args.spec:
        default_spec = Path(__file__).resolve().parents[1] / "envs" / "agency_env_spec.json"
        if default_spec.exists():
            args.spec = str(default_spec)
        else:
            raise SystemExit("AGENCY_ENV_SPEC not set and --spec not provided")

    os.environ.setdefault("AGENCY_ENV_SPEC", args.spec)

    if not args.command:
        raise SystemExit("Command required. Usage: run_in_env.py -- <command> [args]")

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("Command required. Usage: run_in_env.py -- <command> [args]")

    env_overrides = parse_env_overrides(args.env)

    action = {
        "command": command,
        "env": env_overrides,
        "cwd": args.cwd,
        "timeout": args.timeout,
    }

    result = step(action)

    # Write JSON log if requested
    if args.log_file:
        Path(args.log_file).write_text(json.dumps(result, indent=2))

    # Stream stdout/stderr
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    if stdout:
        sys.stdout.write(stdout)
    if stderr:
        sys.stderr.write(stderr)

    status = result.get("status")
    exit_code = int(result.get("exit_code", 1))

    if status in {"ok", "completed"}:
        return 0
    return exit_code or 1


if __name__ == "__main__":
    sys.exit(main())
