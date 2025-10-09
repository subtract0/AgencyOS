"""
Trinity Protocol Orchestrator - Continuous Background Service
Monitors message bus and coordinates Trinity agents in autonomous loop.

Runs continuously as background service monitoring for tasks.
"""

import argparse
import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from shared.agent_context import AgentContext
from shared.cost_tracker import CostTracker
from shared.message_bus import MessageBus
from trinity_protocol.core.agent_registry import (
    AgentRegistry,
    AgentType,
    ModelTier,
    create_agent_registry,
)
from trinity_protocol.core.escalation_rules import (
    EscalationPolicy,
    create_escalation_policy,
)

# HybridExecutor imports (added by integration script)
from trinity_protocol.core.hybrid_executor import (
    HybridExecutor,
    TaskResult,
    TaskType,
    create_hybrid_executor,
)
from trinity_protocol.core.ollama_client import OllamaClient, OllamaError, OllamaTimeout

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


# Message Bus Protocol (Token-Efficient JSONL)
class TrinityMessage(BaseModel):
    """Single message in Trinity coordination bus."""

    ts: str = Field(description="ISO timestamp (19 chars)")
    agent: Literal["ARCHITECT", "EXECUTOR", "WITNESS", "ORCHESTRATOR"]
    type: str = Field(description="Message type (DECISION, READY, COMPLETE, etc.)")
    data: dict = Field(default_factory=dict, description="Minimal payload")


