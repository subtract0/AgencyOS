from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


SECRET_PATTERNS = {
    "openai": re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{32,}"),
    "github": re.compile(r"ghp_[A-Za-z0-9]{36,}"),
    "google_oauth": re.compile(r"ya29\\.[0-9A-Za-z_-]{50,}"),
    "google_api": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "slack": re.compile(r"xox[baprs]-[0-9A-Za-z-]{20,}"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private_key": re.compile(r"-----BEGIN (?:RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----"),
}

ALLOWLIST = {
    ("github", "tests/tools/ci_monitor/test_smart_notifier.py"),
}

BINARY_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".pkl",
    ".bin",
    ".ico",
    ".zip",
    ".gz",
    ".tar",
    ".tgz",
    ".bz2",
    ".xz",
    ".mp3",
    ".mp4",
    ".mov",
    ".wav",
    ".aiff",
    ".aif",
    ".avi",
    ".flac",
    ".onnx",
    ".pt",
    ".otf",
    ".ttf",
    ".dylib",
    ".so",
    ".dll",
}


def _tracked_files() -> list[str]:
    try:
        output = subprocess.check_output(["git", "ls-files"], text=True)
    except Exception as exc:
        pytest.skip(f"git ls-files unavailable: {exc}")
    return [line for line in output.splitlines() if line.strip()]


def _is_binary(path: Path) -> bool:
    if path.suffix.lower() in BINARY_EXTS:
        return True
    try:
        data = path.read_bytes()
    except Exception:
        return True
    return b"\x00" in data


def test_repo_has_no_tracked_secrets() -> None:
    matches: list[tuple[str, str, int]] = []

    for rel_path in _tracked_files():
        path = Path(rel_path)
        if _is_binary(path):
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in SECRET_PATTERNS.items():
            if not pattern.search(text):
                continue

            for line_no, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    if (name, rel_path) in ALLOWLIST:
                        break
                    matches.append((name, rel_path, line_no))
                    break

    if matches:
        lines = [f"{name} {path}:{line_no}" for name, path, line_no in matches]
        pytest.fail("Potential secrets found in tracked files:\\n" + "\\n".join(lines))
