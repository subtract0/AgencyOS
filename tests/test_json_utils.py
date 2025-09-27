# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value,union-attr,dict-item,operator"
"""
Test cases for the json_utils module.
"""
import pytest
from typing import Dict, List
from learning_agent.json_utils import (
    is_dict, is_list, is_str, is_int, is_float, is_number, is_none,
    safe_get, safe_get_dict, safe_get_list, safe_get_str,
    safe_get_int, safe_get_float, safe_get_number,
    ensure_dict, ensure_list, ensure_str,
    json_to_any_dict, any_to_json_dict,
    extract_numeric_list, safe_len
)
from shared.type_definitions.json import JSONValue


class TestTypeGuards:
    """Test type guard functions."""

    def test_is_dict(self):
        assert is_dict({"key": "value"})
        assert not is_dict([])
        assert not is_dict("string")
        assert not is_dict(42)
        assert not is_dict(None)

    def test_is_list(self):
        assert is_list([1, 2, 3])
        assert not is_list({})
        assert not is_list("string")
        assert not is_list(42)
        assert not is_list(None)

    def test_is_str(self):
        assert is_str("string")
        assert not is_str({})
        assert not is_str([])
        assert not is_str(42)
        assert not is_str(None)

    def test_is_int(self):
        assert is_int(42)
        assert not is_int(42.5)
        assert not is_int("42")
        assert not is_int({})
        assert not is_int(None)

    def test_is_float(self):
        assert is_float(42.5)
        assert not is_float(42)
        assert not is_float("42.5")
        assert not is_float({})
        assert not is_float(None)

    def test_is_number(self):
        assert is_number(42)
        assert is_number(42.5)
        assert not is_number("42")
        assert not is_number({})
        assert not is_number(None)

    def test_is_none(self):
        assert is_none(None)
        assert not is_none(0)
        assert not is_none("")
        assert not is_none([])
        assert not is_none({})


class TestSafeGetters:
    """Test safe getter functions."""

    def test_safe_get(self):
        data: JSONValue = {"key": "value", "num": 42}
        assert safe_get(data, "key") == "value"
        assert safe_get(data, "missing") is None
        assert safe_get(data, "missing", "default") == "default"
        assert safe_get([], "key") is None
        assert safe_get(None, "key") is None

    def test_safe_get_dict(self):
        data: JSONValue = {"nested": {"key": "value"}, "other": 42}
        result = safe_get_dict(data, "nested")
        assert result == {"key": "value"}
        assert safe_get_dict(data, "other") == {}
        assert safe_get_dict(data, "missing") == {}
        assert safe_get_dict([], "key") == {}

    def test_safe_get_list(self):
        data: JSONValue = {"items": [1, 2, 3], "other": 42}
        assert safe_get_list(data, "items") == [1, 2, 3]
        assert safe_get_list(data, "other") == []
        assert safe_get_list(data, "missing") == []
        assert safe_get_list({}, "key") == []

    def test_safe_get_str(self):
        data: JSONValue = {"name": "test", "num": 42, "none": None}
        assert safe_get_str(data, "name") == "test"
        assert safe_get_str(data, "num") == "42"
        assert safe_get_str(data, "none") == ""
        assert safe_get_str(data, "missing") == ""
        assert safe_get_str(data, "missing", "default") == "default"

    def test_safe_get_int(self):
        data: JSONValue = {"int": 42, "float": 42.9, "str": "123", "bad": "abc"}
        assert safe_get_int(data, "int") == 42
        assert safe_get_int(data, "float") == 42
        assert safe_get_int(data, "str") == 123
        assert safe_get_int(data, "bad") == 0
        assert safe_get_int(data, "missing", 99) == 99

    def test_safe_get_float(self):
        data: JSONValue = {"int": 42, "float": 42.5, "str": "123.5", "bad": "abc"}
        assert safe_get_float(data, "int") == 42.0
        assert safe_get_float(data, "float") == 42.5
        assert safe_get_float(data, "str") == 123.5
        assert safe_get_float(data, "bad") == 0.0
        assert safe_get_float(data, "missing", 99.9) == 99.9

    def test_safe_get_number(self):
        data: JSONValue = {"int": 42, "float": 42.5}
        assert safe_get_number(data, "int") == 42.0
        assert safe_get_number(data, "float") == 42.5
        assert safe_get_number(data, "missing") == 0.0


class TestEnsureFunctions:
    """Test ensure type functions."""

    def test_ensure_dict(self):
        assert ensure_dict({"key": "value"}) == {"key": "value"}
        assert ensure_dict([]) == {}
        assert ensure_dict("string") == {}
        assert ensure_dict(None) == {}

    def test_ensure_list(self):
        assert ensure_list([1, 2, 3]) == [1, 2, 3]
        assert ensure_list({}) == []
        assert ensure_list("string") == []
        assert ensure_list(None) == []

    def test_ensure_str(self):
        assert ensure_str("string") == "string"
        assert ensure_str(42) == "42"
        assert ensure_str(42.5) == "42.5"
        assert ensure_str(None) == ""
        assert ensure_str([]) == "[]"


class TestConversionFunctions:
    """Test conversion functions."""

    def test_json_to_any_dict(self):
        data: JSONValue = {"key": "value", "num": 42}
        result = json_to_any_dict(data)
        assert result == {"key": "value", "num": 42}
        assert json_to_any_dict([]) == {}
        assert json_to_any_dict(None) == {}

    def test_any_to_json_dict(self):
        data = {"key": "value", "num": 42}
        result = any_to_json_dict(data)
        assert result == {"key": "value", "num": 42}

    def test_extract_numeric_list(self):
        data: List[JSONValue] = [1, 2.5, "3", None, "abc", 4]
        result = extract_numeric_list(data)
        assert result == [1.0, 2.5, 4.0]
        assert extract_numeric_list([]) == []

    def test_safe_len(self):
        assert safe_len([1, 2, 3]) == 3
        assert safe_len({"a": 1, "b": 2}) == 2
        assert safe_len("hello") == 5
        assert safe_len(42) == 0
        assert safe_len(None) == 0