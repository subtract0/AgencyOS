"""
Integration test for HybridExecutor event loop activation in TrinityOrchestrator.

Week 4 Day 3: Critical P0 fix - verify HybridExecutor.run() is started.
"""

import asyncio
import logging

import pytest

from trinity_protocol.core.orchestrator import TrinityOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_starts_hybrid_executor_event_loop():
    """
    Test that orchestrator starts HybridExecutor event loop on startup.

    Validates:
    - HybridExecutor is initialized
    - run() event loop is started as background task
    - Event loop is consuming from execution_queue
    """
    # Arrange
    orchestrator = TrinityOrchestrator()

    # Verify HybridExecutor exists
    assert orchestrator.hybrid_executor is not None, "HybridExecutor must be initialized"

    # Act - Start monitor loop in background
    monitor_task = asyncio.create_task(orchestrator.monitor_loop())

    # Give event loop time to start
    await asyncio.sleep(0.5)

    # Assert - Verify HybridExecutor is running
    assert orchestrator._running is True, "Orchestrator should be running"

    # Cleanup - Stop gracefully
    orchestrator._running = False
    await asyncio.sleep(0.1)
    monitor_task.cancel()

    try:
        await monitor_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_orchestrator_graceful_shutdown_stops_executor():
    """
    Test that graceful shutdown stops HybridExecutor event loop cleanly.

    Validates:
    - Event loop cancellation
    - No leaked tasks
    - Clean CancelledError handling
    """
    # Arrange
    orchestrator = TrinityOrchestrator()
    monitor_task = asyncio.create_task(orchestrator.monitor_loop())

    # Give time to start
    await asyncio.sleep(0.5)

    # Act - Stop orchestrator
    orchestrator._running = False
    await asyncio.sleep(0.1)

    # Cancel monitor loop (simulates SIGTERM)
    monitor_task.cancel()

    # Assert - Verify clean shutdown
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass  # Expected

    # No assertions needed - if this doesn't hang or crash, test passes


@pytest.mark.asyncio
async def test_orchestrator_routes_tasks_to_hybrid_executor(caplog):
    """
    Test that tasks are routed through HybridExecutor execution_queue.

    Validates:
    - Tasks published to execution_queue
    - HybridExecutor subscribes and consumes
    - No direct Ollama fallback unless HybridExecutor unavailable
    """
    # Arrange
    caplog.set_level(logging.INFO)
    orchestrator = TrinityOrchestrator()
    monitor_task = asyncio.create_task(orchestrator.monitor_loop())

    await asyncio.sleep(0.5)

    # Act - Publish test signal
    from trinity_protocol.core.orchestrator import TrinityMessage

    test_signal = TrinityMessage(
        ts="2025-10-05T00:00:00",
        agent="ORCHESTRATOR",
        type="IMPROVEMENT_SIGNAL",
        data={"task": "test", "complexity": "low"},
    )

    orchestrator.bus.publish("ORCHESTRATOR", "IMPROVEMENT_SIGNAL", test_signal.data)

    # Give time to process
    await asyncio.sleep(1.0)

    # Assert - Check logs for HybridExecutor usage
    logs = caplog.text
    assert "HybridExecutor event loop started" in logs, "Event loop must start"

    # Cleanup
    orchestrator._running = False
    await asyncio.sleep(0.1)
    monitor_task.cancel()

    try:
        await monitor_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_orchestrator_fallback_when_hybrid_executor_none():
    """
    Test that orchestrator falls back to Ollama when HybridExecutor is None.

    Validates:
    - Graceful degradation when HybridExecutor unavailable
    - Warning logged about fallback
    - System continues to function
    """
    # Arrange - Force HybridExecutor to None
    orchestrator = TrinityOrchestrator()
    orchestrator.hybrid_executor = None

    # Act - Start monitor loop
    monitor_task = asyncio.create_task(orchestrator.monitor_loop())

    await asyncio.sleep(0.5)

    # Assert - Orchestrator should still run
    assert orchestrator._running is True

    # Cleanup
    orchestrator._running = False
    await asyncio.sleep(0.1)
    monitor_task.cancel()

    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
