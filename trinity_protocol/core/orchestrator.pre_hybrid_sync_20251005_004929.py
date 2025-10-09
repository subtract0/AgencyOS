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
        """Spawn ARCHITECT agent via Ollama to analyze signal and create plan."""
        self.logger.info("🏗️  Spawning ARCHITECT for strategic planning...")

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
        """Spawn EXECUTOR agent to implement the plan."""
        self.logger.info("⚡ Spawning EXECUTOR for implementation...")

        # Get model config
        model_name = self._config.get("models", {}).get("executor", {}).get("name", "codestral:22b")
        timeout = self._config.get("models", {}).get("executor", {}).get("timeout", 300)

        # Extract original signal data if available
        original_data = plan_msg.data.get("raw_response", "")

        # Get file path from original signal (if it exists in the chain)
        target_file = "trinity_protocol/core/orchestrator.py"  # Default for now

        messages = [
            {"role": "system", "content": EXECUTOR_SPEC},
            {
                "role": "user",
                "content": f"""Generate pytest tests for: {target_file}

Target file: {target_file}
Requirements:
- Test TrinityBus initialization
- Test TrinityOrchestrator initialization
- Test message detection with timestamps

Output ONLY in this format:
FILE_PATH: tests/trinity_protocol/core/test_orchestrator.py
TEST_CODE:
[your complete test code here]
""",
            },
        ]

        try:
            response = await self.ollama.chat(model=model_name, messages=messages, timeout=timeout)

            self.logger.info(f"✅ EXECUTOR generated code ({len(response)} chars)")

            # Parse response and write file
            file_written = await self._write_test_file(response)

            self.bus.publish(
                "EXECUTOR", "EXECUTOR_COMPLETE", {"result": response, "file_written": file_written}
            )

        except (OllamaTimeout, OllamaError) as e:
            self.logger.error(f"❌ EXECUTOR failed: {e}")

    async def _write_test_file(self, response: str) -> bool:
        """Extract test code from EXECUTOR response and write to file."""
        try:
            # Extract FILE_PATH
            import re

            file_match = re.search(r"FILE_PATH:\s*(.+)", response)
            if not file_match:
                self.logger.error("No FILE_PATH found in response")
                return False

            file_path = Path(file_match.group(1).strip())

            # Extract TEST_CODE
            code_match = re.search(r"TEST_CODE:\s*```python\s*\n(.*?)```", response, re.DOTALL)
            if not code_match:
                # Try without ```python markers
                code_match = re.search(r"TEST_CODE:\s*\n(.*)", response, re.DOTALL)

            if not code_match:
                self.logger.error("No TEST_CODE found in response")
                return False

            test_code = code_match.group(1).strip()

            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            file_path.write_text(test_code)

            self.logger.info(f"✅ Test file written: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to write test file: {e}")
            return False

    async def _spawn_witness_verify(self, result_msg: TrinityMessage) -> None:
        """Spawn WITNESS agent to verify implementation quality."""
        self.logger.info("🔍 Spawning WITNESS for verification...")

        # Get model config
        model_name = (
            self._config.get("models", {}).get("witness", {}).get("name", "qwen2.5-coder:1.5b")
        )
        timeout = self._config.get("models", {}).get("witness", {}).get("timeout", 30)

        messages = [
            {"role": "system", "content": WITNESS_SPEC},
            {
                "role": "user",
                "content": f"Verify this implementation:\n\n{json.dumps(result_msg.data, indent=2)}",
            },
        ]

        try:
            response = await self.ollama.chat(model=model_name, messages=messages, timeout=timeout)

            self.logger.info(f"✅ WITNESS verification complete ({len(response)} chars)")

            # Parse approval status
            if "APPROVED" in response:
                self.bus.publish("WITNESS", "WITNESS_APPROVED", {"verification": response})
            else:
                self.bus.publish("WITNESS", "WITNESS_BLOCKED", {"verification": response})

        except (OllamaTimeout, OllamaError) as e:
            self.logger.error(f"❌ WITNESS failed: {e}")

    def _parse_architect_response(self, response: str) -> dict:
        """
        Parse ARCHITECT LLM response into structured plan.

        Expected format:
        ```json
        {
          "tasks": [...]
        }
        ```
        """
        # Extract JSON from markdown code blocks
        import re

        json_match = re.search(r"```json\s*\n(.*?)\n```", response, re.DOTALL)
        if json_match:
            plan = json.loads(json_match.group(1))
        else:
            # Try parsing entire response as JSON
            try:
                plan = json.loads(response)
            except json.JSONDecodeError:
                # Fallback: return raw response
                plan = {"raw_response": response, "tasks": []}

        # Add metadata
        if "tasks" in plan:
            plan["task_count"] = len(plan["tasks"])

        return plan

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
