"""Tests for memory-aware test runner (ADR-023).

Constitutional compliance:
- Article I: Prevents incomplete test execution from memory crashes
- Article II: 100% test success validation
- Article III: Automated worker adjustment enforcement
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import psutil
import pytest


def test_get_safe_worker_count_with_local_model():
    """When local model active and low memory, use 3 workers."""
    with patch('psutil.virtual_memory') as mock_mem:
        # Simulate 12GB available (local model uses 38GB, total 48GB)
        mock_mem.return_value = MagicMock(available=12 * 1024**3)

        with patch('os.path.exists', return_value=True):  # Ollama running
            from tools.memory_aware_test_runner import get_safe_worker_count
            workers = get_safe_worker_count()
            assert workers == 3, "Should use conservative parallelism with local model"


def test_get_safe_worker_count_without_local_model():
    """When local model OFF and high memory, use 10 workers."""
    with patch('psutil.virtual_memory') as mock_mem:
        # Simulate 30GB available
        mock_mem.return_value = MagicMock(available=30 * 1024**3)

        with patch('os.path.exists', return_value=False):  # Ollama not running
            from tools.memory_aware_test_runner import get_safe_worker_count
            workers = get_safe_worker_count()
            assert workers == 10, "Should use full parallelism without local model"


def test_get_safe_worker_count_critical_memory():
    """When memory critically low, use 1 worker (sequential)."""
    with patch('psutil.virtual_memory') as mock_mem:
        # Simulate 5GB available (critical)
        mock_mem.return_value = MagicMock(available=5 * 1024**3)

        from tools.memory_aware_test_runner import get_safe_worker_count
        workers = get_safe_worker_count()
        assert workers == 1, "Should use sequential execution when memory critical"


def test_verify_memory_safe():
    """verify_memory_safe should check if enough memory for tests."""
    with patch('psutil.virtual_memory') as mock_mem:
        # Simulate 20GB available
        mock_mem.return_value = MagicMock(available=20 * 1024**3)

        from tools.memory_aware_test_runner import verify_memory_safe
        assert verify_memory_safe(required_gb=10) == True
        assert verify_memory_safe(required_gb=25) == False


def test_get_test_execution_config_parallel_mode():
    """High memory without local model should use parallel mode."""
    with patch('psutil.virtual_memory') as mock_mem:
        mock_mem.return_value = MagicMock(available=30 * 1024**3)

        with patch('psutil.process_iter', return_value=[]):
            with patch('os.path.exists', return_value=False):
                from tools.memory_aware_test_runner import get_test_execution_config

                result = get_test_execution_config()
                assert result.is_ok()

                config = result.unwrap()
                assert config.worker_count == 10
                assert config.execution_mode == "parallel"
                assert config.local_model_active == False
                assert config.fallback_to_cloud == False


def test_get_test_execution_config_adaptive_mode():
    """Local model with medium memory should use adaptive mode."""
    with patch('psutil.virtual_memory') as mock_mem:
        mock_mem.return_value = MagicMock(available=12 * 1024**3)

        mock_process = MagicMock()
        mock_process.info = {'name': 'ollama'}

        with patch('psutil.process_iter', return_value=[mock_process]):
            from tools.memory_aware_test_runner import get_test_execution_config

            result = get_test_execution_config()
            assert result.is_ok()

            config = result.unwrap()
            assert config.worker_count == 3
            assert config.execution_mode == "adaptive"
            assert config.local_model_active == True


def test_get_test_execution_config_serial_mode():
    """Critical memory should use serial mode."""
    with patch('psutil.virtual_memory') as mock_mem:
        mock_mem.return_value = MagicMock(available=5 * 1024**3)

        from tools.memory_aware_test_runner import get_test_execution_config

        result = get_test_execution_config()
        assert result.is_ok()

        config = result.unwrap()
        assert config.worker_count == 1
        assert config.execution_mode == "serial"


def test_get_test_execution_config_cloud_fallback():
    """Very low memory should trigger cloud fallback."""
    with patch('psutil.virtual_memory') as mock_mem:
        mock_mem.return_value = MagicMock(available=6 * 1024**3)

        from tools.memory_aware_test_runner import get_test_execution_config

        result = get_test_execution_config()
        assert result.is_ok()

        config = result.unwrap()
        assert config.fallback_to_cloud == True, "Should trigger cloud fallback when memory very low"


def test_check_ollama_running_via_process():
    """Should detect Ollama via process name."""
    mock_process = MagicMock()
    mock_process.info = {'name': 'ollama'}

    with patch('psutil.process_iter', return_value=[mock_process]):
        with patch('os.path.exists', return_value=False):  # No marker file
            from tools.memory_aware_test_runner import check_ollama_running
            assert check_ollama_running() == True


def test_check_ollama_running_via_marker_file():
    """Should detect Ollama via marker file."""
    with patch('psutil.process_iter', return_value=[]):  # No process
        with patch('os.path.exists', return_value=True):  # Marker file exists
            from tools.memory_aware_test_runner import check_ollama_running
            assert check_ollama_running() == True


def test_check_ollama_not_running():
    """Should return False when Ollama not running."""
    with patch('psutil.process_iter', return_value=[]):
        with patch('os.path.exists', return_value=False):
            from tools.memory_aware_test_runner import check_ollama_running
            assert check_ollama_running() == False
