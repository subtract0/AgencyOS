# Sample test for fib.py

def test_fib_iter_zero():
    from fib import fib_iter
    assert fib_iter(0) == 0

def test_fib_iter_five():
    from fib import fib_iter
    assert fib_iter(5) == 5
