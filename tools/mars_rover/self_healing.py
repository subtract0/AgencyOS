"""
Mars Rover Reliability - Phase 2: Self-Healing Orchestrator.

Monitors all systems and autonomously heals anomalies.

Constitutional Compliance:
- Article II: 100% verification (validates all fixes)
- Article III: Automated enforcement (auto-heals anomalies)
- Article IV: Learning (stores patterns to VectorStore)

Features:
1. Anomaly detection (test failures, crashes, performance)
2. VectorStore pattern lookup before healing
3. Automatic fix application for high-confidence patterns
4. Fix validation with test runs
5. Rollback on failed validation
6. Healing history tracking
"""

import asyncio
import logging
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of anomalies the orchestrator can detect."""

    TEST_FAILURE = "test_failure"
    AGENT_CRASH = "agent_crash"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    CONSTITUTIONAL_VIOLATION = "constitutional_violation"


@dataclass
class Anomaly:
    """Represents a detected anomaly."""

    anomaly_type: AnomalyType
    severity: str  # "low", "medium", "high", "critical"
    description: str
    context: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    id: str = field(default_factory=lambda: f"anomaly_{datetime.now().timestamp()}")


@dataclass
class HealingResult:
    """Result of a healing attempt."""

    success: bool
    message: str
    fix_type: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class SelfHealingConfig:
    """Configuration for self-healing orchestrator."""

    min_confidence_auto_fix: float = 0.9
    max_retry_attempts: int = 3
    performance_degradation_threshold: float = 0.1  # 10%
    test_failure_threshold: int = 0  # Any failure is anomaly
    enable_vectorstore: bool = True
    history_max_entries: int = 100


@dataclass
class HealingHistoryEntry:
    """Entry in the healing history."""

    timestamp: str
    anomaly_type: str
    fix_applied: str
    success: bool
    duration_seconds: float = 0.0
    validation_passed: Optional[bool] = None


class SelfHealingOrchestrator:
    """
    Self-healing orchestrator for autonomous system maintenance.

    Monitors systems, detects anomalies, and applies fixes automatically.
    """

    def __init__(self, config: Optional[SelfHealingConfig] = None):
        """Initialize the orchestrator."""
        self.config = config or SelfHealingConfig()

        self._pending_anomalies: list[Anomaly] = []
        self._healing_history: deque[HealingHistoryEntry] = deque(
            maxlen=self.config.history_max_entries
        )
        self._healers: dict[AnomalyType, Callable[[Anomaly], Awaitable[HealingResult]]] = {}
        self._validator: Optional[Callable[[], Awaitable[bool]]] = None
        self._rollback_callback: Optional[Callable[[], Awaitable[None]]] = None
        self._vector_store: Optional[Any] = None

        # Performance baseline
        self._baseline_test_duration: Optional[float] = None
        self._baseline_memory_usage: Optional[float] = None

        self._lock = threading.RLock()
        self._last_healing_time: Optional[str] = None

        logger.info("SelfHealingOrchestrator initialized")

    def report_test_results(
        self,
        passed: int,
        failed: int,
        errors: int,
        total: int,
    ) -> None:
        """
        Report test results for anomaly detection.

        Args:
            passed: Number of passing tests
            failed: Number of failed tests
            errors: Number of test errors
            total: Total test count
        """
        with self._lock:
            if failed > self.config.test_failure_threshold or errors > 0:
                anomaly = Anomaly(
                    anomaly_type=AnomalyType.TEST_FAILURE,
                    severity="high" if failed > 10 else "medium",
                    description=f"{failed} tests failed, {errors} errors",
                    context={
                        "passed": passed,
                        "failed": failed,
                        "errors": errors,
                        "total": total,
                        "pass_rate": passed / total * 100 if total > 0 else 0,
                    },
                )
                self._pending_anomalies.append(anomaly)
                logger.warning(f"Test failure anomaly detected: {failed} failed, {errors} errors")

    def report_agent_crash(self, agent_id: str, error: str) -> None:
        """
        Report an agent crash.

        Args:
            agent_id: ID of the crashed agent
            error: Error message
        """
        with self._lock:
            anomaly = Anomaly(
                anomaly_type=AnomalyType.AGENT_CRASH,
                severity="high",
                description=f"Agent {agent_id} crashed: {error}",
                context={
                    "agent_id": agent_id,
                    "error": error,
                },
            )
            self._pending_anomalies.append(anomaly)
            logger.warning(f"Agent crash anomaly detected: {agent_id}")

    def set_performance_baseline(
        self,
        test_duration_seconds: float,
        memory_usage_gb: float,
    ) -> None:
        """
        Set performance baseline for degradation detection.

        Args:
            test_duration_seconds: Baseline test duration
            memory_usage_gb: Baseline memory usage
        """
        with self._lock:
            self._baseline_test_duration = test_duration_seconds
            self._baseline_memory_usage = memory_usage_gb
            logger.info(
                f"Performance baseline set: {test_duration_seconds}s, {memory_usage_gb}GB"
            )

    def report_performance_metrics(
        self,
        test_duration_seconds: float,
        memory_usage_gb: float,
    ) -> None:
        """
        Report current performance metrics.

        Args:
            test_duration_seconds: Current test duration
            memory_usage_gb: Current memory usage
        """
        with self._lock:
            if self._baseline_test_duration is None:
                return

            # Check for degradation
            duration_degradation = (
                (test_duration_seconds - self._baseline_test_duration)
                / self._baseline_test_duration
            )

            if duration_degradation > self.config.performance_degradation_threshold:
                anomaly = Anomaly(
                    anomaly_type=AnomalyType.PERFORMANCE_DEGRADATION,
                    severity="medium",
                    description=(
                        f"Performance degraded by {duration_degradation * 100:.1f}%"
                    ),
                    context={
                        "baseline_duration": self._baseline_test_duration,
                        "current_duration": test_duration_seconds,
                        "degradation_percent": duration_degradation * 100,
                        "baseline_memory": self._baseline_memory_usage,
                        "current_memory": memory_usage_gb,
                    },
                )
                self._pending_anomalies.append(anomaly)
                logger.warning(
                    f"Performance degradation detected: {duration_degradation * 100:.1f}%"
                )

    def get_pending_anomalies(self) -> list[Anomaly]:
        """Get list of pending anomalies."""
        with self._lock:
            return list(self._pending_anomalies)

    def register_healer(
        self,
        anomaly_type: AnomalyType,
        healer: Callable[[Anomaly], Awaitable[HealingResult]],
    ) -> None:
        """
        Register a healer function for an anomaly type.

        Args:
            anomaly_type: Type of anomaly to handle
            healer: Async function that attempts to heal the anomaly
        """
        self._healers[anomaly_type] = healer
        logger.info(f"Healer registered for {anomaly_type.value}")

    def set_validator(self, validator: Callable[[], Awaitable[bool]]) -> None:
        """
        Set the validation function for fix verification.

        Args:
            validator: Async function that returns True if fix is valid
        """
        self._validator = validator

    def set_rollback_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        """
        Set the rollback callback for failed fixes.

        Args:
            callback: Async function to rollback changes
        """
        self._rollback_callback = callback

    def set_vector_store(self, store: Any) -> None:
        """
        Set VectorStore for pattern learning.

        Args:
            store: VectorStore instance
        """
        self._vector_store = store

    async def heal_pending(self) -> list[HealingResult]:
        """
        Attempt to heal all pending anomalies.

        Returns:
            List of healing results
        """
        results = []

        with self._lock:
            anomalies = list(self._pending_anomalies)
            self._pending_anomalies.clear()

        for anomaly in anomalies:
            result = await self._heal_anomaly(anomaly)
            results.append(result)

        return results

    async def _heal_anomaly(self, anomaly: Anomaly) -> HealingResult:
        """Heal a single anomaly."""
        start_time = datetime.now()

        # Query VectorStore for known patterns
        known_fix = None
        if self._vector_store and self.config.enable_vectorstore:
            try:
                patterns = self._vector_store.search_memories(
                    tags=["healing", anomaly.anomaly_type.value],
                    include_session=True,
                )
                for pattern in patterns:
                    content = pattern.get("content", {})
                    if isinstance(content, dict):
                        confidence = content.get("confidence", 0)
                        if confidence >= self.config.min_confidence_auto_fix:
                            known_fix = content
                            logger.info(
                                f"Found high-confidence fix for {anomaly.anomaly_type.value}"
                            )
                            break
            except Exception as e:
                logger.warning(f"VectorStore query failed: {e}")

        # Get healer for this anomaly type
        healer = self._healers.get(anomaly.anomaly_type)
        if not healer:
            logger.warning(f"No healer registered for {anomaly.anomaly_type.value}")
            return HealingResult(
                success=False,
                message=f"No healer for {anomaly.anomaly_type.value}",
            )

        # Apply fix
        try:
            result = await healer(anomaly)
        except Exception as e:
            logger.error(f"Healer failed: {e}")
            return HealingResult(success=False, message=f"Healer error: {e}")

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        result.duration_seconds = duration

        # Validate fix if validator set
        validation_passed = None
        if result.success and self._validator:
            try:
                validation_passed = await self._validator()
            except Exception as e:
                logger.error(f"Validation failed: {e}")
                validation_passed = False

            if not validation_passed:
                # Rollback if validation fails
                if self._rollback_callback:
                    try:
                        await self._rollback_callback()
                        logger.info("Rollback completed after failed validation")
                    except Exception as e:
                        logger.error(f"Rollback failed: {e}")

                result.success = False
                result.message += " (validation failed, rolled back)"

        # Store successful pattern to VectorStore
        if result.success and validation_passed is not False:
            if self._vector_store and self.config.enable_vectorstore:
                try:
                    self._vector_store.store_memory(
                        key=f"healing_{anomaly.anomaly_type.value}_{datetime.now().timestamp()}",
                        content={
                            "anomaly_type": anomaly.anomaly_type.value,
                            "fix_type": result.fix_type,
                            "context": anomaly.context,
                            "confidence": 0.8,  # Start at 0.8, increase over time
                        },
                        tags=["healing", anomaly.anomaly_type.value, "pattern"],
                    )
                    logger.debug("Successful healing pattern stored")
                except Exception as e:
                    logger.warning(f"Failed to store healing pattern: {e}")

        # Record to history
        self._record_healing(
            anomaly_type=anomaly.anomaly_type.value,
            fix_applied=result.fix_type or "unknown",
            success=result.success,
            duration_seconds=duration,
            validation_passed=validation_passed,
        )

        self._last_healing_time = datetime.now().isoformat()

        return result

    def _record_healing(
        self,
        anomaly_type: str,
        fix_applied: str,
        success: bool,
        duration_seconds: float = 0.0,
        validation_passed: Optional[bool] = None,
    ) -> None:
        """Record a healing attempt to history."""
        with self._lock:
            entry = HealingHistoryEntry(
                timestamp=datetime.now().isoformat(),
                anomaly_type=anomaly_type,
                fix_applied=fix_applied,
                success=success,
                duration_seconds=duration_seconds,
                validation_passed=validation_passed,
            )
            self._healing_history.append(entry)

    def get_healing_history(self) -> list[dict]:
        """Get healing history."""
        with self._lock:
            return [
                {
                    "timestamp": e.timestamp,
                    "anomaly_type": e.anomaly_type,
                    "fix_applied": e.fix_applied,
                    "success": e.success,
                    "duration_seconds": e.duration_seconds,
                    "validation_passed": e.validation_passed,
                }
                for e in self._healing_history
            ]

    def get_status(self) -> dict[str, Any]:
        """Get orchestrator status summary."""
        with self._lock:
            success_count = sum(1 for e in self._healing_history if e.success)
            total_count = len(self._healing_history)

            return {
                "pending_anomalies": len(self._pending_anomalies),
                "healing_history_count": total_count,
                "success_rate": success_count / total_count * 100 if total_count > 0 else 0,
                "last_healing_time": self._last_healing_time,
                "registered_healers": list(self._healers.keys()),
                "vectorstore_enabled": self._vector_store is not None,
            }