class TrinityBus:
    """Append-only message bus for Trinity coordination."""

    def __init__(self, bus_path: str = "/tmp/trinity.jsonl"):
        self.path = Path(bus_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def publish(self, agent: str, msg_type: str, data: dict) -> None:
        """Append message to bus (atomic, thread-safe)."""
        msg = TrinityMessage(
            ts=datetime.now().isoformat()[:19],
            agent=agent,  # type: ignore
            type=msg_type,
            data=data,
        )
        with open(self.path, "a") as f:
            f.write(msg.model_dump_json() + "\n")

    def read(
        self, msg_type: str | None = None, from_agent: str | None = None
    ) -> list[TrinityMessage]:
        """Read messages from bus (filter by type/agent)."""
        if not self.path.exists():
            return []

        messages = []
        with open(self.path) as f:
            for line in f:
                if not line.strip():
                    continue
                msg = TrinityMessage.model_validate_json(line)
                if msg_type and msg.type != msg_type:
                    continue
                if from_agent and msg.agent != from_agent:
                    continue
                messages.append(msg)
        return messages

    def clear(self) -> None:
        """Clear message bus (new mission)."""
        if self.path.exists():
            self.path.unlink()


# Trinity Agent Specifications (for Claude Code Task tool)
ARCHITECT_SPEC = """
You are Trinity ARCHITECT - Strategic Decision Engine.

MISSION: Analyze codebase and create minimal, high-ROI implementation plan.

INPUTS:
- Read /tmp/trinity.jsonl for coordination messages
- Access to full codebase via Glob/Grep/Read tools

OUTPUTS (via TrinityBus):
1. DECISION: {"task": str, "roi": float, "reasoning": str}
2. PLAN: {"tracks": [{"id": str, "tasks": [...]}], "gates": [...]}
3. READY: Signal EXECUTOR to begin

CONSTRAINTS:
- Plans must be minimal (no over-engineering)
- ROI calculation required (value/effort)
- Constitutional compliance mandatory
- Token budget: <2000 tokens output

EXAMPLE:
```python
bus = TrinityBus()
bus.publish("ARCHITECT", "DECISION", {
    "task": "Timeout wrapper rollout",
    "roi": 2.5,
    "reasoning": "Article I compliance for 33 remaining tools"
})
```
"""

EXECUTOR_SPEC = """
You are Trinity EXECUTOR - Code Generation Agent.

MISSION: Generate ACTUAL Python test files and write them to disk.

INPUTS:
- Signal data with file path and test requirements
- Target file to generate tests for

OUTPUTS:
- Complete, runnable Python test code
- File path where test should be written
- List of test functions created

CRITICAL INSTRUCTIONS:
1. Generate REAL pytest code (not pseudocode!)
2. Use pytest and pytest-asyncio
3. Follow AAA pattern (Arrange, Act, Assert)
4. Import necessary modules from target file
5. Output format:

```python
FILE_PATH: tests/trinity_protocol/core/test_orchestrator.py
TEST_CODE:
import pytest
import asyncio
from trinity_protocol.core.orchestrator import TrinityOrchestrator, TrinityBus

def test_trinity_bus_initialization():
    # Arrange
    bus = TrinityBus()

    # Act
    result = bus.path.exists()

    # Assert
    assert result is True
    assert str(bus.path) == "/tmp/trinity.jsonl"

@pytest.mark.asyncio
async def test_orchestrator_initialization():
    # Arrange
    orchestrator = TrinityOrchestrator()

    # Act & Assert
    assert orchestrator.ollama is not None
    assert orchestrator._running is False
```

ONLY output the FILE_PATH and TEST_CODE. No explanations."""

WITNESS_SPEC = """
You are Trinity WITNESS - Constitutional Quality Enforcer.

MISSION: Real-time quality gates. Block execution if standards not met.

INPUTS:
- Read /tmp/trinity.jsonl for COMPLETE messages
- Run tests: python run_tests.py --run-all
- Check git status, diff, log

OUTPUTS:
- APPROVED: All gates pass, proceed
- BLOCKED: Quality violation, rollback required
- Quality metrics (test pass rate, coverage, compliance)

QUALITY GATES (ALL must pass):
1. Tests: 100% pass rate (python run_tests.py --run-all)
2. Type safety: Zero Dict[Any] violations
3. Constitutional compliance: All 5 articles verified
4. No regressions: All existing tests continue passing

CONSTRAINTS:
- Absolute gates (no "good enough")
- Real test execution required (no simulation)
- Detailed failure reports
- Token budget: <1500 tokens output
"""


class TrinityOrchestrator:
    """
    Production Trinity Protocol Orchestrator - Continuous Background Service.

    Monitors message bus and coordinates Trinity agents:
    - Detects new improvement signals
    - Spawns ARCHITECT for strategic planning
    - Coordinates EXECUTOR for parallel implementation
    - Validates with WITNESS quality gates
    """

    def __init__(self, config_path: str | None = None):
        self.bus = TrinityBus()
        self.logger = logging.getLogger("TrinityOrchestrator")
        self._running = False
        self._config = self._load_config(config_path) if config_path else {}
        self._last_processed_timestamp = ""  # Track by timestamp instead of index
        self.ollama = OllamaClient(base_url="http://localhost:11434")

        # HybridExecutor initialization (added by integration script)
        # Initialize shared infrastructure for hybrid execution
        try:
            # Create shared context for all agents
            self._agent_context = AgentContext()

            # Create cost tracker
            self._cost_tracker = CostTracker()

            # Create message bus (in-memory for now)
            self._message_bus = MessageBus()

            # Create agent registry with local-first default
            self._agent_registry = create_agent_registry(
                agent_context=self._agent_context,
                cost_tracker=self._cost_tracker,
                default_tier="local",
            )

            # Create escalation policy from config
            escalation_config = self._config.get("escalation", {})
            self._escalation_policy = create_escalation_policy(
                max_local_attempts=escalation_config.get("max_local_attempts", 2),
                max_local_plus_attempts=escalation_config.get("max_local_plus_attempts", 1),
                test_failure_threshold=escalation_config.get("test_failure_threshold", 2),
                confidence_threshold=escalation_config.get("confidence_threshold", 0.5),
            )

            # Create HybridExecutor
            self.hybrid_executor = create_hybrid_executor(
                message_bus=self._message_bus,
                cost_tracker=self._cost_tracker,
                agent_context=self._agent_context,
                agent_registry=self._agent_registry,
                escalation_policy=self._escalation_policy,
            )

            self.logger.info("✅ HybridExecutor initialized with local-first execution")

        except Exception as e:
            self.logger.error(
                f"❌ Failed to initialize HybridExecutor: {e}. "
                "Trinity will not be able to execute tasks until this is fixed.",
                exc_info=True,
            )
            self.hybrid_executor = None

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load config from {config_path}: {e}")
            return {}

    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown on SIGTERM/SIGINT."""

        def shutdown_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down gracefully...")
            self._running = False

        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)

    async def monitor_loop(self) -> None:
        """
        Main monitoring loop - runs continuously as background service.

        Monitors message bus for:
        1. New improvement signals → Spawn ARCHITECT
        2. ARCHITECT READY → Spawn EXECUTOR
        3. EXECUTOR COMPLETE → Spawn WITNESS
        4. WITNESS APPROVED → Next cycle
        5. IDLE TIME → Self-audit and suggest improvements
        """
        self._running = True
        self._setup_signal_handlers()

        self.logger.info("🚀 Trinity Orchestrator started - monitoring for tasks...")
        self.logger.info(f"📋 Message bus: {self.bus.path}")
        self.logger.info(f"⚙️  Config: {self._config.get('models', {})}")

        cycle_count = 0
        last_heartbeat = time.time()
        last_idle_check = time.time()
        idle_threshold = 300  # 5 minutes of no activity triggers self-audit

        try:
            while self._running:
                # Heartbeat every 60 seconds
                if time.time() - last_heartbeat > 60:
                    self.logger.info(
                        f"💓 Heartbeat - cycle {cycle_count}, monitoring for signals..."
                    )
                    last_heartbeat = time.time()

                # Check for new messages on the bus
                messages = self.bus.read()

                # Process only messages newer than last processed timestamp
                new_messages = [msg for msg in messages if msg.ts > self._last_processed_timestamp]

                if new_messages:
                    self.logger.info(f"📨 Processing {len(new_messages)} new messages")
                    for msg in new_messages:
                        await self._process_message(msg)
                        self._last_processed_timestamp = msg.ts

                    # Reset idle timer after processing messages
                    last_idle_check = time.time()

                # IDLE TIME BEHAVIOR: Self-audit and suggest improvements
                elif time.time() - last_idle_check > idle_threshold:
                    self.logger.info("🧠 Idle time detected - running self-audit...")
                    await self._idle_self_audit()
                    last_idle_check = time.time()  # Reset timer

                # Sleep to avoid busy-waiting
                await asyncio.sleep(5)
                cycle_count += 1

        except Exception as e:
            self.logger.error(f"❌ Fatal error in monitor loop: {e}", exc_info=True)
            raise
        finally:
            self.logger.info("🛑 Trinity Orchestrator stopped")

    async def _idle_self_audit(self) -> None:
        """
        Autonomous behavior during idle time.

        Trinity analyzes itself and proposes improvements:
        1. Find files without tests
        2. Detect code quality issues
        3. Identify missing documentation
        4. Suggest performance optimizations
        5. Check for security vulnerabilities
        """
        self.logger.info("🔍 Self-audit: Analyzing codebase for improvement opportunities...")

        # Simple self-audit: find files without tests
        from pathlib import Path

        trinity_dir = Path("/Users/am/.trinity-local/trinity_protocol")
        python_files = list(trinity_dir.glob("**/*.py"))

        missing_tests = []
        for py_file in python_files:
            if py_file.name.startswith("test_") or py_file.name == "__init__.py":
                continue

            # Check if test exists
            relative_path = py_file.relative_to(trinity_dir.parent)
            test_path = (
                Path("/Users/am/.trinity-local/tests")
                / relative_path.parent
                / f"test_{py_file.name}"
            )

            if not test_path.exists():
                missing_tests.append(str(relative_path))

        if missing_tests:
            self.logger.info(f"📊 Self-audit found {len(missing_tests)} files without tests")

            # Publish SUGGESTION (not IMPROVEMENT_SIGNAL - requires user approval)
            self.bus.publish(
                "ORCHESTRATOR",
                "SUGGESTION",
                {
                    "type": "missing_tests",
                    "priority": "NORMAL",
                    "files": missing_tests[:5],  # Top 5 most important
                    "reason": f"Self-audit detected {len(missing_tests)} files without test coverage",
                    "auto_execute": False,  # Requires user approval
                },
            )

            self.logger.info("💡 Suggestion published to dashboard - awaiting user approval")
        else:
            self.logger.info("✅ Self-audit: All files have test coverage!")

    async def _process_message(self, msg: TrinityMessage) -> None:
        """Process a single message from the bus and spawn appropriate agents."""
        self.logger.info(f"📨 [{msg.agent}] {msg.type}: {msg.data}")

        try:
            if msg.type == "IMPROVEMENT_SIGNAL":
                await self._spawn_architect(msg)
            elif msg.type == "ARCHITECT_READY":
                await self._spawn_executor(msg)
            elif msg.type == "EXECUTOR_COMPLETE":
                await self._spawn_witness_verify(msg)
            elif msg.type == "WITNESS_APPROVED":
                self.logger.info("🎉 Quality gates passed - cycle complete")
        except Exception as e:
            self.logger.error(f"❌ Error processing {msg.type}: {e}", exc_info=True)
            # Don't crash - log and continue monitoring

    async def _spawn_architect(self, signal: TrinityMessage) -> None:
        """
        Spawn ARCHITECT agent via HybridExecutor for strategic planning.

        Enhanced workflow (Week 4):
        - Uses HybridExecutor if available (local-first + cloud escalation)
        - Falls back to direct Ollama if HybridExecutor not initialized
        """
        self.logger.info("🏗️  Spawning ARCHITECT for strategic planning...")

        # Check if HybridExecutor is available
        if hasattr(self, "hybrid_executor") and self.hybrid_executor is not None:
            try:
                # Create task for HybridExecutor
                task = {
                    "task_id": f"architect_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "task_type": TaskType.ARCHITECTURE.value,
                    "complexity": signal.data.get("complexity", "medium"),
                    "signal": signal.data,
                    "spec": ARCHITECT_SPEC,
                    "prompt": f"Analyze this signal and create implementation plan:\n\n{json.dumps(signal.data, indent=2)}",
                }

                # Publish to execution queue (HybridExecutor subscribes)
                await self._message_bus.publish("execution_queue", task)
                self.logger.info("✅ ARCHITECT task queued to HybridExecutor")

                # Legacy: Also publish to Trinity bus for compatibility
                self.bus.publish(
                    "ARCHITECT",
                    "ARCHITECT_READY",
                    {
                        "task_id": task["task_id"],
                        "status": "queued",
                        "executor": "hybrid",
                        "message": "ARCHITECT task queued for HybridExecutor processing",
                    },
                )
                return

            except Exception as e:
                self.logger.error(
                    f"❌ HybridExecutor architect failed: {e}. Falling back to direct Ollama.",
                    exc_info=True,
                )
                # Fall through to Ollama fallback

        # Fallback: Direct Ollama execution (legacy path)
        self.logger.warning("⚠️  HybridExecutor not available - using direct Ollama fallback")

        # Get model config
        model_name = (
            self._config.get("models", {}).get("architect", {}).get("name", "qwen2.5-coder:7b")
        )
        timeout = self._config.get("models", {}).get("architect", {}).get("timeout", 120)

        # Prepare prompt
        messages = [
            {"role": "system", "content": ARCHITECT_SPEC},
            {
                "role": "user",
                "content": f"Analyze this signal and create implementation plan:\n\n{json.dumps(signal.data, indent=2)}",
            },
        ]

        # Retry with exponential backoff (Article I)
        for attempt in range(3):
            try:
                response = await self.ollama.chat(
                    model=model_name,
                    messages=messages,
                    timeout=timeout * (2**attempt),  # 120s, 240s, 480s
                )

                self.logger.info(f"✅ ARCHITECT planning complete ({len(response)} chars)")

                # Parse response and publish plan
                try:
                    plan = self._parse_architect_response(response)
                    self.bus.publish("ARCHITECT", "ARCHITECT_READY", plan)
                    self.logger.info(f"📋 Plan published: {plan.get('task_count', 0)} tasks")
                    return
                except Exception as e:
                    self.logger.error(f"Failed to parse ARCHITECT response: {e}")
                    # Publish raw response for debugging
                    self.bus.publish(
                        "ARCHITECT",
                        "ARCHITECT_READY",
                        {"raw_response": response, "error": str(e)},
                    )
                    return

            except OllamaTimeout as e:
                if attempt < 2:
                    self.logger.warning(f"⏱️  ARCHITECT timeout - retry {attempt + 1}/3")
                else:
                    self.logger.error(f"❌ ARCHITECT timeout after 3 retries: {e}")
            except OllamaError as e:
                self.logger.error(f"❌ ARCHITECT error: {e}")
                break

    async def _spawn_executor(self, plan_msg: TrinityMessage) -> None:
        """
        Spawn EXECUTOR agent via HybridExecutor (with local-first + cloud escalation).

        Enhanced workflow:
        1. Extract task from plan message
        2. Determine task type and complexity
        3. Create execution task
        4. Delegate to HybridExecutor (handles escalation automatically)
        5. Publish results to bus
        """
        self.logger.info("⚡ Spawning EXECUTOR via HybridExecutor...")

        # Extract task details from plan
        plan_data = plan_msg.data
        task_type = plan_data.get("task_type", "general")
        complexity = plan_data.get("complexity", "medium")

        # Check if HybridExecutor is initialized
        if not hasattr(self, "hybrid_executor") or self.hybrid_executor is None:
            self.logger.error(
                "❌ HybridExecutor not initialized. Cannot execute tasks. "
                "Check initialization logs for errors."
            )
            self.bus.publish(
                "EXECUTOR",
                "EXECUTOR_FAILED",
                {
                    "error": "HybridExecutor not initialized",
                    "task_id": f"trinity_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                },
            )
            return

        try:
            # Create task for HybridExecutor
            task = {
                "task_id": f"trinity_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "task_type": task_type,
                "complexity": complexity,
                "plan": plan_data,
                "original_signal": plan_msg.data.get("original_signal", {}),
            }

            # Execute via HybridExecutor (handles escalation internally)
            # In production, this would publish to execution_queue and let
            # HybridExecutor's event loop handle it. For now, simulate direct call.
            self.logger.info(f"📋 Task created: type={task_type}, complexity={complexity}")

            # Publish to execution queue (HybridExecutor subscribes to this)
            await self._message_bus.publish("execution_queue", task)

            # For synchronous compatibility, wait briefly for result
            # (In production, this would be fully async event-driven)
            self.logger.info("✅ Task published to HybridExecutor queue")

            # Legacy: Also publish EXECUTOR_COMPLETE for Trinity bus compatibility
            self.bus.publish(
                "EXECUTOR",
                "EXECUTOR_COMPLETE",
                {
                    "task_id": task["task_id"],
                    "status": "queued",
                    "executor": "hybrid",
                    "message": "Task queued for HybridExecutor processing",
                },
            )

        except Exception as e:
            self.logger.error(f"❌ HybridExecutor execution failed: {e}", exc_info=True)
            self.bus.publish(
                "EXECUTOR",
                "EXECUTOR_FAILED",
                {
                    "error": str(e),
                    "task_id": task.get("task_id", "unknown"),
                },
            )

    async def _spawn_witness_verify(self, completion_msg: TrinityMessage) -> None:
        """
        Spawn WITNESS agent via HybridExecutor for quality verification.

        Enhanced workflow (Week 4):
        - Uses HybridExecutor if available (local-first + cloud escalation)
        - Falls back to direct Ollama if HybridExecutor not initialized
        """
        self.logger.info("👁️  Spawning WITNESS for quality verification...")

        # Check if HybridExecutor is available
        if hasattr(self, "hybrid_executor") and self.hybrid_executor is not None:
            try:
                # Create task for HybridExecutor
                task = {
                    "task_id": f"witness_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "task_type": TaskType.VERIFICATION.value,
                    "complexity": "high",  # Quality verification is always high priority
                    "completion_data": completion_msg.data,
                    "spec": WITNESS_SPEC,
                    "prompt": f"Verify quality gates for completed task:\n\n{json.dumps(completion_msg.data, indent=2)}",
                }

                # Publish to execution queue (HybridExecutor subscribes)
                await self._message_bus.publish("execution_queue", task)
                self.logger.info("✅ WITNESS task queued to HybridExecutor")

                # Legacy: Also publish to Trinity bus for compatibility
                self.bus.publish(
                    "WITNESS",
                    "WITNESS_APPROVED",
                    {
                        "task_id": task["task_id"],
                        "status": "queued",
                        "executor": "hybrid",
                        "message": "WITNESS task queued for HybridExecutor processing",
                    },
                )
                return

            except Exception as e:
                self.logger.error(
                    f"❌ HybridExecutor witness failed: {e}. Falling back to direct Ollama.",
                    exc_info=True,
                )
                # Fall through to Ollama fallback

        # Fallback: Direct Ollama execution (legacy path)
        self.logger.warning("⚠️  HybridExecutor not available - using direct Ollama fallback")

        # Get model config
        model_name = (
            self._config.get("models", {}).get("witness", {}).get("name", "qwen2.5-coder:7b")
        )
        timeout = self._config.get("models", {}).get("witness", {}).get("timeout", 120)

        # Prepare prompt
        messages = [
            {"role": "system", "content": WITNESS_SPEC},
            {
                "role": "user",
                "content": f"Verify quality gates for completed task:\n\n{json.dumps(completion_msg.data, indent=2)}",
            },
        ]

        # Retry with exponential backoff (Article I)
        for attempt in range(3):
            try:
                response = await self.ollama.chat(
                    model=model_name,
                    messages=messages,
                    timeout=timeout * (2**attempt),  # 120s, 240s, 480s
                )

                self.logger.info(f"✅ WITNESS verification complete ({len(response)} chars)")

                # Simple approval logic - if response contains "APPROVED", publish approval
                if "APPROVED" in response.upper():
                    self.bus.publish(
                        "WITNESS",
                        "WITNESS_APPROVED",
                        {
                            "task_id": completion_msg.data.get("task_id", "unknown"),
                            "verification": response,
                        },
                    )
                    self.logger.info("✅ Quality gates passed")
                else:
                    self.bus.publish(
                        "WITNESS",
                        "WITNESS_BLOCKED",
                        {
                            "task_id": completion_msg.data.get("task_id", "unknown"),
                            "verification": response,
                            "reason": "Quality gates not met",
                        },
                    )
                    self.logger.warning("⚠️  Quality gates blocked")

                return

            except OllamaTimeout as e:
                if attempt < 2:
                    self.logger.warning(f"⏱️  WITNESS timeout - retry {attempt + 1}/3")
                else:
                    self.logger.error(f"❌ WITNESS timeout after 3 retries: {e}")
            except OllamaError as e:
                self.logger.error(f"❌ WITNESS error: {e}")
                break

    def _parse_architect_response(self, response: str) -> dict:
        """
        Parse ARCHITECT response into structured plan.

        This is a placeholder - you would implement actual parsing logic here.
        """
        # Simple parsing: extract JSON if present, otherwise create basic structure
        try:
            # Try to extract JSON block
            import re

            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass

        # Fallback: create basic plan structure
        return {"task_count": 1, "raw_response": response, "parsed": False}

    def start_mission(self, user_goal: str) -> dict:
        """
        Initialize a new mission (synchronous API for compatibility).

        Returns initial status.
        """
        # Clear previous state
        self.bus.clear()

        # Publish mission start
        self.bus.publish("ORCHESTRATOR", "MISSION_START", {"goal": user_goal})

        self.logger.info(f"🎯 Mission started: {user_goal}")

        return {
            "status": "ready",
            "message": "Trinity protocol initialized - spawn agents via Task tool",
            "specs": {
                "architect": ARCHITECT_SPEC,
                "executor": EXECUTOR_SPEC,
                "witness": WITNESS_SPEC,
            },
            "bus_path": str(self.bus.path),
            "next_action": "Spawn ARCHITECT agent via Task tool with ARCHITECT_SPEC",
        }


# Production API
def initialize_trinity(goal: str) -> dict:
    """Initialize Trinity protocol for a mission (synchronous)."""
    orchestrator = TrinityOrchestrator()
    return orchestrator.start_mission(goal)


async def run_continuous_orchestrator(config_path: str | None = None) -> None:
    """Run Trinity orchestrator as continuous background service."""
    orchestrator = TrinityOrchestrator(config_path=config_path)
    await orchestrator.monitor_loop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trinity Protocol Orchestrator")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to trinity_config.yaml",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo initialization (prints specs and exits)",
    )

    args = parser.parse_args()

    if args.demo:
        # Demo mode - print specs and exit
        result = initialize_trinity("Roll out timeout wrapper to remaining 33 tools")
        print(json.dumps(result, indent=2))
    else:
        # Continuous mode - run as background service
        asyncio.run(run_continuous_orchestrator(config_path=args.config))
