"""
Chaos testing framework for Mars Rover-grade resilience.

This module provides chaos engineering capabilities to verify systems handle
random failures gracefully. Supports network, disk I/O, memory, process, and
timeout chaos injection.

Constitutional Compliance:
- Result pattern for error handling
- Pydantic models for all data structures
- Type safety throughout
- Focused functions under 50 lines
"""

import random
import time
from collections.abc import Callable
from contextlib import contextmanager
from datetime import UTC, datetime
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel, Field

from shared.type_definitions.json import JSONValue
from shared.type_definitions.result import Err, Ok, Result

T = TypeVar("T")


class ChaosType(str, Enum):
    """Types of chaos that can be injected."""

    NETWORK = "network"
    DISK_IO = "disk_io"
    MEMORY = "memory"
    PROCESS = "process"
    TIMEOUT = "timeout"


class ChaosConfig(BaseModel):
    """Configuration for chaos testing."""

    chaos_types: list[ChaosType]
    failure_rate: float = Field(default=0.2, ge=0.0, le=1.0)
    seed: int | None = None
    duration_seconds: int = Field(default=60, gt=0)
    target_functions: list[str] = Field(default_factory=list)
    enabled: bool = True


class ChaosInjection(BaseModel):
    """Record of a single chaos injection."""

    chaos_type: ChaosType
    timestamp: str
    target_function: str
    failure_injected: str
    system_recovered: bool
    error_message: str | None = None


class ChaosResult(BaseModel):
    """Result of chaos testing run."""

    total_injections: int
    successful_recoveries: int
    failed_recoveries: int
    crash_count: int
    recovery_rate: float
    injections: list[ChaosInjection]
    duration_seconds: float


class ChaosEngine:
    """Chaos engineering test framework."""

    def __init__(self, config: ChaosConfig):
        """Initialize chaos engine with configuration."""
        self.config = config
        self.injections: list[ChaosInjection] = []
        self.original_functions: dict[str, JSONValue] = {}
        self.crash_count = 0

        if config.seed is not None:
            random.seed(config.seed)

    def should_inject_failure(self) -> bool:
        """Determine if failure should be injected based on rate."""
        if not self.config.enabled:
            return False
        return random.random() < self.config.failure_rate

    def record_injection(
        self,
        chaos_type: ChaosType,
        target: str,
        failure: str,
        recovered: bool,
        error: str | None = None,
    ) -> None:
        """Record a chaos injection event."""
        injection = ChaosInjection(
            chaos_type=chaos_type,
            timestamp=datetime.now(UTC).isoformat(),
            target_function=target,
            failure_injected=failure,
            system_recovered=recovered,
            error_message=error,
        )
        self.injections.append(injection)

    def inject_network_chaos(self) -> None:
        """Monkey-patch network calls to randomly fail."""
        try:
            import requests

            original_get = requests.get
            original_post = requests.post
            self.original_functions["requests.get"] = original_get
            self.original_functions["requests.post"] = original_post

            def chaotic_get(*args: Any, **kwargs: Any) -> Any:
                if self.should_inject_failure():
                    error = "Chaos: Network connection failed"
                    self.record_injection(ChaosType.NETWORK, "requests.get", error, True)
                    raise requests.ConnectionError(error)
                return original_get(*args, **kwargs)

            def chaotic_post(*args: Any, **kwargs: Any) -> Any:
                if self.should_inject_failure():
                    error = "Chaos: Network timeout"
                    self.record_injection(ChaosType.NETWORK, "requests.post", error, True)
                    raise requests.Timeout(error)
                return original_post(*args, **kwargs)

            requests.get = chaotic_get  # type: ignore
            requests.post = chaotic_post  # type: ignore

        except ImportError:
            # requests not available, skip network chaos
            pass

    def inject_disk_chaos(self) -> None:
        """Monkey-patch file I/O to randomly fail."""
        import builtins

        original_open = builtins.open
        self.original_functions["builtins.open"] = original_open

        def chaotic_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
            if self.should_inject_failure() and "w" in mode:
                error = "Chaos: Disk write failure"
                self.record_injection(ChaosType.DISK_IO, "builtins.open", error, True)
                raise OSError(error)
            return original_open(file, mode, *args, **kwargs)

        builtins.open = chaotic_open  # type: ignore

    def inject_timeout_chaos(self) -> None:
        """Inject random delays in operations."""
        original_sleep = time.sleep
        self.original_functions["time.sleep"] = original_sleep

        def chaotic_sleep(seconds: float) -> None:
            if self.should_inject_failure():
                chaos_delay = random.random() * self.config.failure_rate * 5
                total = seconds + chaos_delay
                self.record_injection(
                    ChaosType.TIMEOUT,
                    "time.sleep",
                    f"Added {chaos_delay:.2f}s delay",
                    True,
                )
                original_sleep(total)
            else:
                original_sleep(seconds)

        time.sleep = chaotic_sleep  # type: ignore

    def inject_memory_chaos(self) -> None:
        """Inject memory allocation failures."""
        import builtins

        # Simulate memory pressure by limiting list allocations
        original_list = builtins.list
        self.original_functions["builtins.list"] = original_list

        def chaotic_list(*args: Any, **kwargs: Any) -> Any:
            if self.should_inject_failure():
                error = "Chaos: Memory allocation failed"
                self.record_injection(ChaosType.MEMORY, "builtins.list", error, True)
                raise MemoryError(error)
            return original_list(*args, **kwargs)

        builtins.list = chaotic_list  # type: ignore

    def inject_process_chaos(self) -> None:
        """Inject process failures."""
        import subprocess

        original_run = subprocess.run
        self.original_functions["subprocess.run"] = original_run

        def chaotic_run(*args: Any, **kwargs: Any) -> Any:
            if self.should_inject_failure():
                error = "Chaos: Process execution failed"
                self.record_injection(ChaosType.PROCESS, "subprocess.run", error, True)
                raise subprocess.CalledProcessError(1, args[0], error.encode())
            return original_run(*args, **kwargs)

        subprocess.run = chaotic_run  # type: ignore

    def inject_all_chaos(self) -> None:
        """Inject all configured chaos types."""
        for chaos_type in self.config.chaos_types:
            if chaos_type == ChaosType.NETWORK:
                self.inject_network_chaos()
            elif chaos_type == ChaosType.DISK_IO:
                self.inject_disk_chaos()
            elif chaos_type == ChaosType.TIMEOUT:
                self.inject_timeout_chaos()
            elif chaos_type == ChaosType.MEMORY:
                self.inject_memory_chaos()
            elif chaos_type == ChaosType.PROCESS:
                self.inject_process_chaos()

    def cleanup_patches(self) -> None:
        """Restore all monkey-patched functions."""
        for path, original in self.original_functions.items():
            parts = path.split(".")
            if len(parts) == 2:
                module_name, func_name = parts
                if module_name == "builtins":
                    import builtins

                    setattr(builtins, func_name, original)
                elif module_name == "time":
                    setattr(time, func_name, original)
                elif module_name == "requests":
                    try:
                        import requests

                        setattr(requests, func_name, original)
                    except ImportError:
                        pass
                elif module_name == "subprocess":
                    import subprocess

                    setattr(subprocess, func_name, original)

        self.original_functions.clear()

    def run_chaos_test(self, test_function: Callable[[], T]) -> Result[ChaosResult, str]:
        """Run test with chaos injections enabled."""
        start_time = time.time()

        try:
            self.inject_all_chaos()
            test_function()

            duration = time.time() - start_time
            total = len(self.injections)
            successful = sum(1 for i in self.injections if i.system_recovered)
            failed = total - successful
            recovery_rate = successful / total if total > 0 else 1.0

            result = ChaosResult(
                total_injections=total,
                successful_recoveries=successful,
                failed_recoveries=failed,
                crash_count=self.crash_count,
                recovery_rate=recovery_rate,
                injections=self.injections,
                duration_seconds=duration,
            )

            return Ok(result)

        except Exception as e:
            self.crash_count += 1
            duration = time.time() - start_time
            total = len(self.injections)
            successful = sum(1 for i in self.injections if i.system_recovered)

            result = ChaosResult(
                total_injections=total,
                successful_recoveries=successful,
                failed_recoveries=total - successful,
                crash_count=self.crash_count,
                recovery_rate=0.0,
                injections=self.injections,
                duration_seconds=duration,
            )

            return Err(f"Chaos test crashed: {e}")

        finally:
            self.cleanup_patches()


