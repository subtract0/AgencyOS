"""
Basic tests for calculator - intentionally incomplete for demonstration.
"""

import pytest
from calculator import Calculator

def test_add() -> None:
    calc = Calculator()
    assert calc.add(2, 3) == 5
    assert calc.add(-1, 1) == 0

def test_divide() -> None:
    calc = Calculator()
    assert calc.divide(10, 2) == 5

def test_divide_by_zero() -> None:
    calc = Calculator()
    with pytest.raises(ValueError):
        calc.divide(10, 0)