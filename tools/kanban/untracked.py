"""
Untracked learning ingestion: discover useful notes from allowlisted paths.

- Opt-in via LEARNING_UNTRACKED=true
- Allowlist globs via LEARNING_UNTRACKED_GLOBS (comma-separated)
- Default allowlist: notes/**/*.md, scratch/**/*.txt
- Denylist directories: .git, .venv, venv, env, node_modules, secrets, secret
- Privacy: redacts likely secrets from summaries
"""
from __future__ import annotations

import glob
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List
from shared.types.json import JSONValue

from .adapters import _redact, _shorten, _iso_now, Card, _stable_id

REPO_ROOT = Path(__file__).resolve().parents[2]
DENY_DIRS = {".git", ".venv", "venv", "env", "node_modules", "secrets", "secret"}
DEFAULT_ALLOWLIST = ["notes/**/*.md", "scratch/**/*.txt"]
MAX_BYTES = 32_000  # cap reads for safety


def _is_denied(path: Path) -> bool:
    parts = set(p.lower() for p in path.parts)
    return any(d in parts for d in DENY_DIRS)


def _read_snippet(fp: Path) -> str:
    try:
        with fp.open("rb") as f:
            raw = f.read(MAX_BYTES)
        try:
            text = raw.decode("utf-8", errors="ignore")
        except Exception:
            text = str(raw[:200])
        # Use first 200 chars as summary (redacted)
        from json import dumps
        red = _redact(text)
        if isinstance(red, (dict, list)):
            text = dumps(red)[:200]
        else:
            text = str(red)
        return _shorten(text, 200)
    except Exception:
        return ""


def discover_untracked_cards() -> List[Dict[str, JSONValue]]:
    # Check flag
    if os.getenv("LEARNING_UNTRACKED", "false").lower() != "true":
        return []

    # Globs
    globs_env = os.getenv("LEARNING_UNTRACKED_GLOBS")
    patterns = [g.strip() for g in globs_env.split(",") if g.strip()] if globs_env else DEFAULT_ALLOWLIST

    cards: List[Card] = []

    for pattern in patterns:
        # Absolute pattern rooted at repo
        abs_pattern = str(REPO_ROOT / pattern)
        for path_str in glob.iglob(abs_pattern, recursive=True):
            p = Path(path_str)
            if not p.is_file():
                continue
            if _is_denied(p):
                continue
            # Build card
            try:
                rel = p.relative_to(REPO_ROOT)
            except Exception:
                rel = p
            summary = _read_snippet(p)
            cid = _stable_id("untracked", str(rel))
            cards.append(
                Card(
                    id=cid,
                    type="discovery",
                    title=f"Note: {rel}",
                    summary=summary,
                    source_ref=str(rel),
                    status="Learned",
                    created_at=_iso_now(),
                    links=[],
                    tags=["untracked", "note"],
                )
            )

    # Deduplicate by id
    uniq = {}
    for c in cards:
        uniq[c.id] = c
    return [c.to_dict() for c in uniq.values()]
