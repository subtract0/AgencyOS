"""
Hybrid EXECUTOR - Trinity Protocol with Local-First + Cloud Escalation.

Enhances ExecutorAgent with:
- All 10 Agency agents (not just 6)
- Hybrid model support (LOCAL → LOCAL_PLUS → CLOUD)
- Intelligent escalation based on failures/complexity
- Cost tracking for local vs. cloud usage

Constitutional Compliance:
- Article I: Complete context with retry + escalation
- Article II: 100% verification (tests must pass)
- Article III: Automated enforcement (no bypasses)
- Article IV: Learning from escalation patterns
"""

import asyncio
import json
import logging
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from shared.agent_context import AgentContext
from shared.cost_tracker import CostTracker
from shared.message_bus import MessageBus
from shared.type_definitions import JSONValue
from trinity_protocol.core.agent_registry import (
    AgentRegistry,
    AgentType,
    ModelTier,
    create_agent_registry,
)
from trinity_protocol.core.escalation_rules import (
    EscalationContext,
    EscalationPolicy,
    create_escalation_policy,
)
from trinity_protocol.core.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks the executor can handle."""

    CODE_GENERATION = "code_generation"
    CODE_FIX = "code_fix"
    TEST_GENERATION = "test_generation"
    TOOL_CREATION = "tool_creation"
    VERIFICATION = "verification"
    REFACTORING = "refactoring"
    ARCHITECTURE = "architecture"
    GENERAL = "general"  # Generic task, executor decides agent


@dataclass
class TaskResult:
    """Result from task execution."""

    task_id: str
    status: Literal["success", "failure"]
    summary: str
    duration_seconds: float
    cost_usd: float
    model_tier: ModelTier
    escalation_count: int
    test_pass_rate: float
    agents_used: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class ExecutionAttempt:
    """Single execution attempt with result."""

    attempt_number: int
    tier: ModelTier
    agents_used: list[AgentType]
    duration_seconds: float
    success: bool
    test_failures: int
    error: str | None = None


@dataclass
class ExecutionStats:
    """Execution statistics tracking."""

    tasks_processed: int = 0
    tasks_succeeded: int = 0
    tasks_failed: int = 0
    local_successes: int = 0
    local_plus_successes: int = 0
    cloud_successes: int = 0
    total_cost_usd: float = 0.0
    cost_saved_usd: float = 0.0  # vs. 100% cloud


@dataclass
class EnrichedStats:
    """Execution statistics with computed rates."""

    tasks_processed: int
    tasks_succeeded: int
    tasks_failed: int
    local_successes: int
    local_plus_successes: int
    cloud_successes: int
    total_cost_usd: float
    cost_saved_usd: float
    local_success_rate: str  # e.g., "75.0%"
    cloud_usage_pct: str  # e.g., "25.0%"


class HybridExecutor:
    """
    Enhanced EXECUTOR with hybrid local-first + cloud escalation.

    Workflow:
    1. Receive task
    2. Attempt with LOCAL models (qwen2.5-coder)
    3. If failure → Escalate to LOCAL_PLUS
    4. If failure → Escalate to CLOUD (GPT-5)
    5. Track cost savings from local-first approach
    """

    def __init__(
        self,
        message_bus: MessageBus,
        cost_tracker: CostTracker,
        agent_context: AgentContext,
        agent_registry: AgentRegistry | None = None,
        escalation_policy: EscalationPolicy | None = None,
        plans_dir: str = "/tmp/executor_plans",
        verification_timeout: int = 600,
        max_total_attempts: int = 6,
    ):
        """
        Initialize Hybrid EXECUTOR.

        Args:
            message_bus: Message bus for coordination
            cost_tracker: Cost tracking instance
            agent_context: Shared context for memory/learning
            agent_registry: Agent factory (creates if None)
            escalation_policy: Escalation rules (creates if None)
            plans_dir: Directory for execution plans
            verification_timeout: Test execution timeout
            max_total_attempts: Max attempts across all tiers
        """
        self.message_bus = message_bus
        self.cost_tracker = cost_tracker
        self.agent_context = agent_context
        self.plans_dir = Path(plans_dir)
        self.verification_timeout = verification_timeout
        self.max_total_attempts = max_total_attempts
        self._running = False

        # Initialize agent registry and escalation policy
        self.agent_registry = agent_registry or create_agent_registry(
            agent_context=agent_context,
            cost_tracker=cost_tracker,
            default_tier="local",
        )

        self.escalation_policy = escalation_policy or create_escalation_policy(
            max_local_attempts=2,
            max_local_plus_attempts=1,
            test_failure_threshold=2,
        )

        # Initialize Ollama client for local model execution
        self.ollama = OllamaClient(base_url="http://localhost:11434")

        # Statistics tracking
        self._stats = ExecutionStats()

        self.plans_dir.mkdir(parents=True, exist_ok=True)
        logger.info("HybridExecutor initialized with local-first + cloud escalation")

    async def run(self) -> None:
        """Main loop: subscribe to execution_queue and process tasks."""
        self._running = True

        try:
            async for message in self.message_bus.subscribe("execution_queue"):
                if not self._running:
                    break

                await self._handle_message(message)

        except asyncio.CancelledError:
            pass

    async def _handle_message(self, message: JSONValue) -> None:
        """Handle a single task message."""
        task_id = message.get("task_id", str(uuid.uuid4()))

        try:
            result = await self._execute_task_with_escalation(message, task_id)
            await self._publish_result(result)
            self._update_stats(result)
            logger.info(
                f"✅ Task {task_id} completed: tier={result.model_tier.value}, "
                f"cost=${result.cost_usd:.4f}, escalations={result.escalation_count}"
            )
        except Exception as e:
            logger.error(f"❌ Task {task_id} failed: {e}", exc_info=True)
            await self._publish_failure(task_id, message, str(e))
        finally:
            await self.message_bus.ack(message.get("_message_id"))

    async def _execute_task_with_escalation(
        self, task: JSONValue, task_id: str
    ) -> TaskResult:
        """
        Execute task with escalation support.

        Workflow:
        - Attempt 1-2: LOCAL tier
        - Attempt 3: LOCAL_PLUS tier
        - Attempt 4+: CLOUD tier
        """
        attempts: list[ExecutionAttempt] = []
        current_tier = ModelTier.LOCAL
        total_duration = 0.0
        total_cost = 0.0

        for attempt_num in range(1, self.max_total_attempts + 1):
            logger.info(
                f"🔄 Task {task_id} attempt {attempt_num}/{self.max_total_attempts} "
                f"with tier={current_tier.value}"
            )

            start_time = datetime.now()

            try:
                # Execute with current tier
                attempt_result = await self._execute_at_tier(
                    task, task_id, current_tier, attempt_num
                )

                duration = (datetime.now() - start_time).total_seconds()
                total_duration += duration
                attempt_result.duration_seconds = duration

                # Calculate cost (local = $0, cloud = actual cost)
                cost = 0.0 if current_tier != ModelTier.CLOUD else self._estimate_cloud_cost(duration)
                total_cost += cost

                attempts.append(attempt_result)

                # Success! Return result
                if attempt_result.success and attempt_result.test_failures == 0:
                    return TaskResult(
                        task_id=task_id,
                        status="success",
                        summary=f"Task completed at {current_tier.value} tier",
                        duration_seconds=total_duration,
                        cost_usd=total_cost,
                        model_tier=current_tier,
                        escalation_count=attempt_num - 1,
                        test_pass_rate=1.0,
                        agents_used=[a.value for a in attempt_result.agents_used],
                    )

                # Failure - evaluate escalation
                escalation_context = EscalationContext(
                    attempt_count=self._count_attempts_at_tier(attempts, current_tier),
                    current_tier=current_tier,
                    test_failures=attempt_result.test_failures,
                    has_timeout=False,
                    user_complexity=task.get("complexity"),
                )

                decision = self.escalation_policy.evaluate(escalation_context)

                if decision.should_escalate:
                    logger.warning(
                        f"⚠️  Escalating: {decision.reason} → {decision.next_tier.value}"
                    )
                    current_tier = decision.next_tier
                else:
                    # No more escalation, retry at same tier
                    logger.info(f"🔁 Retrying at {current_tier.value}: {decision.reason}")

            except Exception as e:
                logger.error(f"❌ Attempt {attempt_num} failed: {e}")
                # Escalate on exception
                if current_tier != ModelTier.CLOUD:
                    current_tier = self.agent_registry.escalation_policy._get_next_tier(current_tier)

        # Max attempts exhausted
        return TaskResult(
            task_id=task_id,
            status="failure",
            summary=f"Task failed after {self.max_total_attempts} attempts",
            duration_seconds=total_duration,
            cost_usd=total_cost,
            model_tier=current_tier,
            escalation_count=self.max_total_attempts,
            test_pass_rate=0.0,
            error="Max attempts exhausted",
        )

    async def _execute_at_tier(
        self, task: JSONValue, task_id: str, tier: ModelTier, attempt_num: int
    ) -> ExecutionAttempt:
        """Execute task at specified model tier."""
        task_type = TaskType(task.get("task_type", "general"))
        agents_needed = self._select_agents_for_task(task_type)

        logger.info(
            f"📋 Executing {task_type.value} with agents: {[a.value for a in agents_needed]}"
        )

        # Execute agents with task specification (via Ollama, not Agency objects)
        success = True
        test_failures = 0
        agent_outputs = []

        try:
            # 1. Call each agent type via Ollama
            for agent_type in agents_needed:
                task_prompt = self._format_task_prompt(task, agent_type)

                # Get model name for this agent type at this tier
                model_name = self.agent_registry.get_model_for_agent(agent_type, tier)

                # Strip "ollama/" prefix if present (OllamaClient expects bare model names)
                if model_name.startswith("ollama/"):
                    model_name = model_name.replace("ollama/", "", 1)

                # Execute via Ollama chat (async)
                output = await self.ollama.chat(
                    model=model_name,
                    messages=[{"role": "user", "content": task_prompt}],
                    timeout=180,  # 3 minutes per agent call
                )

                # chat() returns string directly, not dict
                agent_outputs.append(output)

                # Validate output is executable code
                is_valid, validation_msg = self._validate_executable_code(output)
                if not is_valid:
                    logger.warning(
                        f"Agent {agent_type.value} at tier {tier.value} generated pseudocode: {validation_msg}"
                    )
                    success = False
                    break

            # 2. Run tests to verify implementation
            test_result = self._run_verification()
            if "FAILED" in test_result or "ERROR" in test_result:
                success = False
                test_failures = self._count_test_failures(test_result)

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            success = False

        return ExecutionAttempt(
            attempt_number=attempt_num,
            tier=tier,
            agents_used=agents_needed,
            duration_seconds=0.0,  # Set by caller
            success=success,
            test_failures=test_failures,
        )

    def _select_agents_for_task(self, task_type: TaskType) -> list[AgentType]:
        """
        Select appropriate agents based on task type.

        This is the key improvement: we now have ALL 10 agents available!
        """
        agent_map = {
            TaskType.CODE_GENERATION: [AgentType.CODER, AgentType.TEST_GENERATOR],
            TaskType.CODE_FIX: [AgentType.CODER, AgentType.QUALITY_ENFORCER],
            TaskType.TEST_GENERATION: [AgentType.TEST_GENERATOR],
            TaskType.TOOL_CREATION: [AgentType.TOOLSMITH, AgentType.TEST_GENERATOR],
            TaskType.VERIFICATION: [AgentType.QUALITY_ENFORCER],
            TaskType.REFACTORING: [AgentType.CODER, AgentType.AUDITOR, AgentType.QUALITY_ENFORCER],
            TaskType.ARCHITECTURE: [AgentType.CHIEF_ARCHITECT, AgentType.PLANNER],
            TaskType.GENERAL: [AgentType.CODER],  # Default
        }

        return agent_map.get(task_type, [AgentType.CODER])

    def _format_task_prompt(self, task: JSONValue, agent_type: AgentType) -> str:
        """Format task specification as agent prompt emphasizing executable code generation."""
        # Add executable code generation instructions at the beginning
        executable_code_header = """**CRITICAL REQUIREMENTS FOR CODE GENERATION:**

