"""
Simple calculator module for demonstration.
This module intentionally has limited test coverage to demonstrate CodeHealer capabilities.
"""

from typing import List, Union

Number = Union[int, float]

class Calculator:
    """A basic calculator implementation."""

    def __init__(self) -> None:
        """Initialize the calculator with memory."""
        self.memory: Number = 0
        self.history: List[str] = []

    def add(self, a: Number, b: Number) -> Number:
        """Add two numbers."""
        result = a + b
        self.history.append(f"add({a}, {b}) = {result}")
        return result

    def subtract(self, a: Number, b: Number) -> Number:
        """Subtract b from a."""
        result = a - b
        self.history.append(f"subtract({a}, {b}) = {result}")
        return result

    def multiply(self, a: Number, b: Number) -> Number:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"multiply({a}, {b}) = {result}")
        return result

    def divide(self, a: Number, b: Number) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self.history.append(f"divide({a}, {b}) = {result}")
        return result

    def power(self, base: Number, exponent: Number) -> Number:
        """Raise base to the power of exponent."""
        result = base ** exponent
        self.history.append(f"power({base}, {exponent}) = {result}")
        return result

    def store_in_memory(self, value: Number) -> None:
        """Store a value in memory."""
        self.memory = float(value)  # Convert to ensure type compatibility
        self.history.append(f"stored {value} in memory")

    def recall_memory(self) -> Number:
        """Recall the value from memory."""
        self.history.append(f"recalled {self.memory} from memory")
        return self.memory

    def clear_memory(self) -> None:
        """Clear the memory."""
        self.memory = 0
        self.history.append("cleared memory")

    def get_history(self) -> List[str]:
        """Get the calculation history."""
        return self.history.copy()

    def clear_history(self) -> None:
        """Clear the calculation history."""
        self.history = []

    def calculate_percentage(self, value: Number, percentage: Number) -> float:
        """Calculate percentage of a value."""
        result = (value * percentage) / 100
        self.history.append(f"percentage({value}, {percentage}%) = {result}")
        return result

    def square_root(self, n: Number) -> float:
        """Calculate square root."""
        if n < 0:
            raise ValueError("Cannot calculate square root of negative number")
        result = float(n ** 0.5)
        self.history.append(f"sqrt({n}) = {result}")
        return result