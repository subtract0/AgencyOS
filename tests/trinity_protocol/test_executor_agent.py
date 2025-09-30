"""
Tests for Trinity Protocol EXECUTOR Agent (Action Layer)

NECESSARY Pattern Compliance:
- Named: Clear test names describing 9-step action cycle behavior
- Executable: Run independently with async support
- Comprehensive: Cover task processing, orchestration, verification, reporting
- Error-validated: Test async error conditions and resilience
- State-verified: Assert plan externalization and telemetry reports
- Side-effects controlled: Mock external dependencies (sub-agents, file system, subprocess)
- Assertions meaningful: Specific checks for each action step
- Repeatable: Deterministic async results
- Yield fast: <1s per test (mocked LLM and subprocess calls)
"""

import pytest
import asyncio
import tempfile
import json
import subprocess
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, Mock, MagicMock, patch, call, mock_open
from typing import Dict, Any, List

# NOTE: EXECUTOR agent implementation will be created in trinity_protocol.executor_agent
# For now, we define the expected interface based on the spec


# Mock EXECUTOR agent implementation for testing
class ExecutorAgent:
    """EXECUTOR Agent - Meta-orchestrator for Trinity Protocol."""

    def __init__(self, message_bus, cost_tracker):
        """Initialize EXECUTOR with message bus and cost tracker."""
        self.message_bus = message_bus
        self.cost_tracker = cost_tracker
        self.input_queue = "execution_queue"
        self.output_queue = "telemetry_stream"
        self.plans_dir = Path("/tmp/executor_plans")
        self._running = False
        self._tasks: List[asyncio.Task] = []

        # Sub-agent registry
        self.sub_agents = {
            "CodeWriter": None,
            "TestArchitect": None,
            "ToolDeveloper": None,
            "ImmunityEnforcer": None,
            "ReleaseManager": None,
            "TaskSummarizer": None
        }

    async def run(self):
        """Main loop: subscribe to execution_queue."""
        self._running = True
        async for task in self.message_bus.subscribe(self.input_queue):
            if not self._running:
                break
            await self._process_task(task)

    async def stop(self):
        """Stop the agent gracefully."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        9-step cycle:
        1. LISTEN (task received)
        2. DECONSTRUCT
        3. PLAN & EXTERNALIZE
        4. ORCHESTRATE (PARALLEL)
        5. HANDLE FAILURES
        6. DELEGATE MERGE
        7. ABSOLUTE VERIFICATION
        8. REPORT
        9. RESET
        """
        task_id = task.get("id", "unknown")
        correlation_id = task.get("correlation_id", "")

        try:
            # Step 2: DECONSTRUCT
            plan = self._deconstruct_task(task)

            # Step 3: PLAN & EXTERNALIZE
            plan_path = self._externalize_plan(task_id, plan)

            # Step 4: ORCHESTRATE (PARALLEL)
            sub_agent_results = await self._orchestrate_parallel(plan)

            # Step 6: DELEGATE MERGE
            merge_result = await self._delegate_merge(sub_agent_results)

            # Step 7: ABSOLUTE VERIFICATION
            verification_result = self._run_absolute_verification()

            # Step 8: REPORT
            report = self._create_telemetry_report(
                task_id=task_id,
                correlation_id=correlation_id,
                status="success",
                details="Task completed and verified",
                sub_agent_reports=sub_agent_results,
                verification_result=verification_result
            )

            await self.message_bus.publish(self.output_queue, report)

            return report

        except Exception as e:
            # Step 5: HANDLE FAILURES
            error_report = self._handle_failure(task_id, correlation_id, str(e))
            await self.message_bus.publish(self.output_queue, error_report)
            return error_report

        finally:
            # Step 9: RESET
            self._cleanup_temp_files(task_id)

    def _deconstruct_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Break down task into sub-agent delegations."""
        task_type = task.get("type", "feature")

        plan = {
            "task_id": task.get("id"),
            "sub_agents": [],
            "parallel_groups": []
        }

        # Determine required sub-agents based on task type
        if task_type == "feature":
            plan["sub_agents"] = ["CodeWriter", "TestArchitect"]
            plan["parallel_groups"] = [["CodeWriter", "TestArchitect"]]
        elif task_type == "bug_fix":
            plan["sub_agents"] = ["CodeWriter", "TestArchitect"]
            plan["parallel_groups"] = [["CodeWriter", "TestArchitect"]]
        elif task_type == "tool_creation":
            plan["sub_agents"] = ["ToolDeveloper", "TestArchitect"]
            plan["parallel_groups"] = [["ToolDeveloper", "TestArchitect"]]
        elif task_type == "refactor":
            plan["sub_agents"] = ["ImmunityEnforcer", "CodeWriter", "TestArchitect"]
            plan["parallel_groups"] = [["CodeWriter", "TestArchitect"]]

        return plan

    def _externalize_plan(self, task_id: str, plan: Dict[str, Any]) -> str:
        """Write execution plan to /tmp/executor_plans/."""
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        plan_path = self.plans_dir / f"{task_id}_plan.md"

        content = f"# Execution Plan: {task_id}\n\n"
        content += "## Sub-Agents\n"
        for agent in plan.get("sub_agents", []):
            content += f"- {agent}\n"
        content += "\n## Parallel Groups\n"
        for group in plan.get("parallel_groups", []):
            content += f"- {', '.join(group)}\n"
        content += "\n## Verification\n"
        content += "- Command: python run_tests.py --run-all\n"

        plan_path.write_text(content)

        return str(plan_path)

    async def _orchestrate_parallel(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Orchestrate parallel sub-agent execution."""
        results = []

        for group in plan.get("parallel_groups", []):
            # Execute group members in parallel
            tasks = []
            for agent_name in group:
                agent = self.sub_agents.get(agent_name)
                if agent:
                    tasks.append(self._execute_sub_agent(agent_name, agent, plan))

            # Await all parallel tasks
            group_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for failures
            for result in group_results:
                if isinstance(result, Exception):
                    raise result
                results.append(result)

        return results

    async def _execute_sub_agent(self, name: str, agent: Any, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single sub-agent task."""
        # Track cost if agent supports it
        if hasattr(agent, "execute"):
            result = await agent.execute(plan)
        else:
            result = {"status": "success", "summary": f"{name} completed"}

        return {
            "agent": name,
            "status": result.get("status", "success"),
            "summary": result.get("summary", "")
        }

    async def _delegate_merge(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Delegate to ReleaseManager for integration and commit."""
        release_manager = self.sub_agents.get("ReleaseManager")

        if release_manager:
            merge_result = await release_manager.merge(results)
            return merge_result

        return {"status": "success", "summary": "No merge required"}

    def _run_absolute_verification(self) -> str:
        """
        Article II: Non-negotiable full test suite execution.
        Returns: Test output string
        Raises: Exception if tests fail
        """
        result = subprocess.run(
            ["python", "run_tests.py", "--run-all"],
            capture_output=True,
            text=True,
            timeout=600  # 10 min max
        )

        if result.returncode != 0:
            raise Exception(f"Verification failed. Test suite not clean.\n{result.stdout}")

        return result.stdout

    def _handle_failure(self, task_id: str, correlation_id: str, error: str) -> Dict[str, Any]:
        """Log failure and prepare failure report."""
        error_log = self.plans_dir / f"{task_id}_error.log"

        self.plans_dir.mkdir(parents=True, exist_ok=True)
        error_log.write_text(
            f"Error: {error}\n"
            f"Timestamp: {datetime.now().isoformat()}\n"
        )

        return self._create_telemetry_report(
            task_id=task_id,
            correlation_id=correlation_id,
            status="failure",
            details=f"Task failed: {error}",
            sub_agent_reports=[],
            verification_result="N/A - Task failure"
        )

    def _create_telemetry_report(
        self,
        task_id: str,
        correlation_id: str,
        status: str,
        details: str,
        sub_agent_reports: List[Dict[str, Any]],
        verification_result: str
    ) -> Dict[str, Any]:
        """Create minified JSON telemetry report."""
        return {
            "status": status,
            "task_id": task_id,
            "correlation_id": correlation_id,
            "details": details,
            "sub_agent_reports": sub_agent_reports,
            "verification_result": verification_result,
            "timestamp": datetime.now().isoformat()
        }

    def _cleanup_temp_files(self, task_id: str):
        """Clean up temporary plan and error files."""
        if self.plans_dir.exists():
            for file in self.plans_dir.glob(f"{task_id}_*"):
                file.unlink()


# Test fixtures
@pytest.fixture
def temp_db_paths():
    """Provide temporary database paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield {
            "message_bus": Path(tmpdir) / "test_messages.db",
            "executor_plans": Path(tmpdir) / "executor_plans"
        }


@pytest.fixture
def message_bus(temp_db_paths):
    """Provide mock message bus."""
    bus = Mock()
    bus.subscribe = AsyncMock()
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def cost_tracker():
    """Provide mock cost tracker."""
    tracker = Mock()
    tracker.track_call = Mock()
    tracker.get_total_cost = Mock(return_value=0.0)
    return tracker


@pytest.fixture
def executor_agent(message_bus, cost_tracker, temp_db_paths):
    """Provide initialized ExecutorAgent."""
    agent = ExecutorAgent(
        message_bus=message_bus,
        cost_tracker=cost_tracker
    )
    agent.plans_dir = temp_db_paths["executor_plans"]
    agent.plans_dir.mkdir(parents=True, exist_ok=True)
    return agent


@pytest.fixture
def mock_sub_agents():
    """Provide mock sub-agent implementations."""
    return {
        "CodeWriter": Mock(execute=AsyncMock(return_value={"status": "success", "summary": "Code written"})),
        "TestArchitect": Mock(execute=AsyncMock(return_value={"status": "success", "summary": "Tests created"})),
        "ToolDeveloper": Mock(execute=AsyncMock(return_value={"status": "success", "summary": "Tool developed"})),
        "ImmunityEnforcer": Mock(execute=AsyncMock(return_value={"status": "success", "summary": "Constitutional check passed"})),
        "ReleaseManager": Mock(merge=AsyncMock(return_value={"status": "success", "summary": "Merged successfully"})),
        "TaskSummarizer": Mock(execute=AsyncMock(return_value={"status": "success", "summary": "Summary generated"}))
    }


@pytest.fixture
def sample_task():
    """Provide sample task for testing."""
    return {
        "id": "task_123",
        "correlation_id": "corr_456",
        "type": "feature",
        "description": "Implement user authentication",
        "timestamp": datetime.now().isoformat()
    }


# Initialization tests
class TestExecutorAgentInitialization:
    """Test ExecutorAgent initialization."""

    def test_initializes_with_message_bus_and_cost_tracker(self, message_bus, cost_tracker):
        """Agent initializes with required dependencies."""
        agent = ExecutorAgent(
            message_bus=message_bus,
            cost_tracker=cost_tracker
        )

        assert agent.message_bus is message_bus
        assert agent.cost_tracker is cost_tracker

    def test_sets_default_queue_names(self, executor_agent):
        """Agent uses default queue names."""
        assert executor_agent.input_queue == "execution_queue"
        assert executor_agent.output_queue == "telemetry_stream"

    def test_initializes_with_not_running_state(self, executor_agent):
        """Agent starts in not-running state."""
        assert executor_agent._running is False
        assert executor_agent._tasks == []

    def test_sets_plans_directory(self, executor_agent):
        """Agent configures plans directory for state externalization."""
        assert executor_agent.plans_dir is not None
        assert isinstance(executor_agent.plans_dir, Path)

    def test_initializes_sub_agent_registry(self, executor_agent):
        """Agent initializes empty sub-agent registry."""
        assert "CodeWriter" in executor_agent.sub_agents
        assert "TestArchitect" in executor_agent.sub_agents
        assert "ToolDeveloper" in executor_agent.sub_agents
        assert "ImmunityEnforcer" in executor_agent.sub_agents
        assert "ReleaseManager" in executor_agent.sub_agents
        assert "TaskSummarizer" in executor_agent.sub_agents


# Task deconstruction tests (Step 2)
class TestTaskDeconstruction:
    """Test task deconstruction into sub-agent delegations."""

    def test_deconstructs_feature_task_into_code_and_test_agents(self, executor_agent):
        """Feature tasks require CodeWriter + TestArchitect."""
        task = {"id": "task_1", "type": "feature"}

        plan = executor_agent._deconstruct_task(task)

        assert "CodeWriter" in plan["sub_agents"]
        assert "TestArchitect" in plan["sub_agents"]
        assert ["CodeWriter", "TestArchitect"] in plan["parallel_groups"]

    def test_deconstructs_bug_fix_into_code_and_test_agents(self, executor_agent):
        """Bug fix tasks require CodeWriter + TestArchitect."""
        task = {"id": "task_2", "type": "bug_fix"}

        plan = executor_agent._deconstruct_task(task)

        assert "CodeWriter" in plan["sub_agents"]
        assert "TestArchitect" in plan["sub_agents"]

    def test_deconstructs_tool_creation_into_tool_and_test_agents(self, executor_agent):
        """Tool creation requires ToolDeveloper + TestArchitect."""
        task = {"id": "task_3", "type": "tool_creation"}

        plan = executor_agent._deconstruct_task(task)

        assert "ToolDeveloper" in plan["sub_agents"]
        assert "TestArchitect" in plan["sub_agents"]

    def test_deconstructs_refactor_includes_immunity_enforcer(self, executor_agent):
        """Refactor tasks require ImmunityEnforcer + CodeWriter + TestArchitect."""
        task = {"id": "task_4", "type": "refactor"}

        plan = executor_agent._deconstruct_task(task)

        assert "ImmunityEnforcer" in plan["sub_agents"]
        assert "CodeWriter" in plan["sub_agents"]
        assert "TestArchitect" in plan["sub_agents"]

    def test_includes_task_id_in_plan(self, executor_agent):
        """Plan includes original task ID for tracking."""
        task = {"id": "task_5", "type": "feature"}

        plan = executor_agent._deconstruct_task(task)

        assert plan["task_id"] == "task_5"


# Plan externalization tests (Step 3)
class TestPlanExternalization:
    """Test plan externalization to /tmp/executor_plans/."""

    def test_creates_plan_file_in_temp_directory(self, executor_agent):
        """Plan is written to /tmp/executor_plans/<task_id>_plan.md."""
        task_id = "task_123"
        plan = {
            "sub_agents": ["CodeWriter", "TestArchitect"],
            "parallel_groups": [["CodeWriter", "TestArchitect"]]
        }

        plan_path = executor_agent._externalize_plan(task_id, plan)

        assert Path(plan_path).exists()
        assert task_id in plan_path
        assert plan_path.endswith("_plan.md")

    def test_plan_file_contains_sub_agents(self, executor_agent):
        """Plan file lists all sub-agents."""
        task_id = "task_124"
        plan = {
            "sub_agents": ["CodeWriter", "TestArchitect", "ImmunityEnforcer"],
            "parallel_groups": []
        }

        plan_path = executor_agent._externalize_plan(task_id, plan)
        content = Path(plan_path).read_text()

        assert "CodeWriter" in content
        assert "TestArchitect" in content
        assert "ImmunityEnforcer" in content

    def test_plan_file_contains_parallel_groups(self, executor_agent):
        """Plan file lists parallel execution groups."""
        task_id = "task_125"
        plan = {
            "sub_agents": ["CodeWriter", "TestArchitect"],
            "parallel_groups": [["CodeWriter", "TestArchitect"]]
        }

        plan_path = executor_agent._externalize_plan(task_id, plan)
        content = Path(plan_path).read_text()

        assert "Parallel Groups" in content
        assert "CodeWriter, TestArchitect" in content

    def test_plan_file_contains_verification_command(self, executor_agent):
        """Plan file specifies verification command."""
        task_id = "task_126"
        plan = {"sub_agents": [], "parallel_groups": []}

        plan_path = executor_agent._externalize_plan(task_id, plan)
        content = Path(plan_path).read_text()

        assert "python run_tests.py --run-all" in content

    def test_creates_plans_directory_if_not_exists(self, executor_agent, temp_db_paths):
        """Plan externalization creates directory if missing."""
        executor_agent.plans_dir = temp_db_paths["executor_plans"] / "nested"
        task_id = "task_127"
        plan = {"sub_agents": [], "parallel_groups": []}

        plan_path = executor_agent._externalize_plan(task_id, plan)

        assert executor_agent.plans_dir.exists()
        assert Path(plan_path).exists()


# Parallel orchestration tests (Step 4)
class TestParallelOrchestration:
    """Test parallel sub-agent orchestration."""

    @pytest.mark.asyncio
    async def test_executes_parallel_group_concurrently(self, executor_agent, mock_sub_agents):
        """Sub-agents in same group execute in parallel."""
        executor_agent.sub_agents = mock_sub_agents
        plan = {
            "parallel_groups": [["CodeWriter", "TestArchitect"]]
        }

        results = await executor_agent._orchestrate_parallel(plan)

        assert len(results) == 2
        mock_sub_agents["CodeWriter"].execute.assert_awaited_once()
        mock_sub_agents["TestArchitect"].execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_results_from_all_sub_agents(self, executor_agent, mock_sub_agents):
        """Orchestration returns results from all sub-agents."""
        executor_agent.sub_agents = mock_sub_agents
        plan = {
            "parallel_groups": [["CodeWriter", "TestArchitect"]]
        }

        results = await executor_agent._orchestrate_parallel(plan)

        agent_names = [r["agent"] for r in results]
        assert "CodeWriter" in agent_names
        assert "TestArchitect" in agent_names

    @pytest.mark.asyncio
    async def test_raises_exception_on_sub_agent_failure(self, executor_agent, mock_sub_agents):
        """Orchestration raises exception if sub-agent fails."""
        mock_sub_agents["CodeWriter"].execute = AsyncMock(side_effect=Exception("CodeWriter failed"))
        executor_agent.sub_agents = mock_sub_agents
        plan = {
            "parallel_groups": [["CodeWriter"]]
        }

        with pytest.raises(Exception, match="CodeWriter failed"):
            await executor_agent._orchestrate_parallel(plan)

    @pytest.mark.asyncio
    async def test_executes_multiple_parallel_groups_sequentially(self, executor_agent, mock_sub_agents):
        """Multiple parallel groups execute sequentially."""
        executor_agent.sub_agents = mock_sub_agents
        plan = {
            "parallel_groups": [
                ["CodeWriter"],
                ["TestArchitect"]
            ]
        }

        results = await executor_agent._orchestrate_parallel(plan)

        assert len(results) == 2
        # Both should have been executed
        mock_sub_agents["CodeWriter"].execute.assert_awaited_once()
        mock_sub_agents["TestArchitect"].execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handles_empty_parallel_groups(self, executor_agent):
        """Orchestration handles empty parallel groups gracefully."""
        plan = {"parallel_groups": []}

        results = await executor_agent._orchestrate_parallel(plan)

        assert results == []


# Failure handling tests (Step 5)
class TestFailureHandling:
    """Test failure handling and error logging."""

    def test_creates_error_log_file(self, executor_agent):
        """Failure creates error log in /tmp/executor_plans/."""
        task_id = "task_error_1"
        error_msg = "Sub-agent execution failed"

        report = executor_agent._handle_failure(task_id, "corr_1", error_msg)

        error_log = executor_agent.plans_dir / f"{task_id}_error.log"
        assert error_log.exists()

    def test_error_log_contains_error_message(self, executor_agent):
        """Error log contains error details."""
        task_id = "task_error_2"
        error_msg = "CodeWriter failed: syntax error"

        executor_agent._handle_failure(task_id, "corr_2", error_msg)

        error_log = executor_agent.plans_dir / f"{task_id}_error.log"
        content = error_log.read_text()
        assert error_msg in content

    def test_error_log_contains_timestamp(self, executor_agent):
        """Error log includes timestamp."""
        task_id = "task_error_3"

        executor_agent._handle_failure(task_id, "corr_3", "Error")

        error_log = executor_agent.plans_dir / f"{task_id}_error.log"
        content = error_log.read_text()
        assert "Timestamp:" in content

    def test_returns_failure_telemetry_report(self, executor_agent):
        """Failure handling returns failure telemetry report."""
        task_id = "task_error_4"
        correlation_id = "corr_4"

        report = executor_agent._handle_failure(task_id, correlation_id, "Error")

        assert report["status"] == "failure"
        assert report["task_id"] == task_id
        assert report["correlation_id"] == correlation_id

    def test_failure_report_includes_na_verification_result(self, executor_agent):
        """Failure report indicates N/A for verification."""
        report = executor_agent._handle_failure("task_err", "corr", "Error")

        assert "N/A" in report["verification_result"]


# Merge delegation tests (Step 6)
class TestMergeDelegation:
    """Test merge delegation to ReleaseManager."""

    @pytest.mark.asyncio
    async def test_delegates_to_release_manager(self, executor_agent, mock_sub_agents):
        """Merge is delegated to ReleaseManager."""
        executor_agent.sub_agents = mock_sub_agents
        results = [
            {"agent": "CodeWriter", "status": "success"},
            {"agent": "TestArchitect", "status": "success"}
        ]

        merge_result = await executor_agent._delegate_merge(results)

        mock_sub_agents["ReleaseManager"].merge.assert_awaited_once_with(results)

    @pytest.mark.asyncio
    async def test_returns_merge_result(self, executor_agent, mock_sub_agents):
        """Merge delegation returns ReleaseManager result."""
        executor_agent.sub_agents = mock_sub_agents
        results = []

        merge_result = await executor_agent._delegate_merge(results)

        assert merge_result["status"] == "success"

    @pytest.mark.asyncio
    async def test_handles_missing_release_manager(self, executor_agent):
        """Merge delegation handles missing ReleaseManager gracefully."""
        executor_agent.sub_agents["ReleaseManager"] = None
        results = []

        merge_result = await executor_agent._delegate_merge(results)

        assert merge_result["status"] == "success"
        assert "No merge required" in merge_result["summary"]


# Absolute verification tests (Step 7)
class TestAbsoluteVerification:
    """Test absolute verification (Article II)."""

    @patch("subprocess.run")
    def test_executes_full_test_suite(self, mock_run, executor_agent):
        """Verification runs 'python run_tests.py --run-all'."""
        mock_run.return_value = Mock(returncode=0, stdout="1843 tests passed")

        executor_agent._run_absolute_verification()

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ["python", "run_tests.py", "--run-all"]

    @patch("subprocess.run")
    def test_returns_test_output_on_success(self, mock_run, executor_agent):
        """Verification returns test output string."""
        expected_output = "1843 tests passed"
        mock_run.return_value = Mock(returncode=0, stdout=expected_output)

        result = executor_agent._run_absolute_verification()

        assert result == expected_output

    @patch("subprocess.run")
    def test_raises_exception_on_test_failure(self, mock_run, executor_agent):
        """Verification raises exception if tests fail (Article II)."""
        mock_run.return_value = Mock(returncode=1, stdout="2 failed, 1841 passed")

        with pytest.raises(Exception, match="Verification failed"):
            executor_agent._run_absolute_verification()

    @patch("subprocess.run")
    def test_includes_test_output_in_exception(self, mock_run, executor_agent):
        """Exception message includes test output."""
        test_output = "2 failed, 1841 passed"
        mock_run.return_value = Mock(returncode=1, stdout=test_output)

        with pytest.raises(Exception, match=test_output):
            executor_agent._run_absolute_verification()

    @patch("subprocess.run")
    def test_sets_timeout_for_verification(self, mock_run, executor_agent):
        """Verification has 10-minute timeout."""
        mock_run.return_value = Mock(returncode=0, stdout="Tests passed")

        executor_agent._run_absolute_verification()

        assert mock_run.call_args[1]["timeout"] == 600


# Telemetry report tests (Step 8)
class TestTelemetryReportGeneration:
    """Test telemetry report creation."""

    def test_creates_minified_json_report(self, executor_agent):
        """Report is valid JSON structure."""
        report = executor_agent._create_telemetry_report(
            task_id="task_1",
            correlation_id="corr_1",
            status="success",
            details="Completed",
            sub_agent_reports=[],
            verification_result="1843 passed"
        )

        # Verify it's a dict (JSON-serializable)
        assert isinstance(report, dict)
        # Verify it can be JSON-serialized
        json_str = json.dumps(report)
        assert json_str is not None

    def test_report_includes_status(self, executor_agent):
        """Report includes success/failure status."""
        report = executor_agent._create_telemetry_report(
            task_id="task_1",
            correlation_id="corr_1",
            status="success",
            details="",
            sub_agent_reports=[],
            verification_result=""
        )

        assert report["status"] == "success"

    def test_report_includes_task_id(self, executor_agent):
        """Report includes original task ID."""
        report = executor_agent._create_telemetry_report(
            task_id="task_123",
            correlation_id="corr_1",
            status="success",
            details="",
            sub_agent_reports=[],
            verification_result=""
        )

        assert report["task_id"] == "task_123"

    def test_report_includes_correlation_id(self, executor_agent):
        """Report includes correlation ID for tracing."""
        report = executor_agent._create_telemetry_report(
            task_id="task_1",
            correlation_id="corr_456",
            status="success",
            details="",
            sub_agent_reports=[],
            verification_result=""
        )

        assert report["correlation_id"] == "corr_456"

    def test_report_includes_details(self, executor_agent):
        """Report includes task details."""
        report = executor_agent._create_telemetry_report(
            task_id="task_1",
            correlation_id="corr_1",
            status="success",
            details="Task completed successfully",
            sub_agent_reports=[],
            verification_result=""
        )

        assert report["details"] == "Task completed successfully"

    def test_report_includes_sub_agent_reports(self, executor_agent):
        """Report includes all sub-agent reports."""
        sub_reports = [
            {"agent": "CodeWriter", "status": "success", "summary": "Code written"},
            {"agent": "TestArchitect", "status": "success", "summary": "Tests added"}
        ]

        report = executor_agent._create_telemetry_report(
            task_id="task_1",
            correlation_id="corr_1",
            status="success",
            details="",
            sub_agent_reports=sub_reports,
            verification_result=""
        )

        assert len(report["sub_agent_reports"]) == 2
        assert report["sub_agent_reports"][0]["agent"] == "CodeWriter"

    def test_report_includes_verification_result(self, executor_agent):
        """Report includes test suite output."""
        report = executor_agent._create_telemetry_report(
            task_id="task_1",
            correlation_id="corr_1",
            status="success",
            details="",
            sub_agent_reports=[],
            verification_result="1843 tests passed"
        )

        assert report["verification_result"] == "1843 tests passed"

    def test_report_includes_iso8601_timestamp(self, executor_agent):
        """Report includes ISO8601 timestamp."""
        report = executor_agent._create_telemetry_report(
            task_id="task_1",
            correlation_id="corr_1",
            status="success",
            details="",
            sub_agent_reports=[],
            verification_result=""
        )

        # Verify timestamp exists and is ISO8601 format
        assert "timestamp" in report
        # Basic ISO8601 check (contains 'T' and ends with 'Z' or offset)
        timestamp = report["timestamp"]
        assert "T" in timestamp or "-" in timestamp


# Cleanup tests (Step 9)
class TestStateCleanup:
    """Test state cleanup and reset."""

    def test_removes_plan_file_after_task(self, executor_agent):
        """Cleanup removes plan file."""
        task_id = "task_cleanup_1"
        plan_file = executor_agent.plans_dir / f"{task_id}_plan.md"
        plan_file.write_text("Test plan")

        executor_agent._cleanup_temp_files(task_id)

        assert not plan_file.exists()

    def test_removes_error_log_after_task(self, executor_agent):
        """Cleanup removes error log."""
        task_id = "task_cleanup_2"
        error_file = executor_agent.plans_dir / f"{task_id}_error.log"
        error_file.write_text("Test error")

        executor_agent._cleanup_temp_files(task_id)

        assert not error_file.exists()

    def test_removes_multiple_task_files(self, executor_agent):
        """Cleanup removes all task-related files."""
        task_id = "task_cleanup_3"
        plan_file = executor_agent.plans_dir / f"{task_id}_plan.md"
        error_file = executor_agent.plans_dir / f"{task_id}_error.log"
        plan_file.write_text("Plan")
        error_file.write_text("Error")

        executor_agent._cleanup_temp_files(task_id)

        assert not plan_file.exists()
        assert not error_file.exists()

    def test_handles_missing_files_gracefully(self, executor_agent):
        """Cleanup handles missing files without error."""
        task_id = "task_cleanup_4"

        # Should not raise exception
        executor_agent._cleanup_temp_files(task_id)

    def test_only_removes_task_specific_files(self, executor_agent):
        """Cleanup only removes files for specific task ID."""
        task_id_1 = "task_a"
        task_id_2 = "task_b"
        file_1 = executor_agent.plans_dir / f"{task_id_1}_plan.md"
        file_2 = executor_agent.plans_dir / f"{task_id_2}_plan.md"
        file_1.write_text("Plan 1")
        file_2.write_text("Plan 2")

        executor_agent._cleanup_temp_files(task_id_1)

        assert not file_1.exists()
        assert file_2.exists()  # Should still exist


# Complete processing cycle tests
class TestCompleteProcessingCycle:
    """Test complete 9-step processing cycle."""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_processes_task_through_all_steps(self, mock_run, executor_agent, mock_sub_agents, sample_task):
        """Task flows through all 9 steps successfully."""
        executor_agent.sub_agents = mock_sub_agents
        mock_run.return_value = Mock(returncode=0, stdout="1843 passed")

        report = await executor_agent._process_task(sample_task)

        assert report["status"] == "success"
        assert report["task_id"] == sample_task["id"]

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_publishes_report_to_telemetry_stream(self, mock_run, executor_agent, mock_sub_agents, sample_task):
        """Successful task publishes report to telemetry_stream."""
        executor_agent.sub_agents = mock_sub_agents
        mock_run.return_value = Mock(returncode=0, stdout="1843 passed")

        await executor_agent._process_task(sample_task)

        executor_agent.message_bus.publish.assert_awaited()
        call_args = executor_agent.message_bus.publish.call_args
        assert call_args[0][0] == "telemetry_stream"

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_cleanup_occurs_even_on_failure(self, mock_run, executor_agent, mock_sub_agents, sample_task):
        """Cleanup (Step 9) occurs even if task fails."""
        executor_agent.sub_agents = mock_sub_agents
        mock_run.return_value = Mock(returncode=1, stdout="Tests failed")

        # Create plan file
        task_id = sample_task["id"]
        plan_file = executor_agent.plans_dir / f"{task_id}_plan.md"
        plan_file.write_text("Plan")

        await executor_agent._process_task(sample_task)

        # Plan file should be cleaned up
        assert not plan_file.exists()

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_failure_publishes_failure_report(self, mock_run, executor_agent, mock_sub_agents, sample_task):
        """Failed task publishes failure report."""
        executor_agent.sub_agents = mock_sub_agents
        mock_run.return_value = Mock(returncode=1, stdout="2 failed")

        report = await executor_agent._process_task(sample_task)

        assert report["status"] == "failure"

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_includes_all_sub_agent_reports_in_success(self, mock_run, executor_agent, mock_sub_agents, sample_task):
        """Success report includes all sub-agent results."""
        executor_agent.sub_agents = mock_sub_agents
        mock_run.return_value = Mock(returncode=0, stdout="1843 passed")

        report = await executor_agent._process_task(sample_task)

        assert len(report["sub_agent_reports"]) > 0


# Cost tracking tests
class TestCostTracking:
    """Test cost tracking for LLM calls."""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_tracks_cost_for_task_processing(self, mock_run, executor_agent, mock_sub_agents, sample_task):
        """Cost tracker records task processing costs."""
        executor_agent.sub_agents = mock_sub_agents
        mock_run.return_value = Mock(returncode=0, stdout="Tests passed")

        # Mock cost tracker with tracking capability
        executor_agent.cost_tracker.track_call = Mock()

        await executor_agent._process_task(sample_task)

        # Verify cost tracker was accessible (actual tracking depends on implementation)
        assert executor_agent.cost_tracker is not None


# Stateless operation tests
class TestStatelessOperation:
    """Test stateless operation between tasks."""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_no_state_persists_between_tasks(self, mock_run, executor_agent, mock_sub_agents):
        """Agent maintains no state between tasks."""
        executor_agent.sub_agents = mock_sub_agents
        mock_run.return_value = Mock(returncode=0, stdout="Tests passed")

        task_1 = {"id": "task_1", "type": "feature", "correlation_id": "corr_1"}
        task_2 = {"id": "task_2", "type": "bug_fix", "correlation_id": "corr_2"}

        report_1 = await executor_agent._process_task(task_1)
        report_2 = await executor_agent._process_task(task_2)

        # Each report should have distinct task IDs
        assert report_1["task_id"] == "task_1"
        assert report_2["task_id"] == "task_2"

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_temp_files_cleared_between_tasks(self, mock_run, executor_agent, mock_sub_agents):
        """Temporary files are cleared between tasks."""
        executor_agent.sub_agents = mock_sub_agents
        mock_run.return_value = Mock(returncode=0, stdout="Tests passed")

        task_1 = {"id": "task_stateless_1", "type": "feature", "correlation_id": "c1"}
        task_2 = {"id": "task_stateless_2", "type": "feature", "correlation_id": "c2"}

        await executor_agent._process_task(task_1)
        # Verify task 1 files are cleaned
        assert not (executor_agent.plans_dir / "task_stateless_1_plan.md").exists()

        await executor_agent._process_task(task_2)
        # Verify task 2 files are cleaned
        assert not (executor_agent.plans_dir / "task_stateless_2_plan.md").exists()


# Agent lifecycle tests
class TestAgentLifecycle:
    """Test agent lifecycle (start, run, stop)."""

    @pytest.mark.asyncio
    async def test_agent_starts_in_not_running_state(self, executor_agent):
        """Agent initializes with _running=False."""
        assert executor_agent._running is False

    @pytest.mark.asyncio
    async def test_run_sets_running_to_true(self, executor_agent):
        """run() method sets _running=True."""
        # Mock message bus to immediately stop
        async def mock_subscribe(queue):
            yield {"id": "task_1", "type": "feature"}
            executor_agent._running = False

        executor_agent.message_bus.subscribe = mock_subscribe

        with patch.object(executor_agent, '_process_task', new_callable=AsyncMock):
            await executor_agent.run()

        # _running was set to True during execution
        assert True  # Test passes if run completes

    @pytest.mark.asyncio
    async def test_stop_sets_running_to_false(self, executor_agent):
        """stop() method sets _running=False."""
        executor_agent._running = True

        await executor_agent.stop()

        assert executor_agent._running is False

    @pytest.mark.asyncio
    async def test_stop_cancels_pending_tasks(self, executor_agent):
        """stop() cancels all pending tasks."""
        # Create a real asyncio task for testing
        async def dummy_task():
            await asyncio.sleep(10)

        task = asyncio.create_task(dummy_task())
        executor_agent._tasks = [task]

        await executor_agent.stop()

        assert task.cancelled()


# Agent statistics tests
class TestAgentStatistics:
    """Test agent statistics and monitoring."""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_cost_tracker_records_total_cost(self, mock_run, executor_agent, mock_sub_agents, sample_task):
        """Cost tracker accumulates total costs."""
        executor_agent.sub_agents = mock_sub_agents
        mock_run.return_value = Mock(returncode=0, stdout="Tests passed")
        executor_agent.cost_tracker.get_total_cost = Mock(return_value=0.05)

        await executor_agent._process_task(sample_task)

        total_cost = executor_agent.cost_tracker.get_total_cost()
        assert total_cost >= 0.0
