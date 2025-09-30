"""
Local Model Server for Trinity Protocol

Provides Ollama adapter for local model inference with fallback to cloud APIs.
Enables hybrid intelligence: local for routine tasks, cloud for critical/complex.

Supported Models:
- qwen2.5-coder:1.5b - Fast detection (AUDITLEARN)
- qwen2.5-coder:7b - Standard execution (EXECUTE)
- codestral-22b - Advanced planning (PLAN)

Constitutional Compliance:
- Article I: Complete context - retry on failures
- Hybrid Doctrine: Local default, cloud escalation for critical tasks
"""

import httpx
from typing import Optional, Dict, Any, List, AsyncIterator
import json
import asyncio
from datetime import datetime


class OllamaClient:
    """
    Async client for Ollama local model server.

    Provides streaming and non-streaming inference with automatic retry.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
        max_retries: int = 3
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama server URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate completion from local model.

        Args:
            model: Model name (e.g., "qwen2.5-coder:1.5b")
            prompt: User prompt
            system: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Enable streaming response

        Returns:
            Response dict with 'response' field

        Raises:
            OllamaConnectionError: If Ollama server unavailable
            OllamaGenerationError: If generation fails
        """
        client = await self._get_client()

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
            }
        }

        if system:
            payload["system"] = system

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        for attempt in range(self.max_retries):
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()

                if stream:
                    # Return full response for streaming handler
                    return {"stream": True, "response_obj": response}
                else:
                    result = response.json()
                    return {
                        "response": result.get("response", ""),
                        "model": result.get("model", model),
                        "created_at": result.get("created_at"),
                        "done": result.get("done", True)
                    }

            except httpx.ConnectError as e:
                if attempt == self.max_retries - 1:
                    raise OllamaConnectionError(
                        f"Cannot connect to Ollama at {self.base_url}"
                    ) from e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except httpx.HTTPStatusError as e:
                if attempt == self.max_retries - 1:
                    raise OllamaGenerationError(
                        f"Generation failed: {e.response.text}"
                    ) from e
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise OllamaGenerationError(f"Unexpected error: {str(e)}") from e
                await asyncio.sleep(2 ** attempt)

        # Should never reach here due to raises in loop
        raise OllamaGenerationError("Max retries exceeded")

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[str]:
        """
        Generate streaming completion from local model.

        Args:
            model: Model name
            prompt: User prompt
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Token chunks as they're generated
        """
        result = await self.generate(
            model=model,
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )

        response_obj = result["response_obj"]

        async for line in response_obj.aiter_lines():
            if line.strip():
                try:
                    chunk = json.loads(line)
                    if chunk.get("done", False):
                        break
                    if "response" in chunk and chunk["response"]:
                        yield chunk["response"]
                except json.JSONDecodeError:
                    continue

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models on Ollama server.

        Returns:
            List of model info dicts
        """
        client = await self._get_client()

        try:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            result = response.json()
            return result.get("models", [])

        except Exception as e:
            raise OllamaConnectionError(f"Failed to list models: {str(e)}") from e

    async def health_check(self) -> bool:
        """
        Check if Ollama server is healthy.

        Returns:
            True if server is responding
        """
        try:
            await self.list_models()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close HTTP client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class LocalModelServer:
    """
    High-level interface for local model inference.

    Provides unified API for local models with automatic fallback to cloud.
    """

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        enable_cloud_fallback: bool = True
    ):
        """
        Initialize local model server.

        Args:
            ollama_url: Ollama server URL
            enable_cloud_fallback: Enable automatic cloud fallback on local failure
        """
        self.ollama = OllamaClient(base_url=ollama_url)
        self.enable_cloud_fallback = enable_cloud_fallback
        self._local_available: Optional[bool] = None

    async def is_local_available(self) -> bool:
        """
        Check if local models are available.

        Returns:
            True if Ollama server is healthy
        """
        if self._local_available is None:
            self._local_available = await self.ollama.health_check()
        return self._local_available

    async def generate(
        self,
        prompt: str,
        model: str = "qwen2.5-coder:1.5b",
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = 512,
        prefer_local: bool = True
    ) -> str:
        """
        Generate completion with automatic local/cloud routing.

        Args:
            prompt: User prompt
            model: Model name (local or cloud)
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            prefer_local: Prefer local inference when available

        Returns:
            Generated text
        """
        if prefer_local:
            local_available = await self.is_local_available()
            if local_available:
                try:
                    result = await self.ollama.generate(
                        model=model,
                        prompt=prompt,
                        system=system,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    return result["response"]

                except (OllamaConnectionError, OllamaGenerationError):
                    if not self.enable_cloud_fallback:
                        raise
                    # Fall through to cloud fallback
            else:
                # Local not available - check if we should try cloud
                if not self.enable_cloud_fallback:
                    raise OllamaConnectionError("Local models not available and cloud fallback is disabled")

        # Cloud fallback (to be implemented with actual API clients)
        raise NotImplementedError(
            "Cloud fallback not yet implemented. Ensure Ollama is running."
        )

    async def generate_stream(
        self,
        prompt: str,
        model: str = "qwen2.5-coder:1.5b",
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = 512
    ) -> AsyncIterator[str]:
        """
        Generate streaming completion.

        Args:
            prompt: User prompt
            model: Model name
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            Token chunks
        """
        if not await self.is_local_available():
            raise OllamaConnectionError("Local models not available")

        async for chunk in self.ollama.generate_stream(
            model=model,
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            yield chunk

    async def get_available_models(self) -> List[str]:
        """
        Get list of available model names.

        Returns:
            List of model names
        """
        if not await self.is_local_available():
            return []

        models = await self.ollama.list_models()
        return [m["name"] for m in models]

    async def close(self) -> None:
        """Close connections."""
        await self.ollama.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class OllamaConnectionError(Exception):
    """Raised when cannot connect to Ollama server."""
    pass


class OllamaGenerationError(Exception):
    """Raised when generation fails."""
    pass