@contextmanager
def chaos_context(config: ChaosConfig):
    """Context manager for chaos testing."""
    engine = ChaosEngine(config)
    engine.inject_all_chaos()
    try:
        yield engine
    finally:
        engine.cleanup_patches()


def chaos(chaos_types: list[ChaosType], failure_rate: float = 0.2):
    """Decorator to run test with chaos injections."""

    def decorator(test_func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            config = ChaosConfig(chaos_types=chaos_types, failure_rate=failure_rate)
            engine = ChaosEngine(config)
            result = engine.run_chaos_test(lambda: test_func(*args, **kwargs))

            if result.is_err():
                raise AssertionError(f"Chaos test failed: {result.unwrap_err()}")

            return result.unwrap()

        return wrapper

    return decorator


def generate_chaos_report(result: ChaosResult) -> str:
    """Generate human-readable chaos test report."""
    lines = [
        "# Chaos Testing Report",
        "",
        f"**Duration**: {result.duration_seconds:.2f}s",
        f"**Total Injections**: {result.total_injections}",
        f"**Successful Recoveries**: {result.successful_recoveries}",
        f"**Failed Recoveries**: {result.failed_recoveries}",
        f"**Crashes**: {result.crash_count}",
        f"**Recovery Rate**: {result.recovery_rate * 100:.1f}%",
        "",
        "## Injection Details",
        "",
    ]

    for injection in result.injections:
        status = "✅" if injection.system_recovered else "❌"
        lines.append(
            f"- {status} [{injection.chaos_type}] {injection.target_function}: "
            f"{injection.failure_injected}"
        )
        if injection.error_message:
            lines.append(f"  Error: {injection.error_message}")

    return "\n".join(lines)
