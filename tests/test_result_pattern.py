"""
Comprehensive tests for the Result<T, E> pattern implementation.

Tests all Result methods, error propagation, type safety, and usage patterns.
"""


import pytest

from shared.type_definitions.result import (
    Err,
    Ok,
    Result,
    ResultException,
    ResultStr,
    err,
    ok,
    try_result,
)


class TestResultBasics:
    """Test basic Result functionality."""

    def test_ok_creation(self):
        """Test Ok result creation."""
        result = Ok(42)
        assert result.is_ok()
        assert not result.is_err()
        assert result.unwrap() == 42

    def test_err_creation(self):
        """Test Err result creation."""
        result = Err("error message")
        assert not result.is_ok()
        assert result.is_err()
        assert result.unwrap_err() == "error message"

    def test_ok_convenience_function(self):
        """Test ok() convenience function."""
        result = ok("success")
        assert result.is_ok()
        assert result.unwrap() == "success"

    def test_err_convenience_function(self):
        """Test err() convenience function."""
        result = err("failure")
        assert result.is_err()
        assert result.unwrap_err() == "failure"


class TestResultUnwrapping:
    """Test Result unwrapping methods."""

    def test_unwrap_ok(self):
        """Test unwrapping Ok values."""
        result = Ok(100)
        assert result.unwrap() == 100

    def test_unwrap_err_panics(self):
        """Test that unwrap() on Err raises RuntimeError."""
        result = Err("error")
        with pytest.raises(RuntimeError, match="Called unwrap\\(\\) on an Err value"):
            result.unwrap()

    def test_unwrap_err_ok_panics(self):
        """Test that unwrap_err() on Ok raises RuntimeError."""
        result = Ok(42)
        with pytest.raises(RuntimeError, match="Called unwrap_err\\(\\) on an Ok value"):
            result.unwrap_err()

    def test_unwrap_or_ok(self):
        """Test unwrap_or() with Ok value."""
        result = Ok(42)
        assert result.unwrap_or(0) == 42

    def test_unwrap_or_err(self):
        """Test unwrap_or() with Err value."""
        result = Err("error")
        assert result.unwrap_or(0) == 0

    def test_unwrap_or_else_ok(self):
        """Test unwrap_or_else() with Ok value."""
        result = Ok(42)
        assert result.unwrap_or_else(lambda e: len(e)) == 42

    def test_unwrap_or_else_err(self):
        """Test unwrap_or_else() with Err value."""
        result = Err("error")
        assert result.unwrap_or_else(lambda e: len(e)) == 5


class TestResultMapping:
    """Test Result mapping operations."""

    def test_map_ok(self):
        """Test map() on Ok value."""
        result = Ok(5)
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_ok()
        assert mapped.unwrap() == 10

    def test_map_err(self):
        """Test map() on Err value."""
        result = Err("error")
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_err()
        assert mapped.unwrap_err() == "error"

    def test_map_err_ok(self):
        """Test map_err() on Ok value."""
        result = Ok(42)
        mapped = result.map_err(lambda e: f"Error: {e}")
        assert mapped.is_ok()
        assert mapped.unwrap() == 42

    def test_map_err_err(self):
        """Test map_err() on Err value."""
        result = Err("error")
        mapped = result.map_err(lambda e: f"Error: {e}")
        assert mapped.is_err()
        assert mapped.unwrap_err() == "Error: error"

    def test_map_chaining(self):
        """Test chaining map operations."""
        result = Ok(5)
        final = result.map(lambda x: x * 2).map(lambda x: x + 1)
        assert final.unwrap() == 11


