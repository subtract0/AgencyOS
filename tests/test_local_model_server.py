"""
Tests for Local Model Server

NECESSARY Pattern Compliance:
- Named: Clear test names for local/cloud behavior
- Executable: Run independently with mocked Ollama
- Comprehensive: Cover success, failures, fallback
- Error-validated: Test connection errors explicitly
- State-verified: Assert model responses
- Side-effects controlled: Mock HTTP calls
- Assertions meaningful: Specific async checks
- Repeatable: Deterministic with mocks
- Yield fast: <1s per test
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from shared.local_model_server import (
    LocalModelServer,
    OllamaClient,
    OllamaConnectionError,
    OllamaGenerationError,
)


class TestOllamaClientInitialization:
    """Test Ollama client initialization."""

    def test_creates_client_with_defaults(self):
        """Client initializes with default Ollama URL."""
        client = OllamaClient()

        assert client.base_url == "http://localhost:11434"
        assert client.timeout == 120.0
        assert client.max_retries == 3

    def test_creates_client_with_custom_url(self):
        """Client accepts custom Ollama URL."""
        client = OllamaClient(base_url="http://custom:8080")

        assert client.base_url == "http://custom:8080"

    def test_strips_trailing_slash_from_url(self):
        """Client strips trailing slash from base URL."""
        client = OllamaClient(base_url="http://localhost:11434/")

        assert client.base_url == "http://localhost:11434"


class TestOllamaGeneration:
    """Test Ollama generation functionality."""

    @pytest.mark.asyncio
    async def test_generates_completion_successfully(self):
        """Client generates completion from model."""
        client = OllamaClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "Test generated response",
            "model": "qwen2.5-coder:1.5b",
            "done": True,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await client.generate(model="qwen2.5-coder:1.5b", prompt="Test prompt")

            assert result["response"] == "Test generated response"
            assert result["model"] == "qwen2.5-coder:1.5b"
            assert result["done"] is True

        await client.close()

    @pytest.mark.asyncio
    async def test_sends_system_prompt_when_provided(self):
        """Client includes system prompt in request."""
        client = OllamaClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "test", "done": True}
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await client.generate(
                model="qwen2.5-coder:1.5b", prompt="Test", system="You are a helpful assistant"
            )

            # Verify system prompt in request
            call_args = mock_post.call_args
            payload = call_args.kwargs["json"]
            assert payload["system"] == "You are a helpful assistant"

        await client.close()

    @pytest.mark.asyncio
    async def test_respects_temperature_setting(self):
        """Client sends correct temperature parameter."""
        client = OllamaClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "test", "done": True}
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await client.generate(model="qwen2.5-coder:1.5b", prompt="Test", temperature=0.7)

            call_args = mock_post.call_args
            payload = call_args.kwargs["json"]
            assert payload["options"]["temperature"] == 0.7

        await client.close()

    @pytest.mark.asyncio
    async def test_respects_max_tokens_setting(self):
        """Client sends max tokens as num_predict."""
        client = OllamaClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "test", "done": True}
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await client.generate(model="qwen2.5-coder:1.5b", prompt="Test", max_tokens=256)

            call_args = mock_post.call_args
            payload = call_args.kwargs["json"]
            assert payload["options"]["num_predict"] == 256

        await client.close()


class TestOllamaRetryLogic:
    """Test retry and error handling."""

    @pytest.mark.asyncio
    async def test_retries_on_connection_error(self):
        """Client retries on connection failures."""
        client = OllamaClient(max_retries=2)

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            # First call fails, second succeeds
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "success", "done": True}
            mock_response.raise_for_status = MagicMock()

            mock_post.side_effect = [httpx.ConnectError("Connection failed"), mock_response]

            result = await client.generate(model="qwen2.5-coder:1.5b", prompt="Test")

            assert result["response"] == "success"
            assert mock_post.call_count == 2

        await client.close()

    @pytest.mark.asyncio
    async def test_raises_error_after_max_retries(self):
        """Client raises error after exhausting retries."""
        client = OllamaClient(max_retries=2)

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")

            with pytest.raises(OllamaConnectionError, match="Cannot connect to Ollama"):
                await client.generate(model="qwen2.5-coder:1.5b", prompt="Test")

            # Should have tried max_retries times
            assert mock_post.call_count == 2

        await client.close()

    @pytest.mark.asyncio
    async def test_raises_generation_error_on_http_error(self):
        """Client raises OllamaGenerationError on HTTP errors."""
        client = OllamaClient(max_retries=1)

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Bad request", request=MagicMock(), response=mock_response
            )
            mock_response.text = "Model not found"

            mock_post.return_value = mock_response

            with pytest.raises(OllamaGenerationError, match="Generation failed"):
                await client.generate(model="invalid-model", prompt="Test")

        await client.close()


class TestOllamaStreaming:
    """Test streaming generation."""

    @pytest.mark.asyncio
    async def test_generates_streaming_response(self):
        """Client yields streaming chunks."""
        client = OllamaClient()

        # Mock streaming response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        async def mock_aiter_lines():
            yield '{"response": "First"}'
            yield '{"response": " chunk"}'
            yield '{"response": "", "done": true}'

        mock_response.aiter_lines = mock_aiter_lines

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            chunks = []
            async for chunk in client.generate_stream(model="qwen2.5-coder:1.5b", prompt="Test"):
                chunks.append(chunk)

            assert chunks == ["First", " chunk"]

        await client.close()


class TestOllamaModelListing:
    """Test model listing functionality."""

    @pytest.mark.asyncio
    async def test_lists_available_models(self):
        """Client lists models from Ollama server."""
        client = OllamaClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen2.5-coder:1.5b", "size": 986000000},
                {"name": "qwen2.5-coder:7b", "size": 4700000000},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            models = await client.list_models()

            assert len(models) == 2
            assert models[0]["name"] == "qwen2.5-coder:1.5b"
            assert models[1]["name"] == "qwen2.5-coder:7b"

        await client.close()

    @pytest.mark.asyncio
    async def test_health_check_returns_true_when_healthy(self):
        """Health check returns True when server responds."""
        client = OllamaClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"models": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            is_healthy = await client.health_check()

            assert is_healthy is True

        await client.close()

    @pytest.mark.asyncio
    async def test_health_check_returns_false_on_error(self):
        """Health check returns False when server unavailable."""
        client = OllamaClient()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")

            is_healthy = await client.health_check()

            assert is_healthy is False

        await client.close()


class TestOllamaContextManager:
    """Test context manager protocol."""

    @pytest.mark.asyncio
    async def test_supports_async_context_manager(self):
        """Client supports async context manager."""
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock):
            async with OllamaClient() as client:
                assert client is not None

            # Client should be closed after context


class TestLocalModelServer:
    """Test high-level LocalModelServer interface."""

    @pytest.mark.asyncio
    async def test_generates_with_local_model(self):
        """Server uses local model when available."""
        server = LocalModelServer()

        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Local response", "done": True}
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            # Health check succeeds
            health_response = MagicMock()
            health_response.json.return_value = {"models": []}
            health_response.raise_for_status = MagicMock()
            mock_get.return_value = health_response

            with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response

                result = await server.generate(prompt="Test", model="qwen2.5-coder:1.5b")

                assert result == "Local response"

        await server.close()

    @pytest.mark.asyncio
    async def test_checks_local_availability_once(self):
        """Server caches local availability check."""
        server = LocalModelServer()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            health_response = MagicMock()
            health_response.json.return_value = {"models": []}
            health_response.raise_for_status = MagicMock()
            mock_get.return_value = health_response

            # Check twice
            result1 = await server.is_local_available()
            result2 = await server.is_local_available()

            assert result1 is True
            assert result2 is True
            # Should only call once (cached)
            assert mock_get.call_count == 1

        await server.close()

    @pytest.mark.asyncio
    async def test_returns_available_model_names(self):
        """Server returns list of available model names."""
        server = LocalModelServer()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "qwen2.5-coder:1.5b"}, {"name": "qwen2.5-coder:7b"}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            models = await server.get_available_models()

            assert models == ["qwen2.5-coder:1.5b", "qwen2.5-coder:7b"]

        await server.close()

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_local_unavailable(self):
        """Server returns empty list when Ollama unavailable."""
        server = LocalModelServer()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")

            models = await server.get_available_models()

            assert models == []

        await server.close()


class TestLocalModelServerFallback:
    """Test cloud fallback behavior."""

    @pytest.mark.asyncio
    async def test_raises_not_implemented_on_cloud_fallback(self):
        """Server raises NotImplementedError for cloud fallback."""
        server = LocalModelServer(enable_cloud_fallback=True)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")

            with pytest.raises(NotImplementedError, match="Cloud fallback not yet implemented"):
                await server.generate(prompt="Test", prefer_local=True)

        await server.close()

    @pytest.mark.asyncio
    async def test_raises_connection_error_when_fallback_disabled(self):
        """Server raises error when fallback disabled."""
        server = LocalModelServer(enable_cloud_fallback=False)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")

            with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
                mock_post.side_effect = OllamaConnectionError("Cannot connect")

                with pytest.raises(OllamaConnectionError):
                    await server.generate(prompt="Test", prefer_local=True)

        await server.close()
