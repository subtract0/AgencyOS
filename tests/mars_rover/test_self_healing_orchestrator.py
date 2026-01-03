"""
Mars Rover Reliability - Phase 2: Self-Healing Orchestrator Tests.

Constitutional Compliance:
- Article VI: TDD (Tests written FIRST)
- Article II: 100% verification (orchestrator ensures system health)
- Article III: Automated enforcement (auto-heals anomalies)
- Article IV: Learning (stores healing patterns to VectorStore)

Acceptance Criteria:
1. Monitors all systems (watchdog, tests, workers, performance)
2. Detects anomalies (test failures, crashes, degradation)
3. Triggers autonomous fixes via workers
4. Validates fixes (tests pass, no regressions)
5. Rollback on failure (atomic operations restore checkpoint)
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAnomalyDetection:
    """Anomaly detection tests."""

    def test_detects_test_failures(self) -> None:
        """Orchestrator should detect test failures."""
        from tools.mars_rover.self_healing import (
            Anomaly,
            AnomalyType,
            SelfHealingOrchestrator,
        )

        orchestrator = SelfHealingOrchestrator()

        # Simulate test failure report
        orchestrator.report_test_results(
            passed=95,
            failed=5,
            errors=0,
            total=100,
        )

        anomalies = orchestrator.get_pending_anomalies()

        assert len(anomalies) > 0, "Should detect test failure anomaly"
        assert any(a.anomaly_type == AnomalyType.TEST_FAILURE for a in anomalies)

    def test_detects_agent_crash(self) -> None:
        """Orchestrator should detect agent crashes."""
        from tools.mars_rover.self_healing import (
            Anomaly,
            AnomalyType,
            SelfHealingOrchestrator,
        )

        orchestrator = SelfHealingOrchestrator()

        # Report agent crash
        orchestrator.report_agent_crash(
            agent_id="worker_001",
            error="Segmentation fault",
        )

        anomalies = orchestrator.get_pending_anomalies()

        assert len(anomalies) > 0, "Should detect agent crash anomaly"
        assert any(a.anomaly_type == AnomalyType.AGENT_CRASH for a in anomalies)
        assert any(a.context.get("agent_id") == "worker_001" for a in anomalies)

    def test_detects_performance_degradation(self) -> None:
        """Orchestrator should detect performance degradation."""
        from tools.mars_rover.self_healing import (
            Anomaly,
            AnomalyType,
            SelfHealingOrchestrator,
        )

        orchestrator = SelfHealingOrchestrator()

        # Set baseline
        orchestrator.set_performance_baseline(
            test_duration_seconds=60.0,
            memory_usage_gb=10.0,
        )

        # Report degraded performance (>10% slower)
        orchestrator.report_performance_metrics(
            test_duration_seconds=90.0,  # 50% slower
            memory_usage_gb=15.0,  # 50% more memory
        )

        anomalies = orchestrator.get_pending_anomalies()

        assert len(anomalies) > 0, "Should detect performance degradation"
        assert any(
            a.anomaly_type == AnomalyType.PERFORMANCE_DEGRADATION for a in anomalies
        )

    def test_no_anomaly_when_healthy(self) -> None:
        """No anomaly should be detected when system is healthy."""
        from tools.mars_rover.self_healing import SelfHealingOrchestrator

        orchestrator = SelfHealingOrchestrator()

        # Report all tests passing
        orchestrator.report_test_results(
            passed=100,
            failed=0,
            errors=0,
            total=100,
        )

        anomalies = orchestrator.get_pending_anomalies()

        assert len(anomalies) == 0, "Should not detect anomaly when healthy"


class TestHealingWorkflow:
    """Healing workflow tests."""

    @pytest.mark.asyncio
    async def test_triggers_healing_on_anomaly(self) -> None:
        """Orchestrator should trigger healing when anomaly detected."""
        from tools.mars_rover.self_healing import (
            AnomalyType,
            HealingResult,
            SelfHealingOrchestrator,
        )

        orchestrator = SelfHealingOrchestrator()

        # Mock healing action
        healing_triggered = False

        async def mock_healer(anomaly):
            nonlocal healing_triggered
            healing_triggered = True
            return HealingResult(success=True, message="Fixed")

        orchestrator.register_healer(AnomalyType.TEST_FAILURE, mock_healer)

        # Report anomaly
        orchestrator.report_test_results(passed=95, failed=5, errors=0, total=100)

        # Trigger healing
        await orchestrator.heal_pending()

        assert healing_triggered, "Healing should be triggered"

    @pytest.mark.asyncio
    async def test_validates_fix_with_tests(self) -> None:
        """Orchestrator should validate fixes by running tests."""
        from tools.mars_rover.self_healing import (
            AnomalyType,
            HealingResult,
            SelfHealingOrchestrator,
        )

        orchestrator = SelfHealingOrchestrator()
        validation_ran = False

        # Mock validation
        async def mock_validator():
            nonlocal validation_ran
            validation_ran = True
            return True  # Tests pass

        orchestrator.set_validator(mock_validator)

        async def mock_healer(anomaly):
            return HealingResult(success=True, message="Fixed")

        orchestrator.register_healer(AnomalyType.TEST_FAILURE, mock_healer)

        # Report and heal
        orchestrator.report_test_results(passed=95, failed=5, errors=0, total=100)
        await orchestrator.heal_pending()

        assert validation_ran, "Validation should run after healing"

    @pytest.mark.asyncio
    async def test_rollback_on_failed_validation(self) -> None:
        """Orchestrator should rollback if validation fails."""
        from tools.mars_rover.self_healing import (
            AnomalyType,
            HealingResult,
            SelfHealingOrchestrator,
        )

        orchestrator = SelfHealingOrchestrator()
        rollback_called = False

        # Mock rollback
        async def mock_rollback():
            nonlocal rollback_called
            rollback_called = True

        orchestrator.set_rollback_callback(mock_rollback)

        # Mock validator that fails
        async def mock_validator():
            return False  # Tests still fail

        orchestrator.set_validator(mock_validator)

        async def mock_healer(anomaly):
            return HealingResult(success=True, message="Fixed (but tests still fail)")

        orchestrator.register_healer(AnomalyType.TEST_FAILURE, mock_healer)

        # Report and heal
        orchestrator.report_test_results(passed=95, failed=5, errors=0, total=100)
        await orchestrator.heal_pending()

        assert rollback_called, "Rollback should be called on failed validation"


class TestVectorStoreIntegration:
    """VectorStore pattern learning tests."""

    @pytest.mark.asyncio
    async def test_queries_vectorstore_before_healing(self) -> None:
        """Orchestrator should query VectorStore for known fixes."""
        from tools.mars_rover.self_healing import (
            AnomalyType,
            HealingResult,
            SelfHealingOrchestrator,
        )

        orchestrator = SelfHealingOrchestrator()
        vectorstore_queried = False

        # Mock VectorStore
        mock_store = MagicMock()

        def mock_search(*args, **kwargs):
            nonlocal vectorstore_queried
            vectorstore_queried = True
            return [
                {
                    "content": {"fix": "restart_agent", "confidence": 0.9},
                }
            ]

        mock_store.search_memories = mock_search
        orchestrator.set_vector_store(mock_store)

        async def mock_healer(anomaly):
            return HealingResult(success=True, message="Fixed")

        orchestrator.register_healer(AnomalyType.TEST_FAILURE, mock_healer)

        # Report and heal
        orchestrator.report_test_results(passed=95, failed=5, errors=0, total=100)
        await orchestrator.heal_pending()

        assert vectorstore_queried, "VectorStore should be queried before healing"

    @pytest.mark.asyncio
    async def test_stores_successful_patterns(self) -> None:
        """Successful healing patterns should be stored to VectorStore."""
        from tools.mars_rover.self_healing import (
            AnomalyType,
            HealingResult,
            SelfHealingOrchestrator,
        )

        orchestrator = SelfHealingOrchestrator()
        pattern_stored = False

        # Mock VectorStore
        mock_store = MagicMock()

        def mock_store_memory(*args, **kwargs):
            nonlocal pattern_stored
            pattern_stored = True

        mock_store.search_memories = MagicMock(return_value=[])
        mock_store.store_memory = mock_store_memory
        orchestrator.set_vector_store(mock_store)

        # Mock successful validation
        async def mock_validator():
            return True

        orchestrator.set_validator(mock_validator)

        async def mock_healer(anomaly):
            return HealingResult(success=True, message="Fixed", fix_type="restart")

        orchestrator.register_healer(AnomalyType.TEST_FAILURE, mock_healer)

        # Report and heal
        orchestrator.report_test_results(passed=95, failed=5, errors=0, total=100)
        await orchestrator.heal_pending()

        assert pattern_stored, "Successful pattern should be stored"


class TestHealingStrategies:
    """Healing strategy tests."""

    @pytest.mark.asyncio
    async def test_applies_high_confidence_patterns_automatically(self) -> None:
        """Patterns with confidence ≥0.9 should be applied automatically."""
        from tools.mars_rover.self_healing import (
            AnomalyType,
            HealingResult,
            SelfHealingOrchestrator,
        )

        orchestrator = SelfHealingOrchestrator()
        auto_fix_applied = False

        # Mock VectorStore with high-confidence pattern
        mock_store = MagicMock()
        mock_store.search_memories = MagicMock(
            return_value=[
                {
                    "content": {
                        "fix_type": "auto_restart",
                        "confidence": 0.95,
                    },
                }
            ]
        )
        mock_store.store_memory = MagicMock()
        orchestrator.set_vector_store(mock_store)

        async def mock_validator():
            return True

        orchestrator.set_validator(mock_validator)

        async def mock_healer(anomaly):
            nonlocal auto_fix_applied
            auto_fix_applied = True
            return HealingResult(success=True, message="Auto-fixed")

        orchestrator.register_healer(AnomalyType.AGENT_CRASH, mock_healer)

        # Report crash
        orchestrator.report_agent_crash("worker_001", "Connection timeout")
        await orchestrator.heal_pending()

        assert auto_fix_applied, "High-confidence fix should be applied automatically"

    @pytest.mark.asyncio
    async def test_uses_fallback_strategy_on_no_pattern(self) -> None:
        """Should use fallback strategy when no pattern found."""
        from tools.mars_rover.self_healing import (
            AnomalyType,
            HealingResult,
            SelfHealingOrchestrator,
        )

        orchestrator = SelfHealingOrchestrator()
        fallback_used = False

        # Mock VectorStore with no patterns
        mock_store = MagicMock()
        mock_store.search_memories = MagicMock(return_value=[])
        orchestrator.set_vector_store(mock_store)

        async def mock_validator():
            return True

        orchestrator.set_validator(mock_validator)

        async def fallback_healer(anomaly):
            nonlocal fallback_used
            fallback_used = True
            return HealingResult(success=True, message="Fallback fix")

        orchestrator.register_healer(AnomalyType.TEST_FAILURE, fallback_healer)

        # Report failure
        orchestrator.report_test_results(passed=95, failed=5, errors=0, total=100)
        await orchestrator.heal_pending()

        assert fallback_used, "Fallback strategy should be used"


class TestOrchestratorStatus:
    """Orchestrator status and metrics tests."""

    def test_tracks_healing_history(self) -> None:
        """Orchestrator should track healing history."""
        from tools.mars_rover.self_healing import SelfHealingOrchestrator

        orchestrator = SelfHealingOrchestrator()

        # Simulate some healing history
        orchestrator._record_healing(
            anomaly_type="TEST_FAILURE",
            fix_applied="restart_tests",
            success=True,
        )

        history = orchestrator.get_healing_history()

        assert len(history) > 0, "Should have healing history"
        assert history[0]["success"], "Should record success"

    def test_provides_status_summary(self) -> None:
        """Orchestrator should provide status summary."""
        from tools.mars_rover.self_healing import SelfHealingOrchestrator

        orchestrator = SelfHealingOrchestrator()

        status = orchestrator.get_status()

        assert "pending_anomalies" in status
        assert "healing_history_count" in status
        assert "last_healing_time" in status


class TestOrchestratorConfiguration:
    """Configuration tests."""

    def test_default_configuration(self) -> None:
        """Default configuration should have sensible values."""
        from tools.mars_rover.self_healing import SelfHealingConfig

        config = SelfHealingConfig()

        assert config.min_confidence_auto_fix >= 0.0
        assert config.min_confidence_auto_fix <= 1.0
        assert config.max_retry_attempts > 0
        assert config.performance_degradation_threshold > 0

    def test_custom_thresholds(self) -> None:
        """Custom thresholds should be applied."""
        from tools.mars_rover.self_healing import (
            SelfHealingConfig,
            SelfHealingOrchestrator,
        )

        config = SelfHealingConfig(
            min_confidence_auto_fix=0.8,
            performance_degradation_threshold=0.05,  # 5%
        )
        orchestrator = SelfHealingOrchestrator(config)

        # Verify config applied
        assert orchestrator.config.min_confidence_auto_fix == 0.8
        assert orchestrator.config.performance_degradation_threshold == 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
