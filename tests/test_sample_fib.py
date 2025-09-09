from fib import fib_iter, fib_sequence


def test_fib_iter_small():
    assert fib_iter(0) == 0
    assert fib_iter(1) == 1
    assert fib_iter(2) == 1
    assert fib_iter(10) == 55


def test_fib_sequence():
    assert fib_sequence(0) == [0]
    assert fib_sequence(1) == [0, 1]
    assert fib_sequence(5) == [0, 1, 1, 2, 3, 5]
