"""
Mars Rover Reliability - Phase 1: Watchdog System Tests.

Constitutional Compliance:
- Article VI: TDD (Tests written FIRST - RED phase)
- Article II: 100% verification (watchdog ensures system health)
- Article III: Automated enforcement (watchdog auto-heals)

Acceptance Criteria:
1. Watchdog detects agent unresponsiveness within 10 seconds
2. Watchdog triggers recovery action on failure
3. Watchdog maintains health history for pattern analysis
4. Watchdog integrates with VectorStore for learning
5. Watchdog provides heartbeat API
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestWatchdogDetection:
    """Watchdog failure detection tests."""

    def test_watchdog_detects_unresponsive_agent(self) -> None:
        """Watchdog must detect agent unresponsiveness within 10 seconds."""
        from tools.mars_rover.watchdog import AgentWatchdog, WatchdogConfig

        config = WatchdogConfig(
            heartbeat_interval_seconds=2,
            timeout_seconds=10,
            max_failures_before_restart=3,
        )
        watchdog = AgentWatchdog(config)

        # Register an agent
        agent_id = "test_agent_001"
        watchdog.register_agent(agent_id)

        # Simulate heartbeat
        watchdog.heartbeat(agent_id)

        # Fast-forward time (simulate no heartbeat for 11 seconds)
        watchdog._last_heartbeat[agent_id] = datetime.now() - timedelta(seconds=11)

        # Check if agent is considered unresponsive
        assert watchdog.is_agent_unresponsive(agent_id), (
            "Watchdog should detect agent as unresponsive after timeout"
        )

    def test_watchdog_responsive_agent_not_flagged(self) -> None:
        """Responsive agents should not be flagged as unresponsive."""
        from tools.mars_rover.watchdog import AgentWatchdog, WatchdogConfig

        config = WatchdogConfig(timeout_seconds=10)
        watchdog = AgentWatchdog(config)

        agent_id = "responsive_agent"
        watchdog.register_agent(agent_id)
        watchdog.heartbeat(agent_id)

        # Agent just sent heartbeat, should be responsive
        assert not watchdog.is_agent_unresponsive(agent_id), (
            "Agent with recent heartbeat should not be flagged unresponsive"
        )

    def test_watchdog_tracks_multiple_agents(self) -> None:
        """Watchdog should track multiple agents independently."""
        from tools.mars_rover.watchdog import AgentWatchdog, WatchdogConfig

        config = WatchdogConfig(timeout_seconds=10)
        watchdog = AgentWatchdog(config)

        # Register multiple agents
        agents = ["agent_1", "agent_2", "agent_3"]
        for agent_id in agents:
            watchdog.register_agent(agent_id)
            watchdog.heartbeat(agent_id)

        # Make only agent_2 unresponsive
        watchdog._last_heartbeat["agent_2"] = datetime.now() - timedelta(seconds=15)

        # Check status
        assert not watchdog.is_agent_unresponsive("agent_1")
        assert watchdog.is_agent_unresponsive("agent_2")
        assert not watchdog.is_agent_unresponsive("agent_3")


class TestWatchdogRecovery:
    """Watchdog recovery action tests."""

    @pytest.mark.asyncio
    async def test_watchdog_triggers_recovery_on_failure(self) -> None:
        """Watchdog must trigger recovery action on agent failure."""
        from tools.mars_rover.watchdog import AgentWatchdog, WatchdogConfig

        config = WatchdogConfig(
            timeout_seconds=5,
            max_failures_before_restart=2,
        )
        watchdog = AgentWatchdog(config)

        agent_id = "failing_agent"
        watchdog.register_agent(agent_id)

        # Mock recovery action
        recovery_called = False
        recovered_agent = None

        async def mock_recovery(aid: str) -> bool:
            nonlocal recovery_called, recovered_agent
            recovery_called = True
            recovered_agent = aid
            return True

        watchdog.set_recovery_callback(mock_recovery)

        # Simulate timeout
        watchdog._last_heartbeat[agent_id] = datetime.now() - timedelta(seconds=10)
        watchdog._failure_count[agent_id] = 2  # At threshold

        # Trigger check (should invoke recovery)
        await watchdog.check_and_recover()

        assert recovery_called, "Recovery callback should be invoked"
        assert recovered_agent == agent_id, "Correct agent should be recovered"

    @pytest.mark.asyncio
    async def test_watchdog_respects_failure_threshold(self) -> None:
        """Watchdog should not trigger recovery until threshold reached."""
        from tools.mars_rover.watchdog import AgentWatchdog, WatchdogConfig

        config = WatchdogConfig(
            timeout_seconds=5,
            max_failures_before_restart=3,
        )
        watchdog = AgentWatchdog(config)

        agent_id = "threshold_agent"
        watchdog.register_agent(agent_id)

        recovery_called = False

        async def mock_recovery(aid: str) -> bool:
            nonlocal recovery_called
            recovery_called = True
            return True

        watchdog.set_recovery_callback(mock_recovery)

        # Simulate timeout with only 1 failure (below threshold)
        watchdog._last_heartbeat[agent_id] = datetime.now() - timedelta(seconds=10)
        watchdog._failure_count[agent_id] = 1  # Below threshold of 3

        await watchdog.check_and_recover()

        assert not recovery_called, (
            "Recovery should not trigger below failure threshold"
        )


class TestWatchdogHistory:
    """Watchdog health history tests."""

    def test_watchdog_maintains_health_history(self) -> None:
        """Watchdog should maintain health history for analysis."""
        from tools.mars_rover.watchdog import AgentWatchdog, WatchdogConfig

        config = WatchdogConfig(history_max_entries=100)
        watchdog = AgentWatchdog(config)

        agent_id = "history_agent"
        watchdog.register_agent(agent_id)

        # Record multiple heartbeats
        for _ in range(5):
            watchdog.heartbeat(agent_id)
            time.sleep(0.01)  # Small delay

        # Get history
        history = watchdog.get_health_history(agent_id)

        assert len(history) >= 5, "History should contain at least 5 entries"
        assert all("timestamp" in entry for entry in history), (
            "Each history entry should have timestamp"
        )

    def test_watchdog_history_respects_max_entries(self) -> None:
        """Health history should respect maximum entry limit."""
        from tools.mars_rover.watchdog import AgentWatchdog, WatchdogConfig

        config = WatchdogConfig(history_max_entries=10)
        watchdog = AgentWatchdog(config)

        agent_id = "limited_history_agent"
        watchdog.register_agent(agent_id)

        # Record more than max entries
        for _ in range(20):
            watchdog.heartbeat(agent_id)

        history = watchdog.get_health_history(agent_id)

        assert len(history) <= 10, "History should not exceed max entries"


class TestWatchdogVectorStore:
    """Watchdog VectorStore integration tests."""

    def test_watchdog_stores_failure_patterns(self) -> None:
        """Watchdog should store failure patterns to VectorStore."""
        from tools.mars_rover.watchdog import AgentWatchdog, WatchdogConfig

        config = WatchdogConfig()
        watchdog = AgentWatchdog(config)

        # Mock VectorStore
        mock_store = MagicMock()
        watchdog.set_vector_store(mock_store)

        agent_id = "pattern_agent"
        watchdog.register_agent(agent_id)

        # Record a failure
        watchdog.record_failure(agent_id, "Connection timeout")

        # Verify pattern was stored
        mock_store.store_memory.assert_called()
        call_args = mock_store.store_memory.call_args
        assert "failure" in str(call_args).lower(), (
            "Failure pattern should be stored in VectorStore"
        )

    def test_watchdog_queries_known_patterns(self) -> None:
        """Watchdog should query VectorStore for known failure patterns."""
        from tools.mars_rover.watchdog import AgentWatchdog, WatchdogConfig

        config = WatchdogConfig()
        watchdog = AgentWatchdog(config)

        # Mock VectorStore with known patterns
        mock_store = MagicMock()
        mock_store.search_memories.return_value = [
            {
                "key": "known_pattern_1",
                "content": {"error": "Connection timeout", "recovery": "restart"},
                "confidence": 0.95,
            }
        ]
        watchdog.set_vector_store(mock_store)

        # Query for recovery suggestion
        suggestion = watchdog.get_recovery_suggestion("Connection timeout")

        assert suggestion is not None, "Should find matching recovery pattern"
        assert "restart" in str(suggestion).lower(), (
            "Should suggest restart based on learned pattern"
        )


class TestWatchdogHeartbeat:
    """Watchdog heartbeat API tests."""

    def test_heartbeat_api_returns_status(self) -> None:
        """Heartbeat API should return current agent status."""
        from tools.mars_rover.watchdog import AgentWatchdog, WatchdogConfig

        config = WatchdogConfig()
        watchdog = AgentWatchdog(config)

        agent_id = "api_agent"
        watchdog.register_agent(agent_id)

        # Send heartbeat and get status
        status = watchdog.heartbeat(agent_id)

        assert status["agent_id"] == agent_id
        assert status["status"] == "healthy"
        assert "timestamp" in status

    def test_heartbeat_with_metadata(self) -> None:
        """Heartbeat should accept and store metadata."""
        from tools.mars_rover.watchdog import AgentWatchdog, WatchdogConfig

        config = WatchdogConfig()
        watchdog = AgentWatchdog(config)

        agent_id = "metadata_agent"
        watchdog.register_agent(agent_id)

        # Send heartbeat with metadata
        metadata = {
            "tasks_completed": 10,
            "memory_usage_mb": 512,
            "current_task": "processing",
        }
        status = watchdog.heartbeat(agent_id, metadata=metadata)

        assert status["metadata"]["tasks_completed"] == 10
        assert status["metadata"]["memory_usage_mb"] == 512


class TestWatchdogConfiguration:
    """Watchdog configuration tests."""

    def test_default_configuration(self) -> None:
        """Default configuration should have sensible values."""
        from tools.mars_rover.watchdog import WatchdogConfig

        config = WatchdogConfig()

        assert config.heartbeat_interval_seconds > 0
        assert config.timeout_seconds >= config.heartbeat_interval_seconds
        assert config.max_failures_before_restart > 0
        assert config.history_max_entries > 0

    def test_custom_configuration(self) -> None:
        """Custom configuration should be applied correctly."""
        from tools.mars_rover.watchdog import WatchdogConfig

        config = WatchdogConfig(
            heartbeat_interval_seconds=5,
            timeout_seconds=15,
            max_failures_before_restart=5,
            history_max_entries=500,
        )

        assert config.heartbeat_interval_seconds == 5
        assert config.timeout_seconds == 15
        assert config.max_failures_before_restart == 5
        assert config.history_max_entries == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
