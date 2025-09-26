from __future__ import annotations

"""
Canonical JSON-compatible type aliases used across the Agency codebase.

These types provide a safe alternative to Dict[str, Any] for payloads that are
persisted as JSON or exchanged across process boundaries.

Usage patterns:
- Use JSONValue for arbitrary JSON-shaped payloads (configs, metadata, telemetry data)
- Prefer concrete Pydantic models where shapes are known and stable
"""

from typing import Union
from pydantic import JsonValue as _PydanticJsonValue

JSONScalar = Union[str, int, float, bool, None]
# Use Pydantic's built-in JsonValue to avoid recursive alias issues in schema generation
JSONValue = _PydanticJsonValue

__all__ = [
    "JSONScalar",
    "JSONValue",
]
