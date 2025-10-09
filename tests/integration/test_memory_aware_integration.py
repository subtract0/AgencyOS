"""Integration test for memory-aware test execution (ADR-023).

Tests the full workflow of memory-aware test runner integration with pytest.
"""

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.integration
def test_memory_aware_runner_integration():
    """Integration test: Memory-aware config works with actual test execution."""
    from tools.memory_aware_test_runner import get_test_execution_config

    # Get current memory-aware configuration
    config_result = get_test_execution_config()
    assert config_result.is_ok(), "Should successfully get test execution config"

    config = config_result.unwrap()

    # Verify configuration is valid
    assert 1 <= config.worker_count <= 10, f"Worker count {config.worker_count} out of range"
    assert config.memory_budget_gb >= 0, "Memory budget must be non-negative"
    assert config.execution_mode in ["parallel", "serial", "adaptive"], f"Invalid mode: {config.execution_mode}"

    # Verify worker count aligns with execution mode
    if config.execution_mode == "serial":
        assert config.worker_count == 1, "Serial mode must use 1 worker"
    elif config.execution_mode == "adaptive":
        assert config.worker_count <= 3, "Adaptive mode should use ≤3 workers"
    else:  # parallel
        assert config.worker_count >= 6, "Parallel mode should use ≥6 workers"


@pytest.mark.integration
def test_run_tests_with_memory_aware_config():
    """Run a small subset of tests with memory-aware configuration."""
    from tools.memory_aware_test_runner import get_test_execution_config

    config = get_test_execution_config().unwrap()

    # Verify config is sensible (actual parallelization tested in run_tests.py)
    assert isinstance(config.worker_count, int), "Worker count must be integer"
    assert 1 <= config.worker_count <= 10, "Worker count must be between 1 and 10"

    # Run a simple test without parallelization to verify basic functionality
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_memory_aware_runner.py::test_verify_memory_safe",
            "-v",
            "-o",
            "addopts=",  # Clear default addopts to avoid pytest.ini conflicts
            "--tb=short",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Verify test execution succeeded
    assert result.returncode == 0, f"Test execution failed:\n{result.stdout}\n{result.stderr}"
    assert "PASSED" in result.stdout, "Test should pass"


@pytest.mark.integration
def test_cloud_fallback_trigger():
    """Verify cloud fallback is triggered when memory is critical."""
    with patch('psutil.virtual_memory') as mock_mem:
        # Simulate critically low memory (6GB available)
        mock_mem.return_value = MagicMock(available=6 * 1024**3)

        from tools.memory_aware_test_runner import get_test_execution_config

        result = get_test_execution_config()
        assert result.is_ok()

        config = result.unwrap()
        assert config.fallback_to_cloud == True, "Should trigger cloud fallback at 6GB available"
        assert config.worker_count == 1, "Should use serial execution when memory critical"


@pytest.mark.integration
def test_memory_aware_runner_handles_errors_gracefully():
    """Verify graceful error handling when memory detection fails."""
    with patch('psutil.virtual_memory', side_effect=Exception("Memory read failed")):
        from tools.memory_aware_test_runner import get_test_execution_config

        result = get_test_execution_config()
        assert result.is_err(), "Should return error when memory detection fails"

        error_msg = result.unwrap_err()
        assert "Failed to get test execution config" in error_msg
        assert "Memory read failed" in error_msg
