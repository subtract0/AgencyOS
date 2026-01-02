"""
Mars Rover Reliability - Phase 1: Agent Watchdog System.

Provides health monitoring and automatic recovery for autonomous agents.

Constitutional Compliance:
- Article II: 100% verification (ensures all agents remain healthy)
- Article III: Automated enforcement (auto-recovers failed agents)
- Article IV: Learning (stores failure patterns to VectorStore)

Features:
1. Heartbeat monitoring with configurable timeout
2. Automatic recovery on failure threshold
3. Health history for pattern analysis
4. VectorStore integration for learning from failures
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class WatchdogConfig:
    """Configuration for the watchdog system."""

    heartbeat_interval_seconds: int = 5
    timeout_seconds: int = 30
    max_failures_before_restart: int = 3
    history_max_entries: int = 100
    enable_vectorstore: bool = True


@dataclass
class HealthEntry:
    """A single health check entry."""

    timestamp: str
    status: str
    agent_id: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "status": self.status,
            "agent_id": self.agent_id,
            "metadata": self.metadata,
        }


class AgentWatchdog:
    """
    Watchdog system for monitoring agent health.

    Detects unresponsive agents and triggers recovery actions
    based on configurable thresholds.
    """

    def __init__(self, config: Optional[WatchdogConfig] = None):
        """Initialize the watchdog."""
        self.config = config or WatchdogConfig()
        self._registered_agents: set[str] = set()
        self._last_heartbeat: dict[str, datetime] = {}
        self._failure_count: dict[str, int] = {}
        self._health_history: dict[str, deque[HealthEntry]] = {}
        self._recovery_callback: Optional[Callable[[str], Awaitable[bool]]] = None
        self._vector_store: Optional[Any] = None

        logger.info(f"Watchdog initialized with config: {self.config}")

    def register_agent(self, agent_id: str) -> None:
        """
        Register an agent for monitoring.

        Args:
            agent_id: Unique identifier for the agent
        """
        self._registered_agents.add(agent_id)
        self._last_heartbeat[agent_id] = datetime.now()
        self._failure_count[agent_id] = 0
        self._health_history[agent_id] = deque(maxlen=self.config.history_max_entries)

        logger.info(f"Agent registered: {agent_id}")

    def unregister_agent(self, agent_id: str) -> None:
        """
        Unregister an agent from monitoring.

        Args:
            agent_id: Agent identifier to unregister
        """
        self._registered_agents.discard(agent_id)
        self._last_heartbeat.pop(agent_id, None)
        self._failure_count.pop(agent_id, None)
        self._health_history.pop(agent_id, None)

        logger.info(f"Agent unregistered: {agent_id}")

    def heartbeat(
        self, agent_id: str, metadata: Optional[dict] = None
    ) -> dict[str, Any]:
        """
        Record a heartbeat from an agent.

        Args:
            agent_id: Agent identifier
            metadata: Optional metadata to include with heartbeat

        Returns:
            Status dictionary with agent health info
        """
        if agent_id not in self._registered_agents:
            self.register_agent(agent_id)

        now = datetime.now()
        self._last_heartbeat[agent_id] = now
        self._failure_count[agent_id] = 0  # Reset failure count on heartbeat

        # Create health entry
        entry = HealthEntry(
            timestamp=now.isoformat(),
            status="healthy",
            agent_id=agent_id,
            metadata=metadata or {},
        )

        # Add to history
        self._health_history[agent_id].append(entry)

        status = {
            "agent_id": agent_id,
            "status": "healthy",
            "timestamp": now.isoformat(),
            "failure_count": 0,
            "metadata": metadata or {},
        }

        logger.debug(f"Heartbeat received: {agent_id}")
        return status

    def is_agent_unresponsive(self, agent_id: str) -> bool:
        """
        Check if an agent is unresponsive.

        Args:
            agent_id: Agent identifier

        Returns:
            True if agent has not sent heartbeat within timeout
        """
        if agent_id not in self._last_heartbeat:
            return True

        last_seen = self._last_heartbeat[agent_id]
        timeout_delta = timedelta(seconds=self.config.timeout_seconds)

        return datetime.now() - last_seen > timeout_delta

    def get_health_history(self, agent_id: str) -> list[dict]:
        """
        Get health history for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            List of health entries
        """
        if agent_id not in self._health_history:
            return []

        return [entry.to_dict() for entry in self._health_history[agent_id]]

    def set_recovery_callback(
        self, callback: Callable[[str], Awaitable[bool]]
    ) -> None:
        """
        Set the callback function for agent recovery.

        Args:
            callback: Async function that takes agent_id and returns success bool
        """
        self._recovery_callback = callback

    def set_vector_store(self, store: Any) -> None:
        """
        Set VectorStore for learning from failures.

        Args:
            store: VectorStore instance with store_memory/search_memories methods
        """
        self._vector_store = store

    def record_failure(self, agent_id: str, error: str) -> None:
        """
        Record a failure for an agent.

        Args:
            agent_id: Agent identifier
            error: Error message describing the failure
        """
        if agent_id not in self._failure_count:
            self._failure_count[agent_id] = 0

        self._failure_count[agent_id] += 1

        # Create failure entry
        entry = HealthEntry(
            timestamp=datetime.now().isoformat(),
            status="failure",
            agent_id=agent_id,
            metadata={"error": error},
        )

        if agent_id in self._health_history:
            self._health_history[agent_id].append(entry)

        # Store failure pattern to VectorStore
        if self._vector_store and self.config.enable_vectorstore:
            try:
                self._vector_store.store_memory(
                    key=f"watchdog_failure_{agent_id}_{datetime.now().timestamp()}",
                    content={
                        "agent_id": agent_id,
                        "error": error,
                        "failure_count": self._failure_count[agent_id],
                        "timestamp": datetime.now().isoformat(),
                    },
                    tags=["watchdog", "failure", "pattern", agent_id],
                )
                logger.debug(f"Failure pattern stored for {agent_id}")
            except Exception as e:
                logger.warning(f"Failed to store failure pattern: {e}")

        logger.warning(
            f"Failure recorded for {agent_id}: {error} "
            f"(count: {self._failure_count[agent_id]})"
        )

    def get_recovery_suggestion(self, error: str) -> Optional[dict]:
        """
        Query VectorStore for known recovery patterns.

        Args:
            error: Error message to match

        Returns:
            Recovery suggestion if found, None otherwise
        """
        if not self._vector_store:
            return None

        try:
            results = self._vector_store.search_memories(
                tags=["watchdog", "failure", "pattern"],
                include_session=True,
            )

            # Find matching patterns
            for result in results:
                content = result.get("content", {})
                if isinstance(content, dict):
                    stored_error = content.get("error", "")
                    if error.lower() in stored_error.lower():
                        return {
                            "matched_pattern": stored_error,
                            "recovery": "restart",  # Default recovery action
                            "confidence": result.get("confidence", 0.5),
                        }

            return None

        except Exception as e:
            logger.warning(f"Failed to query recovery patterns: {e}")
            return None

    async def check_and_recover(self) -> list[str]:
        """
        Check all agents and trigger recovery for unresponsive ones.

        Returns:
            List of agent IDs that recovery was attempted for
        """
        recovered_agents = []

        for agent_id in list(self._registered_agents):
            if self.is_agent_unresponsive(agent_id):
                # Increment failure count
                if agent_id not in self._failure_count:
                    self._failure_count[agent_id] = 0
                self._failure_count[agent_id] += 1

                # Check if threshold reached
                if self._failure_count[agent_id] >= self.config.max_failures_before_restart:
                    logger.warning(
                        f"Agent {agent_id} reached failure threshold "
                        f"({self._failure_count[agent_id]}), triggering recovery"
                    )

                    # Trigger recovery
                    if self._recovery_callback:
                        try:
                            success = await self._recovery_callback(agent_id)
                            if success:
                                self._failure_count[agent_id] = 0
                                recovered_agents.append(agent_id)
                                logger.info(f"Agent {agent_id} recovered successfully")
                            else:
                                logger.error(f"Recovery failed for agent {agent_id}")
                        except Exception as e:
                            logger.error(f"Recovery callback error for {agent_id}: {e}")
                    else:
                        logger.warning(
                            f"No recovery callback set for {agent_id}"
                        )

        return recovered_agents

    def get_status(self) -> dict[str, Any]:
        """
        Get overall watchdog status.

        Returns:
            Status dictionary with all agent states
        """
        agents = {}
        for agent_id in self._registered_agents:
            agents[agent_id] = {
                "responsive": not self.is_agent_unresponsive(agent_id),
                "failure_count": self._failure_count.get(agent_id, 0),
                "last_heartbeat": (
                    self._last_heartbeat[agent_id].isoformat()
                    if agent_id in self._last_heartbeat
                    else None
                ),
            }

        return {
            "total_agents": len(self._registered_agents),
            "healthy_agents": sum(
                1 for a in agents.values() if a["responsive"]
            ),
            "unhealthy_agents": sum(
                1 for a in agents.values() if not a["responsive"]
            ),
            "agents": agents,
            "config": {
                "timeout_seconds": self.config.timeout_seconds,
                "max_failures": self.config.max_failures_before_restart,
            },
        }


# Singleton watchdog instance
_global_watchdog: Optional[AgentWatchdog] = None


def get_watchdog(config: Optional[WatchdogConfig] = None) -> AgentWatchdog:
    """
    Get the global watchdog instance.

    Args:
        config: Optional configuration (only used if creating new instance)

    Returns:
        Global AgentWatchdog instance
    """
    global _global_watchdog
    if _global_watchdog is None:
        _global_watchdog = AgentWatchdog(config)
    return _global_watchdog


def reset_watchdog() -> None:
    """Reset the global watchdog instance (for testing)."""
    global _global_watchdog
    _global_watchdog = None
