"""Task Graph models for /primeA declarative mission execution.

Constitutional Compliance:
- Article II: 100% verification (every Code task must have Test dependency)
- Article IV: Learning integration (tasks reference VectorStore patterns)
- Article V: Spec-driven development (task graph is the specification)

Memory Architecture:
- M4 Pro 48GB constraints: max 3 parallel workers with local model
- Article II Section 2.4: Hardware-aware execution
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class TaskType(str, Enum):
    """Task category for execution routing."""

    SPEC = "Spec"  # Design, architecture, specification
    CODE = "Code"  # Implementation
    TEST = "Test"  # Verification


class TaskTier(str, Enum):
    """Task complexity tier for model routing (Article IV adaptive routing)."""

    TIER_1 = "Tier 1"  # Complex (P1): gpt-5, architecture, ADRs
    TIER_2 = "Tier 2"  # Moderate (P2): gpt-4o or local
    TIER_3 = "Tier 3"  # Simple (P3): local model only (qwen3-coder)


class CheckpointType(str, Enum):
    """Checkpoint type for human review or auto-validation."""

    HUMAN_REVIEW = "human_review"
    AUTO_VALIDATE = "auto_validate"


class Task(BaseModel):
    """Atomic task unit in task graph.

    Every Code task MUST have corresponding Test task (Article II).
    """

    id: str = Field(..., description="Unique task identifier (e.g., spec_command_interface)")
    title: str = Field(..., description="Human-readable task title")
    type: TaskType = Field(..., description="Task category (Spec/Code/Test)")
    tier: TaskTier = Field(..., description="Complexity tier for model routing")
    agent: str = Field(..., description="Agent to execute (planner, coder, test_generator, etc.)")
    description: str = Field(..., description="Actionable instruction for agent")
    dependencies: list[str] = Field(
        default_factory=list, description="Task IDs that must complete first"
    )
    acceptance_criteria: list[str] = Field(
        default_factory=list, description="Verification criteria (required for Spec tasks)"
    )
    estimated_tokens: int | None = Field(
        None, description="Estimated token usage for cost calculation"
    )
    verification_target: str | None = Field(
        None, description="For Test tasks: Code task ID being verified"
    )
    result: dict[str, Any] | None = Field(
        None, description="Task execution result (e.g., files_modified, test_output)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Task metadata (e.g., spec_id, priority, tags)"
    )

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Ensure task ID is valid identifier."""
        if not v.replace("_", "").isalnum():
            raise ValueError(f"Task ID must be alphanumeric with underscores: {v}")
        return v

    @field_validator("agent")
    @classmethod
    def validate_agent_name(cls, v: str) -> str:
        """Ensure agent name is known."""
        valid_agents = {
            "planner",
            "chief_architect",
            "coder",
            "auditor",
            "test_generator",
            "quality_enforcer",
            "learning",
            "merger",
            "toolsmith",
            "summary",
        }

        if v not in valid_agents:
            raise ValueError(f"Unknown agent: {v}. Valid: {valid_agents}")

        return v

    @model_validator(mode="after")
    def validate_test_task_requirements(self) -> "Task":
        """Test tasks must have verification_target (Article II)."""
        if self.type == TaskType.TEST and not self.verification_target:
            raise ValueError(f"Test task {self.id} missing verification_target (Article II)")

        return self

    @model_validator(mode="after")
    def validate_spec_acceptance_criteria(self) -> "Task":
        """Spec tasks should have acceptance criteria (Article V)."""
        if self.type == TaskType.SPEC and not self.acceptance_criteria:
            # Warning, not error (backward compatibility)
            pass

        return self


class Phase(BaseModel):
    """Sequential phase grouping tasks.

    Phases execute sequentially, but tasks within a phase can execute in parallel
    based on dependency graph.
    """

    id: str = Field(..., description="Phase identifier (e.g., phase_1)")
    title: str = Field(..., description="Human-readable phase name")
    tasks: list[Task] = Field(..., description="Tasks in this phase")

    @field_validator("id")
    @classmethod
    def validate_phase_id(cls, v: str) -> str:
        """Ensure phase ID follows convention."""
        if not v.startswith("phase_"):
            raise ValueError(f"Phase ID must start with 'phase_': {v}")
        return v

    @field_validator("tasks")
    @classmethod
    def validate_tasks_not_empty(cls, v: list[Task]) -> list[Task]:
        """Phase must have at least one task."""
        if not v:
            raise ValueError("Phase must contain at least one task")
        return v