1. Generate EXECUTABLE CODE, not pseudocode or abstract plans
2. Include all necessary imports, error handling, and edge cases
3. Code must be ready to run without modifications
4. Use proper Python syntax with type hints and docstrings
5. NO placeholder comments like "# TODO" or "# Implementation here"

**FORBIDDEN OUTPUTS:**
- Pseudocode or abstract outlines
- High-level descriptions without actual code
- Plans or design documents
- Incomplete code with TODOs

**VALIDATION:** Your code will be executed in production. It MUST work.

---

"""
        parts = [executable_code_header]

        # Add task details
        if "description" in task:
            parts.append(f"Task: {task['description']}")
        if "target" in task:
            parts.append(f"Target: {task['target']}")
        if "requirements" in task:
            parts.append(f"Requirements: {task['requirements']}")

        # Add agent-specific context
        parts.append(f"\nYou are the {agent_type.value} agent. Generate production-ready code.")

        # Add final reminder
        parts.append("\n**REMINDER: Generate complete, executable code. No pseudocode or placeholders.**")

        return "\n\n".join(parts)

    def _validate_executable_code(self, code: str) -> tuple[bool, str]:
        """
        Validate that agent output is executable code, not pseudocode.

        Returns:
            (is_valid, error_message)
        """
        # Pseudocode markers that indicate non-executable output
        pseudocode_markers = [
            "# TODO",
            "# Implementation",
            "# Your code here",
            "# Implement this",
            "# Add code here",
            "pseudocode",
            "outline",
            "high-level plan",
            "abstract plan",
            "design document",
            "step 1:",
            "step 2:",
            "// TODO",
            "// Implementation",
        ]

        # Convert to lowercase for case-insensitive checking
        code_lower = code.lower()

        # Check for pseudocode markers
        for marker in pseudocode_markers:
            if marker.lower() in code_lower:
                return False, f"Output contains pseudocode marker: '{marker}'"

        # Check if output is too short to be real implementation
        if len(code.strip()) < 50:
            return False, "Output too short to be real implementation (min 50 chars)"

        # Check for Python syntax validity (if it looks like Python code)
        if any(keyword in code_lower for keyword in ["def ", "import ", "class ", "from "]):
            try:
                compile(code, "<string>", "exec")
            except SyntaxError as e:
                return False, f"Syntax error in generated code: {e}"

        return True, "Valid executable code"

    def _run_verification(self) -> str:
        """Run full test suite (Article II compliance)."""
        try:
            result = subprocess.run(
                ["python", "run_tests.py", "--run-all"],
                capture_output=True,
                text=True,
                timeout=self.verification_timeout,
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return "ERROR: Test execution timed out"
        except Exception as e:
            return f"ERROR: {str(e)}"

    def _count_test_failures(self, test_output: str) -> int:
        """Parse test output to count failures."""
        # Simple heuristic - improve with actual parsing
        if "FAILED" in test_output:
            # Extract number from "X failed"
            import re
            match = re.search(r"(\d+) failed", test_output)
            return int(match.group(1)) if match else 1
        return 0

    def _count_attempts_at_tier(
        self, attempts: list[ExecutionAttempt], tier: ModelTier
    ) -> int:
        """Count how many attempts made at specific tier."""
        return sum(1 for a in attempts if a.tier == tier)

    def _estimate_cloud_cost(self, duration_seconds: float) -> float:
        """
        Estimate cloud cost for GPT-5 execution.

        Rough estimate: $0.10 per minute of execution.
        """
        return (duration_seconds / 60.0) * 0.10

    def _update_stats(self, result: TaskResult) -> None:
        """Update execution statistics."""
        self._stats.tasks_processed += 1

        if result.status == "success":
            self._stats.tasks_succeeded += 1

            # Track which tier succeeded
            if result.model_tier == ModelTier.LOCAL:
                self._stats.local_successes += 1
            elif result.model_tier == ModelTier.LOCAL_PLUS:
                self._stats.local_plus_successes += 1
            elif result.model_tier == ModelTier.CLOUD:
                self._stats.cloud_successes += 1
        else:
            self._stats.tasks_failed += 1

        self._stats.total_cost_usd += result.cost_usd

        # Calculate cost savings (vs. 100% cloud)
        estimated_cloud_cost = self._estimate_cloud_cost(result.duration_seconds)
        if result.model_tier != ModelTier.CLOUD:
            self._stats.cost_saved_usd += estimated_cloud_cost - result.cost_usd

    async def _publish_result(self, result: TaskResult) -> None:
        """Publish successful result to message bus."""
        await self.message_bus.publish(
            "telemetry_stream",
            {
                "type": "task_complete",
                "task_id": result.task_id,
                "status": result.status,
                "tier": result.model_tier.value,
                "cost_usd": result.cost_usd,
                "duration_s": result.duration_seconds,
                "escalation_count": result.escalation_count,
            },
        )

    async def _publish_failure(
        self, task_id: str, task: JSONValue, error: str
    ) -> None:
        """Publish task failure."""
        await self.message_bus.publish(
            "telemetry_stream",
            {
                "type": "task_failed",
                "task_id": task_id,
                "error": error,
            },
        )

    async def stop(self) -> None:
        """Stop the executor gracefully."""
        self._running = False
        logger.info("HybridExecutor stopped")

    def get_stats(self) -> EnrichedStats:
        """Get execution statistics with computed rates."""
        total = self._stats.tasks_processed

        local_pct = (
            self._stats.local_successes / total * 100 if total > 0 else 0.0
        )
        cloud_pct = (
            self._stats.cloud_successes / total * 100 if total > 0 else 0.0
        )

        return EnrichedStats(
            tasks_processed=self._stats.tasks_processed,
            tasks_succeeded=self._stats.tasks_succeeded,
            tasks_failed=self._stats.tasks_failed,
            local_successes=self._stats.local_successes,
            local_plus_successes=self._stats.local_plus_successes,
            cloud_successes=self._stats.cloud_successes,
            total_cost_usd=self._stats.total_cost_usd,
            cost_saved_usd=self._stats.cost_saved_usd,
            local_success_rate=f"{local_pct:.1f}%",
            cloud_usage_pct=f"{cloud_pct:.1f}%",
        )


# Factory function
def create_hybrid_executor(
    message_bus: MessageBus,
    cost_tracker: CostTracker,
    agent_context: AgentContext,
    **kwargs,
) -> HybridExecutor:
    """Create a HybridExecutor instance."""
    return HybridExecutor(
        message_bus=message_bus,
        cost_tracker=cost_tracker,
        agent_context=agent_context,
        **kwargs,
    )
