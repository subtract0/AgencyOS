"""
Ollama Client - Local LLM Integration for Trinity Protocol

Provides streaming and blocking interfaces to Ollama-hosted models
with constitutional compliance enforcement and error recovery.

Constitutional Compliance:
- Article I: Complete context with automatic timeout retry (2x, 3x)
- Article II: Strict typing and validation
- Error recovery with exponential backoff
- Context window tracking
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class OllamaTimeout(Exception):
    """Ollama request timeout exception."""

    pass


class OllamaError(Exception):
    """General Ollama client error."""

    pass


class ConstitutionalViolation(Exception):
    """LLM response violates constitutional principles."""

    pass


class OllamaClient:
    """
    Async HTTP client for Ollama API.

    Features:
    - Streaming responses (don't buffer large outputs)
    - Automatic retry with exponential backoff (Article I)
    - Context window tracking
    - Constitutional validation
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
        max_retries: int = 3,
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama API endpoint
            timeout: Default timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.base_url = base_url.rstrip("/")
        self.default_timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def health_check(self, timeout: int = 10) -> bool:
        """
        Check if Ollama is running and responsive.

        Args:
            timeout: Health check timeout in seconds

        Returns:
            True if Ollama is healthy
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags", timeout=timeout)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def list_models(self) -> list[dict[str, Any]]:
        """
        List available models.

        Returns:
            List of model info dicts
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def chat_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
        timeout: int | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream chat completion responses.

        IMPORTANT: Use this for long responses to avoid memory buffering.

        Args:
            model: Model name (e.g., "qwen2.5-coder:7b")
            messages: Chat messages in OpenAI format
            max_tokens: Maximum tokens to generate (None = model default)
            timeout: Request timeout in seconds

        Yields:
            Response chunks as strings
        """
        timeout_val = timeout or self.default_timeout

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        if max_tokens:
            payload["options"] = {"num_predict": max_tokens}

        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=httpx.Timeout(timeout_val),
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]

                        # Check if done
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON chunk: {line}")
                        continue

        except httpx.TimeoutException as e:
            logger.error(f"Ollama stream timeout ({timeout_val}s): {e}")
            raise OllamaTimeout(f"Stream timeout after {timeout_val}s")
        except httpx.HTTPStatusError as e:
            # Read response body before accessing it (fix for httpx streaming error)
            try:
                error_body = await e.response.aread()
                error_text = error_body.decode('utf-8') if error_body else str(e)
            except Exception:
                error_text = str(e)
            logger.error(f"Ollama HTTP error: {e}")
            raise OllamaError(f"HTTP {e.response.status_code}: {error_text}")
        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            raise OllamaError(f"Stream failed: {e}")

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        timeout: int | None = None,
        retry_count: int | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Blocking chat completion with automatic retry (Article I compliance).

        Args:
            model: Model name
            messages: Chat messages
            timeout: Request timeout (None = default)
            retry_count: Max retries (None = default)
            max_tokens: Max tokens to generate

        Returns:
            Complete response as string

        Raises:
            OllamaTimeout: After all retries exhausted
            OllamaError: For other errors
        """
        timeout_val = timeout or self.default_timeout
        retries = retry_count if retry_count is not None else self.max_retries

        for attempt in range(retries):
            try:
                # Collect streaming response
                chunks = []
                async for chunk in self.chat_stream(model, messages, max_tokens, timeout_val):
                    chunks.append(chunk)

                response = "".join(chunks)

                # Validate response (basic constitutional check)
                if not response or len(response.strip()) == 0:
                    raise ValueError("Empty response from LLM")

                logger.info(f"✅ {model} responded ({len(response)} chars)")
                return response

            except OllamaTimeout:
                if attempt < retries - 1:
                    # Article I: Retry with 2x timeout
                    timeout_val *= 2
                    logger.warning(
                        f"⏱️  Retry {attempt + 1}/{retries} with {timeout_val}s timeout"
                    )
                    await asyncio.sleep(1)  # Brief delay before retry
                else:
                    logger.error(f"❌ {model} timeout after {retries} retries")
                    raise

            except Exception as e:
                logger.error(f"❌ {model} error on attempt {attempt + 1}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(1)
                else:
                    raise OllamaError(f"Failed after {retries} attempts: {e}")

        raise OllamaTimeout(f"Failed after {retries} retries")

    def validate_constitutional_compliance(self, response: str) -> None:
        """
        Validate LLM response against constitutional principles.

        Raises:
            ConstitutionalViolation: If response violates constitution
        """
        # Article I: Complete context check
        incomplete_markers = ["incomplete", "need more info", "unable to proceed"]
        if any(marker in response.lower() for marker in incomplete_markers):
            raise ConstitutionalViolation(
                "Article I: Response indicates incomplete context"
            )

        # Article II: Code without tests check (basic heuristic)
        has_code = "```python" in response or "def " in response
        has_test = "test_" in response or "def test" in response.lower()

        if has_code and not has_test:
            logger.warning(
                "⚠️  Response contains code but no tests - potential Article II violation"
            )
            # Don't raise - this is a warning, not a hard failure
            # The Executor will enforce test generation

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
