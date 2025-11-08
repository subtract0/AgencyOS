"""
Tests for Ollama health check tool.

Constitutional Compliance:
- Article I: Complete context with retry logic testing
- Article II: 100% test coverage, TDD-first approach
- Strict typing with Pydantic models
- Result pattern for all error cases
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import aiohttp
import pytest

from shared.type_definitions.result import Err, Ok, Result
from tools.ollama_health_check import (
    OllamaHealthError,
    OllamaHealthStatus,
    check_inference,
    check_ollama_health,
    detect_docker_ollama,
)


class TestOllamaHealthStatus:
    """Test Pydantic model for health status."""

    def test_health_status_creation(self):
        """Test creating health status with all fields."""
        status = OllamaHealthStatus(
            is_running=True,
            is_docker=False,
            endpoint="http://localhost:11434",
            models_available=["qwen3-coder:30b"],
            inference_working=True,
            error_message=None,
        )

        assert status.is_running is True
        assert status.is_docker is False
        assert status.endpoint == "http://localhost:11434"
        assert status.models_available == ["qwen3-coder:30b"]
        assert status.inference_working is True
        assert status.error_message is None

    def test_health_status_with_error(self):
        """Test health status with error condition."""
        status = OllamaHealthStatus(
            is_running=False,
            is_docker=False,
            endpoint="http://localhost:11434",
            models_available=[],
            inference_working=False,
            error_message="Connection refused",
        )

        assert status.is_running is False
        assert status.error_message == "Connection refused"


class TestDetectDockerOllama:
    """Test Docker detection helper."""

    @patch("subprocess.run")
    def test_detect_docker_ollama_running(self, mock_run):
        """Test detecting Docker Ollama when container is running."""
        mock_run.return_value = Mock(returncode=0, stdout="ollama-container\n", stderr="")

        result = detect_docker_ollama()
        assert result is True

    @patch("subprocess.run")
    def test_detect_docker_ollama_not_running(self, mock_run):
        """Test detecting Docker Ollama when container is not running."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="No containers")

        result = detect_docker_ollama()
        assert result is False

    @patch("subprocess.run")
    def test_detect_docker_ollama_docker_not_installed(self, mock_run):
        """Test when Docker is not installed."""
        mock_run.side_effect = FileNotFoundError("docker not found")

        result = detect_docker_ollama()
        assert result is False


