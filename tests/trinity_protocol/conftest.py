"""
Shared fixtures for Trinity Protocol tests.

Provides mock dependencies for ARCHITECT and EXECUTOR agents.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Any, Dict, List, AsyncIterator
from unittest.mock import AsyncMock, Mock, MagicMock

import pytest

from trinity_protocol.architect_agent import ArchitectAgent
from trinity_protocol.executor_agent import ExecutorAgent
from trinity_protocol.message_bus import MessageBus
from trinity_protocol.persistent_store import PersistentStore
from trinity_protocol.cost_tracker import CostTracker
from shared.agent_context import AgentContext


@pytest.fixture
def message_bus() -> MessageBus:
    """Mock message bus for pub/sub operations."""
    bus = Mock(spec=MessageBus)

    # Track published messages per queue
    queues = {}

    async def mock_publish(queue_name, message, priority=0, correlation_id=None):
        """Track published messages."""
        if queue_name not in queues:
            queues[queue_name] = []
        # Add message ID for ack()
        msg_with_id = {**message, "_message_id": f"msg-{len(queues[queue_name])}"}
        if correlation_id and "correlation_id" not in msg_with_id:
            msg_with_id["correlation_id"] = correlation_id
        queues[queue_name].append(msg_with_id)

    # Mock subscribe to return published messages as async iterator
    async def mock_subscribe(queue_name):
        """Return published messages as async generator."""
        if queue_name not in queues:
            queues[queue_name] = []
        for msg in queues[queue_name]:
            yield msg

    async def mock_get_by_correlation(correlation_id):
        """Get all messages with matching correlation_id."""
        results = []
        for queue_msgs in queues.values():
            for msg in queue_msgs:
                if msg.get('correlation_id') == correlation_id:
                    # Convert dict to object with attributes
                    class TaskMessage:
                        def __init__(self, data):
                            for k, v in data.items():
                                setattr(self, k, v)
                    results.append(TaskMessage(msg))
        return results

    bus.publish = mock_publish
    bus.subscribe = mock_subscribe
    bus.ack = AsyncMock()
    bus.get_pending_count = AsyncMock(side_effect=lambda q: len(queues.get(q, [])))
    bus.get_by_correlation = mock_get_by_correlation
    bus._queues = queues  # Expose for testing
    return bus


@pytest.fixture
def pattern_store() -> PersistentStore:
    """Mock persistent store for historical patterns."""
    store = Mock(spec=PersistentStore)
    store.query_patterns = AsyncMock(return_value=[])
    store.search_patterns = Mock(return_value=[])  # Synchronous method used by ARCHITECT
    store.query_adrs = AsyncMock(return_value=[])
    store.store_pattern = AsyncMock()
    return store


@pytest.fixture
def cost_tracker() -> CostTracker:
    """Mock cost tracker for tracking model usage."""
    tracker = Mock(spec=CostTracker)
    tracker.track_usage = Mock()
    tracker.get_total_cost = Mock(return_value=0.0)
    tracker.get_task_cost = Mock(return_value=0.0)
    return tracker


@pytest.fixture
def temp_workspace() -> Path:
    """Temporary workspace directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def architect_agent(message_bus, pattern_store, temp_workspace) -> ArchitectAgent:
    """ArchitectAgent instance with mocked dependencies."""
    agent = ArchitectAgent(
        message_bus=message_bus,
        pattern_store=pattern_store,
        workspace_dir=str(temp_workspace / "plan_workspace"),
        min_complexity=0.7
    )
    return agent


@pytest.fixture
def mock_agent_context(temp_workspace) -> AgentContext:
    """Mock AgentContext for testing."""
    context = Mock(spec=AgentContext)
    context.store_memory = Mock()
    context.search_memories = Mock(return_value=[])
    context.session_id = "test-session-123"
    return context


@pytest.fixture
def executor_agent(message_bus, cost_tracker, mock_agent_context, temp_workspace) -> ExecutorAgent:
    """ExecutorAgent instance with mocked dependencies."""
    agent = ExecutorAgent(
        message_bus=message_bus,
        cost_tracker=cost_tracker,
        agent_context=mock_agent_context,
        plans_dir=str(temp_workspace / "executor_plans"),
        verification_timeout=60
    )
    return agent


@pytest.fixture
def sample_improvement_signal() -> Dict[str, Any]:
    """Sample improvement signal for testing."""
    return {
        "correlation_id": "test-correlation-123",
        "priority": "HIGH",
        "pattern": "type_error",
        "data": {
            "keywords": ["Dict[Any, Any]", "type_violation"],
            "files": ["shared/models.py"]
        },
        "evidence_count": 3,
        "confidence": 0.85,
        "timestamp": "2025-10-01T12:00:00Z"
    }


@pytest.fixture
def sample_execution_task() -> Dict[str, Any]:
    """Sample execution task for testing."""
    return {
        "task_id": "test-task-456",
        "correlation_id": "test-correlation-123",
        "priority": "HIGH",
        "task_type": "code_generation",
        "sub_agent": "CodeWriter",
        "spec": {
            "description": "Fix type error in shared/models.py",
            "files": ["shared/models.py"],
            "requirements": ["Replace Dict[Any, Any] with Pydantic models"]
        },
        "dependencies": [],
        "timestamp": "2025-10-01T12:00:00Z"
    }


@pytest.fixture
def sample_pattern_results() -> List[Dict[str, Any]]:
    """Sample historical pattern results."""
    return [
        {
            "pattern": "type_violation",
            "solution": "Use Pydantic models",
            "confidence": 0.9,
            "evidence_count": 10
        },
        {
            "pattern": "constitutional_violation",
            "solution": "Apply Article I principles",
            "confidence": 0.85,
            "evidence_count": 5
        }
    ]


@pytest.fixture
def sample_adr_results() -> List[Dict[str, Any]]:
    """Sample ADR query results."""
    return [
        {
            "adr_number": "001",
            "title": "Complete Context Before Action",
            "content": "All agents must gather complete context before proceeding."
        },
        {
            "adr_number": "002",
            "title": "100% Test Success Requirement",
            "content": "Main branch must maintain 100% test pass rate."
        }
    ]