class TestResultAndThen:
    """Test Result and_then operations."""

    def test_and_then_ok(self):
        """Test and_then() with Ok value."""

        def safe_divide(x: int) -> Result[int, str]:
            if x == 0:
                return Err("Division by zero")
            return Ok(10 // x)

        result = Ok(2)
        chained = result.and_then(safe_divide)
        assert chained.is_ok()
        assert chained.unwrap() == 5

    def test_and_then_ok_to_err(self):
        """Test and_then() with Ok value that produces Err."""

        def safe_divide(x: int) -> Result[int, str]:
            if x == 0:
                return Err("Division by zero")
            return Ok(10 // x)

        result = Ok(0)
        chained = result.and_then(safe_divide)
        assert chained.is_err()
        assert chained.unwrap_err() == "Division by zero"

    def test_and_then_err(self):
        """Test and_then() with Err value."""

        def safe_divide(x: int) -> Result[int, str]:
            return Ok(10 // x)

        result = Err("initial error")
        chained = result.and_then(safe_divide)
        assert chained.is_err()
        assert chained.unwrap_err() == "initial error"

    def test_and_then_chaining(self):
        """Test chaining multiple and_then operations."""

        def add_one(x: int) -> Result[int, str]:
            return Ok(x + 1)

        def multiply_two(x: int) -> Result[int, str]:
            return Ok(x * 2)

        result = Ok(5)
        final = result.and_then(add_one).and_then(multiply_two)
        assert final.unwrap() == 12


class TestResultOrElse:
    """Test Result or_else operations."""

    def test_or_else_ok(self):
        """Test or_else() with Ok value."""

        def recovery(e: str) -> Result[int, str]:
            return Ok(0)

        result = Ok(42)
        recovered = result.or_else(recovery)
        assert recovered.is_ok()
        assert recovered.unwrap() == 42

    def test_or_else_err(self):
        """Test or_else() with Err value."""

        def recovery(e: str) -> Result[int, str]:
            return Ok(0)

        result = Err("error")
        recovered = result.or_else(recovery)
        assert recovered.is_ok()
        assert recovered.unwrap() == 0

    def test_or_else_err_to_err(self):
        """Test or_else() with Err value that produces another Err."""

        def recovery(e: str) -> Result[int, int]:
            return Err(404)

        result = Err("original error")
        recovered = result.or_else(recovery)
        assert recovered.is_err()
        assert recovered.unwrap_err() == 404


class TestResultEquality:
    """Test Result equality comparisons."""

    def test_ok_equality(self):
        """Test Ok values equality."""
        ok1 = Ok(42)
        ok2 = Ok(42)
        ok3 = Ok(43)
        assert ok1 == ok2
        assert ok1 != ok3

    def test_err_equality(self):
        """Test Err values equality."""
        err1 = Err("error")
        err2 = Err("error")
        err3 = Err("different error")
        assert err1 == err2
        assert err1 != err3

    def test_ok_err_inequality(self):
        """Test Ok and Err are never equal."""
        ok_result = Ok(42)
        err_result = Err("error")
        assert ok_result != err_result


class TestResultRepr:
    """Test Result string representations."""

    def test_ok_repr(self):
        """Test Ok representation."""
        result = Ok(42)
        assert repr(result) == "Ok(42)"

    def test_err_repr(self):
        """Test Err representation."""
        result = Err("error message")
        assert repr(result) == "Err('error message')"


class TestTryResult:
    """Test try_result utility function."""

    def test_try_result_success(self):
        """Test try_result with successful function."""

        def success_func():
            return 42

        result = try_result(success_func)
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_try_result_failure(self):
        """Test try_result with failing function."""

        def failing_func():
            raise ValueError("Something went wrong")

        result = try_result(failing_func)
        assert result.is_err()
        assert "Something went wrong" in result.unwrap_err()

    def test_try_result_specific_exception(self):
        """Test try_result with specific exception type."""

        def failing_func():
            raise ValueError("Specific error")

        result = try_result(failing_func, ValueError)
        assert result.is_err()
        assert "Specific error" in result.unwrap_err()

    def test_try_result_unhandled_exception(self):
        """Test try_result with unhandled exception type."""

        def failing_func():
            raise KeyError("Key not found")

        with pytest.raises(KeyError):
            try_result(failing_func, ValueError)


class TestTypeAliases:
    """Test Result type aliases."""

    def test_result_str_ok(self):
        """Test ResultStr with Ok value."""
        result: ResultStr[int] = Ok(42)
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_result_str_err(self):
        """Test ResultStr with Err value."""
        result: ResultStr[int] = Err("String error")
        assert result.is_err()
        assert result.unwrap_err() == "String error"

    def test_result_exception_ok(self):
        """Test ResultException with Ok value."""
        result: ResultException[str] = Ok("success")
        assert result.is_ok()
        assert result.unwrap() == "success"

    def test_result_exception_err(self):
        """Test ResultException with Err value."""
        error = ValueError("Test error")
        result: ResultException[str] = Err(error)
        assert result.is_err()
        assert result.unwrap_err() == error


class TestRealWorldUsage:
    """Test real-world usage patterns."""

    def test_divide_function(self):
        """Test divide function with Result pattern."""

        def safe_divide(a: float, b: float) -> Result[float, str]:
            if b == 0:
                return Err("Division by zero")
            return Ok(a / b)

        # Test successful division
        result = safe_divide(10, 2)
        assert result.is_ok()
        assert result.unwrap() == 5.0

        # Test division by zero
        result = safe_divide(10, 0)
        assert result.is_err()
        assert result.unwrap_err() == "Division by zero"

    def test_parse_int_function(self):
        """Test integer parsing with Result pattern."""

        def safe_parse_int(s: str) -> Result[int, str]:
            try:
                return Ok(int(s))
            except ValueError:
                return Err(f"Invalid integer: {s}")

        # Test successful parsing
        result = safe_parse_int("42")
        assert result.is_ok()
        assert result.unwrap() == 42

        # Test failed parsing
        result = safe_parse_int("not_a_number")
        assert result.is_err()
        assert "Invalid integer" in result.unwrap_err()

    def test_chained_operations(self):
        """Test chaining multiple Result operations."""

        def safe_parse_int(s: str) -> Result[int, str]:
            try:
                return Ok(int(s))
            except ValueError:
                return Err(f"Invalid integer: {s}")

        def safe_divide(a: int, b: int) -> Result[float, str]:
            if b == 0:
                return Err("Division by zero")
            return Ok(a / b)

        # Test successful chain
        result = safe_parse_int("10").and_then(
            lambda x: safe_parse_int("2").and_then(lambda y: safe_divide(x, y))
        )
        assert result.is_ok()
        assert result.unwrap() == 5.0

        # Test failed chain (invalid first number)
        result = safe_parse_int("not_a_number").and_then(
            lambda x: safe_parse_int("2").and_then(lambda y: safe_divide(x, y))
        )
        assert result.is_err()
        assert "Invalid integer" in result.unwrap_err()

        # Test failed chain (division by zero)
        result = safe_parse_int("10").and_then(
            lambda x: safe_parse_int("0").and_then(lambda y: safe_divide(x, y))
        )
        assert result.is_err()
        assert "Division by zero" in result.unwrap_err()

    def test_error_recovery(self):
        """Test error recovery patterns."""

        def risky_operation(value: int) -> Result[str, str]:
            if value < 0:
                return Err("Negative value")
            return Ok(f"Success: {value}")

        def fallback_operation(error: str) -> Result[str, str]:
            return Ok("Fallback result")

        # Test successful operation
        result = risky_operation(5)
        final = result.or_else(fallback_operation)
        assert final.is_ok()
        assert final.unwrap() == "Success: 5"

        # Test error recovery
        result = risky_operation(-1)
        final = result.or_else(fallback_operation)
        assert final.is_ok()
        assert final.unwrap() == "Fallback result"

    def test_multiple_error_types(self):
        """Test handling multiple error types."""

        def complex_operation(x: int) -> Result[str, str]:
            if x < 0:
                return Err("NEGATIVE_ERROR")
            elif x == 0:
                return Err("ZERO_ERROR")
            elif x > 100:
                return Err("TOO_LARGE_ERROR")
            else:
                return Ok(f"Valid: {x}")

        # Test different error cases
        assert complex_operation(-1).unwrap_err() == "NEGATIVE_ERROR"
        assert complex_operation(0).unwrap_err() == "ZERO_ERROR"
        assert complex_operation(101).unwrap_err() == "TOO_LARGE_ERROR"
        assert complex_operation(50).unwrap() == "Valid: 50"


if __name__ == "__main__":
    pytest.main([__file__])
