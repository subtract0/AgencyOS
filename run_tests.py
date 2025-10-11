#!/usr/bin/env python3
"""
Test Runner for Agency Code Agency
Runs all tests using pytest framework
"""

import argparse
import atexit
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from types import FrameType
from typing import Any

# Defer pydantic import to avoid module errors in pre-commit hook
JSONValue = Any  # Type hint placeholder


class DockerManager:
    """Manage Docker Compose lifecycle for test execution.

    Constitutional Compliance:
    - Article I: Complete context before action (health check retry logic)
    - Article II: 100% verification (cleanup even on failure)
    """

    def __init__(self, compose_file: Path):
        self.compose_file = compose_file
        self.services_started = False

    def check_docker_available(self) -> tuple[bool, str]:
        """Check if Docker and docker-compose are available.

        Returns:
            Tuple of (is_available, error_message)
        """
        # Check if docker is installed
        try:
            subprocess.run(
                ["docker", "--version"],
                check=True,
                capture_output=True,
                timeout=5,
            )
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False, "Docker not installed. Install from: https://www.docker.com/get-started"

        # Check if Docker daemon is running
        try:
            subprocess.run(
                ["docker", "ps"],
                check=True,
                capture_output=True,
                timeout=5,
            )
        except subprocess.CalledProcessError:
            return (
                False,
                "Docker daemon not running. Start Docker Desktop or run: sudo systemctl start docker",
            )
        except subprocess.TimeoutExpired:
            return False, "Docker daemon not responding (timeout)"

        # Check for docker-compose (try both v1 and v2)
        docker_compose_cmd = None
        for cmd in [["docker", "compose"], ["docker-compose"]]:
            try:
                result = subprocess.run(
                    cmd + ["version"],
                    check=True,
                    capture_output=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    docker_compose_cmd = cmd
                    break
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue

        if docker_compose_cmd is None:
            return (
                False,
                "docker-compose not installed. Docker Compose v2 comes with Docker Desktop.",
            )

        # Store the working command for later use
        self.docker_compose_cmd = docker_compose_cmd
        return True, ""

    def start_services(self) -> tuple[bool, str]:
        """Start Docker Compose services.

        Returns:
            Tuple of (success, error_message)
        """
        if not self.compose_file.exists():
            return False, f"docker-compose.yml not found at {self.compose_file}"

        try:
            # Start docker-compose services
            subprocess.run(
                self.docker_compose_cmd + ["-f", str(self.compose_file), "up", "-d"],
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )

            self.services_started = True
            print("✅ Docker Compose services started successfully")

            # Wait for services to be healthy (Article I: retry logic)
            if not self._wait_for_health():
                return False, "Docker services failed health check"

            return True, ""

        except subprocess.CalledProcessError as e:
            return False, f"Failed to start Docker Compose: {e.stderr}"
        except subprocess.TimeoutExpired:
            return False, "Docker Compose startup timed out (60s)"
        except Exception as e:
            return False, f"Unexpected error starting Docker: {e}"

    def _wait_for_health(self) -> bool:
        """Wait for Docker services to become healthy (Article I).

        Uses exponential backoff: 2s, 4s, 8s, 16s (cap at 16s)
        Max wait: 120 seconds

        Returns:
            True if services healthy, False if timeout
        """
        max_wait_seconds = 120
        initial_interval = 2
        interval = initial_interval
        elapsed = 0

        print("⏳ Waiting for Docker services to become healthy...")

        while elapsed < max_wait_seconds:
            try:
                # Check service health via docker-compose ps
                result = subprocess.run(
                    self.docker_compose_cmd
                    + ["-f", str(self.compose_file), "ps", "--format", "json"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                # Parse JSON output to check health status
                if result.stdout.strip():
                    services = [json.loads(line) for line in result.stdout.strip().split("\n")]
                    # Check if all services are running and healthy
                    all_healthy = all(
                        svc.get("State") == "running"
                        and svc.get("Health", "healthy") in ["healthy", ""]
                        for svc in services
                    )

                    if all_healthy:
                        print("✅ All Docker services are healthy")
                        return True

            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError):
                # Service not ready yet, continue retrying
                pass

            time.sleep(interval)
            elapsed += interval

            # Exponential backoff: 2s, 4s, 8s, 16s, then cap at 16s (Article I)
            interval = min(interval * 2, 16)

        print("⚠️  Docker services did not become healthy within 120s")
        return False

    def stop_services(self) -> None:
        """Stop and cleanup Docker Compose services (Article II: always cleanup)."""
        if not self.services_started:
            return

        try:
            print("\n🧹 Stopping Docker Compose services...")
            subprocess.run(
                self.docker_compose_cmd + ["-f", str(self.compose_file), "down"],
                check=True,
                capture_output=True,
                timeout=30,
            )
            print("✅ Docker Compose services stopped successfully")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"⚠️  Warning: Docker cleanup failed: {e}")
        except Exception as e:
            print(f"⚠️  Warning: Unexpected error during cleanup: {e}")


def _record_timing(
    duration_s: float,
    test_mode: str,
    specific: str | None,
    exit_code: int,
    extra: dict[str, JSONValue] | None = None,
) -> None:
    try:
        root = Path(__file__).resolve().parent
        out_dir = root / "logs" / "benchmarks"
        out_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "ts": datetime.now(UTC).isoformat(),
            "mode": test_mode,
            "specific": specific,
            "duration_s": round(float(duration_s), 3),
            "exit_code": int(exit_code),
        }
        if extra:
            payload.update(extra)
        with open(out_dir / "test_timings.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass


def main(
    test_mode: str = "unit", fast_only: bool = False, timed: bool = False, with_docker: bool = False
) -> int:
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
            with open(pid_file) as f:
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
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    # Clean up PID file on exit
    def cleanup_pid_file() -> None:
        pid_file.unlink(missing_ok=True)

    atexit.register(cleanup_pid_file)

    # DOCKER LIFECYCLE MANAGEMENT (Article I & II compliance)
    docker_manager = None
    if with_docker:
        print("\n🐳 Docker Integration Enabled")
        print("=" * 60)

        # Initialize Docker manager
        project_root = Path(__file__).resolve().parent
        compose_file = project_root / "docker-compose.yml"
        docker_manager = DockerManager(compose_file)

        # Check Docker availability
        available, error_msg = docker_manager.check_docker_available()
        if not available:
            print(f"❌ Docker Check Failed: {error_msg}")
            print("   Tests will run without Docker services")
            print("   Install Docker or run without --with-docker flag")
            return 1

        # Start Docker services
        print("🚀 Starting Docker Compose services...")
        success, error_msg = docker_manager.start_services()
        if not success:
            print(f"❌ Docker Startup Failed: {error_msg}")
            print("   Check Docker logs: docker-compose logs")
            return 1

        # Register cleanup handler (Article II: cleanup even on failure)
        atexit.register(docker_manager.stop_services)

        print("=" * 60)

    # SIGNAL HANDLING: Clean shutdown on interruption
    def signal_handler(sig: int, frame: FrameType | None) -> None:
        print(f"\n⚠️  Received signal {sig}, cleaning up...")
        if docker_manager:
            docker_manager.stop_services()
        cleanup_pid_file()
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    """Run tests using pytest with specified mode

    Args:
        test_mode: "unit", "integration", "all", "fast", "slow", "benchmark", or "github"
        fast_only: If True, exclude slow and benchmark tests from default runs
    """
    print("=" * 60)
    print("AGENCY CODE AGENCY - TEST RUNNER")
    print("=" * 60)

    # Display test mode
    mode_descriptions = {
        "unit": "Unit Tests Only (excluding integration, slow, and benchmark tests)",
        "integration": "Integration Tests Only",
        "all": "All Tests (Unit + Integration)",
        "fast": "Fast Unit Tests Only (excluding slow, benchmark, integration)",
        "slow": "Slow Tests Only",
        "benchmark": "Benchmark Tests Only",
        "github": "GitHub Integration Tests Only",
        "integration-only": "Integration Tests Only (same as integration)",
    }
    print(f"\n🎯 Test Mode: {mode_descriptions.get(test_mode, test_mode)}")
    print("-" * 40)

    # Change to the project root directory
    project_root = Path(__file__).resolve().parent
    os.chdir(project_root)

    # VIRTUAL ENVIRONMENT CHECK AND ACTIVATION
    venv_path = os.environ.get("VIRTUAL_ENV")
    if not venv_path:
        # Try to find and use the .venv in the project
        potential_venv = project_root / ".venv"
        if potential_venv.exists():
            # Use the Python from the virtual environment
            venv_python = potential_venv / "bin" / "python"
            if not venv_python.exists():
                # Windows path
                venv_python = potential_venv / "Scripts" / "python.exe"

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

    # Record start time for timing information
    start_time = time.time()

    # Run pytest with verbose output
    print("\n🧪 Running tests with pytest...")
    print("-" * 40)

    # Pytest arguments for comprehensive testing
    # Use uv run pytest in local dev, python -m pytest in CI
    is_ci = os.environ.get("CI") == "true"

    if is_ci:
        # CI environment - use python -m pytest
        pytest_args = [
            python_executable,
            "-m",
            "pytest",
            "tests/",  # Test directory
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            "--strict-markers",  # Strict marker checking
            "--durations=10",  # Show 10 slowest tests
            # "-x",  # Stop on first failure - commented out to run all tests
            "--color=yes",  # Colored output
            # Exclude integration tests that hang at collection time
            "--ignore=tests/test_firestore_learning_persistence.py",
            "--ignore=tests/test_firestore_mock_integration.py",
            "--ignore=tests/e2e/",  # e2e tests import agency at module level
        ]
    else:
        # Local development - use uv run pytest for better dependency management
        # Use -q (quiet) for fast mode to reduce output overhead
        verbosity_flag = "-q" if test_mode == "fast" else "-v"
        pytest_args = [
            "uv",
            "run",
            "pytest",
            "tests/",  # Test directory
            verbosity_flag,  # Quiet for fast mode, verbose otherwise
            "--tb=short",  # Short traceback format
            "--strict-markers",  # Strict marker checking
            "--durations=10",  # Show 10 slowest tests
            # "-x",  # Stop on first failure - commented out to run all tests
            "--color=yes",  # Colored output
            # Exclude integration tests that hang at collection time
            "--ignore=tests/test_firestore_learning_persistence.py",
            "--ignore=tests/test_firestore_mock_integration.py",
            "--ignore=tests/e2e/",  # e2e tests import agency at module level
        ]

    # Add parallel execution if pytest-xdist is available
    # (Firestore tests excluded via --ignore flags, safe to parallelize)
    # Memory-aware worker count: reduce parallelism when local Ollama model is active
    try:
        import xdist  # noqa: F401 - pytest-xdist module imported as 'xdist', checked for availability

        # Check if local model is active (Phase 3 cost optimization)
        use_local = os.getenv("USE_LOCAL_MODEL", "true").lower() == "true"

        # Docker services consume memory: adjust worker count accordingly
        if with_docker:
            # Docker Ollama service (40GB limit) + tests: reduce workers
            # 48GB Mac: Docker (40GB) + 2 workers (6GB) = 46GB (safe)
            worker_count = int(os.getenv("LOCAL_MODEL_TEST_WORKERS", "2"))
            print(f"🐳 Docker services active: using {worker_count} test workers (memory-safe)")
        elif use_local:
            # Reduce parallelism to prevent memory exhaustion with 32GB local model
            # 48GB Mac: Qwen3-Coder Q8_0 (38GB) + 3 workers (9GB) = 47GB (safe)
            worker_count = int(os.getenv("LOCAL_MODEL_TEST_WORKERS", "3"))
            print(f"🧠 Local model active: using {worker_count} test workers (memory-safe)")
        else:
            # No local model or Docker: default parallelism
            worker_count = 10

        # CRITICAL: Force single worker to avoid PyTorch segfault (SPEC-021)
        # TODO: Fix parallel import issue in sentence_transformers/torch
        if worker_count > 1:
            print("⚠️ WARNING: Reducing to 1 worker to avoid PyTorch segfault (see SPEC-021)")
            worker_count = 1

        pytest_args.extend(["-n", str(worker_count)])
    except ImportError:
        pass  # Run sequentially if xdist not available

    # PRE-IMPORT PYTORCH IN MAIN THREAD (SPEC-021 FIX)
    # CRITICAL: Import torch/transformers BEFORE pytest spawns workers
    # Prevents segfault from parallel imports in VectorStore initialization
    use_enhanced_memory = os.getenv("USE_ENHANCED_MEMORY", "true").lower() == "true"
    if use_enhanced_memory:
        try:
            print("🔧 Pre-importing PyTorch/transformers in main thread (SPEC-021 safety)...")
            import torch  # noqa: F401 - Pre-import to prevent worker segfault
            import transformers  # noqa: F401 - Pre-import to prevent worker segfault

            print("✅ PyTorch/transformers pre-imported successfully")
        except ImportError:
            print(
                "⚠️  PyTorch/transformers not installed - VectorStore will use keyword search only"
            )

    # Prepare environment variables
    env = os.environ.copy()
    env["AGENCY_NESTED_TEST"] = "1"
    env["PYTHONUNBUFFERED"] = "1"  # Disable output buffering for immediate feedback

    # Prevent PyTorch/transformers segfault with parallel testing (SPEC-021)
    env["TOKENIZERS_PARALLELISM"] = "false"  # Disable tokenizer parallelism
    env["OMP_NUM_THREADS"] = "1"  # Limit OpenMP threads to prevent race conditions

    # Docker integration: Enable/disable Ollama tests based on --with-docker flag
    if with_docker:
        # Docker services running: enable Ollama tests
        env["SKIP_OLLAMA_TESTS"] = "0"
        print("✅ Ollama tests ENABLED (Docker services running)")
    else:
        # No Docker services: skip Ollama tests (default behavior)
        env["SKIP_OLLAMA_TESTS"] = "1"

    # Add marker selection based on test mode
    if test_mode == "unit":
        if fast_only:
            pytest_args.extend(["-m", "not integration and not slow and not benchmark"])
        else:
            pytest_args.extend(["-m", "not integration and not slow and not benchmark"])
    elif test_mode == "integration" or test_mode == "integration-only":
        pytest_args.extend(["-m", "integration"])
    elif test_mode == "fast":
        pytest_args.extend(["-m", "not integration and not slow and not benchmark and not github"])
    elif test_mode == "slow":
        pytest_args.extend(["-m", "slow"])
    elif test_mode == "benchmark":
        pytest_args.extend(["-m", "benchmark"])
    elif test_mode == "github":
        pytest_args.extend(["-m", "github"])
    elif test_mode == "all":
        # For "all" mode, force running ALL tests including skipped ones
        pytest_args.extend(["--runxfail", "-p", "no:warnings"])
        # Set environment variables to force-enable all conditional skips
        env["FORCE_RUN_ALL_TESTS"] = "1"
        env["AGENCY_SKIP_GIT"] = "0"
        print("🚀 FORCE MODE: Running ALL tests including normally skipped ones")
        print("   This will make real API calls and may incur costs")
    # Default: no marker filtering is applied

    try:
        # Add timeout for safety (600 seconds for all test modes to prevent timeouts)
        # Allow override from environment for CI environments
        default_timeout = 600  # 10 minutes for all test modes
        timeout_seconds = int(os.environ.get("AGENCY_TEST_TIMEOUT_OVERRIDE", str(default_timeout)))

        # Debug: Print the exact command being run
        print(f"🔍 Running command: {' '.join(pytest_args)}\n")

        result = subprocess.run(
            pytest_args,
            check=False,
            env=env,
            timeout=timeout_seconds,
            # Remove start_new_session to allow proper stdout/stderr inheritance
            # This was causing the subprocess to appear hung
        )

        # Calculate execution time
        end_time = time.time()
        execution_time = end_time - start_time

        if timed:
            _record_timing(execution_time, test_mode, specific=None, exit_code=result.returncode)

        print("\n" + "=" * 60)
        print("TEST EXECUTION COMPLETE")
        print("=" * 60)

        # Display timing information
        print(f"⏱️  Execution time: {execution_time:.2f} seconds")

        if result.returncode == 0:
            print("✅ All tests passed!")
            print("\n📊 Test Summary:")
            print(f"- {mode_descriptions.get(test_mode, test_mode)} executed successfully")
            print(f"- Execution time: {execution_time:.2f} seconds")
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
        timeout_desc = "10 minutes" if test_mode == "all" else "60 seconds"
        print(f"❌ Test run timed out after {timeout_desc}!")
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


def run_specific_test(test_name: str, timed: bool = False) -> int:
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
        t0 = time.time()
        result = subprocess.run(
            pytest_args,
            check=False,
            env=env,
            timeout=300,
            # Removed start_new_session to allow proper stdout/stderr inheritance
        )
        duration = time.time() - t0

        print("\n" + "=" * 60)
        print("SPECIFIC TEST EXECUTION COMPLETE")
        print("=" * 60)

        if timed:
            _record_timing(
                duration, test_mode="specific", specific=test_name, exit_code=result.returncode
            )

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


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for test runner"""
    parser = argparse.ArgumentParser(
        description="Agency Code Agency Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python run_tests.py                    # Run unit tests only (default)
  python run_tests.py --fast             # Run fast unit tests only
  python run_tests.py --slow             # Run slow tests only
  python run_tests.py --benchmark        # Run benchmark tests only
  python run_tests.py --github           # Run GitHub integration tests only
  python run_tests.py --integration-only # Run integration tests only
  python run_tests.py --run-integration  # Run integration tests only (legacy)
  python run_tests.py --run-all          # Run all tests
  python run_tests.py --with-docker      # Run with Docker services (enables Ollama tests)
  python run_tests.py test_specific.py   # Run specific test file""",
    )

    # Test suite options (mutually exclusive)
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument(
        "--fast",
        action="store_true",
        help="Run only fast unit tests (exclude slow, benchmark, integration)",
    )
    test_group.add_argument("--slow", action="store_true", help="Run only slow tests")
    test_group.add_argument("--benchmark", action="store_true", help="Run only benchmark tests")
    test_group.add_argument(
        "--github", action="store_true", help="Run only GitHub integration tests"
    )
    test_group.add_argument(
        "--integration-only",
        action="store_true",
        help="Run ONLY integration tests (what we normally skip)",
    )
    test_group.add_argument(
        "--run-integration", action="store_true", help="Run ONLY integration tests (legacy option)"
    )
    test_group.add_argument(
        "--run-all", action="store_true", help="Run ALL tests (unit + integration)"
    )

    # Docker integration flag
    parser.add_argument(
        "--with-docker",
        action="store_true",
        help="Run with Docker services (starts docker-compose, enables Ollama tests)",
    )

    # Specific test file
    parser.add_argument("specific_test", nargs="?", help="Run specific test file")

    # Optional timing record
    parser.add_argument(
        "--timed",
        action="store_true",
        help="Record run duration to logs/benchmarks/test_timings.jsonl and print it",
    )

    return parser


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    # Determine test mode based on arguments
    test_mode = "unit"  # Default to unit tests only (excluding slow and benchmark)

    if args.fast:
        test_mode = "fast"
    elif args.slow:
        test_mode = "slow"
    elif args.benchmark:
        test_mode = "benchmark"
    elif args.github:
        test_mode = "github"
    elif args.integration_only or args.run_integration:
        test_mode = "integration"
    elif args.run_all:
        test_mode = "all"

    # Execute the appropriate test mode
    if args.specific_test:
        exit_code = run_specific_test(args.specific_test, timed=args.timed)
    else:
        # Default behavior excludes slow and benchmark tests automatically
        fast_only = test_mode == "unit"
        exit_code = main(
            test_mode, fast_only=fast_only, timed=args.timed, with_docker=args.with_docker
        )

    sys.exit(exit_code)
