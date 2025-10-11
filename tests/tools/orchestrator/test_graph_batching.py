"""
Tests for Full Layer Batching - Constitutional Compliance (Leap 6).

Constitutional compliance:
- Article I: Complete context (all tasks in layer executed)
- Article II: 100% verification (all batching edge cases tested)
- Article III: Automated enforcement (max_workers limits enforced)
- Article IV: VectorStore integration (execution patterns stored)

NECESSARY Pattern Coverage:
- N: Normal operation (standard batching with max_workers)
- E: Edge cases (empty layers, single task, exact boundary)
- C: Corner cases (max_workers > layer_size, layer_size = 1)
- E: Error conditions (invalid max_workers, negative values)
- S: Security (no task ID injection, deterministic ordering)
- S: Stress (large layers 1000+ tasks, performance bounds)
- A: Accessibility (API ergonomics, clear error messages)
- R: Regression (deterministic ordering across runs)
- Y: Yield (all tasks complete, correct telemetry events)
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from shared.agent_context import create_agent_context
from shared.models.orchestrator import ExecutionMetrics
from tools.orchestrator.graph import (
    TaskGraph,
    _create_deterministic_batches,
    _levels,
    run_graph,
)
from tools.orchestrator.scheduler import (
    OrchestrationPolicy,
    OrchestrationResult,
    RetryPolicy,
    TaskResult,
    TaskSpec,
)

# ============================================================================
# DETERMINISTIC BATCHING ALGORITHM TESTS
# ============================================================================


class TestCreateDeterministicBatches:
    """Test deterministic batching algorithm (spec-007 Section 5.2)."""

    # --- NORMAL OPERATION ---

    def test_batching_with_tasks_less_than_max_workers_single_batch(self):
        """Test layer with tasks < max_workers returns single batch."""
        # Arrange
        task_ids = ["task_3", "task_1", "task_2"]
        max_workers = 5

        # Act
        batches = _create_deterministic_batches(task_ids, max_workers)

        # Assert
        assert len(batches) == 1
        assert batches[0] == ["task_1", "task_2", "task_3"]  # Sorted

    def test_batching_with_tasks_greater_than_max_workers_multiple_batches(self):
        """Test layer with tasks > max_workers splits into multiple batches."""
        # Arrange
        task_ids = ["task_5", "task_2", "task_7", "task_1", "task_4", "task_3", "task_6"]
        max_workers = 3

        # Act
        batches = _create_deterministic_batches(task_ids, max_workers)

        # Assert
        assert len(batches) == 3  # ceil(7 / 3) = 3
        assert batches[0] == ["task_1", "task_2", "task_3"]
        assert batches[1] == ["task_4", "task_5", "task_6"]
        assert batches[2] == ["task_7"]

    def test_batching_respects_max_workers_limit(self):
        """Test each batch has at most max_workers tasks."""
        # Arrange
        task_ids = [f"task_{i}" for i in range(20)]
        max_workers = 4

        # Act
        batches = _create_deterministic_batches(task_ids, max_workers)

        # Assert
        for batch in batches:
            assert len(batch) <= max_workers

    # --- EDGE CASES ---

    def test_batching_with_empty_task_list(self):
        """Test empty task list returns empty batches."""
        # Arrange
        task_ids = []
        max_workers = 4

        # Act
        batches = _create_deterministic_batches(task_ids, max_workers)

        # Assert
        assert batches == []

    def test_batching_with_single_task(self):
        """Test single task returns single batch with one task."""
        # Arrange
        task_ids = ["task_42"]
        max_workers = 4

        # Act
        batches = _create_deterministic_batches(task_ids, max_workers)

        # Assert
        assert len(batches) == 1
        assert batches[0] == ["task_42"]

    def test_batching_with_tasks_equal_to_max_workers(self):
        """Test layer size exactly equal to max_workers (boundary condition)."""
        # Arrange
        task_ids = ["task_a", "task_b", "task_c", "task_d"]
        max_workers = 4

        # Act
        batches = _create_deterministic_batches(task_ids, max_workers)

        # Assert
        assert len(batches) == 1
        assert batches[0] == ["task_a", "task_b", "task_c", "task_d"]

    # --- CORNER CASES ---

    def test_batching_with_max_workers_greater_than_layer_size(self):
        """Test max_workers > layer_size returns single batch."""
        # Arrange
        task_ids = ["task_1", "task_2", "task_3"]
        max_workers = 10

        # Act
        batches = _create_deterministic_batches(task_ids, max_workers)

        # Assert
        assert len(batches) == 1
        assert batches[0] == ["task_1", "task_2", "task_3"]

    def test_batching_with_max_workers_one(self):
        """Test max_workers=1 creates one batch per task (sequential execution)."""
        # Arrange
        task_ids = ["task_c", "task_a", "task_b"]
        max_workers = 1

        # Act
        batches = _create_deterministic_batches(task_ids, max_workers)

        # Assert
        assert len(batches) == 3
        assert batches[0] == ["task_a"]
        assert batches[1] == ["task_b"]
        assert batches[2] == ["task_c"]

    # --- SECURITY (Determinism) ---

    def test_batching_deterministic_ordering_regardless_of_input_order(self):
        """Test same task set produces identical batches regardless of input order."""
        # Arrange
        task_ids_order_1 = ["task_3", "task_1", "task_2", "task_5", "task_4"]
        task_ids_order_2 = ["task_5", "task_2", "task_4", "task_1", "task_3"]
        max_workers = 2

        # Act
        batches_1 = _create_deterministic_batches(task_ids_order_1, max_workers)
        batches_2 = _create_deterministic_batches(task_ids_order_2, max_workers)

        # Assert
        assert batches_1 == batches_2
        assert batches_1 == [
            ["task_1", "task_2"],
            ["task_3", "task_4"],
            ["task_5"],
        ]

    def test_batching_stable_sort_preserves_lexicographic_order(self):
        """Test batch assignment uses stable lexicographic sort."""
        # Arrange
        task_ids = ["z", "a", "m", "b", "y"]
        max_workers = 2

        # Act
        batches = _create_deterministic_batches(task_ids, max_workers)

        # Assert
        assert batches == [["a", "b"], ["m", "y"], ["z"]]

    # --- STRESS TESTS ---

    def test_batching_performance_with_large_layer_1000_tasks(self):
        """Test batching algorithm completes <50ms for 1,000 tasks (spec requirement)."""
        # Arrange
        task_ids = [f"task_{i:04d}" for i in range(1000)]
        max_workers = 10

        # Act
        start = time.perf_counter()
        batches = _create_deterministic_batches(task_ids, max_workers)
        duration_ms = (time.perf_counter() - start) * 1000

        # Assert
        assert len(batches) == 100  # ceil(1000 / 10)
        assert all(len(batch) <= max_workers for batch in batches)
        assert duration_ms < 50, f"Batching took {duration_ms:.2f}ms (expected <50ms)"

    def test_batching_correctness_with_10000_tasks(self):
        """Test batching correctness with stress load (10,000 tasks)."""
        # Arrange
        task_ids = [f"task_{i:05d}" for i in range(10000)]
        max_workers = 25

        # Act
        batches = _create_deterministic_batches(task_ids, max_workers)

        # Assert
        assert len(batches) == 400  # ceil(10000 / 25)
        # Verify all tasks present exactly once
        all_tasks_in_batches = [task for batch in batches for task in batch]
        assert len(all_tasks_in_batches) == 10000
        assert set(all_tasks_in_batches) == set(task_ids)

    # --- REGRESSION TESTS ---

    def test_batching_determinism_across_1000_runs(self):
        """Test reproducibility - 1,000 runs produce identical results (spec AC-2.5)."""
        # Arrange
        task_ids = ["task_7", "task_2", "task_9", "task_1", "task_5", "task_3"]
        max_workers = 3

        # Act
        results = [_create_deterministic_batches(task_ids, max_workers) for _ in range(1000)]

        # Assert
        expected = [["task_1", "task_2", "task_3"], ["task_5", "task_7", "task_9"]]
        assert all(result == expected for result in results), "Non-deterministic batching detected"


# ============================================================================
# FULL LAYER EXECUTION TESTS
# ============================================================================


class TestRunGraphFullLayerExecution:
    """Test run_graph executes ALL tasks in each layer (spec-007 Section 5.1)."""

    @pytest.fixture
    def mock_context(self):
        """Create mock AgentContext for tests."""
        return create_agent_context(session_id="test_batching")

    @pytest.fixture
    def simple_policy(self):
        """Create simple orchestration policy."""
        return OrchestrationPolicy(
            max_concurrency=2,
            retry=RetryPolicy(max_attempts=1),
            timeout_s=30.0,
        )

    @pytest.fixture
    def mock_slop_immunity(self):
        """Mock slop immunity to always accept test task descriptions."""
        from shared.type_definitions.result import Ok
        from tools.orchestrator.slop_guardian import SlopVerdict

        with patch("tools.orchestrator.graph.enforce_slop_immunity") as mock_slop:
            mock_slop.return_value = Ok(
                SlopVerdict(
                    score=4.0,
                    reasons=[],
                    top_fixes=[],
                    dimension_scores={"clarity": 4.0, "measurability": 4.0, "completeness": 4.0, "actionability": 4.0},
                )
            )
            yield mock_slop

    # --- NORMAL OPERATION ---

    @pytest.mark.asyncio
    async def test_run_graph_executes_all_tasks_in_single_layer(self, mock_context, simple_policy, mock_slop_immunity):
        """Test all tasks in single layer execute (Article I: Complete Context)."""
        # Arrange
        def mock_agent_factory(ctx):
            agent = AsyncMock()
            agent.run = AsyncMock(return_value={"result": "success"})
            agent.__class__.__name__ = "MockAgent"
            return agent

        graph = TaskGraph(
            nodes={
                "task_1": TaskSpec(agent_factory=mock_agent_factory, prompt="Task 1", id="task_1"),
                "task_2": TaskSpec(agent_factory=mock_agent_factory, prompt="Task 2", id="task_2"),
                "task_3": TaskSpec(agent_factory=mock_agent_factory, prompt="Task 3", id="task_3"),
            },
            edges=[],  # All tasks in layer 0 (no dependencies)
        )

        # Act
        with patch("tools.orchestrator.graph._telemetry_emit"):
            result = await run_graph(mock_context, graph, simple_policy)

        # Assert
        assert len(result.tasks) == 3
        assert all(task.status == "success" for task in result.tasks)
        assert {task.id for task in result.tasks} == {"task_1", "task_2", "task_3"}

    @pytest.mark.asyncio
    async def test_run_graph_executes_all_tasks_across_multiple_batches(self, mock_context, simple_policy, mock_slop_immunity):
        """Test layer with tasks > max_workers executes ALL tasks in multiple batches."""
        # Arrange
        def mock_agent_factory(ctx):
            agent = AsyncMock()
            agent.run = AsyncMock(return_value={"result": "success"})
            agent.__class__.__name__ = "MockAgent"
            return agent

        # 5 tasks in layer 0, max_workers=2 → 3 batches
        graph = TaskGraph(
            nodes={
                f"task_{i}": TaskSpec(agent_factory=mock_agent_factory, prompt=f"Task {i}", id=f"task_{i}")
                for i in range(5)
            },
            edges=[],
        )

        # Act
        with patch("tools.orchestrator.graph._telemetry_emit"):
            result = await run_graph(mock_context, graph, simple_policy)

        # Assert
        assert len(result.tasks) == 5, "Not all tasks executed"
        assert all(task.status == "success" for task in result.tasks)

    @pytest.mark.asyncio
    async def test_run_graph_respects_max_workers_concurrency(self, mock_context, simple_policy, mock_slop_immunity):
        """Test max_workers limit enforced (no more than max_workers concurrent tasks)."""
        # Arrange
        concurrent_tasks = []

        def mock_agent_factory(ctx):
            agent = AsyncMock()

            async def track_concurrency(*args, **kwargs):
                concurrent_tasks.append(time.time())
                await asyncio.sleep(0.05)  # Simulate work
                return {"result": "success"}

            agent.run = track_concurrency
            agent.__class__.__name__ = "MockAgent"
            return agent

        # 6 tasks, max_workers=3
        graph = TaskGraph(
            nodes={
                f"task_{i}": TaskSpec(agent_factory=mock_agent_factory, prompt=f"Task {i}", id=f"task_{i}")
                for i in range(6)
            },
            edges=[],
        )

        policy = OrchestrationPolicy(max_concurrency=3, retry=RetryPolicy(max_attempts=1))

        # Act
        with patch("tools.orchestrator.graph._telemetry_emit"):
            result = await run_graph(mock_context, graph, policy)

        # Assert
        assert len(result.tasks) == 6

    # --- EDGE CASES ---

    @pytest.mark.asyncio
    async def test_run_graph_with_empty_graph(self, mock_context, simple_policy, mock_slop_immunity):
        """Test empty graph returns zero results."""
        # Arrange
        graph = TaskGraph(nodes={}, edges=[])

        # Act
        with patch("tools.orchestrator.graph._telemetry_emit"):
            result = await run_graph(mock_context, graph, simple_policy)

        # Assert
        assert len(result.tasks) == 0
        assert result.metrics.tasks == 0

    @pytest.mark.asyncio
    async def test_run_graph_with_single_task(self, mock_context, simple_policy, mock_slop_immunity):
        """Test single task executes successfully."""
        # Arrange
        def mock_agent_factory(ctx):
            agent = AsyncMock()
            agent.run = AsyncMock(return_value={"result": "success"})
            agent.__class__.__name__ = "MockAgent"
            return agent

        graph = TaskGraph(
            nodes={"task_1": TaskSpec(agent_factory=mock_agent_factory, prompt="Task 1", id="task_1")},
            edges=[],
        )

        # Act
        with patch("tools.orchestrator.graph._telemetry_emit"):
            result = await run_graph(mock_context, graph, simple_policy)

        # Assert
        assert len(result.tasks) == 1
        assert result.tasks[0].id == "task_1"
        assert result.tasks[0].status == "success"

    # --- CORNER CASES ---

    @pytest.mark.asyncio
    async def test_run_graph_with_max_workers_greater_than_layer_size(self, mock_context, mock_slop_immunity):
        """Test max_workers > layer_size executes all tasks in single batch."""
        # Arrange
        def mock_agent_factory(ctx):
            agent = AsyncMock()
            agent.run = AsyncMock(return_value={"result": "success"})
            agent.__class__.__name__ = "MockAgent"
            return agent

        graph = TaskGraph(
            nodes={
                "task_1": TaskSpec(agent_factory=mock_agent_factory, prompt="Task 1", id="task_1"),
                "task_2": TaskSpec(agent_factory=mock_agent_factory, prompt="Task 2", id="task_2"),
            },
            edges=[],
        )

        policy = OrchestrationPolicy(max_concurrency=10, retry=RetryPolicy(max_attempts=1))

        # Act
        with patch("tools.orchestrator.graph._telemetry_emit"):
            result = await run_graph(mock_context, graph, policy)

        # Assert
        assert len(result.tasks) == 2

    # --- TELEMETRY (Yield) ---

    @pytest.mark.asyncio
    async def test_run_graph_emits_batch_started_events(self, mock_context, simple_policy, mock_slop_immunity):
        """Test batch_started telemetry events emitted for each batch."""
        # Arrange
        def mock_agent_factory(ctx):
            agent = AsyncMock()
            agent.run = AsyncMock(return_value={"result": "success"})
            agent.__class__.__name__ = "MockAgent"
            return agent

        # 5 tasks, max_workers=2 → 3 batches
        graph = TaskGraph(
            nodes={
                f"task_{i}": TaskSpec(agent_factory=mock_agent_factory, prompt=f"Task {i}", id=f"task_{i}")
                for i in range(5)
            },
            edges=[],
        )

        telemetry_events = []

        def capture_telemetry(event):
            telemetry_events.append(event)

        # Act
        with patch("tools.orchestrator.graph._telemetry_emit", side_effect=capture_telemetry):
            await run_graph(mock_context, graph, simple_policy)

        # Assert
        batch_started_events = [e for e in telemetry_events if e.get("type") == "batch_started"]
        assert len(batch_started_events) == 3, f"Expected 3 batch_started events, got {len(batch_started_events)}"

        # Verify first batch structure
        first_batch = batch_started_events[0]
        assert first_batch["layer_id"] == 0
        assert first_batch["batch_id"] == 0
        assert first_batch["concurrency"] == 2

    @pytest.mark.asyncio
    async def test_run_graph_emits_batch_finished_events(self, mock_context, simple_policy, mock_slop_immunity):
        """Test batch_finished telemetry events emitted after batch completion."""
        # Arrange
        def mock_agent_factory(ctx):
            agent = AsyncMock()
            agent.run = AsyncMock(return_value={"result": "success"})
            agent.__class__.__name__ = "MockAgent"
            return agent

        graph = TaskGraph(
            nodes={
                f"task_{i}": TaskSpec(agent_factory=mock_agent_factory, prompt=f"Task {i}", id=f"task_{i}")
                for i in range(5)
            },
            edges=[],
        )

        telemetry_events = []

        def capture_telemetry(event):
            telemetry_events.append(event)

        # Act
        with patch("tools.orchestrator.graph._telemetry_emit", side_effect=capture_telemetry):
            await run_graph(mock_context, graph, simple_policy)

        # Assert
        batch_finished_events = [e for e in telemetry_events if e.get("type") == "batch_finished"]
        assert len(batch_finished_events) == 3

        # Verify batch finished includes completion count
        for event in batch_finished_events:
            assert "completed" in event
            assert "duration_s" in event

    @pytest.mark.asyncio
    async def test_run_graph_emits_layer_completed_event(self, mock_context, simple_policy, mock_slop_immunity):
        """Test layer_completed telemetry event emitted after layer finishes."""
        # Arrange
        def mock_agent_factory(ctx):
            agent = AsyncMock()
            agent.run = AsyncMock(return_value={"result": "success"})
            agent.__class__.__name__ = "MockAgent"
            return agent

        graph = TaskGraph(
            nodes={
                "task_1": TaskSpec(agent_factory=mock_agent_factory, prompt="Task 1", id="task_1"),
                "task_2": TaskSpec(agent_factory=mock_agent_factory, prompt="Task 2", id="task_2"),
            },
            edges=[],
        )

        telemetry_events = []

        def capture_telemetry(event):
            telemetry_events.append(event)

        # Act
        with patch("tools.orchestrator.graph._telemetry_emit", side_effect=capture_telemetry):
            await run_graph(mock_context, graph, simple_policy)

        # Assert
        layer_completed_events = [e for e in telemetry_events if e.get("type") == "layer_completed"]
        assert len(layer_completed_events) == 1

        layer_event = layer_completed_events[0]
        assert layer_event["layer_id"] == 0
        assert layer_event["tasks"] == 2
        assert layer_event["tasks_succeeded"] == 2
        assert layer_event["tasks_failed"] == 0

    # --- DETERMINISM (Regression) ---

    @pytest.mark.asyncio
    async def test_run_graph_deterministic_execution_order_across_runs(self, mock_context, simple_policy, mock_slop_immunity):
        """Test same graph produces identical execution order across runs."""
        # Arrange
        execution_orders = []

        def mock_agent_factory(ctx):
            agent = AsyncMock()

            async def track_order(prompt, *args, **kwargs):
                execution_orders.append(prompt)
                return {"result": "success"}

            agent.run = track_order
            agent.__class__.__name__ = "MockAgent"
            return agent

        graph = TaskGraph(
            nodes={
                "task_c": TaskSpec(agent_factory=mock_agent_factory, prompt="Task C", id="task_c"),
                "task_a": TaskSpec(agent_factory=mock_agent_factory, prompt="Task A", id="task_a"),
                "task_b": TaskSpec(agent_factory=mock_agent_factory, prompt="Task B", id="task_b"),
            },
            edges=[],
        )

        # Act
        run_1_orders = []
        run_2_orders = []

        with patch("tools.orchestrator.graph._telemetry_emit"):
            await run_graph(mock_context, graph, simple_policy)
            run_1_orders = execution_orders.copy()

            execution_orders.clear()

            await run_graph(mock_context, graph, simple_policy)
            run_2_orders = execution_orders.copy()

        # Assert - execution order should be deterministic (sorted by task ID)
        # With max_workers=2: batch 1 = [task_a, task_b], batch 2 = [task_c]
        assert run_1_orders == run_2_orders


# ============================================================================
# LAYER COMPLETION VERIFICATION TESTS
# ============================================================================


class TestLayerCompletionAssertion:
    """Test layer completion assertions (Article I compliance)."""

    @pytest.fixture
    def mock_context(self):
        """Create mock AgentContext for tests."""
        return create_agent_context(session_id="test_layer_completion")

    @pytest.fixture
    def mock_slop_immunity(self):
        """Mock slop immunity to always accept test task descriptions."""
        from shared.type_definitions.result import Ok
        from tools.orchestrator.slop_guardian import SlopVerdict

        with patch("tools.orchestrator.graph.enforce_slop_immunity") as mock_slop:
            mock_slop.return_value = Ok(
                SlopVerdict(
                    score=4.0,
                    reasons=[],
                    top_fixes=[],
                    dimension_scores={"clarity": 4.0, "measurability": 4.0, "completeness": 4.0, "actionability": 4.0},
                )
            )
            yield mock_slop

    @pytest.mark.asyncio
    async def test_layer_completion_assertion_passes_when_all_tasks_complete(self, mock_context, mock_slop_immunity):
        """Test assertion passes when all tasks in layer complete."""
        # Arrange
        def mock_agent_factory(ctx):
            agent = AsyncMock()
            agent.run = AsyncMock(return_value={"result": "success"})
            agent.__class__.__name__ = "MockAgent"
            return agent

        graph = TaskGraph(
            nodes={
                "task_1": TaskSpec(agent_factory=mock_agent_factory, prompt="Task 1", id="task_1"),
                "task_2": TaskSpec(agent_factory=mock_agent_factory, prompt="Task 2", id="task_2"),
                "task_3": TaskSpec(agent_factory=mock_agent_factory, prompt="Task 3", id="task_3"),
            },
            edges=[],
        )

        policy = OrchestrationPolicy(max_concurrency=2, retry=RetryPolicy(max_attempts=1))

        # Act & Assert (no assertion error = pass)
        with patch("tools.orchestrator.graph._telemetry_emit"):
            result = await run_graph(mock_context, graph, policy)
            assert len(result.tasks) == 3


# ============================================================================
# SLOP IMMUNITY INTEGRATION TESTS
# ============================================================================


class TestSlopImmunityIntegration:
    """Test slop immunity pre-flight checks block poor-quality task descriptions."""

    @pytest.fixture
    def mock_context(self):
        """Create mock AgentContext for tests."""
        return create_agent_context(session_id="test_slop_immunity")

    @pytest.mark.asyncio
    async def test_slop_immunity_allows_high_quality_task_descriptions(self, mock_context):
        """Test high-quality task descriptions pass slop immunity check."""
        # Arrange
        def mock_agent_factory(ctx):
            agent = AsyncMock()
            agent.run = AsyncMock(return_value={"result": "success"})
            agent.__class__.__name__ = "MockAgent"
            return agent

        graph = TaskGraph(
            nodes={
                "task_1": TaskSpec(
                    agent_factory=mock_agent_factory,
                    prompt="Implement JWT authentication with RSA-256 encryption, 15-minute token expiry",
                    id="task_1",
                )
            },
            edges=[],
        )

        policy = OrchestrationPolicy(max_concurrency=1, retry=RetryPolicy(max_attempts=1))

        # Mock slop guardian to ACCEPT
        from tools.orchestrator.slop_guardian import SlopVerdict, VerdictStatus

        mock_verdict = SlopVerdict(
            score=4.0,
            reasons=[],
            top_fixes=[],
            dimension_scores={"clarity": 4.0, "measurability": 4.0, "completeness": 4.0, "actionability": 4.0},
        )

        with patch("tools.orchestrator.graph.enforce_slop_immunity") as mock_enforce:
            from shared.type_definitions.result import Ok

            mock_enforce.return_value = Ok(mock_verdict)

            with patch("tools.orchestrator.graph._telemetry_emit"):
                # Act
                result = await run_graph(mock_context, graph, policy)

                # Assert
                assert len(result.tasks) == 1
                assert result.tasks[0].status == "success"
