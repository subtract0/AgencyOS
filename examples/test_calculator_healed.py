"""
Tests for calculator.py - NECESSARY-compliant comprehensive test suite.
Generated to address quality violations and improve Q(T) score from 0.655 to 0.85+.

NECESSARY Pattern Coverage:
N - No Missing Behaviors: All 13 behaviors tested
E - Edge Cases Covered: Boundary conditions for all operations
C - Comprehensive Coverage: Multiple test vectors per behavior
E - Error Conditions: Exception paths and invalid inputs
S - State Validation: Memory and history state verification
S - Side Effects: History tracking verification
A - Async Operations: N/A (no async operations)
R - Regression Prevention: Common bug scenarios covered
Y - Yielding Confidence: Clear, meaningful test cases
"""

import pytest
import math
from calculator import Calculator


class TestCalculatorBasicOperations:
    """Test basic arithmetic operations."""

    def test_add_positive_numbers(self):
        """Test addition with positive numbers."""
        calc = Calculator()
        result = calc.add(2, 3)
        assert result == 5
        assert "add(2, 3) = 5" in calc.get_history()

    def test_add_negative_numbers(self):
        """Test addition with negative numbers."""
        calc = Calculator()
        assert calc.add(-5, -3) == -8
        assert calc.add(-5, 3) == -2
        assert calc.add(5, -3) == 2

    def test_add_with_zero(self):
        """Test addition with zero (identity element)."""
        calc = Calculator()
        assert calc.add(0, 0) == 0
        assert calc.add(5, 0) == 5
        assert calc.add(0, 5) == 5

    def test_add_large_numbers(self):
        """Test addition with large numbers."""
        calc = Calculator()
        assert calc.add(1000000, 2000000) == 3000000
        assert calc.add(999999999, 1) == 1000000000

    def test_subtract_basic(self):
        """Test basic subtraction."""
        calc = Calculator()
        result = calc.subtract(10, 4)
        assert result == 6
        assert "subtract(10, 4) = 6" in calc.get_history()

    def test_subtract_negative_result(self):
        """Test subtraction resulting in negative number."""
        calc = Calculator()
        assert calc.subtract(3, 7) == -4

    def test_subtract_with_zero(self):
        """Test subtraction with zero."""
        calc = Calculator()
        assert calc.subtract(5, 0) == 5
        assert calc.subtract(0, 5) == -5
        assert calc.subtract(0, 0) == 0

    def test_subtract_negative_numbers(self):
        """Test subtraction with negative numbers."""
        calc = Calculator()
        assert calc.subtract(-5, -3) == -2
        assert calc.subtract(-5, 3) == -8
        assert calc.subtract(5, -3) == 8

    def test_multiply_positive_numbers(self):
        """Test multiplication with positive numbers."""
        calc = Calculator()
        result = calc.multiply(4, 5)
        assert result == 20
        assert "multiply(4, 5) = 20" in calc.get_history()

    def test_multiply_with_zero(self):
        """Test multiplication with zero (absorbing element)."""
        calc = Calculator()
        assert calc.multiply(0, 5) == 0
        assert calc.multiply(5, 0) == 0
        assert calc.multiply(0, 0) == 0

    def test_multiply_with_one(self):
        """Test multiplication with one (identity element)."""
        calc = Calculator()
        assert calc.multiply(1, 5) == 5
        assert calc.multiply(5, 1) == 5
        assert calc.multiply(1, 1) == 1

    def test_multiply_negative_numbers(self):
        """Test multiplication with negative numbers."""
        calc = Calculator()
        assert calc.multiply(-3, 4) == -12
        assert calc.multiply(3, -4) == -12
        assert calc.multiply(-3, -4) == 12

    def test_multiply_fractions(self):
        """Test multiplication with fractional numbers."""
        calc = Calculator()
        assert calc.multiply(0.5, 4) == 2.0
        assert calc.multiply(2.5, 2) == 5.0

    def test_divide_basic(self):
        """Test basic division."""
        calc = Calculator()
        result = calc.divide(10, 2)
        assert result == 5.0
        assert "divide(10, 2) = 5.0" in calc.get_history()

    def test_divide_with_remainder(self):
        """Test division with remainder (float result)."""
        calc = Calculator()
        result = calc.divide(7, 2)
        assert result == 3.5

    def test_divide_by_one(self):
        """Test division by one (identity)."""
        calc = Calculator()
        assert calc.divide(5, 1) == 5.0
        assert calc.divide(-5, 1) == -5.0

    def test_divide_negative_numbers(self):
        """Test division with negative numbers."""
        calc = Calculator()
        assert calc.divide(-10, 2) == -5.0
        assert calc.divide(10, -2) == -5.0
        assert calc.divide(-10, -2) == 5.0

    def test_divide_by_zero_error(self):
        """Test division by zero raises ValueError."""
        calc = Calculator()
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calc.divide(10, 0)

        # Verify no history entry was added for failed operation
        assert len(calc.get_history()) == 0

    def test_power_basic(self):
        """Test basic power operations."""
        calc = Calculator()
        result = calc.power(2, 3)
        assert result == 8
        assert "power(2, 3) = 8" in calc.get_history()

    def test_power_with_zero_exponent(self):
        """Test power with zero exponent (any number to power 0 = 1)."""
        calc = Calculator()
        assert calc.power(5, 0) == 1
        assert calc.power(-5, 0) == 1
        assert calc.power(0, 0) == 1

    def test_power_with_one_exponent(self):
        """Test power with exponent 1 (identity)."""
        calc = Calculator()
        assert calc.power(5, 1) == 5
        assert calc.power(-5, 1) == -5

    def test_power_negative_exponent(self):
        """Test power with negative exponents."""
        calc = Calculator()
        assert calc.power(2, -3) == 0.125
        assert calc.power(4, -2) == 0.0625

    def test_power_fractional_exponent(self):
        """Test power with fractional exponents."""
        calc = Calculator()
        assert calc.power(9, 0.5) == 3.0
        assert calc.power(8, 1/3) == pytest.approx(2.0, rel=1e-10)


