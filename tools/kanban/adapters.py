# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value"
"""
Kanban adapters: build Card records from telemetry and learning sources.

- Defensive by default: ignore malformed events, redact sensitive data
- No external dependencies; stdlib only
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, cast
from shared.type_definitions.json import JSONValue

# Local telemetry aggregator (safe, stdlib)
try:
    from tools.telemetry.aggregator import list_events  # type: ignore
except Exception:  # pragma: no cover
    list_events = None  # type: ignore

# Pattern store (optional)
try:
    from pattern_intelligence import PatternStore
    def get_pattern_store():
        return PatternStore()
except Exception:  # pragma: no cover
    get_pattern_store = None  # type: ignore

REDACT_KEYS = {"password", "token", "secret", "key", "api_key", "authorization"}


@dataclass
class Card:
    id: str
    type: str  # error | task | pattern | antipattern | discovery
    title: str
    summary: str
    source_ref: str
    status: str  # To Investigate | In Progress | Learned | Resolved
    created_at: str
    links: List[str]
    tags: List[str]

    def to_dict(self) -> Dict[str, JSONValue]:
        return asdict(self)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _redact(obj: Any) -> Any:
    """Redact likely secrets in dict-like structures."""
    try:
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if any(s in str(k).lower() for s in REDACT_KEYS):
                    out[k] = "[REDACTED]"
                else:
                    out[k] = _redact(v)
            return out
        if isinstance(obj, list):
            return [_redact(v) for v in obj]
        return obj
    except Exception:
        return obj


def _shorten(text: str, n: int = 200) -> str:
    if not text:
        return ""
    if len(text) <= n:
        return text
    return text[: n - 14].rstrip() + "...[truncated]"


def _stable_id(*parts: str) -> str:
    h = hashlib.sha1()
    for p in parts:
        if p:
            h.update(p.encode("utf-8", errors="ignore"))
            h.update(b"\x00")
    return h.hexdigest()[:16]


def _event_to_card(ev: Dict[str, JSONValue]) -> Optional[Card]:
    typ = str(ev.get("type", "")).lower()
    ts = ev.get("ts") or _iso_now()
    agent = ev.get("agent") or "-"
    status = None
    card_type = None
    title = None
    summary = ""
    tags: List[str] = []

    # Derive status and type
    if typ == "task_started":
        card_type = "task"
        status = "In Progress"
        title = f"Task started: {agent}"
    elif typ == "task_finished":
        st = str(ev.get("status", "")).lower()
        if st == "success":
            card_type = "task"
            status = "Resolved"
            title = f"Task success: {agent}"
        else:
            card_type = "error"
            status = "To Investigate"
            title = f"Task failed: {agent}"
            err = ev.get("error") or ev.get("message") or ev.get("reason")
            if isinstance(err, str):
                summary = _shorten(err)
    elif typ in ("pattern_extracted", "pattern_store.pattern_added"):
        card_type = "pattern"
        status = "Learned"
        title = f"Pattern learned"
        ctx = ev.get("context") or {}
        summary = _shorten(json.dumps(_redact(ctx)) if ctx else "New reusable pattern")
        tags.append("pattern")
    elif typ == "antipattern_learned":
        card_type = "antipattern"
        status = "Learned"
        title = f"Anti-pattern learned"
        ctx = ev.get("context") or {}
        summary = _shorten(json.dumps(_redact(ctx)) if ctx else "Avoid this approach")
        tags.append("antipattern")
    else:
        # Generic error detection
        if any(k in ev for k in ("error", "exception")):
            card_type = "error"
            status = "To Investigate"
            title = f"Error: {agent or typ}"
            err = ev.get("error") or ev.get("exception")
            if isinstance(err, str):
                summary = _shorten(err)
        else:
            return None

    source_ref = str(ev.get("id") or ev.get("run_id") or typ)
    created_at = ts if isinstance(ts, str) else _iso_now()
    links: List[str] = []

    cid = _stable_id(source_ref, typ, created_at)
    return Card(
        id=cid,
        type=card_type or "task",
        title=title or typ,
        summary=summary,
        source_ref=source_ref,
        status=status or "To Investigate",
        created_at=created_at,
        links=links,
        tags=tags,
    )


def _patterns_to_cards() -> List[Card]:
    cards: List[Card] = []
    try:
        if get_pattern_store is None:
            return cards
        store = get_pattern_store()
        patterns = store.get_top_patterns(limit=50)  # Get up to 50 patterns
        for p in patterns:
            created = p.metadata.discovered_timestamp
            title = f"Pattern: {p.metadata.pattern_id}"
            try:
                ctx = {
                    "description": p.context.description,
                    "domain": p.context.domain,
                    "approach": p.solution.approach
                }
                summary = _shorten(json.dumps(_redact(ctx)))
            except (TypeError, ValueError) as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to serialize pattern context for {p.metadata.pattern_id}: {e}")
                summary = "Learned pattern"
            cid = _stable_id("pattern", p.metadata.pattern_id, created)
            cards.append(
                Card(
                    id=cid,
                    type="pattern",
                    title=title,
                    summary=summary,
                    source_ref=p.metadata.pattern_id,
                    status="Learned",
                    created_at=created,
                    links=[],
                    tags=p.metadata.tags if isinstance(p.metadata.tags, list) else ["pattern"],
                )
            )
    except (AttributeError, TypeError) as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create pattern cards: {e}")
        # Return empty list on failure
        pass
    return cards


def build_cards(window: str = "4h", telemetry_dir: Optional[str] = None, include_patterns: bool = True) -> List[Dict[str, JSONValue]]:
    """Build cards from recent telemetry, optional pattern store, and optional untracked files.

    Args:
        window: e.g., '1h', '4h', '24h'
        telemetry_dir: optional override path
        include_patterns: whether to also include learned patterns
    """
    cards: List[Card] = []

    # Telemetry events -> cards
    if list_events is not None:
        try:
            events = list_events(since=window, grep=None, limit=500, telemetry_dir=telemetry_dir)
            for ev in events:
                c = _event_to_card(ev)
                if c:
                    cards.append(c)
        except Exception:
            pass

    # Learned patterns -> cards
    if include_patterns:
        cards.extend(_patterns_to_cards())

    # Untracked learning -> discovery cards (opt-in)
    try:
        if os.getenv("LEARNING_UNTRACKED", "false").lower() == "true":
            from .untracked import discover_untracked_cards
            untracked_dicts = discover_untracked_cards()
            for card_dict in untracked_dicts:
                try:
                    # Convert JSONValue fields back to expected types
                    card = Card(
                        id=str(card_dict.get('id', '')),
                        type=str(card_dict.get('type', 'discovery')),
                        title=str(card_dict.get('title', '')),
                        summary=str(card_dict.get('summary', '')),
                        source_ref=str(card_dict.get('source_ref', '')),
                        status=str(card_dict.get('status', 'Learned')),
                        created_at=str(card_dict.get('created_at', '')),
                        links=[
                            str(l) for l in cast(List[JSONValue], card_dict.get('links', []))
                            if isinstance(l, str)
                        ] if isinstance(card_dict.get('links'), list) else [],
                        tags=[
                            str(t) for t in cast(List[JSONValue], card_dict.get('tags', []))
                            if isinstance(t, str)
                        ] if isinstance(card_dict.get('tags'), list) else [],
                    )
                    cards.append(card)
                except Exception:
                    pass  # Skip malformed cards
    except Exception:
        pass

    # Sort newest first
    try:
        cards.sort(key=lambda c: c.created_at, reverse=True)
    except Exception:
        pass

    return [c.to_dict() for c in cards]


def build_feed(window: str = "4h", telemetry_dir: Optional[str] = None, include_patterns: bool = True) -> Dict[str, JSONValue]:
    return {
        "generated_at": _iso_now(),
        "cards": cast(JSONValue, build_cards(window=window, telemetry_dir=telemetry_dir, include_patterns=include_patterns)),
    }
