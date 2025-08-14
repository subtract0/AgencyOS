"""Simple Fibonacci utilities.

Provides:
- fib_recursive(n): simple recursive implementation (for demonstration)
- fib_iter(n): efficient iterative implementation
- __main__ command-line interface to print first n Fibonacci numbers or the nth value

Usage:
    python fib.py 10   # prints Fibonacci numbers up to index 10 (0-indexed)
    python fib.py -v 10  # prints only the 10th Fibonacci number
"""

import sys
from typing import List


def fib_recursive(n: int) -> int:
    """Return the nth Fibonacci number using recursion.

    Note: exponential time, not for large n.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    return fib_recursive(n - 1) + fib_recursive(n - 2)


def fib_iter(n: int) -> int:
    """Return the nth Fibonacci number using an iterative approach."""
    if n < 0:
        raise ValueError("n must be non-negative")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def fib_sequence(n: int) -> List[int]:
    """Return a list of Fibonacci numbers from F0 up to Fn (inclusive)."""
    if n < 0:
        raise ValueError("n must be non-negative")
    seq = [0]
    if n == 0:
        return seq
    seq.append(1)
    for i in range(2, n + 1):
        seq.append(seq[-1] + seq[-2])
    return seq


def main(argv=None):
    argv = argv or sys.argv[1:]
    verbose = False
    if not argv:
        print("Usage: python fib.py [-v] N")
        return 1
    if argv[0] == "-v":
        verbose = True
        argv = argv[1:]
    try:
        n = int(argv[0])
    except (IndexError, ValueError):
        print("Please provide a non-negative integer N.")
        return 2
    if n < 0:
        print("N must be non-negative.")
        return 3

    if verbose:
        print(fib_iter(n))
    else:
        seq = fib_sequence(n)
        print(", ".join(str(x) for x in seq))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
