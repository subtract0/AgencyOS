"""
Type-safe utilities for working with JSONValue types in learning_agent module.
Provides type guards, safe accessors, and conversion utilities.
"""

from typing import TypeGuard, cast

from shared.type_definitions.json import JSONValue


def is_dict(value: JSONValue) -> TypeGuard[dict[str, JSONValue]]:
    """Type guard for dict JSONValue."""
    return isinstance(value, dict)


def is_list(value: JSONValue) -> TypeGuard[list[JSONValue]]:
    """Type guard for list JSONValue."""
    return isinstance(value, list)


def is_str(value: JSONValue) -> TypeGuard[str]:
    """Type guard for string JSONValue."""
    return isinstance(value, str)


def is_int(value: JSONValue) -> TypeGuard[int]:
    """Type guard for int JSONValue."""
    return isinstance(value, int)


def is_float(value: JSONValue) -> TypeGuard[float]:
    """Type guard for float JSONValue."""
    return isinstance(value, float)


def is_number(value: JSONValue) -> TypeGuard[int | float]:
    """Type guard for numeric JSONValue."""
    return isinstance(value, (int, float))


def is_none(value: JSONValue) -> TypeGuard[None]:
    """Type guard for None JSONValue."""
    return value is None


def safe_get(data: JSONValue, key: str, default: JSONValue | None = None) -> JSONValue:
    """Safely get a value from a JSONValue dict."""
    if is_dict(data):
        return data.get(key, default)
    return default


def safe_get_dict(data: JSONValue, key: str) -> dict[str, JSONValue]:
    """Safely get a dict value from a JSONValue dict."""
    result = safe_get(data, key, {})
    if is_dict(result):
        return result
    return {}


def safe_get_list(data: JSONValue, key: str) -> list[JSONValue]:
    """Safely get a list value from a JSONValue dict."""
    result = safe_get(data, key, [])
    if is_list(result):
        return result
    return []


def safe_get_str(data: JSONValue, key: str, default: str = "") -> str:
    """Safely get a string value from a JSONValue dict."""
    result = safe_get(data, key, default)
    if is_str(result):
        return result
    if result is not None:
        return str(result)
    return default


def safe_get_int(data: JSONValue, key: str, default: int = 0) -> int:
    """Safely get an int value from a JSONValue dict."""
    result = safe_get(data, key, default)
    if is_int(result):
        return result
    if is_float(result):
        return int(result)
    if is_str(result):
        try:
            return int(result)
        except (ValueError, TypeError):
            pass
    return default


def safe_get_float(data: JSONValue, key: str, default: float = 0.0) -> float:
    """Safely get a float value from a JSONValue dict."""
    result = safe_get(data, key, default)
    if is_float(result):
        return result
    if is_int(result):
        return float(result)
    if is_str(result):
        try:
            return float(result)
        except (ValueError, TypeError):
            pass
    return default


def safe_get_number(data: JSONValue, key: str, default: float = 0.0) -> float:
    """Safely get a numeric value from a JSONValue dict as float."""
    return safe_get_float(data, key, default)


def ensure_dict(value: JSONValue) -> dict[str, JSONValue]:
    """Ensure value is a dict, return empty dict if not."""
    if is_dict(value):
        return value
    return {}


def ensure_list(value: JSONValue) -> list[JSONValue]:
    """Ensure value is a list, return empty list if not."""
    if is_list(value):
        return value
    return []


def ensure_str(value: JSONValue) -> str:
    """Ensure value is a string, convert if possible."""
    if is_str(value):
        return value
    if value is not None:
        return str(value)
    return ""


def json_to_any_dict(data: JSONValue) -> dict[str, JSONValue]:
    """Convert JSONValue dict to Dict[str, JSONValue] for compatibility."""
    if is_dict(data):
        return cast(dict[str, JSONValue], data)
    return {}


def any_to_json_dict(data: dict[str, JSONValue]) -> dict[str, JSONValue]:
    """Convert Dict[str, JSONValue] to JSONValue dict."""
    return cast(dict[str, JSONValue], data)


def extract_numeric_list(data: list[JSONValue]) -> list[float]:
    """Extract numeric values from a JSONValue list."""
    result: list[float] = []
    for item in data:
        if is_number(item):
            result.append(float(item))
    return result


def safe_len(value: JSONValue) -> int:
    """Safely get length of a JSONValue collection."""
    if is_list(value):
        return len(value)
    if is_dict(value):
        return len(value)
    if is_str(value):
        return len(value)
    return 0
