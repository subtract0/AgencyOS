#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

SEPARATORS = {"&&", "||", ";", "|", "&"}

HARD_BLOCK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*}\s*;"), "Fork bomb detected"),
    (re.compile(r"\bmkfs\b"), "Filesystem formatting detected"),
    (re.compile(r"\bdiskutil\b\s+erase\b"), "Disk erase detected"),
    (re.compile(r"\b(?:dd|shred|wipefs)\b"), "Raw device write detected"),
    (re.compile(r"\b(?:shutdown|reboot|halt|poweroff)\b"), "Power command detected"),
]


def _emit(decision: str, reason: str) -> None:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))


def _load_input() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid hook JSON input: {exc}", file=sys.stderr)
        sys.exit(1)


def _is_outside_project(path: str, cwd: str, project_dir: str) -> bool:
    expanded = os.path.expanduser(path)
    if not os.path.isabs(expanded):
        expanded = os.path.abspath(os.path.join(cwd, expanded))

    try:
        common = os.path.commonpath([project_dir, expanded])
    except ValueError:
        return True
    return common != project_dir


def _rm_decision(args: list[str], cwd: str, project_dir: str) -> tuple[str | None, str | None]:
    flags = [arg for arg in args if arg.startswith("-")]
    targets = [arg for arg in args if not arg.startswith("-")]

    if not targets:
        return None, None

    recursive = any(re.search(r"-.*[rR].*", flag) for flag in flags) or "--recursive" in flags

    for target in targets:
        if any(ch in target for ch in ("*", "?")):
            return "ask", "Delete with glob patterns requires confirmation."
        if target in {"/", "/*", "~", "~/", "..", "../"}:
            return "deny", f"Refusing to delete dangerous path: {target}"
        if ".." in Path(target).parts:
            return "ask", "Delete with parent traversal requires confirmation."

        if _is_outside_project(target, cwd, project_dir):
            return "deny", f"Refusing to delete outside project: {target}"

    if recursive:
        return "ask", "Recursive delete requires confirmation."
    return None, None


def _git_clean_decision(args: list[str]) -> tuple[str | None, str | None]:
    flags = [arg for arg in args if arg.startswith("-")]
    if any("f" in flag and "d" in flag for flag in flags):
        return "ask", "git clean with -f/-d requires confirmation."
    return None, None


def main() -> None:
    payload = _load_input()
    if payload.get("tool_name") != "Bash":
        return

    tool_input = payload.get("tool_input") or {}
    command = (tool_input.get("command") or "").strip()
    if not command:
        return

    for pattern, message in HARD_BLOCK_PATTERNS:
        if pattern.search(command):
            _emit("deny", message)
            return

    try:
        tokens = shlex.split(command)
    except ValueError:
        _emit("ask", "Unable to parse command safely; manual approval required.")
        return

    if "sudo" in tokens:
        _emit("ask", "sudo requires confirmation.")
        return

    project_dir = os.path.abspath(os.getenv("CLAUDE_PROJECT_DIR", os.getcwd()))
    cwd = os.path.abspath(payload.get("cwd") or os.getcwd())

    for idx, token in enumerate(tokens):
        if token in SEPARATORS:
            continue

        cmd = os.path.basename(token)
        if cmd in {"rm", "rmdir", "unlink"}:
            args = []
            for arg in tokens[idx + 1 :]:
                if arg in SEPARATORS:
                    break
                args.append(arg)
            decision, reason = _rm_decision(args, cwd, project_dir)
            if decision:
                _emit(decision, reason or "Delete requires confirmation.")
                return

        if cmd == "git":
            args = []
            for arg in tokens[idx + 1 :]:
                if arg in SEPARATORS:
                    break
                args.append(arg)
            if args and args[0] == "clean":
                decision, reason = _git_clean_decision(args[1:])
                if decision:
                    _emit(decision, reason or "git clean requires confirmation.")
                    return


if __name__ == "__main__":
    main()
