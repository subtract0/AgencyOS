import pytest

from fib import fib


def test_fib_basic():
    assert fib(0) == 0
    assert fib(1) == 1
    assert fib(5) == 5
    assert fib(10) == 55