@pytest.mark.asyncio
class TestCheckOllamaHealth:
    """Test main health check function."""

    @patch("aiohttp.ClientSession")
    async def test_check_health_success(self, mock_session_class):
        """Test successful health check with all systems operational."""
        # Mock session
        mock_session = MagicMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session

        # Mock /api/tags response
        mock_tags_response = AsyncMock()
        mock_tags_response.status = 200
        mock_tags_response.json = AsyncMock(return_value={"models": [{"name": "qwen3-coder:30b"}]})
        mock_tags_response.raise_for_status = MagicMock()  # Sync method, not async

        # Mock /api/generate response for inference test
        mock_generate_response = AsyncMock()
        mock_generate_response.status = 200
        mock_generate_response.json = AsyncMock(return_value={"response": "2", "done": True})
        mock_generate_response.raise_for_status = MagicMock()  # Sync method, not async

        # Create proper async context managers using MagicMock
        mock_get_cm = MagicMock()
        mock_get_cm.__aenter__ = AsyncMock(return_value=mock_tags_response)
        mock_get_cm.__aexit__ = AsyncMock(return_value=None)

        mock_post_cm = MagicMock()
        mock_post_cm.__aenter__ = AsyncMock(return_value=mock_generate_response)
        mock_post_cm.__aexit__ = AsyncMock(return_value=None)

        # Setup session methods to return context managers
        mock_session.get = MagicMock(return_value=mock_get_cm)
        mock_session.post = MagicMock(return_value=mock_post_cm)

        with patch("tools.ollama_health_check.detect_docker_ollama", return_value=False):
            result = await check_ollama_health()

        assert result.is_ok()
        status = result.unwrap()
        assert isinstance(status, OllamaHealthStatus)
        assert status.is_running is True
        assert status.inference_working is True
        assert status.models_available == ["qwen3-coder:30b"]
        assert status.error_message is None

    @patch("aiohttp.ClientSession")
    async def test_check_health_connection_error(self, mock_session_class):
        """Test health check when Ollama is not running."""
        mock_session = MagicMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session

        # Raise error when creating context manager
        mock_session.get.side_effect = aiohttp.ClientError("Connection refused")

        result = await check_ollama_health()

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, OllamaHealthError)
        assert "Connection refused" in str(error)

    @patch("aiohttp.ClientSession")
    async def test_check_health_timeout(self, mock_session_class):
        """Test health check with timeout (Article I: retry logic)."""
        mock_session = MagicMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session

        # Create context manager that raises timeout
        mock_get_cm = MagicMock()
        mock_get_cm.__aenter__ = AsyncMock(side_effect=TimeoutError("Request timeout"))
        mock_get_cm.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_get_cm)

        result = await check_ollama_health(timeout=5, max_retries=1)

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, OllamaHealthError)
        assert "timeout" in str(error).lower() or "retries" in str(error).lower()

    @patch("aiohttp.ClientSession")
    async def test_check_health_http_error(self, mock_session_class):
        """Test health check with HTTP error response."""
        mock_session = MagicMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session

        mock_response = AsyncMock()
        mock_response.status = 500

        def raise_http_error():  # Sync method
            raise aiohttp.ClientResponseError(
                request_info=Mock(),
                history=(),
                status=500,
                message="Internal Server Error",
            )

        mock_response.raise_for_status = raise_http_error

        # Create proper async context manager
        mock_get_cm = MagicMock()
        mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session.get = MagicMock(return_value=mock_get_cm)

        result = await check_ollama_health()

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, OllamaHealthError)

    @patch("aiohttp.ClientSession")
    async def test_check_health_with_docker(self, mock_session_class):
        """Test health check detecting Docker Ollama."""
        mock_session = MagicMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session

        mock_tags_response = AsyncMock()
        mock_tags_response.status = 200
        mock_tags_response.json = AsyncMock(return_value={"models": []})
        mock_tags_response.raise_for_status = MagicMock()

        # Create proper async context manager
        mock_get_cm = MagicMock()
        mock_get_cm.__aenter__ = AsyncMock(return_value=mock_tags_response)
        mock_get_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session.get = MagicMock(return_value=mock_get_cm)

        with patch("tools.ollama_health_check.detect_docker_ollama", return_value=True):
            result = await check_ollama_health()

        assert result.is_ok()
        status = result.unwrap()
        assert status.is_docker is True

    @patch("aiohttp.ClientSession")
    async def test_check_health_custom_endpoint(self, mock_session_class):
        """Test health check with custom endpoint."""
        mock_session = MagicMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"models": []})
        mock_response.raise_for_status = MagicMock()

        # Create proper async context manager
        mock_get_cm = MagicMock()
        mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session.get = MagicMock(return_value=mock_get_cm)

        custom_endpoint = "http://192.168.1.100:11434"
        result = await check_ollama_health(endpoint=custom_endpoint)

        assert result.is_ok()
        status = result.unwrap()
        assert status.endpoint == custom_endpoint

    @patch("aiohttp.ClientSession")
    async def test_check_health_inference_failure(self, mock_session_class):
        """Test when Ollama is running but inference fails."""
        mock_session = MagicMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session

        # Tags endpoint succeeds
        mock_tags_response = AsyncMock()
        mock_tags_response.status = 200
        mock_tags_response.json = AsyncMock(return_value={"models": [{"name": "qwen3-coder:30b"}]})
        mock_tags_response.raise_for_status = MagicMock()

        # Inference endpoint fails
        mock_generate_response = AsyncMock()
        mock_generate_response.status = 500

        def raise_http_error():  # Sync method
            raise aiohttp.ClientResponseError(
                request_info=Mock(),
                history=(),
                status=500,
                message="Model error",
            )

        mock_generate_response.raise_for_status = raise_http_error

        # Create proper async context managers
        mock_get_cm = MagicMock()
        mock_get_cm.__aenter__ = AsyncMock(return_value=mock_tags_response)
        mock_get_cm.__aexit__ = AsyncMock(return_value=None)

        mock_post_cm = MagicMock()
        mock_post_cm.__aenter__ = AsyncMock(return_value=mock_generate_response)
        mock_post_cm.__aexit__ = AsyncMock(return_value=None)

        # Setup session methods to return context managers
        mock_session.get = MagicMock(return_value=mock_get_cm)
        mock_session.post = MagicMock(return_value=mock_post_cm)

        with patch("tools.ollama_health_check.detect_docker_ollama", return_value=False):
            result = await check_ollama_health()

        assert result.is_ok()
        status = result.unwrap()
        assert status.is_running is True
        assert status.inference_working is False  # Inference failed but Ollama is up

    @patch("aiohttp.ClientSession")
    async def test_check_health_no_models_uses_debug_logging(self, mock_session_class, caplog):
        """
        Test that missing models logs at DEBUG level (not WARNING).

        Regression fix for: ./run_tests.py --run-all abortion due to warning output
        during test discovery. Missing models is an expected condition and should
        use debug-level logging.

        Constitutional Compliance:
        - Article I: Complete context (test discovery must complete)
        - Article II: 100% verification (all tests must be discoverable)
        """
        import logging

        # Set log level to DEBUG to capture debug messages
        caplog.set_level(logging.DEBUG)

        mock_session = MagicMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session

        # Tags endpoint succeeds but returns empty models list
        mock_tags_response = AsyncMock()
        mock_tags_response.status = 200
        mock_tags_response.json = AsyncMock(return_value={"models": []})  # No models
        mock_tags_response.raise_for_status = MagicMock()

        # Create proper async context manager
        mock_get_cm = MagicMock()
        mock_get_cm.__aenter__ = AsyncMock(return_value=mock_tags_response)
        mock_get_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session.get = MagicMock(return_value=mock_get_cm)

        with patch("tools.ollama_health_check.detect_docker_ollama", return_value=False):
            result = await check_ollama_health()

        # Verify health check succeeds gracefully
        assert result.is_ok()
        status = result.unwrap()
        assert status.is_running is True
        assert status.models_available == []
        assert status.inference_working is False  # Can't test inference without models

        # CRITICAL: Verify DEBUG level used (not WARNING)
        # This prevents test discovery abortion in ./run_tests.py --run-all
        debug_messages = [
            record for record in caplog.records
            if "no models available" in record.message.lower()
        ]
        assert len(debug_messages) > 0, "Expected debug message about missing models"
        assert all(record.levelname == "DEBUG" for record in debug_messages), \
            "Missing models should log at DEBUG level, not WARNING"

        # Verify NO warning-level messages about models
        warning_messages = [
            record for record in caplog.records
            if record.levelname == "WARNING" and "models" in record.message.lower()
        ]
        assert len(warning_messages) == 0, \
            "Should not log WARNING for missing models (causes test discovery failure)"
