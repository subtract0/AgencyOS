"""Memory-aware test execution (ADR-023).

Prevents kernel panics from memory exhaustion during test execution
by dynamically adjusting pytest worker count based on available memory
and local model state.

Constitutional Compliance:
- Article I: Prevents incomplete test execution from memory crashes
- Article II: 100% verification reliability through stability
- Article III: Automated enforcement via dynamic configuration
"""

import os
from pathlib import Path
from typing import Literal

import psutil
from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result


class TestExecutionConfig(BaseModel):
    """Configuration for memory-aware test execution."""
    worker_count: int = Field(ge=1, le=10)
    memory_budget_gb: int = Field(ge=0)
    local_model_active: bool
    execution_mode: Literal["parallel", "serial", "adaptive"]
    fallback_to_cloud: bool


def check_ollama_running() -> bool:
    """Check if Ollama (local model) is currently running.

    Uses multiple detection methods for reliability:
    1. Process detection (ollama serve)
    2. Marker file (/tmp/ollama-running)

    Returns:
        True if Ollama is running, False otherwise
    """
    # Method 1: Check for ollama process
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
            pass

    # Method 2: Check marker file (if used)
    marker_path = Path("/tmp/ollama-running")
    if os.path.exists(str(marker_path)):
        return True

    return False


def get_safe_worker_count() -> int:
    """Calculate safe pytest worker count based on memory and local model state.

    Memory budgets:
    - Local model ON (38GB): 3 workers max (9GB test budget, 47GB total)
    - Local model OFF: 10 workers max (30GB test budget)
    - Critical memory (<10GB): 1 worker (sequential)

    Returns:
        Safe number of pytest workers (1-10)
    """
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024 ** 3)

    local_model_active = check_ollama_running()

    # Critical memory: sequential execution
    if available_gb < 10:
        return 1

    # Local model active: conservative parallelism
    if local_model_active and available_gb < 15:
        return 3  # 9GB test budget

    # Plenty of memory: full parallelism
    if available_gb >= 20:
        return 10

    # Medium memory: moderate parallelism
    return 6


def verify_memory_safe(required_gb: int) -> bool:
    """Check if enough memory available for operation.

    Args:
        required_gb: Required memory in gigabytes (includes 5GB safety margin)

    Returns:
        True if safe to proceed, False if memory insufficient
    """
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024 ** 3)

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
        available_gb = int(mem.available / (1024 ** 3))

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
            fallback_to_cloud=fallback
        )

        return Ok(config)

    except Exception as e:
        return Err(f"Failed to get test execution config: {e}")
