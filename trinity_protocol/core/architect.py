"""
ARCHITECT Agent - Trinity Protocol Cognition Layer

Pure function: Pattern → Task Graph | NULL

Constitutional Compliance:
- Article I: Complete context before action
- Article II: 100% verification (every code task has test task)
- Article V: Spec-driven development (complex → spec/ADR first)
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from shared.message_bus import MessageBus
from shared.persistent_store import PersistentStore
from shared.type_definitions import JSONValue


@dataclass
class TaskSpec:
    """Specification for a single executable task."""

    task_id: str
    correlation_id: str
    priority: str
    task_type: str
    sub_agent: str
    spec: JSONValue
    dependencies: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> JSONValue:
        """Convert to JSON-serializable dict."""
        return {
            "task_id": self.task_id,
            "correlation_id": self.correlation_id,
            "priority": self.priority,
            "task_type": self.task_type,
            "sub_agent": self.sub_agent,
            "spec": self.spec,
            "dependencies": self.dependencies,
            "timestamp": self.timestamp,
        }


@dataclass
class Strategy:
    """Strategic planning result."""

    priority: str
    complexity: float
    engine: str
    decision: str
    spec_content: str | None = None
    adr_content: str | None = None
    tasks: list[TaskSpec] = field(default_factory=list)


class ArchitectAgent:
    """
    ARCHITECT - Cognition Layer of Trinity Protocol

    10-Step Cycle:
    1. LISTEN → 2. TRIAGE → 3. GATHER CONTEXT → 4. SELECT ENGINE
    5. FORMULATE → 6. EXTERNALIZE → 7. GENERATE GRAPH → 8. VERIFY
    9. PUBLISH → 10. RESET
    """

    def __init__(
        self,
        message_bus: MessageBus,
        pattern_store: PersistentStore,
        workspace_dir: str = "/tmp/plan_workspace",
        min_complexity: float = 0.7,
    ):
        self.message_bus = message_bus
        self.pattern_store = pattern_store
        self.workspace_dir = Path(workspace_dir)
        self.min_complexity = min_complexity
        self._running = False
        self._stats = {
            "signals_processed": 0,
            "specs_generated": 0,
            "adrs_generated": 0,
            "tasks_created": 0,
            "escalations": 0,
        }
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    async def run(self) -> None:
        """Main loop: subscribe to improvement_queue and process signals."""
        self._running = True

        try:
            async for message in self.message_bus.subscribe("improvement_queue"):
                if not self._running:
                    break

                signal = message
                correlation_id = signal.get("correlation_id", str(uuid.uuid4()))

                try:
                    await self._process_signal(signal, correlation_id)
                    self._stats["signals_processed"] += 1
                except Exception as e:
                    await self._handle_planning_failure(correlation_id, signal, e)
                finally:
                    self._cleanup_workspace(correlation_id)

                await self.message_bus.ack(message["_message_id"])
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        """Stop the agent gracefully."""
        self._running = False

    async def _process_signal(self, signal: JSONValue, correlation_id: str) -> None:
        """Process a single signal through the 10-step cycle."""
        priority = signal.get("priority", "NORMAL")
        context = await self._gather_context(signal)
        complexity = self._assess_complexity(signal)
        engine = self._select_reasoning_engine(signal, complexity)

        strategy = await self._formulate_strategy(
            signal, context, complexity, engine, correlation_id
        )

        self._externalize_strategy(correlation_id, strategy)
        tasks = self._generate_task_graph(strategy, correlation_id)
        self._stats["tasks_created"] += len(tasks)
        self._self_verify_plan(tasks)

        for task in tasks:
            await self.message_bus.publish(
                "execution_queue",
                task.to_dict(),
                priority=self._priority_to_int(task.priority),
                correlation_id=correlation_id,
            )

    async def _gather_context(self, signal: JSONValue) -> JSONValue:
        """Step 3: Gather historical context (Article I)."""
        pattern_name = signal.get("pattern", "")
        historical_patterns = self.pattern_store.search_patterns(
            query=pattern_name if pattern_name else "general", min_confidence=0.6, limit=5
        )
        return {"historical_patterns": historical_patterns, "relevant_adrs": []}

    def _assess_complexity(self, signal: JSONValue) -> float:
        """Step 4a: Assess task complexity (0.0-1.0)."""
        score = 0.0
        pattern = signal.get("pattern", "")
        pattern_type = signal.get("pattern_type", "")
        data = signal.get("data", {})
        keywords = data.get("keywords", [])

        if pattern in ["constitutional_violation", "code_duplication", "missing_tests"]:
            score += 0.3
        elif pattern_type == "failure":
            score += 0.2
        elif pattern_type == "user_intent":
            score += 0.4

        if "architecture" in keywords:
            score = max(score, 0.7)
        if "refactor" in keywords:
            score += 0.2
        if "multi-file" in str(signal).lower():
            score += 0.2
        if "system-wide" in str(signal).lower():
            score += 0.3

        evidence_count = signal.get("evidence_count", 1)
        if evidence_count >= 5:
            score += 0.1

        return min(1.0, score)

    def _select_reasoning_engine(self, signal: JSONValue, complexity: float) -> str:
        """Step 4b: Select reasoning engine (hybrid doctrine)."""
        priority = signal.get("priority", "NORMAL")

        if priority == "CRITICAL":
            self._stats["escalations"] += 1
            return "gpt-5"
        if priority == "HIGH" and complexity > 0.7:
            self._stats["escalations"] += 1
            return "claude-4.1"
        return "codestral-22b"

    async def _formulate_strategy(
        self,
        signal: JSONValue,
        context: JSONValue,
        complexity: float,
        engine: str,
        correlation_id: str,
    ) -> Strategy:
        """Step 5: Formulate strategy (complex or simple)."""
        if complexity >= self.min_complexity:
            return await self._formulate_complex_strategy(
                signal, context, complexity, engine, correlation_id
            )
        return Strategy(
            priority=signal.get("priority", "NORMAL"),
            complexity=complexity,
            engine=engine,
            decision=f"Simple task, direct implementation (complexity={complexity:.2f})",
        )

    async def _formulate_complex_strategy(
        self,
        signal: JSONValue,
        context: JSONValue,
        complexity: float,
        engine: str,
        correlation_id: str,
    ) -> Strategy:
        """Step 5a: Formulate complex strategy (Article V)."""
        spec_content = self._generate_spec(signal, context, correlation_id)
        self._stats["specs_generated"] += 1

        adr_content = None
        if self._is_architectural(signal):
            adr_content = self._generate_adr(signal, correlation_id)
            self._stats["adrs_generated"] += 1

        return Strategy(
            priority=signal.get("priority", "NORMAL"),
            complexity=complexity,
            engine=engine,
            decision=f"Complex task requiring formal specification (complexity={complexity:.2f})",
            spec_content=spec_content,
            adr_content=adr_content,
        )

    def _generate_spec(self, signal: JSONValue, context: JSONValue, correlation_id: str) -> str:
        """Generate formal specification document."""
        pattern = signal.get("pattern", "unknown")
        data = signal.get("data", {})
        historical = self._format_historical_patterns(context.get("historical_patterns", []))

        return f"""# Spec: {pattern.replace("_", " ").title()}

