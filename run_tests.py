#!/usr/bin/env python3
"""
Test Runner for Agency Code Agency
Runs all tests using pytest framework
"""

import os
import subprocess
import sys
from pathlib import Path


def main(test_mode="unit"):
    # RECURSION GUARD: Prevent nested test runs
    if os.environ.get("AGENCY_NESTED_TEST") == "1":
        print("⚠️  Nested test run detected; exiting to prevent recursion.")
        sys.exit(0)
    """Run tests using pytest with specified mode

    Args:
        test_mode: "unit", "integration", or "all"
    """
    print("=" * 60)
    print("AGENCY CODE AGENCY - TEST RUNNER")
    print("=" * 60)

    # Display test mode
    mode_descriptions = {
        "unit": "Unit Tests Only (excluding integration tests)",
        "integration": "Integration Tests Only",
        "all": "All Tests (Unit + Integration)"
    }
    print(f"\n🎯 Test Mode: {mode_descriptions.get(test_mode, test_mode)}")
    print("-" * 40)

    # Change to the project root directory
    project_root = Path(__file__).resolve().parent
    os.chdir(project_root)

    # Install dependencies first
    print("\n📦 Installing test dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True,
            text=True,
        )
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return 1

    # Run pytest with verbose output
    print("\n🧪 Running tests with pytest...")
    print("-" * 40)

    # Pytest arguments for comprehensive testing
    pytest_args = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",  # Test directory
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "--durations=10",  # Show 10 slowest tests
        # "-x",  # Stop on first failure - commented out to run all tests
        "--color=yes",  # Colored output
    ]

    # Add marker selection based on test mode
    if test_mode == "unit":
        pytest_args.extend(["-m", "not integration"])
    elif test_mode == "integration":
        pytest_args.extend(["-m", "integration"])
    # For "all" mode, no marker filtering is applied

    try:
        # Set environment variable to prevent nested test runs
        env = os.environ.copy()
        env["AGENCY_NESTED_TEST"] = "1"
        result = subprocess.run(pytest_args, check=False, env=env)

        print("\n" + "=" * 60)
        print("TEST EXECUTION COMPLETE")
        print("=" * 60)

        if result.returncode == 0:
            print("✅ All tests passed!")
            print("\n📊 Test Summary:")
            print(f"- {mode_descriptions.get(test_mode, test_mode)} executed successfully")
            print("- No failures or errors detected")
            print("- Agency Code Agency is ready for use")
        else:
            print("❌ Some tests failed!")
            print(f"Exit code: {result.returncode}")
            print(f"\n🔧 Troubleshooting ({test_mode} tests):")
            print("- Check the output above for specific test failures")
            print("- Ensure all dependencies are installed correctly")
            print("- Verify environment variables are set (if needed)")
            print("- Check that all tool files are present in agency_code_agent/tools/")
            if test_mode == "integration":
                print("- Integration tests may require additional setup or services")

        return result.returncode

    except FileNotFoundError:
        print("❌ pytest not found! Installing pytest...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"],
                check=True,
            )
            print("✅ pytest installed. Please run again.")
            return 1
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install pytest: {e}")
            return 1

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


def run_specific_test(test_name):
    """Run a specific test file or test function"""
    print("=" * 60)
    print("AGENCY CODE AGENCY - SPECIFIC TEST RUNNER")
    print("=" * 60)
    print(f"\n🧪 Running specific test: {test_name}")
    print("-" * 40)

    pytest_args = [
        sys.executable,
        "-m",
        "pytest",
        f"tests/{test_name}" if not test_name.startswith("tests/") else test_name,
        "-v",
        "--tb=short",
        "--color=yes",
    ]

    try:
        # Set environment variable to prevent nested test runs
        env = os.environ.copy()
        env["AGENCY_NESTED_TEST"] = "1"
        result = subprocess.run(pytest_args, check=False, env=env)

        print("\n" + "=" * 60)
        print("SPECIFIC TEST EXECUTION COMPLETE")
        print("=" * 60)

        if result.returncode == 0:
            print("✅ Specific test passed!")
        else:
            print("❌ Specific test failed!")
            print(f"Exit code: {result.returncode}")

        return result.returncode
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return 1


def print_usage():
    """Print usage information"""
    print("Usage: python run_tests.py [OPTIONS] [SPECIFIC_TEST]")
    print("\nOptions:")
    print("  --run-integration    Run ONLY integration tests")
    print("  --run-all           Run ALL tests (unit + integration)")
    print("  --help              Show this help message")
    print("\nDefault behavior:")
    print("  - Runs unit tests only (excludes integration tests)")
    print("\nExamples:")
    print("  python run_tests.py                    # Run unit tests only")
    print("  python run_tests.py --run-integration  # Run integration tests only")
    print("  python run_tests.py --run-all          # Run all tests")
    print("  python run_tests.py test_specific.py   # Run specific test file")


if __name__ == "__main__":
    # Parse command line arguments
    test_mode = "unit"  # Default to unit tests only
    specific_test = None

    # Check for command line options
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg in ["--help", "-h"]:
            print_usage()
            sys.exit(0)
        elif arg == "--run-integration":
            test_mode = "integration"
        elif arg == "--run-all":
            test_mode = "all"
        elif arg.startswith("--"):
            print(f"❌ Unknown option: {arg}")
            print_usage()
            sys.exit(1)
        else:
            # Treat as specific test file
            specific_test = arg

    # Execute the appropriate test mode
    if specific_test:
        exit_code = run_specific_test(specific_test)
    else:
        exit_code = main(test_mode)

    sys.exit(exit_code)
