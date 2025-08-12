#!/usr/bin/env python3
"""
A simple Fibonacci calculator.

Usage examples:
  python fib.py 10      # prints the 10th Fibonacci number (55)
"""

import argparse
import sys
from typing import Optional


def fib(n: int) -> int:
    """Return the n-th Fibonacci number (F0=0, F1=1).

    Uses an iterative approach for O(n) time and O(1) space.
    """
    if n < 0:
        raise ValueError("n must be a non-negative integer")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Calculate the n-th Fibonacci number.")
    parser.add_argument("n", type=int, help="Index n (non-negative integer)")
    args = parser.parse_args(argv)

    try:
        print(fib(args.n))
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
