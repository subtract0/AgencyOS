"""
Tests for Agent Orchestrator (Phase 5).

Tests the multi-agent coordination including:
- Task creation and management
- Agent routing
- Plan execution
- Task decomposition
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_all_statuses_defined(self):
        """Test that all expected statuses are defined."""
        from tools.agent_orchestrator import TaskStatus

        expected = ["PENDING", "QUEUED", "ASSIGNED", "RUNNING",
                    "COMPLETED", "FAILED", "BLOCKED", "CANCELLED"]
        for status in expected:
            assert hasattr(TaskStatus, status)


class TestTaskPriority:
    """Tests for TaskPriority enum."""

    def test_priority_ordering(self):
        """Test that priorities are correctly ordered."""
        from tools.agent_orchestrator import TaskPriority

        assert TaskPriority.CRITICAL.value < TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value < TaskPriority.MEDIUM.value
        assert TaskPriority.MEDIUM.value < TaskPriority.LOW.value


class TestTask:
    """Tests for Task dataclass."""

    def test_task_creation(self):
        """Test creating a task."""
        from tools.agent_factory import AgentCapability
        from tools.agent_orchestrator import Task, TaskPriority, TaskStatus

        task = Task(
            id="task-001",
            name="Write tests",
            description="Write unit tests for module",
            required_capabilities=[AgentCapability.TEST_GENERATION],
            priority=TaskPriority.HIGH,
        )

        assert task.id == "task-001"
        assert task.status == TaskStatus.PENDING
        assert task.retries == 0

    def test_task_comparison(self):
        """Test task comparison for priority queue."""
        from tools.agent_factory import AgentCapability
        from tools.agent_orchestrator import Task, TaskPriority

        high = Task(
            id="high",
            name="High priority",
            description="",
            required_capabilities=[AgentCapability.CODE_GENERATION],
            priority=TaskPriority.HIGH,
        )

        low = Task(
            id="low",
            name="Low priority",
            description="",
            required_capabilities=[AgentCapability.CODE_GENERATION],
            priority=TaskPriority.LOW,
        )

        # High priority should come before low
        assert high < low


class TestTaskResult:
    """Tests for TaskResult dataclass."""

    def test_task_result_creation(self):
        """Test creating a task result."""
        from tools.agent_orchestrator import TaskResult

        result = TaskResult(
            task_id="task-001",
            success=True,
            output={"status": "done"},
            duration_ms=150.5,
            agent_id="coder-abc123",
        )

        assert result.success
        assert result.duration_ms == 150.5


class TestOrchestrationPlan:
    """Tests for OrchestrationPlan dataclass."""

    def test_plan_creation(self):
        """Test creating an orchestration plan."""
        from tools.agent_factory import AgentCapability
        from tools.agent_orchestrator import OrchestrationPlan, Task

        task = Task(
            id="task-1",
            name="Task 1",
            description="",
            required_capabilities=[AgentCapability.CODE_GENERATION],
        )

        plan = OrchestrationPlan(
            id="plan-001",
            name="Test Plan",
            tasks=[task],
            parallel_groups=[["task-1"]],
        )

        assert plan.id == "plan-001"
        assert len(plan.tasks) == 1
        assert plan.status == "created"


class TestTaskRouter:
    """Tests for TaskRouter class."""

    @pytest.fixture
    def router(self):
        """Create a router instance."""
        from tools.agent_factory import AgentFactory
        from tools.agent_orchestrator import TaskRouter

        factory = AgentFactory()
        return TaskRouter(factory)

    def test_select_agent_type_for_code_gen(self, router):
        """Test selecting agent type for code generation."""
        from tools.agent_factory import AgentCapability
        from tools.agent_orchestrator import Task

        task = Task(
            id="test",
            name="Test",
            description="",
            required_capabilities=[AgentCapability.CODE_GENERATION],
        )

        agent_type = router.select_agent_type(task)

        assert agent_type == "coder"

    def test_select_agent_type_for_review(self, router):
        """Test selecting agent type for code review."""
        from tools.agent_factory import AgentCapability
        from tools.agent_orchestrator import Task

        task = Task(
            id="test",
            name="Test",
            description="",
            required_capabilities=[AgentCapability.CODE_REVIEW],
        )

        agent_type = router.select_agent_type(task)

        assert agent_type == "reviewer"

    def test_select_agent_type_for_testing(self, router):
        """Test selecting agent type for test generation."""
        from tools.agent_factory import AgentCapability
        from tools.agent_orchestrator import Task

        task = Task(
            id="test",
            name="Test",
            description="",
            required_capabilities=[AgentCapability.TEST_GENERATION],
        )

        agent_type = router.select_agent_type(task)

        assert agent_type == "tester"


class TestAgentOrchestrator:
    """Tests for AgentOrchestrator class."""

    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator instance."""
        from tools.agent_factory import AgentFactory
        from tools.agent_orchestrator import AgentOrchestrator

        factory = AgentFactory()
        return AgentOrchestrator(factory)

    def test_create_task(self, orchestrator):
        """Test creating a task."""
        from tools.agent_factory import AgentCapability

        result = orchestrator.create_task(
            name="Write function",
            description="Write a helper function",
            capabilities=[AgentCapability.CODE_GENERATION],
        )

        assert result.is_ok()
        task = result.unwrap()
        assert task.id.startswith("task-")
        assert task.name == "Write function"

    def test_create_task_requires_name(self, orchestrator):
        """Test that task creation requires name."""
        from tools.agent_factory import AgentCapability

        result = orchestrator.create_task(
            name="",
            description="",
            capabilities=[AgentCapability.CODE_GENERATION],
        )

        assert result.is_err()
        assert "name" in result.unwrap_err().lower()

    def test_create_task_requires_capabilities(self, orchestrator):
        """Test that task creation requires capabilities."""
        result = orchestrator.create_task(
            name="Test",
            description="",
            capabilities=[],
        )

        assert result.is_err()
        assert "capability" in result.unwrap_err().lower()

    def test_queue_task(self, orchestrator):
        """Test queuing a task."""
        from tools.agent_factory import AgentCapability
        from tools.agent_orchestrator import TaskStatus

        task_result = orchestrator.create_task(
            name="Test",
            description="",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        task = task_result.unwrap()

        result = orchestrator.queue_task(task.id)

        assert result.is_ok()
        assert orchestrator.get_task(task.id).status == TaskStatus.QUEUED

    def test_queue_task_with_unmet_dependencies(self, orchestrator):
        """Test queuing task with unmet dependencies blocks it."""
        from tools.agent_factory import AgentCapability
        from tools.agent_orchestrator import TaskStatus

        # Create dependency task
        dep_result = orchestrator.create_task(
            name="Dependency",
            description="",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        dep_task = dep_result.unwrap()

        # Create dependent task
        task_result = orchestrator.create_task(
            name="Dependent",
            description="",
            capabilities=[AgentCapability.CODE_GENERATION],
            dependencies=[dep_task.id],
        )
        task = task_result.unwrap()

        result = orchestrator.queue_task(task.id)

        assert result.is_ok()
        # Task should be blocked, not queued
        assert orchestrator.get_task(task.id).status == TaskStatus.BLOCKED

    def test_execute_task(self, orchestrator):
        """Test executing a task."""
        from tools.agent_factory import AgentCapability

        task_result = orchestrator.create_task(
            name="Execute test",
            description="Test execution",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        task = task_result.unwrap()

        result = orchestrator.execute_task(task.id)

        assert result.is_ok()
        exec_result = result.unwrap()
        assert exec_result.success
        assert exec_result.agent_id is not None

    def test_execute_nonexistent_task(self, orchestrator):
        """Test executing nonexistent task fails."""
        result = orchestrator.execute_task("nonexistent")

        assert result.is_err()
        assert "not found" in result.unwrap_err().lower()

    def test_create_plan(self, orchestrator):
        """Test creating an orchestration plan."""
        from tools.agent_factory import AgentCapability
        from tools.agent_orchestrator import Task

        tasks = [
            Task(
                id=f"task-{i}",
                name=f"Task {i}",
                description="",
                required_capabilities=[AgentCapability.CODE_GENERATION],
            )
            for i in range(3)
        ]

        result = orchestrator.create_plan("Test Plan", tasks)

        assert result.is_ok()
        plan = result.unwrap()
        assert plan.name == "Test Plan"
        assert len(plan.tasks) == 3

    def test_create_plan_requires_tasks(self, orchestrator):
        """Test that plan creation requires tasks."""
        result = orchestrator.create_plan("Empty Plan", [])

        assert result.is_err()
        assert "task" in result.unwrap_err().lower()

    def test_execute_plan(self, orchestrator):
        """Test executing a plan."""
        from tools.agent_factory import AgentCapability
        from tools.agent_orchestrator import Task

        tasks = [
            Task(
                id=f"plan-task-{i}",
                name=f"Task {i}",
                description="",
                required_capabilities=[AgentCapability.CODE_GENERATION],
            )
            for i in range(2)
        ]

        plan_result = orchestrator.create_plan("Exec Plan", tasks)
        plan = plan_result.unwrap()

        result = orchestrator.execute_plan(plan.id)

        assert result.is_ok()
        results = result.unwrap()
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_compute_parallel_groups(self, orchestrator):
        """Test computing parallel groups."""
        from tools.agent_factory import AgentCapability
        from tools.agent_orchestrator import Task

        # Task 1 and 2 can run in parallel, Task 3 depends on both
        tasks = [
            Task(
                id="t1",
                name="Task 1",
                description="",
                required_capabilities=[AgentCapability.CODE_GENERATION],
            ),
            Task(
                id="t2",
                name="Task 2",
                description="",
                required_capabilities=[AgentCapability.CODE_GENERATION],
            ),
            Task(
                id="t3",
                name="Task 3",
                description="",
                required_capabilities=[AgentCapability.CODE_GENERATION],
                dependencies=["t1", "t2"],
            ),
        ]

        groups = orchestrator._compute_parallel_groups(tasks)

        # First group: t1, t2 (no deps)
        assert len(groups) >= 2
        assert set(groups[0]) == {"t1", "t2"}
        # Second group: t3 (after deps)
        assert "t3" in groups[1]

    def test_decompose_task(self, orchestrator):
        """Test decomposing a complex task."""
        from tools.agent_factory import AgentCapability
        from tools.agent_orchestrator import Task

        complex_task = Task(
            id="complex",
            name="Complex Task",
            description="A task with multiple capabilities",
            required_capabilities=[
                AgentCapability.CODE_GENERATION,
                AgentCapability.TEST_GENERATION,
                AgentCapability.DOCUMENTATION,
            ],
        )

        result = orchestrator.decompose_task(complex_task)

        assert result.is_ok()
        subtasks = result.unwrap()
        assert len(subtasks) == 3  # One per capability

    def test_cancel_task(self, orchestrator):
        """Test cancelling a task."""
        from tools.agent_factory import AgentCapability
        from tools.agent_orchestrator import TaskStatus

        task_result = orchestrator.create_task(
            name="To Cancel",
            description="",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        task = task_result.unwrap()

        result = orchestrator.cancel_task(task.id)

        assert result.is_ok()
        assert orchestrator.get_task(task.id).status == TaskStatus.CANCELLED

    def test_get_stats(self, orchestrator):
        """Test getting orchestrator stats."""
        from tools.agent_factory import AgentCapability

        # Create some tasks
        for i in range(3):
            orchestrator.create_task(
                name=f"Task {i}",
                description="",
                capabilities=[AgentCapability.CODE_GENERATION],
            )

        stats = orchestrator.get_stats()

        assert stats.total_tasks == 3
        assert stats.pending_tasks == 3
        assert stats.completed_tasks == 0


class TestOrchestratorStats:
    """Tests for OrchestratorStats dataclass."""

    def test_stats_creation(self):
        """Test creating orchestrator stats."""
        from tools.agent_orchestrator import OrchestratorStats

        stats = OrchestratorStats(
            total_tasks=100,
            completed_tasks=80,
            failed_tasks=5,
            running_tasks=10,
            pending_tasks=5,
            active_agents=3,
            avg_task_duration_ms=150.0,
            success_rate=0.94,
        )

        assert stats.total_tasks == 100
        assert stats.success_rate == 0.94
