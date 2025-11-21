"""Memory-aware test execution (ADR-023).

Prevents kernel panics from memory exhaustion during test execution
by dynamically adjusting pytest worker count based on available memory
and local model state.

Constitutional Compliance:
- Article I: Prevents incomplete test execution from memory crashes
- Article II: 100% verification reliability through stability
- Article III: Automated enforcement via dynamic configuration
"""

import asyncio
import os
from pathlib import Path
from typing import Literal

import psutil
from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result
from tools.ollama_health_check import check_ollama_health

MAX_WORKERS = 12


class TestExecutionConfig(BaseModel):
    """Configuration for memory-aware test execution."""

    __test__ = False  # Tell pytest this is not a test class

    worker_count: int = Field(ge=1, le=MAX_WORKERS)
    memory_budget_gb: int = Field(ge=0)
    local_model_active: bool
    execution_mode: Literal["parallel", "serial", "adaptive"]
    fallback_to_cloud: bool


def check_ollama_running() -> bool:
    """Check if Ollama (local model) is currently running.

    Uses comprehensive health check to detect both Docker and native Ollama:
    1. Health check (async API validation)
    2. Docker detection (container inspection)
    3. Process detection (fallback for native)
    4. Marker file (/tmp/ollama-running, fallback)

    Returns:
        True if Ollama is running (Docker or native), False otherwise

    Constitutional Compliance:
    - Article I: Health check uses timeout and retry logic
    - ADR-023: Accurate detection for memory-aware worker adjustment
    """
    # Method 1: Comprehensive health check (detects Docker + native)
    try:
        # Run with timeout to prevent hanging
        async def _check_with_timeout():
            try:
                return await asyncio.wait_for(
                    check_ollama_health(timeout=2, max_retries=1),
                    timeout=5.0,  # Overall timeout for health check
                )
            except TimeoutError:
                return Err("Health check timeout")

        result = asyncio.run(_check_with_timeout())

        if isinstance(result, Ok):
            return result.value.is_running

    except Exception:
        # Fallback to process/marker detection if health check fails
        pass

    # Method 2: Check for ollama process (native only)
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and "ollama" in proc.info["name"].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
            pass

    # Method 3: Check marker file (if used)
    marker_path = Path("/tmp/ollama-running")
    if os.path.exists(str(marker_path)):
        return True

    return False


def get_safe_worker_count() -> int:
    """Calculate safe pytest worker count based on memory and local model state.

    Memory budgets (Updated 2025-11-21 for M4 Max 128GB):
    - M4 Max 128GB (>120GB total): 12 workers (full performance cores)
    - Large memory (>60GB): 6 workers
    - Medium memory (20-60GB): 3 workers
    - Critical memory (<10GB): 1 worker (sequential)

    Local model consideration:
    - Current setup uses REMOTE LM Studio (no local RAM impact)
    - If local model running: reduce by 50% for safety

    Returns:
        Safe number of pytest workers (1-12 depending on available memory)
    """
    mem = psutil.virtual_memory()

    raw_total = getattr(mem, "total", 0)
    if isinstance(raw_total, (int, float)):
        total_gb = raw_total / (1024**3)
    else:
        total_gb = 0

    raw_available = getattr(mem, "available", 0)
    if isinstance(raw_available, (int, float)):
        available_gb = raw_available / (1024**3)
    else:
        available_gb = 0

    local_model_active = check_ollama_running()

    # Manual override for advanced scenarios (use with caution)
    forced_workers = os.getenv("AGENCY_FORCE_TEST_WORKERS")
    if forced_workers:
        try:
            return max(1, min(MAX_WORKERS, int(forced_workers)))
        except ValueError:
            pass  # Ignore invalid overrides and fall through to auto-detection

    # Critical memory: sequential execution
    if available_gb < 10:
        return 1

    cpu_count = os.cpu_count() or 12

    high_memory_mode = total_gb >= 120

    # M4 Max 128GB detected (or similar high-memory system)
    if high_memory_mode:
        base_workers = min(MAX_WORKERS, cpu_count)   # Utilize all performance cores
    elif available_gb >= 60:
        base_workers = min(6, cpu_count)   # Large memory system
    elif available_gb >= 20:
        base_workers = min(3, cpu_count)   # Medium memory system
    else:
        base_workers = 1   # Low memory

    # Local model active: reduce workers by 50% for safety unless we're on a high-memory config
    if local_model_active and not high_memory_mode:
        return max(1, base_workers // 2)

    return base_workers


def verify_memory_safe(required_gb: int) -> bool:
    """Check if enough memory available for operation.

    Args:
        required_gb: Required memory in gigabytes (includes 5GB safety margin)

    Returns:
        True if safe to proceed, False if memory insufficient
    """
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024**3)

    # 5GB safety margin for system stability
    return available_gb >= (required_gb + 5)


def get_test_execution_config() -> Result[TestExecutionConfig, str]:
    """Get memory-aware test execution configuration.

    Returns:
        Result containing TestExecutionConfig or error message
    """
    try:
        worker_count = get_safe_worker_count()
        local_model_active = check_ollama_running()

        mem = psutil.virtual_memory()
        available_gb = int(mem.available / (1024**3))

        # Determine execution mode
        if worker_count == 1:
            mode = "serial"
        elif worker_count <= 3:
            mode = "adaptive"
        else:
            mode = "parallel"

        # Trigger cloud fallback if memory very low
        fallback = available_gb < 8

        config = TestExecutionConfig(
            worker_count=worker_count,
            memory_budget_gb=available_gb,
            local_model_active=local_model_active,
            execution_mode=mode,
            fallback_to_cloud=fallback,
        )

        return Ok(config)

    except Exception as e:
        return Err(f"Failed to get test execution config: {e}")