class TestCalculatorMemoryOperations:
    """Test memory-related operations."""

    def test_store_in_memory_basic(self):
        """Test storing values in memory."""
        calc = Calculator()
        calc.store_in_memory(42)
        assert calc.memory == 42
        assert "stored 42 in memory" in calc.get_history()

    def test_store_in_memory_overwrite(self):
        """Test overwriting memory values."""
        calc = Calculator()
        calc.store_in_memory(10)
        calc.store_in_memory(20)
        assert calc.memory == 20

    def test_store_negative_in_memory(self):
        """Test storing negative values in memory."""
        calc = Calculator()
        calc.store_in_memory(-15)
        assert calc.memory == -15

    def test_store_float_in_memory(self):
        """Test storing float values in memory."""
        calc = Calculator()
        calc.store_in_memory(3.14159)
        assert calc.memory == 3.14159

    def test_recall_memory_basic(self):
        """Test recalling values from memory."""
        calc = Calculator()
        calc.store_in_memory(99)
        result = calc.recall_memory()
        assert result == 99
        assert "recalled 99 from memory" in calc.get_history()

    def test_recall_memory_initial_state(self):
        """Test recalling from memory in initial state (should be 0)."""
        calc = Calculator()
        result = calc.recall_memory()
        assert result == 0
        assert "recalled 0 from memory" in calc.get_history()

    def test_clear_memory_basic(self):
        """Test clearing memory."""
        calc = Calculator()
        calc.store_in_memory(55)
        calc.clear_memory()
        assert calc.memory == 0
        assert "cleared memory" in calc.get_history()

    def test_clear_memory_already_zero(self):
        """Test clearing memory when already zero."""
        calc = Calculator()
        calc.clear_memory()
        assert calc.memory == 0

    def test_memory_operations_sequence(self):
        """Test sequence of memory operations."""
        calc = Calculator()
        # Store, recall, clear, recall sequence
        calc.store_in_memory(100)
        assert calc.recall_memory() == 100
        calc.clear_memory()
        assert calc.recall_memory() == 0


