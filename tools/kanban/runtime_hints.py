"""
Runtime hints application helpers.

Applies environment-level hint actions from LearningHintRegistry in a conservative way.
- Only active if ENABLE_RUNTIME_HINTS=true
- Hints with action.env are applied; others are ignored here
- Confidence threshold via RUNTIME_HINTS_MIN_CONF (default 0.5)
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple
from shared.types.json import JSONValue

from .hints import LearningHintRegistry, Hint


def _apply_env(env: ConfigData, key: str, value: str) -> Tuple[str, str, str]:
    """Apply env var with support for *_APPEND convention."""
    if key.endswith("_APPEND"):
        base = key[:-7]
        prev = env.get(base, "")
        sep = os.pathsep if prev else ""
        env[base] = f"{prev}{sep}{value}"
        return (base, "append", env[base])
    else:
        if not env.get(key):
            env[key] = value
            return (key, "set", value)
        return (key, "kept", env[key])


def apply_env_hints_from_registry(registry: LearningHintRegistry, env: ConfigData | None = None) -> List[dict[str, JSONValue]]:
    env = env if env is not None else os.environ
    min_conf = float(os.getenv("RUNTIME_HINTS_MIN_CONF", "0.5"))
    applied: List[dict[str, JSONValue]] = []

    for h in registry.all():
        try:
            if h.confidence < min_conf:
                continue
            action = h.action or {}
            env_map = action.get("env") if isinstance(action, dict) else None
            if not isinstance(env_map, dict):
                continue
            for k, v in env_map.items():
                if not isinstance(k, str) or not isinstance(v, str):
                    continue
                name, mode, value = _apply_env(env, k, v)
                applied.append({"var": name, "mode": mode, "value": value, "source": h.match})
        except Exception:
            continue

    return applied
