"""
Result<T, E> pattern for functional error handling.

Inspired by Rust's Result type, this provides a type-safe way to handle
operations that may succeed or fail without using exceptions for control flow.

IMPORTANT AGENCY OS PATTERN:
The Result<T,E> pattern is the PREFERRED error handling approach throughout
the Agency codebase. Don't use try/catch for control flow. This pattern makes
error handling explicit, type-safe, and composable.

Example usage:
    from shared.type_definitions.result import Result, Ok, Err

    def divide(a: float, b: float) -> Result[float, str]:
        if b == 0:
            return Err("Division by zero")
        return Ok(a / b)

    result = divide(10, 2)
    if result.is_ok():
        print(f"Success: {result.unwrap()}")
    else:
        print(f"Error: {result.unwrap_err()}")

    # Chain operations with and_then
    result = divide(10, 2).and_then(lambda x: divide(x, 2))

    # Provide defaults with unwrap_or
    value = divide(10, 0).unwrap_or(0.0)
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")
F = TypeVar("F")


class Result(Generic[T, E], ABC):
    """
    Abstract base class for Result type.

    A Result<T, E> represents either success (Ok) or failure (Err).
    This pattern allows for explicit error handling without exceptions.
    """

    @abstractmethod
    def is_ok(self) -> bool:
        """Returns True if the result is Ok."""
        pass

    @abstractmethod
    def is_err(self) -> bool:
        """Returns True if the result is Err."""
        pass

    @abstractmethod
    def unwrap(self) -> T:
        """
        Returns the contained Ok value.

        Raises:
            RuntimeError: If the result is Err.
        """
        pass

    @abstractmethod
    def unwrap_err(self) -> E:
        """
        Returns the contained Err value.

        Raises:
            RuntimeError: If the result is Ok.
        """
        pass

    @abstractmethod
    def unwrap_or(self, default: T) -> T:
        """Returns the contained Ok value or the provided default."""
        pass

    @abstractmethod
    def unwrap_or_else(self, func: Callable[[E], T]) -> T:
        """Returns the contained Ok value or computes it from the error."""
        pass

    @abstractmethod
    def map(self, func: Callable[[T], U]) -> "Result[U, E]":
        """Maps a Result<T, E> to Result<U, E> by applying a function to Ok value."""
        pass

    @abstractmethod
    def map_err(self, func: Callable[[E], F]) -> "Result[T, F]":
        """Maps a Result<T, E> to Result<T, F> by applying a function to Err value."""
        pass

    @abstractmethod
    def and_then(self, func: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """
        Calls func if the result is Ok, otherwise returns the Err value.
        This is useful for chaining operations that may fail.
        """
        pass

    @abstractmethod
    def or_else(self, func: Callable[[E], "Result[T, F]"]) -> "Result[T, F]":
        """
        Calls func if the result is Err, otherwise returns the Ok value.
        This is useful for providing fallback operations.
        """
        pass


class Ok(Result[T, E]):
    """Represents a successful result containing a value."""

    def __init__(self, value: T) -> None:
        self._value = value

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self._value

    def unwrap_err(self) -> E:
        raise RuntimeError("Called unwrap_err() on an Ok value")

    def unwrap_or(self, default: T) -> T:
        return self._value

    def unwrap_or_else(self, func: Callable[[E], T]) -> T:
        return self._value

    def map(self, func: Callable[[T], U]) -> "Result[U, E]":
        return Ok(func(self._value))

    def map_err(self, func: Callable[[E], F]) -> "Result[T, F]":
        return Ok(self._value)

    def and_then(self, func: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return func(self._value)

    def or_else(self, func: Callable[[E], "Result[T, F]"]) -> "Result[T, F]":
        return Ok(self._value)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Ok) and self._value == other._value

    def __repr__(self) -> str:
        return f"Ok({self._value!r})"


class Err(Result[T, E]):
    """Represents a failed result containing an error."""

    def __init__(self, error: E) -> None:
        self._error = error

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> T:
        raise RuntimeError(f"Called unwrap() on an Err value: {self._error}")

    def unwrap_err(self) -> E:
        return self._error

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_or_else(self, func: Callable[[E], T]) -> T:
        return func(self._error)

    def map(self, func: Callable[[T], U]) -> "Result[U, E]":
        return Err(self._error)

    def map_err(self, func: Callable[[E], F]) -> "Result[T, F]":
        return Err(func(self._error))

    def and_then(self, func: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return Err(self._error)

    def or_else(self, func: Callable[[E], "Result[T, F]"]) -> "Result[T, F]":
        return func(self._error)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Err) and self._error == other._error

    def __repr__(self) -> str:
        return f"Err({self._error!r})"


# Convenience functions for creating Results
def ok(value: T) -> Result[T, Any]:
    """Create an Ok result."""
    return Ok(value)


def err(error: E) -> Result[Any, E]:
    """Create an Err result."""
    return Err(error)


def try_result(func: Callable[[], T], catch_type: type = Exception) -> Result[T, str]:
    """
    Execute a function and wrap the result in a Result type.

    Args:
        func: Function to execute
        catch_type: Exception type to catch (default: Exception)

    Returns:
        Ok(result) if successful, Err(error_message) if an exception occurs
    """
    try:
        return Ok(func())
    except catch_type as e:
        return Err(str(e))


# Type aliases for common error types
ResultStr = Result[T, str]  # Result with string error
ResultException = Result[T, Exception]  # Result with exception error
