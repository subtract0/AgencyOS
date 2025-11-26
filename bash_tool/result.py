from typing import Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")


class Result(Generic[T, E]):
    """Simple Result<T,E> container."""

    __slots__ = ("_value", "_error")

    def __init__(self, value: T | None = None, error: E | None = None):
        if (value is None) == (error is None):
            raise ValueError("Result must hold either a value or an error, not both/neither.")
        self._value = value
        self._error = error

    @property
    def is_ok(self) -> bool:
        return self._error is None

    @property
    def is_err(self) -> bool:
        return self._value is None

    def unwrap(self) -> T:
        if self.is_ok:
            return self._value  # type: ignore
        raise RuntimeError(f"Unwrapped Result with error: {self._error}")

    def unwrap_err(self) -> E:
        if self.is_err:
            return self._error  # type: ignore
        raise RuntimeError("Unwrapped_err on ok Result")
