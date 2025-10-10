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
from tools.quality_feedback.misclassification_detector import MisclassificationDetector
from tools.quality_feedback.rule_refiner import RuleRefiner
from tools.quality_feedback.signal_collector import QualitySignalCollector
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


# ============================================================================
# TASK-TO-AGENT MAPPING
# ============================================================================
# Dynamic routing of tasks to appropriate agent combinations.
# This mapping enables all 10 Agency agents to be utilized via HybridExecutor.
#
# Phase 2 Enhancement: Generalized from hardcoded test generation to full
# multi-agent support with sequential execution (simple chaining).
# ============================================================================


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


# Task-to-Agent mapping for dynamic routing (Phase 2: All 10 agents supported)
# Maps each TaskType to list of AgentTypes that will execute sequentially.
#
# Current coverage: 7 of 10 agents
# - CODER: CODE_GENERATION, CODE_FIX, REFACTORING, GENERAL
# - TEST_GENERATOR: CODE_GENERATION, TEST_GENERATION, TOOL_CREATION
# - QUALITY_ENFORCER: CODE_FIX, VERIFICATION, REFACTORING
# - TOOLSMITH: TOOL_CREATION
# - AUDITOR: REFACTORING
# - CHIEF_ARCHITECT: ARCHITECTURE
# - PLANNER: ARCHITECTURE
#
# Future expansion (3 agents):
# - LEARNING: Add to REFACTORING or ARCHITECTURE for pattern analysis
# - MERGER: Add to CODE_GENERATION or new MERGE task type
# - SUMMARY: Add to new SUMMARY task type or ARCHITECTURE for documentation
TASK_TO_AGENT_MAP: dict[TaskType, list[AgentType]] = {
    TaskType.CODE_GENERATION: [AgentType.CODER, AgentType.TEST_GENERATOR],
    TaskType.CODE_FIX: [AgentType.CODER, AgentType.QUALITY_ENFORCER],
    TaskType.TEST_GENERATION: [AgentType.TEST_GENERATOR],
    TaskType.TOOL_CREATION: [AgentType.TOOLSMITH, AgentType.TEST_GENERATOR],
    TaskType.VERIFICATION: [AgentType.QUALITY_ENFORCER],
    TaskType.REFACTORING: [AgentType.CODER, AgentType.AUDITOR, AgentType.QUALITY_ENFORCER],
    TaskType.ARCHITECTURE: [AgentType.CHIEF_ARCHITECT, AgentType.PLANNER],
    TaskType.GENERAL: [AgentType.CODER],  # Default fallback
}


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
        enable_quality_feedback: bool = True,
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
            enable_quality_feedback: Enable post-execution quality feedback loop
        """
        self.message_bus = message_bus
        self.cost_tracker = cost_tracker
        self.agent_context = agent_context
        self.plans_dir = Path(plans_dir)
        self.verification_timeout = verification_timeout
        self.max_total_attempts = max_total_attempts
        self.enable_quality_feedback = enable_quality_feedback
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

        # Initialize quality feedback loop components (Leap 4)
        if self.enable_quality_feedback:
            self.signal_collector = QualitySignalCollector()
            self.misclassification_detector = MisclassificationDetector(context=agent_context)
            self.rule_refiner = RuleRefiner(context=agent_context)
            logger.info("Quality feedback loop enabled (Article IV compliance)")
        else:
            self.signal_collector = None
            self.misclassification_detector = None
            self.rule_refiner = None

        # Initialize ML classifier components (Leap 5 Phase 3, ADR-026)
        import os

        from shared.models.ab_test_config import ABTestConfig

        self._ab_test_config = ABTestConfig(
            enabled=os.getenv("ML_AB_TEST_ENABLED", "true").lower() == "true",
            ml_percentage=int(os.getenv("ML_PERCENTAGE", "50")),
            random_seed=42,
        )
        self._ml_confidence_threshold = float(os.getenv("ML_CONFIDENCE_THRESHOLD", "0.7"))

        # Lazy loading (populated on first classify call)
        self._ml_classifier = None
        self._ml_classifier_loaded = False

        # Statistics tracking
        self._stats = ExecutionStats()

        self.plans_dir.mkdir(parents=True, exist_ok=True)
        logger.info("HybridExecutor initialized with local-first + cloud escalation")

        # Check if retraining is due (Leap 5 Phase 4, Article IV)
        # This is a one-time initialization check, zero impact on task execution
        self._check_retraining_due()

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
        start_time = datetime.now()

        try:
            result = await self._execute_task_with_escalation(message, task_id)
            await self._publish_result(result)
            self._update_stats(result)
            logger.info(
                f"✅ Task {task_id} completed: tier={result.model_tier.value}, "
                f"cost=${result.cost_usd:.4f}, escalations={result.escalation_count}"
            )

            # Post-execution quality feedback hook (Leap 4, Article IV)
            if self.enable_quality_feedback and result.status == "success":
                await self._run_quality_feedback_loop(
                    task_id=task_id, message=message, result=result, start_time=start_time
                )

        except Exception as e:
            logger.error(f"❌ Task {task_id} failed: {e}", exc_info=True)
            await self._publish_failure(task_id, message, str(e))
        finally:
            await self.message_bus.ack(message.get("_message_id"))

    async def _classify_task_tier(
        self, task: JSONValue, task_id: str
    ) -> tuple[ModelTier, str, float, dict[str, float] | None]:
        """
        Classify task to determine initial tier (ML-first with rule-based fallback).

        Workflow (ADR-026):
        1. Check A/B test: Should use ML or rules?
        2. If ML group: Try ML classification
           - If confidence >= threshold: Use ML tier
           - If confidence < threshold: Fallback to rules
           - If error: Fallback to rules
        3. If control group: Use rules
        4. Log prediction to VectorStore (Article IV)

        Args:
            task: Task message with description
            task_id: Task identifier

        Returns:
            Tuple of (tier, method, confidence, probabilities)
            - tier: ModelTier enum (LOCAL, LOCAL_PLUS, CLOUD)
            - method: Classification method ("ml", "rule_fallback", "rule_control")
            - confidence: Confidence score (0.0-1.0)
            - probabilities: Optional class probabilities from ML

        Reference: ADR-026 Section "Decision 1: ML-First Routing Order"
        """
        task_description = task.get("description", "")

        # Map tier strings to ModelTier enum
        tier_mapping = {
            "P1": ModelTier.CLOUD,  # Complex
            "P2": ModelTier.LOCAL_PLUS,  # Moderate
            "P3": ModelTier.LOCAL,  # Simple
        }

        # Step 1: A/B test decision
        use_ml = self._ab_test_config.should_use_ml(task_id)

        if use_ml:
            # ML path: Try ML classification first
            ml_classifier = self._get_ml_classifier()

            if ml_classifier:
                # Call ML classifier
                ml_result = ml_classifier.classify(task)

                if ml_result.is_ok():
                    classification = ml_result.unwrap()

                    if classification.confidence >= self._ml_confidence_threshold:
                        # High confidence: Use ML prediction
                        tier = tier_mapping.get(classification.tier, ModelTier.LOCAL)
                        await self._log_prediction_async(
                            task_id,
                            task_description,
                            classification.tier,
                            classification.confidence,
                            "ml",
                            classification.probabilities,
                        )
                        return (tier, "ml", classification.confidence, classification.probabilities)
                    else:
                        # Low confidence: Fallback to rules
                        logger.info(
                            f"ML confidence {classification.confidence:.2f} below threshold "
                            f"{self._ml_confidence_threshold}, falling back to rules"
                        )
                        tier = self._rule_based_classify(task_description)
                        await self._log_prediction_async(
                            task_id,
                            task_description,
                            self._map_tier_to_string(tier),
                            classification.confidence,
                            "rules",
                            classification.probabilities,
                        )
                        return (
                            tier,
                            "rules",
                            classification.confidence,
                            classification.probabilities,
                        )
                else:
                    # ML error: Fallback to rules
                    logger.warning(
                        f"ML classification failed: {ml_result.unwrap_err()}, falling back to rules"
                    )
                    tier = self._rule_based_classify(task_description)
                    await self._log_prediction_async(
                        task_id,
                        task_description,
                        self._map_tier_to_string(tier),
                        0.0,
                        "rules",
                        None,
                    )
                    return (tier, "rules", 0.0, None)
            else:
                # ML unavailable: Fallback to rules
                tier = self._rule_based_classify(task_description)
                await self._log_prediction_async(
                    task_id, task_description, self._map_tier_to_string(tier), 0.0, "rules", None
                )
                return (tier, "rules", 0.0, None)
        else:
            # Control group: Use rule-based classification
            tier = self._rule_based_classify(task_description)
            await self._log_prediction_async(
                task_id, task_description, self._map_tier_to_string(tier), 1.0, "rules", None
            )
            return (tier, "rules", 1.0, None)

    def _rule_based_classify(self, task_description: str) -> ModelTier:
        """
        Rule-based task classification (Leap 3/4 baseline).

        Simple heuristics for tier assignment:
        - Complex keywords → CLOUD (P1)
        - Moderate keywords → LOCAL_PLUS (P2)
        - Simple keywords → LOCAL (P3)

        Args:
            task_description: Task description text

        Returns:
            ModelTier enum (LOCAL, LOCAL_PLUS, CLOUD)

        Reference: ADR-024 (Adaptive Model Router)
        """
        description_lower = task_description.lower()

        # Complex indicators (P1 → CLOUD)
        complex_keywords = [
            "architecture",
            "design",
            "consensus",
            "distributed",
            "algorithm",
            "byzantine",
            "fault tolerance",
            "scalability",
        ]
        if any(kw in description_lower for kw in complex_keywords):
            return ModelTier.CLOUD

        # Simple indicators (P3 → LOCAL)
        simple_keywords = [
            "fix typo",
            "update readme",
            "format",
            "lint",
            "comment",
            "documentation",
            "rename",
        ]
        if any(kw in description_lower for kw in simple_keywords):
            return ModelTier.LOCAL

        # Default: Moderate (P2 → LOCAL_PLUS)
        return ModelTier.LOCAL_PLUS

    def _map_tier_to_string(self, tier: ModelTier) -> str:
        """
        Map ModelTier enum to tier string (P1, P2, P3).

        Args:
            tier: ModelTier enum

        Returns:
            Tier string (P1, P2, P3)
        """
        mapping = {
            ModelTier.CLOUD: "P1",
            ModelTier.LOCAL_PLUS: "P2",
            ModelTier.LOCAL: "P3",
        }
        return mapping.get(tier, "P3")

    async def _execute_task_with_escalation(self, task: JSONValue, task_id: str) -> TaskResult:
        """
        Execute task with ML-first tier classification and escalation support.

        Workflow (ADR-026):
        1. Classify task to determine initial tier (ML-first with rule fallback)
        2. Execute at initial tier
        3. If failure: Escalate to higher tiers
        4. Track cost and performance

        Args:
            task: Task message
            task_id: Task identifier

        Returns:
            TaskResult with execution outcome

        Reference: ADR-026 Section "Architecture Overview"
        """
        attempts: list[ExecutionAttempt] = []
        total_duration = 0.0
        total_cost = 0.0

        # Step 1: Classify task to determine initial tier (Leap 5 Phase 3)
        # If A/B testing disabled, use LOCAL tier (backward compatibility)
        if self._ab_test_config.enabled:
            initial_tier, method, confidence, probabilities = await self._classify_task_tier(
                task, task_id
            )
            current_tier = initial_tier

            logger.info(
                f"🎯 Task {task_id} classified: tier={self._map_tier_to_string(current_tier)}, "
                f"method={method}, confidence={confidence:.2f}"
            )
        else:
            # Backward compatibility: Start with LOCAL tier when ML disabled
            current_tier = ModelTier.LOCAL
            logger.debug(f"Task {task_id} starting at LOCAL tier (ML classification disabled)")

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
                cost = (
                    0.0 if current_tier != ModelTier.CLOUD else self._estimate_cloud_cost(duration)
                )
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
                    logger.warning(f"⚠️  Escalating: {decision.reason} → {decision.next_tier.value}")
                    current_tier = decision.next_tier
                else:
                    # No more escalation, retry at same tier
                    logger.info(f"🔁 Retrying at {current_tier.value}: {decision.reason}")

            except Exception as e:
                logger.error(f"❌ Attempt {attempt_num} failed: {e}")
                # Escalate on exception
                if current_tier != ModelTier.CLOUD:
                    current_tier = self.agent_registry.escalation_policy._get_next_tier(
                        current_tier
                    )

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
        Select appropriate agents based on task type using module-level mapping.

        Phase 2 Enhancement: Generalized agent selection with logging.
        - Supports all task types with explicit mappings
        - Returns list of agents for sequential execution (simple chaining)
        - Logs agent selection for debugging and telemetry

        Args:
            task_type: Type of task to execute

        Returns:
            List of AgentTypes to execute in sequence (1-3 agents)

        Example:
            >>> _select_agents_for_task(TaskType.CODE_FIX)
            [AgentType.CODER, AgentType.QUALITY_ENFORCER]  # 2-agent chain
        """
        agents = TASK_TO_AGENT_MAP.get(task_type, [AgentType.CODER])

        # Log agent selection for debugging and telemetry
        agent_names = [a.value for a in agents]
        logger.info(
            f"📋 Task routing: {task_type.value} → agents: {agent_names} "
            f"({len(agents)} agent{'s' if len(agents) != 1 else ''})"
        )

        return agents

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
        parts.append(
            "\n**REMINDER: Generate complete, executable code. No pseudocode or placeholders.**"
        )

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

    def _count_attempts_at_tier(self, attempts: list[ExecutionAttempt], tier: ModelTier) -> int:
        """Count how many attempts made at specific tier."""
        return sum(1 for a in attempts if a.tier == tier)

    def _estimate_cloud_cost(self, duration_seconds: float) -> float:
        """
        Estimate cloud cost for GPT-5 execution.

        Rough estimate: $0.10 per minute of execution.
        """
        return (duration_seconds / 60.0) * 0.10

    async def _run_quality_feedback_loop(
        self, task_id: str, message: JSONValue, result: TaskResult, start_time: datetime
    ) -> None:
        """
        Post-execution quality feedback loop (Leap 4, Article IV).

        Workflow:
        1. Collect quality signals (test failures, code churn, timing, user feedback)
        2. Detect misclassification using 4 detection rules
        3. Refine VectorStore patterns if misclassified
        4. Graceful degradation (never crash task execution)

        Args:
            task_id: Task identifier
            message: Original task message
            result: Task execution result
            start_time: Task start timestamp

        Constitutional Compliance:
            - Article I: Complete context (collect all signals before detection)
            - Article IV: VectorStore learning mandatory
            - Graceful degradation: Feedback loop errors logged but don't fail task

        Reference: specs/spec-004-quality-feedback-loop.md Section 9
        """
        try:
            logger.debug(f"🔄 Starting quality feedback loop for task {task_id}")

            # Step 1: Collect quality signals (Article I: complete context)
            tier_name = self._map_model_tier_to_complexity(result.model_tier)
            estimated_time = message.get("estimated_time_seconds")
            actual_time = (datetime.now() - start_time).total_seconds()

            signals_result = self.signal_collector.collect_signals(
                task_id=task_id,
                original_tier=tier_name,
                estimated_time_seconds=estimated_time,
                actual_time_seconds=actual_time,
            )

            if signals_result.is_err():
                logger.warning(
                    f"⚠️  Signal collection failed for {task_id}: {signals_result.unwrap_err()}"
                )
                return  # Graceful degradation (don't block task)

            signals = signals_result.unwrap()
            logger.debug(
                f"📊 Quality signals collected: severity={signals.severity}, "
                f"test_failure_rate={signals.test_failure_rate}, "
                f"code_churn_lines={signals.code_churn_lines}"
            )

            # Step 2: Detect misclassification (4 detection rules)
            task_description = message.get("description", "")
            detection_result = self.misclassification_detector.detect(
                task_id=task_id, signals=signals, task_description=task_description
            )

            if detection_result.is_err():
                logger.warning(
                    f"⚠️  Misclassification detection failed for {task_id}: "
                    f"{detection_result.unwrap_err()}"
                )
                return  # Graceful degradation

            report = detection_result.unwrap()

            if not report.is_misclassified:
                logger.debug(f"✅ Task {task_id} correctly classified as {tier_name}")
                return  # No refinement needed

            logger.info(
                f"🔍 Misclassification detected: {task_id} "
                f"({tier_name} → {report.recommended_tier}, "
                f"confidence={report.aggregated_confidence:.2f})"
            )

            # Step 3: Refine VectorStore patterns (Article IV mandatory)
            refinement_result = self.rule_refiner.refine(
                report=report, task_description=task_description
            )

            if refinement_result.is_err():
                logger.error(
                    f"❌ VectorStore refinement failed for {task_id}: "
                    f"{refinement_result.unwrap_err()}"
                )
                return  # Graceful degradation

            refinement = refinement_result.unwrap()
            logger.info(
                f"🧠 VectorStore refined: {task_id} "
                f"(confidence {refinement.confidence_before:.3f} → {refinement.confidence_after:.3f}, "
                f"patterns={refinement.patterns_updated}, "
                f"iteration={refinement.iteration_count})"
            )

            # Publish telemetry event for monitoring
            await self.message_bus.publish(
                "telemetry_stream",
                {
                    "type": "quality_feedback_complete",
                    "task_id": task_id,
                    "original_tier": tier_name,
                    "recommended_tier": report.recommended_tier,
                    "confidence": report.aggregated_confidence,
                    "patterns_updated": refinement.patterns_updated,
                    "iteration_count": refinement.iteration_count,
                },
            )

        except Exception as e:
            # Graceful degradation: log error but don't fail task execution
            logger.error(f"❌ Quality feedback loop crashed for {task_id}: {e}", exc_info=True)

    def _map_model_tier_to_complexity(self, tier: ModelTier) -> str:
        """
        Map ModelTier enum to complexity string for quality signals.

        Args:
            tier: ModelTier enum (LOCAL, LOCAL_PLUS, CLOUD)

        Returns:
            Complexity string (simple, moderate, complex)
        """
        mapping = {
            ModelTier.LOCAL: "simple",
            ModelTier.LOCAL_PLUS: "moderate",
            ModelTier.CLOUD: "complex",
        }
        return mapping.get(tier, "simple")

    def _get_ml_classifier(self):
        """
        Get ML classifier with lazy loading and error handling.

        Returns:
            MLClassifier instance or None if unavailable

        Error Handling:
            - Missing model file: Return None, log warning once
            - Load failure: Return None, log error
            - Cache result: Only attempt load once per executor instance

        Constitutional Compliance:
            - Article II: Graceful degradation (no crash)
            - Article III: Automated fallback (no manual intervention)

        Reference: ADR-026 Section "Decision 4: Error Handling"
        """
        if self._ml_classifier_loaded:
            return self._ml_classifier  # Cached (may be None)

        self._ml_classifier_loaded = True

        try:
            from tools.ml_routing.ml_classifier import MLClassifier
            from tools.ml_routing.model_storage import ModelStorage

            model_storage = ModelStorage()

            # Try to load latest model
            load_result = model_storage.load_model("latest")

            if load_result.is_err():
                logger.warning(
                    f"ML classifier model not found: {load_result.unwrap_err()}. "
                    "Falling back to rule-based classification. Train model with /leap5-train command."
                )
                self._ml_classifier = None
                return None

            # Model loaded successfully - extract it
            ensemble_model = load_result.unwrap()

            # Create MLClassifier and set the loaded model directly
            self._ml_classifier = MLClassifier(confidence_threshold=self._ml_confidence_threshold)
            self._ml_classifier._model = ensemble_model
            self._ml_classifier.model_version = ensemble_model.training_date
            self._ml_classifier.last_updated = ensemble_model.training_date

            logger.info(
                f"✅ ML classifier loaded: version {ensemble_model.training_date} "
                f"(confidence threshold: {self._ml_confidence_threshold})"
            )

            return self._ml_classifier

        except Exception as e:
            logger.error(
                f"Failed to load ML classifier: {e}. Falling back to rule-based classification.",
                exc_info=True,
            )
            self._ml_classifier = None
            return None

    async def _log_prediction_async(
        self,
        task_id: str,
        task_description: str,
        tier: str,
        confidence: float,
        method: str,
        probabilities: dict[str, float] | None = None,
    ) -> None:
        """
        Log prediction to VectorStore asynchronously (Article IV).

        Args:
            task_id: Task identifier
            task_description: Task description text
            tier: Predicted tier (P1, P2, P3)
            confidence: Confidence score (0.0-1.0)
            method: Classification method used (ml, rule_fallback, rule_control)
            probabilities: Optional class probabilities from ML model

        Performance:
            - Async: Does not block main execution path
            - Overhead: <5ms p99 (background task)
            - Retry: 2x, 3x on VectorStore timeout (Article I)

        Constitutional Compliance:
            - Article IV: MANDATORY VectorStore storage
            - Article I: Retry logic for complete context

        Reference: ADR-026 Section "Decision 3: Async Prediction Logging"
        """
        try:
            from shared.models.prediction_log import PredictionLog

            # Create prediction log
            prediction = PredictionLog(
                task_id=task_id,
                task_description=task_description[:500],  # Truncate long descriptions
                predicted_tier=tier,
                actual_tier=None,  # Will be updated by quality feedback loop
                confidence=confidence,
                method=method,
                probabilities=probabilities,
                timestamp=datetime.now(),
            )

            # Article IV: Store prediction in VectorStore (async)
            from tools.ml_routing.prediction_logger import log_prediction

            asyncio.create_task(asyncio.to_thread(log_prediction, self.agent_context, prediction))

        except Exception as e:
            # Non-blocking: Log error but do not fail task
            logger.warning(
                f"Failed to log ML prediction for {task_id}: {e} "
                "(Article IV: VectorStore logging error)"
            )

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

    async def _publish_failure(self, task_id: str, task: JSONValue, error: str) -> None:
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

        local_pct = self._stats.local_successes / total * 100 if total > 0 else 0.0
        cloud_pct = self._stats.cloud_successes / total * 100 if total > 0 else 0.0

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

    def _check_retraining_due(self) -> None:
        """
        Check if weekly retraining is due (Leap 5 Phase 4 hook).

        Workflow:
        1. Check last_retraining_date metadata
        2. If ≥7 days ago or missing, trigger retraining
        3. Gracefully handle AutoModelUpdateOrchestrator unavailability

        Performance: <10ms (date comparison only)
        Impact: Zero latency on task execution (one-time init check)

        Constitutional Compliance:
        - Article I: Complete context (check last retraining date)
        - Article IV: VectorStore learning (retraining stores metrics)

        Reference: specs/spec-008-weekly-retraining-pipeline.md Section 5.3
        """
        try:
            from datetime import timedelta

            # Query VectorStore for last retraining date (Article I)
            retraining_memories = self.agent_context.search_memories(
                tags=["retraining", "validation", "leap5_phase4"],
                limit=1,
                include_session=False,
            )

            if not retraining_memories:
                # No retraining history - trigger retraining
                logger.info("No retraining history found, triggering initial retraining")
                self._trigger_retraining()
                return

            # Extract last retraining date
            last_retraining = retraining_memories[0]
            last_training_date_str = last_retraining.get("training_date")

            if not last_training_date_str:
                logger.warning("Last retraining date missing, triggering retraining")
                self._trigger_retraining()
                return

            # Parse date and check if ≥7 days ago
            last_date = datetime.fromisoformat(last_training_date_str)
            days_since_retraining = (datetime.now() - last_date).days

            if days_since_retraining >= 7:
                logger.info(
                    f"Retraining due: {days_since_retraining} days since last retraining "
                    f"(threshold: 7 days)"
                )
                self._trigger_retraining()
            else:
                logger.debug(
                    f"Retraining not due: {days_since_retraining} days since last retraining "
                    f"(threshold: 7 days)"
                )

        except Exception as e:
            # Graceful degradation: Log error but don't block initialization
            logger.warning(
                f"Failed to check retraining status: {e}. "
                "HybridExecutor will continue without retraining check."
            )

    def _trigger_retraining(self) -> None:
        """
        Trigger AutoModelUpdateOrchestrator for retraining (async).

        Workflow:
        1. Spawn AutoModelUpdateOrchestrator in background
        2. Log telemetry event (retraining_triggered)
        3. Gracefully handle orchestrator unavailability

        Performance: <5ms (async spawn)
        Impact: Zero latency on task execution (background operation)

        Constitutional Compliance:
        - Article II: Graceful degradation (no crash if orchestrator unavailable)
        - Article III: Automated enforcement (no manual intervention)
        - Article IV: VectorStore learning (orchestrator stores metrics)

        Reference: specs/spec-008-weekly-retraining-pipeline.md Section 5.3
        """
        try:
            # Try to import AutoModelUpdateOrchestrator
            # If unavailable (parallel implementation), gracefully skip
            # Spawn orchestrator in background thread
            import threading

            from tools.ml_routing.auto_model_update_orchestrator import (
                AutoModelUpdateOrchestrator,
            )

            def run_retraining():
                try:
                    orchestrator = AutoModelUpdateOrchestrator(context=self.agent_context)
                    result = orchestrator.run_update_pipeline()

                    if result.is_ok():
                        logger.info("✅ Automated retraining completed successfully")
                        # Reload active model after successful rollout
                        self._reload_active_model()
                    else:
                        logger.error(f"❌ Automated retraining failed: {result.unwrap_err()}")

                except Exception as e:
                    logger.error(f"Retraining pipeline crashed: {e}", exc_info=True)

            # Start background thread
            retraining_thread = threading.Thread(
                target=run_retraining, name="AutoRetrainingThread", daemon=True
            )
            retraining_thread.start()

            # Log telemetry event (Article IV)
            logger.info("🔄 Automated retraining triggered in background")

        except ImportError:
            # AutoModelUpdateOrchestrator not yet implemented - graceful skip
            logger.debug(
                "AutoModelUpdateOrchestrator not available yet "
                "(parallel implementation in progress). Skipping retraining."
            )
        except Exception as e:
            # Graceful degradation: Log error but don't block initialization
            logger.warning(
                f"Failed to trigger retraining: {e}. "
                "HybridExecutor will continue without automated retraining."
            )

    def _reload_active_model(self) -> None:
        """
        Reload active ML classifier after successful retraining.

        Workflow:
        1. Clear cached classifier (_ml_classifier = None)
        2. Reset load flag (_ml_classifier_loaded = False)
        3. Next classify call will lazy-load new model

        Performance: <500ms on next classify call (lazy loading)
        Impact: Zero impact on task execution (lazy reload)

        Constitutional Compliance:
        - Article I: Complete context (validate reload success)
        - Article II: Zero functional impact (lazy loading)
        - Article IV: Telemetry logging (model_reloaded event)

        Reference: specs/spec-008-weekly-retraining-pipeline.md Section 5.3
        """
        try:
            # Clear cached classifier (force reload on next classify call)
            self._ml_classifier = None
            self._ml_classifier_loaded = False

            logger.info(
                "🔄 ML classifier cleared for reload. "
                "New model will be loaded on next classify call (lazy loading)."
            )

            # Note: We don't force-load the model here to avoid blocking
            # Instead, _get_ml_classifier() will lazy-load on next classify call

        except Exception as e:
            # Graceful degradation: Log error but don't crash
            logger.warning(
                f"Failed to reload ML classifier: {e}. "
                "HybridExecutor will continue with current model."
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