class TestCalculatorHistoryOperations:
    """Test history-related operations."""

    def test_get_history_initial_state(self):
        """Test getting history in initial state."""
        calc = Calculator()
        history = calc.get_history()
        assert history == []
        assert isinstance(history, list)

    def test_get_history_returns_copy(self):
        """Test that get_history returns a copy, not reference."""
        calc = Calculator()
        calc.add(1, 2)
        history1 = calc.get_history()
        history2 = calc.get_history()

        # Modify one copy
        history1.append("modified")

        # Other copy should be unchanged
        assert "modified" not in history2
        assert "modified" not in calc.get_history()

    def test_get_history_with_operations(self):
        """Test getting history after various operations."""
        calc = Calculator()
        calc.add(2, 3)
        calc.multiply(4, 5)
        calc.store_in_memory(10)

        history = calc.get_history()
        assert len(history) == 3
        assert "add(2, 3) = 5" in history
        assert "multiply(4, 5) = 20" in history
        assert "stored 10 in memory" in history

    def test_clear_history_basic(self):
        """Test clearing history."""
        calc = Calculator()
        calc.add(1, 2)
        calc.subtract(5, 3)
        calc.clear_history()

        assert calc.get_history() == []

    def test_clear_history_empty(self):
        """Test clearing already empty history."""
        calc = Calculator()
        calc.clear_history()
        assert calc.get_history() == []

    def test_history_persistence_after_clear(self):
        """Test that new operations create history after clearing."""
        calc = Calculator()
        calc.add(1, 2)
        calc.clear_history()
        calc.multiply(3, 4)

        history = calc.get_history()
        assert len(history) == 1
        assert "multiply(3, 4) = 12" in history
        assert "add(1, 2) = 3" not in history


class TestCalculatorSpecialOperations:
    """Test special mathematical operations."""

    def test_calculate_percentage_basic(self):
        """Test basic percentage calculations."""
        calc = Calculator()
        result = calc.calculate_percentage(200, 50)
        assert result == 100.0
        assert "percentage(200, 50%) = 100.0" in calc.get_history()

    def test_calculate_percentage_zero_value(self):
        """Test percentage of zero."""
        calc = Calculator()
        assert calc.calculate_percentage(0, 50) == 0.0

    def test_calculate_percentage_zero_percent(self):
        """Test zero percentage."""
        calc = Calculator()
        assert calc.calculate_percentage(100, 0) == 0.0

    def test_calculate_percentage_hundred_percent(self):
        """Test 100% calculation."""
        calc = Calculator()
        assert calc.calculate_percentage(75, 100) == 75.0

    def test_calculate_percentage_over_hundred(self):
        """Test percentage over 100%."""
        calc = Calculator()
        assert calc.calculate_percentage(50, 150) == 75.0

    def test_calculate_percentage_decimal(self):
        """Test percentage with decimal values."""
        calc = Calculator()
        result = calc.calculate_percentage(33.33, 10)
        assert result == pytest.approx(3.333, rel=1e-3)

    def test_square_root_basic(self):
        """Test basic square root calculations."""
        calc = Calculator()
        result = calc.square_root(16)
        assert result == 4.0
        assert "sqrt(16) = 4.0" in calc.get_history()

    def test_square_root_perfect_squares(self):
        """Test square root of perfect squares."""
        calc = Calculator()
        assert calc.square_root(0) == 0.0
        assert calc.square_root(1) == 1.0
        assert calc.square_root(4) == 2.0
        assert calc.square_root(9) == 3.0
        assert calc.square_root(25) == 5.0

    def test_square_root_non_perfect_squares(self):
        """Test square root of non-perfect squares."""
        calc = Calculator()
        assert calc.square_root(2) == pytest.approx(1.414213562, rel=1e-9)
        assert calc.square_root(3) == pytest.approx(1.732050808, rel=1e-9)
        assert calc.square_root(10) == pytest.approx(3.162277660, rel=1e-9)

    def test_square_root_decimal_input(self):
        """Test square root of decimal numbers."""
        calc = Calculator()
        assert calc.square_root(0.25) == 0.5
        assert calc.square_root(6.25) == 2.5

    def test_square_root_negative_error(self):
        """Test square root of negative number raises ValueError."""
        calc = Calculator()
        with pytest.raises(ValueError, match="Cannot calculate square root of negative number"):
            calc.square_root(-1)

        # Verify no history entry was added for failed operation
        assert len(calc.get_history()) == 0