class Checkpoint(BaseModel):
    """Human review or auto-validation checkpoint between phases."""

    after_phase: str = Field(..., description="Phase ID to trigger after")
    type: CheckpointType = Field(..., description="Checkpoint type")
    prompt: str | None = Field(None, description="User prompt for human review checkpoints")

    @model_validator(mode="after")
    def validate_human_review_prompt(self) -> "Checkpoint":
        """Human review checkpoints should have prompt."""
        if self.type == CheckpointType.HUMAN_REVIEW and not self.prompt:
            raise ValueError("Human review checkpoint missing prompt")

        return self


class TaskGraph(BaseModel):
    """Complete mission specification as declarative task graph.

    Constitutional Compliance:
    - Article II: Every Code task must have Test dependency
    - Article V: Task graph is the specification
    - Hardware-aware: Validates max parallelism doesn't exceed memory budget
    """

    mission: str = Field(..., description="Mission title")
    leap_number: int | None = Field(None, description="Leap number for evolution tracking")
    phases: list[Phase] = Field(..., description="Sequential phases")
    checkpoints: list[Checkpoint] = Field(
        default_factory=list, description="Human review or validation checkpoints"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata (estimated_tokens, estimated_cost_usd, complexity)",
    )

    @field_validator("phases")
    @classmethod
    def validate_phases_not_empty(cls, v: list[Phase]) -> list[Phase]:
        """Task graph must have at least one phase."""
        if not v:
            raise ValueError("Task graph must contain at least one phase")
        return v

    @model_validator(mode="after")
    def validate_code_test_dependencies(self) -> "TaskGraph":
        """Every Code task must have Test dependency (Article II)."""
        all_tasks = [task for phase in self.phases for task in phase.tasks]
        code_tasks = [t for t in all_tasks if t.type == TaskType.CODE]
        test_tasks = [t for t in all_tasks if t.type == TaskType.TEST]

        for code_task in code_tasks:
            # Article VI: TDD workflow - Test tasks come BEFORE Code tasks
            # Code task must depend on a Test task that verifies it
            has_test = any(
                test.id in code_task.dependencies and test.verification_target == code_task.id
                for test in test_tasks
            )

            if not has_test:
                raise ValueError(
                    f"Code task {code_task.id} missing Test dependency (Article II violation). "
                    f"TDD requires Test task BEFORE Code task with verification_target='{code_task.id}'"
                )

        return self

    @model_validator(mode="after")
    def validate_no_circular_dependencies(self) -> "TaskGraph":
        """Ensure task graph is a DAG (no circular dependencies)."""
        all_tasks = [task for phase in self.phases for task in phase.tasks]
        task_map = {t.id: t for t in all_tasks}

        def has_cycle(task_id: str, visited: set[str], rec_stack: set[str]) -> bool:
            """DFS to detect cycles."""
            visited.add(task_id)
            rec_stack.add(task_id)

            task = task_map.get(task_id)
            if not task:
                return False

            for dep_id in task.dependencies:
                if dep_id not in visited:
                    if has_cycle(dep_id, visited, rec_stack):
                        return True
                elif dep_id in rec_stack:
                    return True

            rec_stack.remove(task_id)
            return False

        visited: set[str] = set()
        for task in all_tasks:
            if task.id not in visited:
                if has_cycle(task.id, visited, set()):
                    raise ValueError(f"Circular dependency detected in task graph (task {task.id})")

        return self

    @model_validator(mode="after")
    def validate_all_dependencies_exist(self) -> "TaskGraph":
        """Ensure all task dependencies reference valid task IDs."""
        all_task_ids = {task.id for phase in self.phases for task in phase.tasks}

        for phase in self.phases:
            for task in phase.tasks:
                for dep_id in task.dependencies:
                    if dep_id not in all_task_ids:
                        raise ValueError(f"Task {task.id} depends on non-existent task {dep_id}")

        return self

    @model_validator(mode="after")
    def validate_checkpoint_phases_exist(self) -> "TaskGraph":
        """Ensure checkpoint after_phase references valid phase IDs."""
        phase_ids = {phase.id for phase in self.phases}

        for checkpoint in self.checkpoints:
            if checkpoint.after_phase not in phase_ids:
                raise ValueError(
                    f"Checkpoint references non-existent phase: {checkpoint.after_phase}"
                )

        return self

    def all_tasks(self) -> list[Task]:
        """Get flat list of all tasks across phases."""
        return [task for phase in self.phases for task in phase.tasks]

    def topological_sort(self) -> list[list[Task]]:
        """Sort tasks into parallelizable layers.

        Returns:
            List of task layers, where each layer can execute in parallel.

        Raises:
            ValueError: If circular dependency detected (should not happen after validation).
        """
        all_tasks = self.all_tasks()
        task_map = {t.id: t for t in all_tasks}

        # Calculate in-degree (number of dependencies)
        in_degree = {t.id: len(t.dependencies) for t in all_tasks}

        layers = []
        remaining = set(t.id for t in all_tasks)

        while remaining:
            # Find tasks with no remaining dependencies
            ready = [tid for tid in remaining if in_degree[tid] == 0]

            if not ready:
                raise ValueError("Circular dependency detected during topological sort")

            layers.append([task_map[tid] for tid in ready])

            # Remove ready tasks and update in-degrees
            for tid in ready:
                remaining.remove(tid)

                # Decrement in-degree for dependent tasks
                for other_tid in remaining:
                    if tid in task_map[other_tid].dependencies:
                        in_degree[other_tid] -= 1

        return layers

    def estimate_cost(self) -> float:
        """Estimate execution cost in USD based on task tiers.

        Assumes:
        - Tier 1 (P1): gpt-5 @ $4/1M tokens
        - Tier 2 (P2/P3): 60% local (free), 40% gpt-4o @ $1.5/1M tokens
        """
        tier1_tasks = [t for t in self.all_tasks() if t.tier == TaskTier.TIER_1]
        tier2_tasks = [t for t in self.all_tasks() if t.tier == TaskTier.TIER_2]

        # Tier 1: All gpt-5
        tier1_tokens = sum(t.estimated_tokens or 3000 for t in tier1_tasks)
        tier1_cost = (tier1_tokens / 1_000_000) * 4.0

        # Tier 2: 60% local (free), 40% gpt-4o
        tier2_tokens = sum(t.estimated_tokens or 3000 for t in tier2_tasks)
        tier2_cloud_tokens = tier2_tokens * 0.4  # 40% go to cloud
        tier2_cost = (tier2_cloud_tokens / 1_000_000) * 1.5

        return tier1_cost + tier2_cost

    def to_ascii_tree(self) -> str:
        """Generate ASCII tree representation of task graph."""
        lines = [f"Mission: {self.mission}"]

        if self.leap_number:
            lines.append(f"Leap: {self.leap_number}")

        lines.append("")

        for phase in self.phases:
            lines.append(f"📦 {phase.title}")

            for i, task in enumerate(phase.tasks):
                is_last = i == len(phase.tasks) - 1
                prefix = "└─" if is_last else "├─"

                deps_str = (
                    f" (depends on: {', '.join(task.dependencies)})" if task.dependencies else ""
                )
                lines.append(f"   {prefix} {task.type.value} {task.title}{deps_str}")

        if self.checkpoints:
            lines.append("")
            lines.append("🚦 Checkpoints:")
            for checkpoint in self.checkpoints:
                lines.append(f"   - {checkpoint.type.value} after {checkpoint.after_phase}")

        return "\n".join(lines)

    def to_mermaid(self) -> str:
        """Generate Mermaid diagram representation."""
        lines = ["graph TD"]

        # Add tasks with styling
        for phase in self.phases:
            lines.append(f'    subgraph {phase.id}["{phase.title}"]')

            for task in phase.tasks:
                # Node styling by tier
                style_class = "tier1" if task.tier == TaskTier.TIER_1 else "tier2"
                node_label = f"{task.type.value}: {task.title}"
                lines.append(f'        {task.id}["{node_label}"]:::{style_class}')

                # Edges for dependencies
                for dep_id in task.dependencies:
                    lines.append(f"        {dep_id} --> {task.id}")

            lines.append("    end")

        # Add styling classes
        lines.append("")
        lines.append("    classDef tier1 fill:#cce5ff,stroke:#0066cc")
        lines.append("    classDef tier2 fill:#d4edda,stroke:#28a745")

        return "\n".join(lines)


