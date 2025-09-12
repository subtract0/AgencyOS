#!/usr/bin/env python3
"""
Test Runner for Agency Code Agency
Runs all tests using pytest framework
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Run all tests using pytest"""
    print("=" * 60)
    print("AGENCY CODE AGENCY - TEST RUNNER")
    print("=" * 60)

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

    try:
        result = subprocess.run(pytest_args, check=False)

        print("\n" + "=" * 60)
        print("TEST EXECUTION COMPLETE")
        print("=" * 60)

        if result.returncode == 0:
            print("✅ All tests passed!")
            print("\n📊 Test Summary:")
            print("- All test suites executed successfully")
            print("- No failures or errors detected")
            print("- Agency Code Agency is ready for use")
        else:
            print("❌ Some tests failed!")
            print(f"Exit code: {result.returncode}")
            print("\n🔧 Troubleshooting:")
            print("- Check the output above for specific test failures")
            print("- Ensure all dependencies are installed correctly")
            print("- Verify environment variables are set (if needed)")
            print("- Check that all tool files are present in agency_code_agent/tools/")

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
    print(f"🧪 Running specific test: {test_name}")

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
        result = subprocess.run(pytest_args, check=False)
        return result.returncode
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test if provided as argument
        test_arg = sys.argv[1]
        exit_code = run_specific_test(test_arg)
    else:
        # Run all tests
        exit_code = main()

    sys.exit(exit_code)