class TestCalculatorStateValidation:
    """Test state validation and object integrity."""

    def test_initial_state(self):
        """Test calculator initial state."""
        calc = Calculator()
        assert calc.memory == 0
        assert calc.history == []

    def test_state_independence_multiple_instances(self):
        """Test that multiple calculator instances maintain independent state."""
        calc1 = Calculator()
        calc2 = Calculator()

        calc1.store_in_memory(10)
        calc1.add(2, 3)

        # calc2 should be unaffected
        assert calc2.memory == 0
        assert calc2.get_history() == []

    def test_memory_state_persistence(self):
        """Test memory state persists across operations."""
        calc = Calculator()
        calc.store_in_memory(42)

        # Perform other operations
        calc.add(1, 2)
        calc.multiply(3, 4)

        # Memory should still be 42
        assert calc.memory == 42

    def test_history_state_accumulation(self):
        """Test history accumulates correctly."""
        calc = Calculator()
        initial_count = len(calc.get_history())

        calc.add(1, 2)
        assert len(calc.get_history()) == initial_count + 1

        calc.subtract(5, 3)
        assert len(calc.get_history()) == initial_count + 2

        calc.store_in_memory(10)
        assert len(calc.get_history()) == initial_count + 3


class TestCalculatorEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_large_numbers(self):
        """Test operations with very large numbers."""
        calc = Calculator()
        large_num = 10**15
        assert calc.add(large_num, 1) == large_num + 1
        assert calc.multiply(large_num, 2) == large_num * 2

    def test_very_small_numbers(self):
        """Test operations with very small numbers."""
        calc = Calculator()
        small_num = 10**-15
        result = calc.add(small_num, small_num)
        assert result == pytest.approx(2 * small_num, rel=1e-10)

    def test_floating_point_precision(self):
        """Test floating point precision edge cases."""
        calc = Calculator()
        # Classic floating point precision test
        result = calc.add(0.1, 0.2)
        assert result == pytest.approx(0.3, rel=1e-10)

    def test_zero_division_variants(self):
        """Test various zero division scenarios."""
        calc = Calculator()

        with pytest.raises(ValueError):
            calc.divide(0, 0)

        with pytest.raises(ValueError):
            calc.divide(1, 0)

        with pytest.raises(ValueError):
            calc.divide(-1, 0)

        with pytest.raises(ValueError):
            calc.divide(float('inf'), 0)

    def test_power_edge_cases(self):
        """Test power operation edge cases."""
        calc = Calculator()

        # Zero to positive power
        assert calc.power(0, 5) == 0

        # Negative base with even exponent
        assert calc.power(-2, 2) == 4

        # Negative base with odd exponent
        assert calc.power(-2, 3) == -8

    def test_square_root_edge_cases(self):
        """Test square root edge cases."""
        calc = Calculator()

        # Square root of very small positive number
        assert calc.square_root(1e-10) == pytest.approx(1e-5, rel=1e-15)

        # Square root of very large number
        large_sqrt = calc.square_root(1e20)
        assert large_sqrt == pytest.approx(1e10, rel=1e-10)


