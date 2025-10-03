"""
JSON Value Type - Type-safe replacement for Dict[str, Any]

Per Constitutional Article II: No Dict[str, Any] allowed.
Use JSONValue for JSON-serializable data with proper type safety.
"""

from typing import Union, Dict, List, Any

# JSONValue represents any valid JSON value
# More specific than Any, enforces JSON-serializability
JSONValue = Union[
    None,
    bool,
    int,
    float,
    str,
    List["JSONValue"],
    Dict[str, "JSONValue"]
]

__all__ = ["JSONValue"]