class ValidationResult(BaseModel):
    """Result of task graph validation."""

    valid: bool = Field(..., description="Whether task graph is valid")
    violations: list[str] = Field(default_factory=list, description="List of validation violations")
    warnings: list[str] = Field(default_factory=list, description="Non-blocking warnings")

    def __str__(self) -> str:
        if self.valid:
            status = "✅ VALID"
        else:
            status = "❌ INVALID"

        lines = [f"{status} Task Graph Validation"]

        if self.violations:
            lines.append("\nViolations:")
            for v in self.violations:
                lines.append(f"  - {v}")

        if self.warnings:
            lines.append("\nWarnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")

        return "\n".join(lines)


class ExecutionResult(BaseModel):
    """Result of task graph execution."""

    graph: TaskGraph = Field(..., description="Executed task graph")
    completed: int = Field(..., description="Number of completed tasks")
    failed: int = Field(..., description="Number of failed tasks")
    skipped: int = Field(..., description="Number of skipped tasks")
    total_time: str = Field(..., description="Total execution time (HH:MM:SS)")
    layers: int = Field(..., description="Number of parallel layers executed")
    max_concurrency: int = Field(..., description="Maximum concurrent workers used")
    peak_memory_gb: float = Field(..., description="Peak memory usage in GB")
    modified_files: list[str] = Field(default_factory=list, description="Files modified")
    created_files: list[str] = Field(default_factory=list, description="Files created")
    tests_written: int = Field(0, description="Number of tests written")
    tests_passing: int = Field(0, description="Number of tests passing")
    model_usage: dict[str, int] = Field(
        default_factory=dict, description="Tasks executed per model"
    )
    cost_by_model: dict[str, float] = Field(default_factory=dict, description="Cost per model")
    total_cost: float = Field(0.0, description="Total execution cost in USD")
    cost_savings: float = Field(0.0, description="Cost savings vs all-gpt-5")

    @property
    def total(self) -> int:
        """Total number of tasks."""
        return self.completed + self.failed + self.skipped

    @property
    def count_by_type(self) -> dict[str, int]:
        """Count tasks by type."""
        counts = {"Spec": 0, "Code": 0, "Test": 0}
        for task in self.graph.all_tasks():
            counts[task.type.value] += 1
        return counts

    @property
    def count_by_tier(self) -> dict[str, int]:
        """Count tasks by tier."""
        counts = {"Tier 1": 0, "Tier 2": 0}
        for task in self.graph.all_tasks():
            counts[task.tier.value] += 1
        return counts


class ReflectionReport(BaseModel):
    """Post-execution reflection and evolution report (Article IV)."""

    patterns_extracted: int = Field(..., description="Number of patterns extracted to VectorStore")
    adr_generated: str | None = Field(None, description="Path to generated ADR")
    next_mission_proposed: str = Field(..., description="Title of proposed next mission")
    next_mission_motivation: str = Field(..., description="Why next mission is necessary")
    gaps_identified: list[dict[str, str]] = Field(
        default_factory=list, description="Capability gaps found during execution"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(), description="Reflection timestamp"
    )

    @property
    def patterns(self) -> list[dict[str, str]]:
        """Get extracted patterns (placeholder for actual implementation)."""
        # In real implementation, load from VectorStore
        return []