class TestCalculatorComprehensiveCoverage:
    """Comprehensive test scenarios combining multiple operations."""

    def test_arithmetic_operation_sequence(self):
        """Test sequence of arithmetic operations."""
        calc = Calculator()

        # Complex calculation: ((2 + 3) * 4) ^ 2 / 10
        result1 = calc.add(2, 3)       # 5
        result2 = calc.multiply(result1, 4)  # 20
        result3 = calc.power(result2, 2)     # 400
        result4 = calc.divide(result3, 10)   # 40.0

        assert result4 == 40.0
        assert len(calc.get_history()) == 4

    def test_memory_calculation_workflow(self):
        """Test workflow involving memory operations."""
        calc = Calculator()

        # Calculate and store intermediate result
        intermediate = calc.add(10, 5)     # 15
        calc.store_in_memory(intermediate)

        # Perform other calculations
        calc.multiply(3, 4)                # 12

        # Use stored value
        stored = calc.recall_memory()      # 15
        final = calc.add(stored, 25)       # 40

        assert final == 40
        assert calc.memory == 15

    def test_percentage_calculation_scenarios(self):
        """Test realistic percentage calculation scenarios."""
        calc = Calculator()

        # Tax calculation: 15% of $120
        tax = calc.calculate_percentage(120, 15)
        assert tax == 18.0

        # Discount calculation: 25% off $80
        discount = calc.calculate_percentage(80, 25)
        total = calc.subtract(80, discount)
        assert total == 60.0

    def test_complex_mathematical_expressions(self):
        """Test complex mathematical expressions."""
        calc = Calculator()

        # Calculate: sqrt(169) + 20% of 50 - 3^2
        sqrt_result = calc.square_root(169)        # 13.0
        percentage_result = calc.calculate_percentage(50, 20)  # 10.0
        power_result = calc.power(3, 2)            # 9

        step1 = calc.add(sqrt_result, percentage_result)  # 23.0
        final = calc.subtract(step1, power_result)         # 14.0

        assert final == 14.0

    def test_history_tracking_accuracy(self):
        """Test accuracy of history tracking across operations."""
        calc = Calculator()

        calc.add(1, 1)
        calc.subtract(5, 2)
        calc.multiply(3, 3)
        calc.divide(8, 2)
        calc.power(2, 4)
        calc.store_in_memory(100)
        calc.recall_memory()
        calc.clear_memory()
        calc.calculate_percentage(200, 10)
        calc.square_root(64)

        history = calc.get_history()
        assert len(history) == 10

        # Verify specific entries exist
        expected_entries = [
            "add(1, 1) = 2",
            "subtract(5, 2) = 3",
            "multiply(3, 3) = 9",
            "divide(8, 2) = 4.0",
            "power(2, 4) = 16",
            "stored 100 in memory",
            "recalled 100 from memory",
            "cleared memory",
            "percentage(200, 10%) = 20.0",
            "sqrt(64) = 8.0"
        ]

        for entry in expected_entries:
            assert entry in history


class TestCalculatorErrorHandling:
    """Test error handling and exception scenarios."""

    def test_type_safety_operations(self):
        """Test operations maintain type safety (Python duck typing allows various numeric types)."""
        calc = Calculator()

        # Test with different numeric types
        assert calc.add(1, 2.5) == 3.5  # int + float
        assert calc.multiply(2, True) == 2  # int + bool (True = 1)
        assert calc.power(2.0, 3) == 8.0  # float ** int

    def test_infinity_handling(self):
        """Test handling of infinity values."""
        calc = Calculator()

        # Python allows infinity in calculations
        inf = float('inf')
        assert calc.add(inf, 1) == inf
        assert calc.multiply(inf, 2) == inf
        assert calc.subtract(inf, inf) != calc.subtract(inf, inf)  # NaN != NaN

    def test_nan_handling(self):
        """Test handling of NaN (Not a Number) values."""
        calc = Calculator()

        nan = float('nan')
        result = calc.add(nan, 5)
        assert math.isnan(result)

    def test_operation_atomicity(self):
        """Test that failed operations don't corrupt state."""
        calc = Calculator()

        # Perform successful operation
        calc.add(2, 3)
        initial_history_length = len(calc.get_history())

        # Attempt operations that should fail
        try:
            calc.divide(10, 0)
        except ValueError:
            pass

        try:
            calc.square_root(-1)
        except ValueError:
            pass

        # History should not contain failed operations
        assert len(calc.get_history()) == initial_history_length

        # Subsequent operations should still work
        calc.multiply(4, 5)
        assert len(calc.get_history()) == initial_history_length + 1


