#!/usr/bin/env python3
"""
Cleanup Script for Compiled Files and Caches

Removes:
- Python bytecode files (*.pyc)
- __pycache__ directories
- mypy cache
- pytest cache
- ruff cache

Constitutional Compliance:
- Article III: Automated enforcement (no manual cleanup needed)
- Article II: Zero broken windows (pristine codebase)
"""

import subprocess
import sys
from pathlib import Path


def cleanup_compiled_files(verbose: bool = True) -> int:
    """Remove all compiled files and caches from the repository.

    Args:
        verbose: Print cleanup progress

    Returns:
        0 on success, 1 on error
    """
    repo_root = Path(__file__).parent.parent

    cleanup_commands = [
        # Remove Python bytecode
        ['find', str(repo_root), '-type', 'f', '-name', '*.pyc', '-delete'],
        ['find', str(repo_root), '-type', 'd', '-name', '__pycache__', '-exec', 'rm', '-rf', '{}', '+'],

        # Remove type checker caches
        ['find', str(repo_root), '-type', 'd', '-name', '.mypy_cache', '-exec', 'rm', '-rf', '{}', '+'],
        ['find', str(repo_root), '-type', 'd', '-name', '.pytype', '-exec', 'rm', '-rf', '{}', '+'],

        # Remove test caches
        ['find', str(repo_root), '-type', 'd', '-name', '.pytest_cache', '-exec', 'rm', '-rf', '{}', '+'],
        ['find', str(repo_root), '-type', 'd', '-name', '.hypothesis', '-exec', 'rm', '-rf', '{}', '+'],

        # Remove linter caches
        ['find', str(repo_root), '-type', 'd', '-name', '.ruff_cache', '-exec', 'rm', '-rf', '{}', '+'],
    ]

    if verbose:
        print("🧹 Cleaning compiled files and caches...")

    errors = 0
    for cmd in cleanup_commands:
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            if result.returncode != 0 and result.returncode != 1:  # 1 = no files found (ok)
                if verbose:
                    print(f"⚠️  Warning: {' '.join(cmd)} returned {result.returncode}")
                errors += 1
        except subprocess.TimeoutExpired:
            if verbose:
                print(f"⚠️  Timeout: {' '.join(cmd)}")
            errors += 1
        except Exception as e:
            if verbose:
                print(f"⚠️  Error: {e}")
            errors += 1

    if verbose:
        if errors == 0:
            print("✅ Cleanup complete - repository is pristine")
        else:
            print(f"⚠️  Cleanup completed with {errors} warnings")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    verbose = "--quiet" not in sys.argv
    sys.exit(cleanup_compiled_files(verbose=verbose))
