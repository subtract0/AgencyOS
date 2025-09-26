"""
Learning Hint Registry: simple JSON-backed mapping from observed patterns to safe remediations.

- Kept conservative and opt-in
- Stored under logs/learning/hints.json
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from shared.types.json import JSONValue

DEFAULT_PATH = os.path.join(os.getcwd(), "logs", "learning", "hints.json")


@dataclass
class Hint:
    match: Dict[str, JSONValue]
    action: Dict[str, JSONValue]
    confidence: float = 0.5

    def to_dict(self) -> BaseResponse:
        return asdict(self)


class LearningHintRegistry:
    def __init__(self, path: Optional[str] = None):
        self.path = path or DEFAULT_PATH
        self.data: BaseResponse = {"version": 1, "hints": []}
        # Auto-load if exists
        self._load()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def _load(self):
        try:
            if os.path.isfile(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "hints" in data:
                        self.data = data
        except Exception:
            # Start fresh on errors
            self.data = {"version": 1, "hints": []}

    def _save(self):
        try:
            self._ensure_dir()
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

    def register(self, hint: Hint) -> None:
        hints = self.data.setdefault("hints", [])
        hints.append(hint.to_dict())
        self._save()

    def all(self) -> List[Hint]:
        return [Hint(**h) for h in self.data.get("hints", []) if isinstance(h, dict)]

    def match_for_error(self, error_type: Optional[str], error_message: Optional[str]) -> Optional[Hint]:
        """Find a hint matching error type or error pattern."""
        if not self.data.get("hints"):
            return None
        et = (error_type or "").lower()
        em = error_message or ""
        for h in self.data.get("hints", []):
            try:
                m = h.get("match", {})
                mt = (m.get("error_type") or "").lower()
                mp = m.get("error_pattern")
                if mt and mt == et:
                    return Hint(**h)
                if mp and isinstance(mp, str) and mp in em:
                    return Hint(**h)
            except Exception:
                continue
        return None

    def ensure_default_hints(self):
        """Seed with a few safe defaults if empty."""
        if self.data.get("hints"):
            return
        defaults = [
            Hint(match={"error_type": "modulenotfounderror"}, action={"note": "Consider ensuring dependency is installed or extras enabled."}, confidence=0.4),
            Hint(match={"error_pattern": "AttributeError: 'NoneType'"}, action={"note": "Add null check before attribute access."}, confidence=0.3),
        ]
        for d in defaults:
            self.register(d)
