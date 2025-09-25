from __future__ import annotations

import copy
import re
from typing import Any, Dict
from shared.models.telemetry import TelemetryEvent

# Patterns for secret-like values
_SECRET_VALUE_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{10,}"),        # OpenAI-style keys
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),       # GitHub PAT (min 20 chars)
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), # Slack tokens
    re.compile(r"AIza[0-9A-Za-z\-_]{15,}"),    # Google API key
]

# Keys that should always be redacted when present
_SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "client_secret",
    "password",
    "passwd",
}

_REPLACEMENT = "[REDACTED]"


def _redact_str(s: str) -> str:
    out = s
    for pat in _SECRET_VALUE_PATTERNS:
        out = pat.sub(_REPLACEMENT, out)
    return out


def _redact_any(val: Any) -> Any:
    if isinstance(val, str):
        return _redact_str(val)
    if isinstance(val, dict):
        return {k: _redact_any(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_redact_any(v) for v in val]
    return val


def redact_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive material from a telemetry event.

    Rules:
    - For known sensitive keys (case-insensitive), replace value with [REDACTED]
    - For string values, mask known secret-like patterns (OpenAI, GH PAT, Slack, Google)
    - Keep structure intact; avoid removing non-secret fields

    Note: Still accepts Dict for backward compatibility, but can work with TelemetryEvent
    """
    if not isinstance(event, dict):
        return event
    safe = copy.deepcopy(event)

    def _walk(obj: Any) -> Any:
        if isinstance(obj, dict):
            new: Dict[str, Any] = {}
            for k, v in obj.items():
                if k.lower() in _SENSITIVE_KEYS:
                    new[k] = _REPLACEMENT
                else:
                    new[k] = _walk(v)
            return new
        if isinstance(obj, list):
            return [_walk(v) for v in obj]
        if isinstance(obj, str):
            return _redact_str(obj)
        return obj

    return _walk(safe)


def redact_telemetry_event(event: TelemetryEvent) -> TelemetryEvent:
    """Redact sensitive material from a TelemetryEvent model.

    Args:
        event: TelemetryEvent to sanitize

    Returns:
        New TelemetryEvent with redacted metadata
    """
    # Convert to dict, redact, then rebuild
    event_dict = event.model_dump()
    redacted_dict = redact_event(event_dict)

    # Create new TelemetryEvent with redacted data
    return TelemetryEvent(
        event_id=event.event_id,
        event_type=event.event_type,
        severity=event.severity,
        timestamp=event.timestamp,
        agent_id=event.agent_id,
        session_id=event.session_id,
        tool_name=event.tool_name,
        duration_ms=event.duration_ms,
        success=event.success,
        error_message=redacted_dict.get('error_message'),
        metadata=redacted_dict.get('metadata', {}),
        tags=event.tags
    )
