"""Shared JSON and type aliases.

This package contains canonical type aliases used across the Agency codebase.
"""

from .json import JSONScalar, JSONValue
from .result import Err, Ok, Result, ResultException, ResultStr, err, ok, try_result

__all__ = [
    "JSONScalar",
    "JSONValue",
    "Result",
    "Ok",
    "Err",
    "ok",
    "err",
    "try_result",
    "ResultStr",
    "ResultException",
]
