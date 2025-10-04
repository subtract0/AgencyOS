#!/usr/bin/env python3
"""Unified test runner script for Agency OS.

This script provides a unified interface for running tests with health checks,
coverage analysis, and various test execution modes.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_health_check() -> bool:
    """Run test health check."""
    print("🔍 Running test health check...")
    try:
        result = subprocess.run(
            [sys.executable, "scripts/test_health_check.py"],
            cwd=Path(__file__).parent.parent,
            check=False,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def run_tests_with_coverage(
    test_pattern: str | None = None,
    min_coverage: float = 80.0,
    include_slow: bool = False,
    html_report: bool = False,
) -> bool:
    """Run tests with coverage."""
    print("🧪 Running tests with coverage...")

    cmd = [sys.executable, "scripts/test_coverage.py", "--min-coverage", str(min_coverage)]

    if test_pattern:
        cmd.extend(["--test-pattern", test_pattern])

    if include_slow:
        cmd.append("--include-slow")

    if html_report:
        cmd.append("--html")

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Coverage tests failed: {e}")
        return False


def run_fast_tests(test_pattern: str | None = None) -> bool:
    """Run fast tests only."""
    print("⚡ Running fast tests...")

    cmd = [sys.executable, "-m", "pytest", "-m", "not slow and not integration", "-v", "--tb=short"]

    if test_pattern:
        cmd.extend(["-k", test_pattern])

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Fast tests failed: {e}")
        return False


def run_all_tests(test_pattern: str | None = None) -> bool:
    """Run all tests."""
    print("🧪 Running all tests...")

    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]

    if test_pattern:
        cmd.extend(["-k", test_pattern])

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ All tests failed: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Unified test runner for Agency OS")
    parser.add_argument(
        "mode", choices=["health", "fast", "all", "coverage"], help="Test execution mode"
    )
    parser.add_argument("--pattern", type=str, help="Pattern to select specific tests")
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=80.0,
        help="Minimum coverage percentage (for coverage mode)",
    )
    parser.add_argument(
        "--include-slow", action="store_true", help="Include slow tests (for coverage mode)"
    )
    parser.add_argument(
        "--html", action="store_true", help="Generate HTML coverage report (for coverage mode)"
    )
    parser.add_argument(
        "--no-health-check", action="store_true", help="Skip health check before running tests"
    )

    args = parser.parse_args()

    try:
        # Run health check first (unless skipped)
        if not args.no_health_check and args.mode != "health":
            print("🔍 Running preliminary health check...")
            if not run_health_check():
                print("⚠️  Health check found issues, but continuing with tests...")
                print("💡 Run 'python scripts/test_runner.py health' for detailed report")

        # Execute the requested mode
        if args.mode == "health":
            success = run_health_check()
        elif args.mode == "fast":
            success = run_fast_tests(args.pattern)
        elif args.mode == "all":
            success = run_all_tests(args.pattern)
        elif args.mode == "coverage":
            success = run_tests_with_coverage(
                test_pattern=args.pattern,
                min_coverage=args.min_coverage,
                include_slow=args.include_slow,
                html_report=args.html,
            )
        else:
            print(f"❌ Unknown mode: {args.mode}")
            return 1

        if success:
            print(f"✅ {args.mode.capitalize()} mode completed successfully!")
            return 0
        else:
            print(f"❌ {args.mode.capitalize()} mode failed!")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️  Test run interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
