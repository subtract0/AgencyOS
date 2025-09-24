#!/usr/bin/env python3
"""
Test Runner for Agency Code Agency
Runs all tests using pytest framework
"""

import os
import subprocess
import sys
import signal
import tempfile
import atexit
from pathlib import Path


def main(test_mode="unit"):
    # RECURSION GUARDS: Prevent nested test runs
    if os.environ.get("AGENCY_NESTED_TEST") == "1":
        print("⚠️  Nested test run detected; exiting to prevent recursion.")
        sys.exit(0)

    if "PYTEST_CURRENT_TEST" in os.environ:
        print("⚠️  Running inside pytest process; exiting to prevent recursion.")
        sys.exit(0)

    # SINGLE INSTANCE LOCK: Prevent overlapping test runs
    pid_file = Path(tempfile.gettempdir()) / "agency_test_runner.pid"

    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            # Check if process is still running
            os.kill(old_pid, 0)  # Will raise OSError if process doesn't exist
            print(f"⚠️  Another test run is already active (PID: {old_pid})")
            print("   Wait for it to complete or kill it manually if stuck.")
            sys.exit(1)
        except (OSError, ValueError):
            # Process doesn't exist or PID file is corrupted, remove it
            pid_file.unlink(missing_ok=True)

    # Create PID file for this run
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))

    # Clean up PID file on exit
    def cleanup_pid_file():
        pid_file.unlink(missing_ok=True)

    atexit.register(cleanup_pid_file)

    # SIGNAL HANDLING: Clean shutdown on interruption
    def signal_handler(sig, frame):
        print(f"\n⚠️  Received signal {sig}, cleaning up...")
        cleanup_pid_file()
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

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

    # VIRTUAL ENVIRONMENT CHECK AND ACTIVATION
    venv_path = os.environ.get('VIRTUAL_ENV')
    if not venv_path:
        # Try to find and use the .venv in the project
        potential_venv = project_root / '.venv'
        if potential_venv.exists():
            # Use the Python from the virtual environment
            venv_python = potential_venv / 'bin' / 'python'
            if not venv_python.exists():
                # Windows path
                venv_python = potential_venv / 'Scripts' / 'python.exe'

            if venv_python.exists():
                print(f"✅ Using virtual environment: {potential_venv}")
                # Update sys.executable to use venv Python
                python_executable = str(venv_python)
            else:
                print("⚠️  Warning: Virtual environment found but Python executable not found")
                print("   Using system Python instead")
                python_executable = sys.executable
        else:
            print("⚠️  Warning: Not running in a virtual environment")
            print("   Consider running: source .venv/bin/activate")
            print("   Proceeding with system Python...\n")
            python_executable = sys.executable
    else:
        print(f"✅ Virtual environment: {venv_path}")
        python_executable = sys.executable

    # Run pytest with verbose output
    print("\n🧪 Running tests with pytest...")
    print("-" * 40)

    # Pytest arguments for comprehensive testing
    pytest_args = [
        python_executable,  # Use the determined Python executable
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

        # Add timeout for safety (10 minutes max)
        result = subprocess.run(
            pytest_args,
            check=False,
            env=env,
            timeout=600,
            start_new_session=True  # Create process group for clean shutdown
        )

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

    except subprocess.TimeoutExpired:
        print("❌ Test run timed out after 10 minutes!")
        print("   This may indicate infinite loops or stuck processes.")
        print("   Check for:")
        print("   - Recursive test execution")
        print("   - Hanging network requests")
        print("   - Deadlocks in async code")
        return 124  # Timeout exit code

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

        # Add timeout for safety (5 minutes for specific tests)
        result = subprocess.run(
            pytest_args,
            check=False,
            env=env,
            timeout=300,
            start_new_session=True
        )

        print("\n" + "=" * 60)
        print("SPECIFIC TEST EXECUTION COMPLETE")
        print("=" * 60)

        if result.returncode == 0:
            print("✅ Specific test passed!")
        else:
            print("❌ Specific test failed!")
            print(f"Exit code: {result.returncode}")

        return result.returncode

    except subprocess.TimeoutExpired:
        print("❌ Specific test run timed out after 5 minutes!")
        return 124  # Timeout exit code

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
