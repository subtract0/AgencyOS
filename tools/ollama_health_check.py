"""
Ollama Health Check Tool - Comprehensive health validation for local LLM.

Provides detailed health status checking for Ollama instances with:
- Connection validation
- Docker detection
- Model availability
- Inference testing
- Retry logic with exponential backoff (Article I)

Constitutional Compliance:
- Article I: Complete context with automatic retry (2x, 3x)
- Article II: Strict typing with Pydantic, Result pattern
- Functions under 50 lines
"""

import asyncio
import logging
import subprocess
from typing import Optional

import aiohttp
from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)


class OllamaHealthError(Exception):
    """Exception for Ollama health check failures."""

    pass


class OllamaHealthStatus(BaseModel):
    """
    Health status for Ollama instance.

    Constitutional Law #2: Strict typing with Pydantic (no Dict[Any, Any])
    """

    is_running: bool = Field(description="Whether Ollama is running and responsive")
    is_docker: bool = Field(description="Whether Ollama is running in Docker")
    endpoint: str = Field(description="Ollama API endpoint")
    models_available: list[str] = Field(
        default_factory=list, description="List of available model names"
    )
    inference_working: bool = Field(
        description="Whether inference requests are working"
    )
    error_message: str | None = Field(
        default=None, description="Error message if health check failed"
    )


def detect_docker_ollama() -> bool:
    """
    Detect if Ollama is running in Docker.

    Returns:
        True if Docker container with 'ollama' in name is running

    Constitutional Law #8: Focused function <50 lines
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            containers = result.stdout.lower()
            return "ollama" in containers

        return False

    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
        logger.debug(f"Docker detection failed (Docker may not be installed): {e}")
        return False


async def check_inference(
    endpoint: str, timeout: int = 10
) -> Result[bool, OllamaHealthError]:
    """
    Check if Ollama can perform inference.

    Args:
        endpoint: Ollama API endpoint
        timeout: Request timeout in seconds

    Returns:
        Result with True if inference works, OllamaHealthError otherwise

    Constitutional Law #5: Result pattern for error handling
    Constitutional Law #8: Focused function <50 lines
    """
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "qwen3-coder:30b",
                "prompt": "1+1=",
                "stream": False,
            }

            async with session.post(
                f"{endpoint}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                response.raise_for_status()
                data = await response.json()

                # Validate response structure
                if "response" in data:
                    return Ok(True)

                return Err(OllamaHealthError("Invalid inference response format"))

    except TimeoutError:
        return Err(OllamaHealthError(f"Inference timeout after {timeout}s"))
    except aiohttp.ClientError as e:
        return Err(OllamaHealthError(f"Inference request failed: {e}"))
    except Exception as e:
        return Err(OllamaHealthError(f"Inference test error: {e}"))


async def check_ollama_health(
    endpoint: str = "http://localhost:11434",
    timeout: int = 10,
    max_retries: int = 3,
) -> Result[OllamaHealthStatus, OllamaHealthError]:
    """
    Comprehensive health check for Ollama instance.

    Performs:
    1. Connection validation (/api/tags)
    2. Docker detection
    3. Model availability check
    4. Inference test (optional, may fail if no models)

    Args:
        endpoint: Ollama API endpoint (default: http://localhost:11434)
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts (Article I compliance)

    Returns:
        Result with OllamaHealthStatus or OllamaHealthError

    Constitutional Compliance:
    - Article I: Retry with exponential backoff on timeout
    - Law #2: Strict typing with Pydantic
    - Law #5: Result pattern for error handling
    - Law #8: Orchestration function, delegates to helpers
    """
    is_docker = detect_docker_ollama()
    current_timeout = timeout

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: Check if Ollama is running
                async with session.get(
                    f"{endpoint}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=current_timeout),
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                    # Extract model names
                    models_raw = data.get("models", [])
                    models = [m.get("name", "") for m in models_raw if "name" in m]

                    # Step 2: Check inference if models available
                    inference_working = False
                    if models:
                        inference_result = await check_inference(endpoint, timeout)
                        inference_working = inference_result.is_ok()
                    else:
                        logger.warning("No models available for inference test")

                    # Success - return healthy status
                    return Ok(
                        OllamaHealthStatus(
                            is_running=True,
                            is_docker=is_docker,
                            endpoint=endpoint,
                            models_available=models,
                            inference_working=inference_working,
                            error_message=None,
                        )
                    )

        except TimeoutError:
            if attempt < max_retries - 1:
                # Article I: Retry with 2x timeout
                current_timeout *= 2
                logger.warning(
                    f"Health check timeout, retry {attempt + 1}/{max_retries} "
                    f"with {current_timeout}s timeout"
                )
                await asyncio.sleep(1)
                continue
            else:
                error_msg = f"Timeout after {max_retries} retries"
                logger.error(error_msg)
                return Err(OllamaHealthError(error_msg))

        except aiohttp.ClientError as e:
            error_msg = f"Connection error: {e}"
            logger.error(error_msg)
            return Err(OllamaHealthError(error_msg))

        except Exception as e:
            error_msg = f"Health check failed: {e}"
            logger.error(error_msg)
            return Err(OllamaHealthError(error_msg))

    # Should not reach here, but satisfy type checker
    return Err(OllamaHealthError(f"Failed after {max_retries} retries"))
