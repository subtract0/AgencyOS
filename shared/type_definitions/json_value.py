"""
JSON Value Type - Type-safe replacement for Dict[str, Any]

Per Constitutional Article II: No Dict[str, Any] allowed.
Use JSONValue for JSON-serializable data with proper type safety.
"""

from typing import Any, TypeAlias

# JSONValue represents any valid JSON value
# More specific than Any, enforces JSON-serializability
# Using TypeAlias to properly define recursive type for Pydantic compatibility
JSONValue: TypeAlias = None | bool | int | float | str | list[Any] | dict[str, Any]

__all__ = ["JSONValue"]