class TestCalculatorRegressionPrevention:
    """Test scenarios that prevent common regression bugs."""

    def test_division_result_type_consistency(self):
        """Ensure division always returns float (prevents integer division bugs)."""
        calc = Calculator()

        assert isinstance(calc.divide(4, 2), float)
        assert isinstance(calc.divide(5, 2), float)
        assert calc.divide(4, 2) == 2.0  # Not 2
        assert calc.divide(5, 2) == 2.5

    def test_power_operation_precedence(self):
        """Test power operation handles precedence correctly."""
        calc = Calculator()

        # Test that 2^3^2 is calculated as 2^(3^2) = 2^9 = 512, not (2^3)^2 = 8^2 = 64
        # Note: Python's ** is right-associative, but our function is binary
        inner = calc.power(3, 2)  # 9
        result = calc.power(2, inner)  # 2^9 = 512
        assert result == 512

    def test_memory_operation_isolation(self):
        """Ensure memory operations don't interfere with calculations."""
        calc = Calculator()

        # Store something in memory
        calc.store_in_memory(999)

        # Perform calculations
        result = calc.add(2, 3)

        # Memory should be unchanged
        assert calc.recall_memory() == 999
        assert result == 5

    def test_floating_point_comparison_safety(self):
        """Test that floating point results are handled safely."""
        calc = Calculator()

        # Operations that might have precision issues
        result1 = calc.divide(1, 3)
        result2 = calc.multiply(result1, 3)

        # Should be very close to 1, but might not be exactly 1
        assert result2 == pytest.approx(1.0, rel=1e-10)

    def test_history_memory_leak_prevention(self):
        """Test that history doesn't cause memory leaks with large operations."""
        calc = Calculator()

        # Perform many operations
        for i in range(100):
            calc.add(i, i+1)

        # History should contain exactly 100 entries
        assert len(calc.get_history()) == 100

        # Clear should work properly
        calc.clear_history()
        assert len(calc.get_history()) == 0

    def test_zero_handling_consistency(self):
        """Test consistent handling of zero across all operations."""
        calc = Calculator()

        # Zero should behave consistently
        assert calc.add(0, 5) == 5
        assert calc.subtract(0, 5) == -5
        assert calc.multiply(0, 5) == 0
        assert calc.power(0, 5) == 0
        assert calc.square_root(0) == 0.0
        assert calc.calculate_percentage(0, 50) == 0.0
        assert calc.calculate_percentage(100, 0) == 0.0


# Additional confidence-building tests
class TestCalculatorConfidenceBuilding:
    """Tests that build confidence in the calculator's reliability."""

    def test_mathematical_identities(self):
        """Test fundamental mathematical identities."""
        calc = Calculator()

        # Additive identity: a + 0 = a
        assert calc.add(42, 0) == 42

        # Multiplicative identity: a * 1 = a
        assert calc.multiply(42, 1) == 42

        # Multiplicative zero: a * 0 = 0
        assert calc.multiply(42, 0) == 0

        # Square root of square: sqrt(a^2) = |a| for a >= 0
        assert calc.square_root(calc.power(5, 2)) == 5.0

    def test_inverse_operations(self):
        """Test that inverse operations cancel each other."""
        calc = Calculator()

        # Addition and subtraction
        original = 42
        result = calc.subtract(calc.add(original, 10), 10)
        assert result == original

        # Multiplication and division
        result = calc.divide(calc.multiply(original, 5), 5)
        assert result == float(original)

        # Power and square root (for perfect squares)
        result = calc.square_root(calc.power(7, 2))
        assert result == 7.0

    def test_commutative_properties(self):
        """Test commutative properties of operations."""
        calc = Calculator()

        # Addition: a + b = b + a
        assert calc.add(3, 7) == calc.add(7, 3)

        # Multiplication: a * b = b * a
        assert calc.multiply(4, 6) == calc.multiply(6, 4)

    def test_real_world_scenarios(self):
        """Test realistic usage scenarios."""
        calc = Calculator()

        # Calculate compound interest: P(1 + r)^t where P=1000, r=0.05, t=2
        principal = 1000
        rate = 0.05
        time = 2

        growth_factor = calc.add(1, rate)  # 1.05
        compound_growth = calc.power(growth_factor, time)  # 1.1025
        final_amount = calc.multiply(principal, compound_growth)  # 1102.5

        assert final_amount == 1102.5

    def test_boundary_value_analysis(self):
        """Test boundary values systematically."""
        calc = Calculator()

        # Test around zero
        assert calc.add(-1, 1) == 0
        assert calc.multiply(0, 999999) == 0
        assert calc.power(0, 1) == 0

        # Test around one
        assert calc.divide(5, 5) == 1.0
        assert calc.power(999, 0) == 1
        assert calc.square_root(1) == 1.0