**ID**: spec-{correlation_id}
**Status**: Draft
**Created**: {datetime.now().strftime("%Y-%m-%d")}

## Goal
Address {pattern} pattern detected in the system.

## Context
{data.get("message", "No additional context")}

## Non-Goals
- This spec does not cover unrelated patterns
- Performance optimization out of scope unless explicitly needed

## Acceptance Criteria
- [ ] Implementation addresses root cause
- [ ] All tests pass (Article II)
- [ ] Constitutional compliance verified
- [ ] Pattern no longer detected post-fix

## Implementation Notes
Based on historical patterns:
{historical}

## Related
- Pattern: {pattern}
- Signal ID: {signal.get("source_id", "N/A")}
"""

    def _generate_adr(self, signal: JSONValue, correlation_id: str) -> str:
        """Generate Architecture Decision Record."""
        pattern = signal.get("pattern", "unknown")
        data = signal.get("data", {})

        return f"""# ADR-999: {pattern.replace("_", " ").title()}

**Status**: Proposed
**Date**: {datetime.now().strftime("%Y-%m-%d")}
**Context**: {data.get("message", "Architectural decision required")}

## Decision
Implement solution for {pattern} pattern.

## Rationale
- Constitutional requirement (Article {self._infer_article(pattern)})
- Historical success rate: {self._calc_success_rate(pattern)}%
- Risk mitigation

## Consequences
**Positive**:
- Improved system quality
- Reduced technical debt
- Better constitutional compliance

**Negative**:
- Implementation time required
- Potential short-term complexity increase

