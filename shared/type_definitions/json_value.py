"""
JSON Value Type - Type-safe replacement for Dict[str, Any]

Per Constitutional Article II: No Dict[str, Any] allowed.
Use JSONValue for JSON-serializable data with proper type safety.
"""

from typing import Union, Dict, List, Any, TypeAlias

# JSONValue represents any valid JSON value
# More specific than Any, enforces JSON-serializability
# Using TypeAlias to properly define recursive type for Pydantic compatibility
JSONValue: TypeAlias = Union[
    None,
    bool,
    int,
    float,
    str,
    List[Any],  # Use Any to avoid recursion issues with Pydantic
    Dict[str, Any]  # Use Any to avoid recursion issues with Pydantic
]

__all__ = ["JSONValue"]
