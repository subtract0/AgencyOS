"""
ARCHITECT Agent - Trinity Protocol Cognition Layer

The strategic reasoning engine that transforms signals into executable task graphs.

Pure function: Pattern → Task Graph | NULL

Constitutional Compliance:
- Article I: Complete context before action (historical patterns, ADRs)
- Article II: 100% verification (every code task has test task)
- Article V: Spec-driven development (complex → spec/ADR first)
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from trinity_protocol.message_bus import MessageBus
from trinity_protocol.persistent_store import PersistentStore


@dataclass
class TaskSpec:
    """Specification for a single executable task."""

    task_id: str
    correlation_id: str
    priority: str  # CRITICAL, HIGH, NORMAL
    task_type: str  # code_generation, test_generation, tool_creation, merge, verification
    sub_agent: str  # CodeWriter, TestArchitect, ToolDeveloper, ReleaseManager, ImmunityEnforcer
    spec: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "task_id": self.task_id,
            "correlation_id": self.correlation_id,
            "priority": self.priority,
            "task_type": self.task_type,
            "sub_agent": self.sub_agent,
            "spec": self.spec,
            "dependencies": self.dependencies,
            "timestamp": self.timestamp
        }


@dataclass
class Strategy:
    """Strategic planning result."""

    priority: str
    complexity: float
    engine: str  # Model used for reasoning
    decision: str  # Strategic decision summary
    spec_content: Optional[str] = None
    adr_content: Optional[str] = None
    tasks: List[TaskSpec] = field(default_factory=list)


class ArchitectAgent:
    """
    ARCHITECT - Cognition Layer of Trinity Protocol

    Transforms improvement signals into verified execution plans.

    10-Step Cycle:
    1. LISTEN - Await signal from improvement_queue
    2. TRIAGE - Assess priority
    3. GATHER CONTEXT - Query historical patterns and ADRs
    4. SELECT REASONING ENGINE - Hybrid local/cloud based on complexity
    5. FORMULATE STRATEGY - Generate spec/ADR if complex
    6. EXTERNALIZE STRATEGY - Write to /tmp/plan_workspace/
    7. GENERATE TASK GRAPH - Create DAG with dependencies
    8. SELF-VERIFY PLAN - Validate constitutional compliance
    9. PUBLISH PLAN - Send tasks to execution_queue
    10. RESET - Clean workspace, return to stateless state
    """

    def __init__(
        self,
        message_bus: MessageBus,
        pattern_store: PersistentStore,
        workspace_dir: str = "/tmp/plan_workspace",
        min_complexity: float = 0.7
    ):
        """
        Initialize ARCHITECT agent.

        Args:
            message_bus: Message bus for pub/sub
            pattern_store: Historical pattern database
            workspace_dir: Directory for strategy externalization
            min_complexity: Threshold for complex vs simple (0.7 default)
        """
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
            "escalations": 0
        }

        # Ensure workspace exists
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    async def run(self) -> None:
        """
        Main loop: subscribe to improvement_queue and process signals.

        Stateless operation - each signal processed independently.
        """
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
                    # Step 10: RESET - cleanup workspace
                    self._cleanup_workspace(correlation_id)

                # Acknowledge message
                await self.message_bus.ack(message["_message_id"])

        except asyncio.CancelledError:
            pass  # Expected on shutdown

    async def stop(self) -> None:
        """Stop the agent gracefully."""
        self._running = False

    async def _process_signal(self, signal: Dict[str, Any], correlation_id: str) -> None:
        """
        Process a single signal through the 10-step cycle.

        Args:
            signal: Improvement signal from WITNESS
            correlation_id: Unique ID linking related tasks
        """
        # Step 1: LISTEN (implicit - signal received)

        # Step 2: TRIAGE
        priority = signal.get("priority", "NORMAL")

        # Step 3: GATHER CONTEXT
        context = await self._gather_context(signal)

        # Step 4: SELECT REASONING ENGINE
        complexity = self._assess_complexity(signal)
        engine = self._select_reasoning_engine(signal, complexity)

        # Step 5: FORMULATE STRATEGY
        if complexity >= self.min_complexity:
            # Complex: Generate spec/ADR first (Article V)
            strategy = await self._formulate_complex_strategy(
                signal, context, complexity, engine, correlation_id
            )
        else:
            # Simple: Direct task generation
            strategy = await self._formulate_simple_strategy(
                signal, context, complexity, engine, correlation_id
            )

        # Step 6: EXTERNALIZE STRATEGY
        self._externalize_strategy(correlation_id, strategy)

        # Step 7: GENERATE TASK GRAPH
        tasks = self._generate_task_graph(strategy, correlation_id)
        self._stats["tasks_created"] += len(tasks)

        # Step 8: SELF-VERIFY PLAN
        self._self_verify_plan(tasks)

        # Step 9: PUBLISH PLAN
        for task in tasks:
            await self.message_bus.publish(
                "execution_queue",
                task.to_dict(),
                priority=self._priority_to_int(task.priority),
                correlation_id=correlation_id
            )

    async def _gather_context(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 3: Gather historical context from patterns database.

        Article I: Complete context before action.

        Args:
            signal: Improvement signal

        Returns:
            Context dict with historical patterns and relevant ADRs
        """
        pattern_name = signal.get("pattern", "")

        # Query historical patterns (top 5 by success rate)
        # search_patterns uses semantic query, not pattern_name filter
        historical_patterns = self.pattern_store.search_patterns(
            query=pattern_name if pattern_name else "general",
            min_confidence=0.6,
            limit=5
        )

        return {
            "historical_patterns": historical_patterns,
            "relevant_adrs": []  # TODO: Implement ADR search when ADR index ready
        }

    def _assess_complexity(self, signal: Dict[str, Any]) -> float:
        """
        Step 4a: Assess task complexity (0.0-1.0 scoring).

        Factors:
        - Pattern type (failure=0.2, opportunity=0.3-0.4)
        - Keywords (architecture/refactor=+0.5, multi-file=+0.2)
        - Evidence count (≥5=+0.1)

        Thresholds:
        - < 0.3: Simple (single file, bug fix)
        - 0.3-0.7: Moderate (multi-file, refactor)
        - > 0.7: Complex (architecture, system-wide)

        Args:
            signal: Improvement signal

        Returns:
            Complexity score 0.0-1.0
        """
        score = 0.0

        # Pattern type baseline
        pattern = signal.get("pattern", "")
        pattern_type = signal.get("pattern_type", "")

        if pattern in ["constitutional_violation", "code_duplication", "missing_tests"]:
            score += 0.3
        elif pattern_type == "failure":
            score += 0.2  # Failures are often localized
        elif pattern_type == "user_intent":
            score += 0.4  # User requests often broader

        # Keyword analysis
        data = signal.get("data", {})
        keywords = data.get("keywords", [])

        # Architecture keyword is highest priority - sets floor at 0.7
        if "architecture" in keywords:
            score = max(score, 0.7)  # Architecture changes always complex

        if "refactor" in keywords:
            score += 0.2
        if "multi-file" in str(signal).lower():
            score += 0.2
        if "system-wide" in str(signal).lower():
            score += 0.3

        # Evidence accumulation
        evidence_count = signal.get("evidence_count", 1)
        if evidence_count >= 5:
            score += 0.1

        return min(1.0, score)

    def _select_reasoning_engine(self, signal: Dict[str, Any], complexity: float) -> str:
        """
        Step 4b: Select reasoning engine (hybrid doctrine).

        Escalation Rules:
        - CRITICAL priority → GPT-5 (mandatory)
        - HIGH priority + complexity > 0.7 → Claude 4.1 (mandatory)
        - Otherwise → Codestral-22B (local, cost-efficient)

        Args:
            signal: Improvement signal
            complexity: Complexity score

        Returns:
            Model name
        """
        priority = signal.get("priority", "NORMAL")

        if priority == "CRITICAL":
            self._stats["escalations"] += 1
            return "gpt-5"

        if priority == "HIGH" and complexity > 0.7:
            self._stats["escalations"] += 1
            return "claude-4.1"

        return "codestral-22b"  # Local default

    async def _formulate_complex_strategy(
        self,
        signal: Dict[str, Any],
        context: Dict[str, Any],
        complexity: float,
        engine: str,
        correlation_id: str
    ) -> Strategy:
        """
        Step 5a: Formulate strategy for complex tasks.

        Article V: Complex tasks require formal spec, architectural tasks require ADR.

        Args:
            signal: Improvement signal
            context: Historical context
            complexity: Complexity score
            engine: Selected reasoning engine
            correlation_id: Unique ID

        Returns:
            Strategy with spec/ADR content
        """
        # Generate spec
        spec_content = self._generate_spec(signal, context, correlation_id)
        self._stats["specs_generated"] += 1

        # Generate ADR if architectural
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
            tasks=[]  # Populated in task graph generation
        )

    async def _formulate_simple_strategy(
        self,
        signal: Dict[str, Any],
        context: Dict[str, Any],
        complexity: float,
        engine: str,
        correlation_id: str
    ) -> Strategy:
        """
        Step 5b: Formulate strategy for simple tasks.

        No spec/ADR required - direct task generation.

        Args:
            signal: Improvement signal
            context: Historical context
            complexity: Complexity score
            engine: Selected reasoning engine
            correlation_id: Unique ID

        Returns:
            Strategy without spec/ADR
        """
        return Strategy(
            priority=signal.get("priority", "NORMAL"),
            complexity=complexity,
            engine=engine,
            decision=f"Simple task, direct implementation (complexity={complexity:.2f})",
            spec_content=None,
            adr_content=None,
            tasks=[]
        )

    def _generate_spec(
        self,
        signal: Dict[str, Any],
        context: Dict[str, Any],
        correlation_id: str
    ) -> str:
        """
        Generate formal specification document.

        Args:
            signal: Improvement signal
            context: Historical context
            correlation_id: Unique ID

        Returns:
            Spec markdown content
        """
        pattern = signal.get("pattern", "unknown")
        data = signal.get("data", {})

        spec = f"""# Spec: {pattern.replace('_', ' ').title()}

**ID**: spec-{correlation_id}
**Status**: Draft
**Created**: {datetime.now().strftime('%Y-%m-%d')}

## Goal
Address {pattern} pattern detected in the system.

## Context
{data.get('message', 'No additional context')}

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
{self._format_historical_patterns(context.get('historical_patterns', []))}

## Related
- Pattern: {pattern}
- Signal ID: {signal.get('source_id', 'N/A')}
"""
        return spec

    def _generate_adr(self, signal: Dict[str, Any], correlation_id: str) -> str:
        """
        Generate Architecture Decision Record.

        Args:
            signal: Improvement signal
            correlation_id: Unique ID

        Returns:
            ADR markdown content
        """
        pattern = signal.get("pattern", "unknown")
        data = signal.get("data", {})

        # TODO: Get next ADR number from existing ADRs
        adr_num = 999  # Placeholder

        adr = f"""# ADR-{adr_num}: {pattern.replace('_', ' ').title()}

**Status**: Proposed
**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Context**: {data.get('message', 'Architectural decision required')}

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
        return adr

    def _generate_task_graph(self, strategy: Strategy, correlation_id: str) -> List[TaskSpec]:
        """
        Step 7: Generate DAG of executable tasks.

        Article II: Every code task has corresponding test task (parallel).

        Args:
            strategy: Strategic plan
            correlation_id: Unique ID

        Returns:
            List of TaskSpec with dependencies
        """
        tasks = []

        # Task 1: Code generation (no dependencies)
        code_task = TaskSpec(
            task_id=f"{correlation_id}_code",
            correlation_id=correlation_id,
            priority=strategy.priority,
            task_type="code_generation",
            sub_agent="CodeWriter",
            spec={
                "details": strategy.decision,
                "spec_content": strategy.spec_content,
                "complexity": strategy.complexity
            },
            dependencies=[]
        )
        tasks.append(code_task)

        # Task 2: Test generation (parallel with code - Article II)
        test_task = TaskSpec(
            task_id=f"{correlation_id}_test",
            correlation_id=correlation_id,
            priority=strategy.priority,
            task_type="test_generation",
            sub_agent="TestArchitect",
            spec={
                "details": f"Tests for {strategy.decision}",
                "spec_content": strategy.spec_content,
                "complexity": strategy.complexity
            },
            dependencies=[]  # Parallel with code
        )
        tasks.append(test_task)

        # Task 3: Merge (depends on both code + test)
        merge_task = TaskSpec(
            task_id=f"{correlation_id}_merge",
            correlation_id=correlation_id,
            priority=strategy.priority,
            task_type="merge",
            sub_agent="ReleaseManager",
            spec={
                "details": "Integrate code and tests, commit with constitutional compliance"
            },
            dependencies=[code_task.task_id, test_task.task_id]
        )
        tasks.append(merge_task)

        return tasks

    def _self_verify_plan(self, tasks: List[TaskSpec]) -> bool:
        """
        Step 8: Verify plan constitutional compliance.

        Checks:
        - All tasks have sub_agent assigned
        - Code tasks have corresponding test tasks (Article II)
        - Valid dependencies (no cycles, all referenced tasks exist)

        Args:
            tasks: Task graph

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        if not tasks:
            raise ValueError("Task graph is empty")

        # Check: All tasks have sub_agent
        for task in tasks:
            if not task.sub_agent or task.sub_agent.strip() == "":
                raise ValueError(f"Task {task.task_id} missing or empty sub_agent")

        # Check: Code tasks have corresponding test tasks (Article II)
        code_tasks = [t for t in tasks if t.task_type == "code_generation"]
        test_tasks = [t for t in tasks if t.task_type == "test_generation"]

        if code_tasks and not test_tasks:
            raise ValueError("Code task without corresponding test task (Article II violation)")

        # Check: Valid dependencies
        task_ids = {t.task_id for t in tasks}
        for task in tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    raise ValueError(f"Task {task.task_id} has invalid dependency: {dep} (not in task graph)")

        # Check: No circular dependencies (simple check - full DAG validation could be more robust)
        for task in tasks:
            if task.task_id in task.dependencies:
                raise ValueError(f"Circular dependency: {task.task_id} depends on itself")

        return True

    def _externalize_strategy(self, correlation_id: str, strategy: Strategy) -> str:
        """
        Step 6: Write strategy to observable file (short-term memory).

        Args:
            correlation_id: Unique ID
            strategy: Strategic plan

        Returns:
            Path to strategy file
        """
        strategy_path = self.workspace_dir / f"{correlation_id}_strategy.md"

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

        strategy_path.write_text(content)
        return str(strategy_path)

    def _cleanup_workspace(self, correlation_id: str) -> None:
        """
        Step 10: Clean workspace for stateless operation.

        Args:
            correlation_id: Unique ID
        """
        strategy_file = self.workspace_dir / f"{correlation_id}_strategy.md"
        if strategy_file.exists():
            strategy_file.unlink()

    async def _handle_planning_failure(
        self,
        correlation_id: str,
        signal: Dict[str, Any],
        error: Exception
    ) -> None:
        """
        Handle planning failures by publishing error to telemetry.

        Args:
            correlation_id: Unique ID
            signal: Original signal
            error: Exception that occurred
        """
        error_report = {
            "status": "failure",
            "correlation_id": correlation_id,
            "signal": signal,
            "error": str(error),
            "timestamp": datetime.now().isoformat()
        }

        await self.message_bus.publish(
            "telemetry_stream",
            error_report,
            priority=10,  # High priority for failures
            correlation_id=correlation_id
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get agent statistics.

        Returns:
            Stats dict
        """
        return self._stats.copy()

    # Helper methods

    def _is_architectural(self, signal: Dict[str, Any]) -> bool:
        """Check if signal requires architectural decision."""
        data = signal.get("data", {})
        keywords = data.get("keywords", [])
        return "architecture" in keywords or signal.get("pattern") == "constitutional_violation"

    def _format_historical_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """Format historical patterns for spec."""
        if not patterns:
            return "No historical patterns found."

        formatted = []
        for p in patterns[:3]:  # Top 3
            formatted.append(
                f"- {p.get('pattern_name')}: "
                f"confidence={p.get('confidence', 0):.2f}, "
                f"seen={p.get('times_seen', 0)} times"
            )
        return "\n".join(formatted)

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
        # Simplified - would query pattern_store in full implementation
        return 85

    def _priority_to_int(self, priority: str) -> int:
        """Convert priority string to integer for message bus."""
        return {"CRITICAL": 10, "HIGH": 5, "NORMAL": 0}.get(priority, 0)