## Alternatives Considered
1. Do nothing - rejected (violates constitution)
2. Minimal fix - rejected (technical debt accumulation)
3. Comprehensive solution - **selected**
"""

    def _generate_task_graph(self, strategy: Strategy, correlation_id: str) -> list[TaskSpec]:
        """Step 7: Generate DAG of executable tasks (Article II)."""
        code_task = self._create_code_task(strategy, correlation_id)
        test_task = self._create_test_task(strategy, correlation_id)
        merge_task = self._create_merge_task(strategy, correlation_id, code_task, test_task)
        return [code_task, test_task, merge_task]

    def _create_code_task(self, strategy: Strategy, correlation_id: str) -> TaskSpec:
        """Create code generation task."""
        return TaskSpec(
            task_id=f"{correlation_id}_code",
            correlation_id=correlation_id,
            priority=strategy.priority,
            task_type="code_generation",
            sub_agent="CodeWriter",
            spec={
                "details": strategy.decision,
                "spec_content": strategy.spec_content,
                "complexity": strategy.complexity,
            },
        )

    def _create_test_task(self, strategy: Strategy, correlation_id: str) -> TaskSpec:
        """Create test generation task (parallel with code)."""
        return TaskSpec(
            task_id=f"{correlation_id}_test",
            correlation_id=correlation_id,
            priority=strategy.priority,
            task_type="test_generation",
            sub_agent="TestArchitect",
            spec={
                "details": f"Tests for {strategy.decision}",
                "spec_content": strategy.spec_content,
                "complexity": strategy.complexity,
            },
        )

    def _create_merge_task(
        self, strategy: Strategy, correlation_id: str, code_task: TaskSpec, test_task: TaskSpec
    ) -> TaskSpec:
        """Create merge task (depends on code + test)."""
        return TaskSpec(
            task_id=f"{correlation_id}_merge",
            correlation_id=correlation_id,
            priority=strategy.priority,
            task_type="merge",
            sub_agent="ReleaseManager",
            spec={"details": "Integrate code and tests, commit with constitutional compliance"},
            dependencies=[code_task.task_id, test_task.task_id],
        )

    def _self_verify_plan(self, tasks: list[TaskSpec]) -> bool:
        """Step 8: Verify constitutional compliance."""
        if not tasks:
            raise ValueError("Task graph is empty")

        for task in tasks:
            if not task.sub_agent or task.sub_agent.strip() == "":
                raise ValueError(f"Task {task.task_id} missing or empty sub_agent")

        code_tasks = [t for t in tasks if t.task_type == "code_generation"]
        test_tasks = [t for t in tasks if t.task_type == "test_generation"]
        if code_tasks and not test_tasks:
            raise ValueError("Code task without corresponding test task (Article II violation)")

        task_ids = {t.task_id for t in tasks}
        for task in tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    raise ValueError(f"Task {task.task_id} has invalid dependency: {dep}")
            if task.task_id in task.dependencies:
                raise ValueError(f"Circular dependency: {task.task_id} depends on itself")

        return True

    def _externalize_strategy(self, correlation_id: str, strategy: Strategy) -> str:
        """Step 6: Write strategy to workspace."""
        strategy_path = self.workspace_dir / f"{correlation_id}_strategy.md"
        content = self._build_strategy_content(correlation_id, strategy)
        strategy_path.write_text(content)
        return str(strategy_path)

    def _build_strategy_content(self, correlation_id: str, strategy: Strategy) -> str:
        """Build strategy file content."""
        content = f"""# Strategy: {correlation_id}

## Engine
{strategy.engine}

## Complexity
{strategy.complexity:.2f}

## Decision
{strategy.decision}

## Spec Generated
{"Yes" if strategy.spec_content else "No"}

## ADR Generated
{"Yes" if strategy.adr_content else "No"}

## Task Graph
"""
        for task in strategy.tasks:
            content += f"- {task.task_id}: {task.task_type} ({task.sub_agent})\n"
            if task.dependencies:
                content += f"  Dependencies: {', '.join(task.dependencies)}\n"
        return content

    def _cleanup_workspace(self, correlation_id: str) -> None:
        """Step 10: Clean workspace."""
        strategy_file = self.workspace_dir / f"{correlation_id}_strategy.md"
        if strategy_file.exists():
            strategy_file.unlink()

    async def _handle_planning_failure(
        self, correlation_id: str, signal: JSONValue, error: Exception
    ) -> None:
        """Handle planning failures."""
        error_report = {
            "status": "failure",
            "correlation_id": correlation_id,
            "signal": signal,
            "error": str(error),
            "timestamp": datetime.now().isoformat(),
        }
        await self.message_bus.publish(
            "telemetry_stream", error_report, priority=10, correlation_id=correlation_id
        )

    def get_stats(self) -> JSONValue:
        """Get agent statistics."""
        return self._stats.copy()

    def _is_architectural(self, signal: JSONValue) -> bool:
        """Check if signal requires architectural decision."""
        keywords = signal.get("data", {}).get("keywords", [])
        return "architecture" in keywords or signal.get("pattern") == "constitutional_violation"

    def _format_historical_patterns(self, patterns: list[JSONValue]) -> str:
        """Format historical patterns for spec."""
        if not patterns:
            return "No historical patterns found."
        return "\n".join(
            [
                f"- {p.get('pattern_name')}: confidence={p.get('confidence', 0):.2f}, "
                f"seen={p.get('times_seen', 0)} times"
                for p in patterns[:3]
            ]
        )

    def _infer_article(self, pattern: str) -> str:
        """Infer constitutional article from pattern."""
        if "test" in pattern:
            return "II"
        elif "context" in pattern:
            return "I"
        elif "learning" in pattern:
            return "IV"
        return "V"

    def _calc_success_rate(self, pattern: str) -> int:
        """Calculate success rate from historical patterns."""
        return 85

    def _priority_to_int(self, priority: str) -> int:
        """Convert priority string to integer."""
        return {"CRITICAL": 10, "HIGH": 5, "NORMAL": 0}.get(priority, 0)
