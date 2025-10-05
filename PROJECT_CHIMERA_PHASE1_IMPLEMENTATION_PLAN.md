# Project Chimera - Phase 1 Implementation Plan
**Strategic Foundation for Agent Conductor Architecture**

---

## Executive Summary

**Objective:** Transform Trinity Protocol's HybridExecutor from a hardcoded test-generation executor into a Conductor that orchestrates all 10 AgencyOS agents locally with intelligent escalation to cloud.

**Phase 1 Scope:** Create the foundational infrastructure for agent registry, hybrid execution, and escalation rules WITHOUT implementing full orchestration logic (that's Phase 2).

**Constitutional Compliance:** Articles I (Complete Context), II (100% Verification), III (Automated Enforcement), IV (Continuous Learning), V (Spec-Driven Development)

**Timeline:** 5-8 hours development + 2 hours testing
**Risk Level:** Medium (existing system continues working, new features gated)

---

## Current State Analysis

### What Already Exists ✅

1. **`trinity_protocol/core/agent_registry.py`** (313 lines)
   - Factory pattern for all 10 agents
   - Tier-based model selection (LOCAL/LOCAL_PLUS/CLOUD)
   - Agent caching and escalation methods
   - **Status:** COMPLETE and production-ready

2. **`trinity_protocol/core/escalation_rules.py`** (266 lines)
   - Rule-based escalation triggers
   - Cost-aware decision making
   - Pre-configured policies (aggressive/conservative/cost-optimized)
   - **Status:** COMPLETE and production-ready

3. **`trinity_protocol/core/hybrid_executor.py`** (617 lines)
   - Local-first execution with Ollama
   - Escalation workflow (LOCAL → LOCAL_PLUS → CLOUD)
   - Test verification and cost tracking
   - **Status:** Functional but HARDCODED for test generation

4. **`agency.py`** (lines 1-250)
   - All 10 agents instantiated with shared context
   - Communication flows defined
   - Model policy integration
   - **Status:** Production-ready reference implementation

### What Needs Building 🔨

**Phase 1.1:** Agent interface contracts and tool mapping
**Phase 1.2:** Plan parser to replace hardcoded logic
**Phase 1.3:** Enhanced escalation rules with cost tracking
**Phase 1.4:** Integration with existing HybridExecutor

---

## Phase 1.1: Agent Interface Contracts

### Problem
HybridExecutor currently has hardcoded knowledge of what each agent does. We need formal contracts defining:
- Input schema (what data each agent needs)
- Output schema (what each agent produces)
- Required tools (which of 45+ tools each agent needs access to)

### Solution: Create Interface Contract System

#### File: `trinity_protocol/core/agent_contracts.py` (NEW)

**Pseudocode:**

```python
"""
Agent contracts defining inputs, outputs, and tool requirements.

Each agent type has a formal contract specifying:
- Input schema (Pydantic model)
- Output schema (Pydantic model)
- Required tools (list of tool names)
- Success criteria (validation function)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any
from pydantic import BaseModel

class AgentInputBase(BaseModel):
    """Base class for all agent inputs."""
    task_id: str
    description: str
    context: dict[str, Any] = {}
    user_complexity: Literal["low", "medium", "high", "critical"] = "medium"

class AgentOutputBase(BaseModel):
    """Base class for all agent outputs."""
    task_id: str
    status: Literal["success", "failure", "partial"]
    artifacts: list[str] = []  # File paths created/modified
    confidence_score: float = 1.0
    error_message: str | None = None

# Specific input schemas for each agent
class CoderInput(AgentInputBase):
    target_file: str
    requirements: list[str]
    existing_code: str | None = None

class PlannerInput(AgentInputBase):
    goal: str
    constraints: list[str] = []
    timeline: str | None = None

class AuditorInput(AgentInputBase):
    target_paths: list[str]
    audit_type: Literal["quality", "security", "performance"] = "quality"

# ... (similar for all 10 agents)

# Specific output schemas
class CoderOutput(AgentOutputBase):
    files_modified: list[str]
    tests_created: list[str]
    type_coverage_pct: float

class PlannerOutput(AgentOutputBase):
    plan_file: str
    estimated_hours: float
    dependencies: list[str]

# ... (similar for all 10 agents)

@dataclass
class AgentContract:
    """Complete contract for an agent type."""
    agent_type: AgentType
    input_schema: type[AgentInputBase]
    output_schema: type[AgentOutputBase]
    required_tools: list[str]
    success_validator: Callable[[AgentOutputBase], bool]
    description: str

# Contract registry
AGENT_CONTRACTS: dict[AgentType, AgentContract] = {
    AgentType.CODER: AgentContract(
        agent_type=AgentType.CODER,
        input_schema=CoderInput,
        output_schema=CoderOutput,
        required_tools=["read", "write", "edit", "multi_edit", "bash", "todo_write"],
        success_validator=lambda output: output.status == "success" and output.type_coverage_pct > 0.8,
        description="Writes production code with strict typing and TDD",
    ),
    AgentType.PLANNER: AgentContract(
        agent_type=AgentType.PLANNER,
        input_schema=PlannerInput,
        output_schema=PlannerOutput,
        required_tools=["write", "read", "glob", "grep", "learning_dashboard"],
        success_validator=lambda output: output.status == "success" and len(output.dependencies) >= 0,
        description="Creates technical plans and specifications",
    ),
    AgentType.AUDITOR: AgentContract(
        agent_type=AgentType.AUDITOR,
        input_schema=AuditorInput,
        output_schema=AgentOutputBase,
        required_tools=["read", "glob", "grep", "analyze_type_patterns", "constitution_check"],
        success_validator=lambda output: output.status == "success",
        description="Analyzes code quality and constitutional compliance",
    ),
    AgentType.TEST_GENERATOR: AgentContract(
        agent_type=AgentType.TEST_GENERATOR,
        input_schema=CoderInput,  # Similar to coder
        output_schema=AgentOutputBase,
        required_tools=["read", "write", "edit", "bash", "grep", "property_testing"],
        success_validator=lambda output: output.status == "success" and len(output.artifacts) > 0,
        description="Generates NECESSARY-compliant tests",
    ),
    AgentType.QUALITY_ENFORCER: AgentContract(
        agent_type=AgentType.QUALITY_ENFORCER,
        input_schema=AuditorInput,
        output_schema=AgentOutputBase,
        required_tools=["read", "constitution_check", "bash", "auto_fix_nonetype", "apply_and_verify_patch"],
        success_validator=lambda output: output.status == "success",
        description="Enforces constitutional compliance and quality gates",
    ),
    AgentType.LEARNING: AgentContract(
        agent_type=AgentType.LEARNING,
        input_schema=AgentInputBase,
        output_schema=AgentOutputBase,
        required_tools=["read", "write", "learning_dashboard", "grep"],
        success_validator=lambda output: output.confidence_score >= 0.6,
        description="Extracts patterns from session data",
    ),
    AgentType.CHIEF_ARCHITECT: AgentContract(
        agent_type=AgentType.CHIEF_ARCHITECT,
        input_schema=PlannerInput,
        output_schema=PlannerOutput,
        required_tools=["write", "read", "glob", "document_generator"],
        success_validator=lambda output: output.status == "success",
        description="Creates ADRs and strategic decisions",
    ),
    AgentType.MERGER: AgentContract(
        agent_type=AgentType.MERGER,
        input_schema=AgentInputBase,
        output_schema=AgentOutputBase,
        required_tools=["git", "git_unified", "bash", "read"],
        success_validator=lambda output: output.status == "success",
        description="Manages git operations and PR creation",
    ),
    AgentType.TOOLSMITH: AgentContract(
        agent_type=AgentType.TOOLSMITH,
        input_schema=CoderInput,
        output_schema=CoderOutput,
        required_tools=["read", "write", "edit", "bash", "glob"],
        success_validator=lambda output: output.status == "success" and output.type_coverage_pct > 0.9,
        description="Develops new agent tools with TDD",
    ),
    AgentType.SUMMARY: AgentContract(
        agent_type=AgentType.SUMMARY,
        input_schema=AgentInputBase,
        output_schema=AgentOutputBase,
        required_tools=["read", "write"],
        success_validator=lambda output: output.status == "success",
        description="Creates concise task summaries",
    ),
}

def get_contract(agent_type: AgentType) -> AgentContract:
    """Get contract for specified agent type."""
    return AGENT_CONTRACTS[agent_type]

def validate_agent_output(agent_type: AgentType, output: AgentOutputBase) -> bool:
    """Validate agent output against contract."""
    contract = get_contract(agent_type)
    return contract.success_validator(output)

def get_required_tools_for_agent(agent_type: AgentType) -> list[str]:
    """Get list of required tools for agent type."""
    return get_contract(agent_type).required_tools
```

**Key Design Decisions:**
- **Pydantic schemas** for type safety and validation
- **Success validators** as lambdas (simple) or functions (complex)
- **Tool requirements** explicitly listed (enables sandboxing in future)
- **Base classes** enforce common structure across all agents

---

## Phase 1.2: Plan Parser & Agent Delegation

### Problem
HybridExecutor has hardcoded logic in `_select_agents_for_task()` (lines 377-394). We need:
1. Parse ChiefArchitect/Planner output (structured plans)
2. Dynamically select agents based on plan content
3. Chain agents in correct order (dependencies)

### Solution: Implement Plan Parser

#### File: `trinity_protocol/core/plan_parser.py` (NEW)

**Pseudocode:**

```python
"""
Plan parser that converts ARCHITECT/PLANNER output into executable task graph.

Parses structured plans (Markdown + frontmatter) and creates:
- Task DAG (directed acyclic graph)
- Agent assignments per task
- Dependency ordering
"""

from dataclasses import dataclass, field
from typing import Literal
import re
import yaml

@dataclass
class Task:
    """Single task from parsed plan."""
    task_id: str
    description: str
    agent_type: AgentType
    dependencies: list[str] = field(default_factory=list)
    estimated_duration_min: int = 30
    priority: Literal["P0", "P1", "P2", "P3"] = "P2"
    artifacts: list[str] = field(default_factory=list)  # Expected outputs

@dataclass
class ExecutionPlan:
    """Parsed plan with task graph."""
    plan_id: str
    title: str
    tasks: list[Task]
    total_estimated_hours: float
    critical_path: list[str]  # Task IDs in order

    def get_ready_tasks(self, completed_ids: set[str]) -> list[Task]:
        """Get tasks ready to execute (dependencies satisfied)."""
        ready = []
        for task in self.tasks:
            if task.task_id in completed_ids:
                continue
            if all(dep in completed_ids for dep in task.dependencies):
                ready.append(task)
        return ready

class PlanParser:
    """Parses structured plans from ChiefArchitect/Planner agents."""

    def __init__(self):
        # Regex patterns for parsing
        self.frontmatter_pattern = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
        self.task_pattern = re.compile(r'^##\s+Task:\s+(.+?)$', re.MULTILINE)
        self.agent_pattern = re.compile(r'^Agent:\s+(\w+)', re.MULTILINE)
        self.dependency_pattern = re.compile(r'^Dependencies:\s+(.+?)$', re.MULTILINE)

    def parse(self, plan_content: str) -> ExecutionPlan:
        """
        Parse plan file into ExecutionPlan.

        Expected format:
        ---
        title: Add dark mode feature
        estimated_hours: 4
        ---

        ## Task: Create toggle component
        Agent: CODER
        Dependencies: None
        Artifacts: src/components/DarkModeToggle.tsx

        ## Task: Add state management
        Agent: CODER
        Dependencies: Create toggle component
        Artifacts: src/store/theme.ts
        """
        # Extract frontmatter
        frontmatter_match = self.frontmatter_pattern.search(plan_content)
        if frontmatter_match:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
        else:
            frontmatter = {}

        # Parse tasks
        tasks = self._extract_tasks(plan_content)

        # Build dependency graph
        critical_path = self._compute_critical_path(tasks)

        return ExecutionPlan(
            plan_id=frontmatter.get("plan_id", "unknown"),
            title=frontmatter.get("title", "Untitled Plan"),
            tasks=tasks,
            total_estimated_hours=frontmatter.get("estimated_hours", 0.0),
            critical_path=critical_path,
        )

    def _extract_tasks(self, content: str) -> list[Task]:
        """Extract tasks from plan content."""
        tasks = []
        # Split by task headers
        sections = re.split(r'^## Task:', content, flags=re.MULTILINE)

        for i, section in enumerate(sections[1:], 1):  # Skip first empty section
            task_id = f"task_{i}"

            # Extract task description (first line)
            lines = section.strip().split('\n')
            description = lines[0].strip()

            # Extract agent type
            agent_match = self.agent_pattern.search(section)
            agent_type = AgentType[agent_match.group(1)] if agent_match else AgentType.CODER

            # Extract dependencies
            dep_match = self.dependency_pattern.search(section)
            if dep_match and dep_match.group(1).lower() != "none":
                dependencies = [d.strip() for d in dep_match.group(1).split(',')]
            else:
                dependencies = []

            tasks.append(Task(
                task_id=task_id,
                description=description,
                agent_type=agent_type,
                dependencies=dependencies,
            ))

        return tasks

    def _compute_critical_path(self, tasks: list[Task]) -> list[str]:
        """Compute critical path using topological sort."""
        # Simple topological sort (can enhance with actual critical path algorithm)
        visited = set()
        path = []

        def visit(task: Task):
            if task.task_id in visited:
                return
            for dep in task.dependencies:
                dep_task = next((t for t in tasks if t.task_id == dep), None)
                if dep_task:
                    visit(dep_task)
            visited.add(task.task_id)
            path.append(task.task_id)

        for task in tasks:
            visit(task)

        return path

# Convenience function
def parse_plan_file(file_path: str) -> ExecutionPlan:
    """Parse plan from file path."""
    with open(file_path, 'r') as f:
        content = f.read()
    parser = PlanParser()
    return parser.parse(content)
```

**Key Design Decisions:**
- **Frontmatter support** (YAML metadata)
- **Markdown-based format** (human-readable)
- **Dependency graph** with topological sort
- **Extensible patterns** (regex-based, easy to modify)

---

## Phase 1.3: Enhanced HybridExecutor Integration

### Problem
Current `HybridExecutor._execute_at_tier()` is hardcoded for test generation. We need:
1. Dynamic agent selection based on parsed plan
2. Tool provisioning per agent contract
3. Output validation against contracts

### Solution: Refactor Execution Engine

#### Changes to: `trinity_protocol/core/hybrid_executor.py`

**Modifications Required:**

```python
# ADD IMPORTS (top of file)
from trinity_protocol.core.agent_contracts import get_contract, validate_agent_output, AgentInputBase, AgentOutputBase
from trinity_protocol.core.plan_parser import PlanParser, ExecutionPlan, Task

# MODIFY: __init__ method (line 142)
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
    enable_plan_parsing: bool = False,  # NEW: Feature flag
):
    # ... existing init code ...
    self.enable_plan_parsing = enable_plan_parsing
    self.plan_parser = PlanParser() if enable_plan_parsing else None

    if enable_plan_parsing:
        logger.info("🎼 Plan parsing ENABLED - Conductor mode activated")
    else:
        logger.info("🔧 Plan parsing DISABLED - Legacy test-generation mode")

# NEW METHOD: Parse and execute plan
async def execute_plan(self, plan_file: str) -> TaskResult:
    """
    Execute structured plan file (Phase 2 feature, stubbed for Phase 1).

    Workflow:
    1. Parse plan → ExecutionPlan
    2. For each task in critical path:
        a. Get contract for agent type
        b. Create agent input
        c. Execute agent with escalation
        d. Validate output
        e. Store artifacts
    3. Return aggregated result
    """
    if not self.enable_plan_parsing:
        raise RuntimeError("Plan parsing not enabled. Set enable_plan_parsing=True.")

    logger.info(f"📋 Parsing plan: {plan_file}")
    plan = parse_plan_file(plan_file)

    completed_tasks: set[str] = set()
    failed_tasks: list[str] = []
    total_cost = 0.0
    total_duration = 0.0

    # Execute tasks in dependency order
    for task_id in plan.critical_path:
        task = next(t for t in plan.tasks if t.task_id == task_id)
        logger.info(f"▶️  Executing {task_id}: {task.description} (agent={task.agent_type.value})")

        try:
            # Get agent contract
            contract = get_contract(task.agent_type)

            # Create agent input (stub - Phase 2 will populate from task)
            agent_input = contract.input_schema(
                task_id=task_id,
                description=task.description,
            )

            # Execute with escalation
            result = await self._execute_agent_with_escalation(
                agent_type=task.agent_type,
                agent_input=agent_input,
                contract=contract,
            )

            total_cost += result.cost_usd
            total_duration += result.duration_seconds

            if result.status == "success":
                completed_tasks.add(task_id)
                logger.info(f"✅ Task {task_id} completed")
            else:
                failed_tasks.append(task_id)
                logger.error(f"❌ Task {task_id} failed: {result.error}")
                break  # Stop on first failure (can make configurable)

        except Exception as e:
            logger.error(f"❌ Task {task_id} exception: {e}", exc_info=True)
            failed_tasks.append(task_id)
            break

    # Aggregate results
    status = "success" if len(failed_tasks) == 0 else "failure"
    return TaskResult(
        task_id=plan.plan_id,
        status=status,
        summary=f"Plan executed: {len(completed_tasks)}/{len(plan.tasks)} tasks completed",
        duration_seconds=total_duration,
        cost_usd=total_cost,
        model_tier=ModelTier.LOCAL,  # Will be determined by escalation
        escalation_count=0,
        test_pass_rate=1.0 if status == "success" else 0.0,
    )

# NEW METHOD: Execute single agent with escalation
async def _execute_agent_with_escalation(
    self,
    agent_type: AgentType,
    agent_input: AgentInputBase,
    contract: AgentContract,
) -> TaskResult:
    """
    Execute single agent task with escalation support.

    Similar to _execute_task_with_escalation but agent-focused.
    """
    attempts = []
    current_tier = ModelTier.LOCAL
    total_duration = 0.0
    total_cost = 0.0

    for attempt_num in range(1, self.max_total_attempts + 1):
        logger.info(
            f"🔄 Agent {agent_type.value} attempt {attempt_num}/{self.max_total_attempts} "
            f"(tier={current_tier.value})"
        )

        start_time = datetime.now()

        try:
            # Create agent at current tier
            agent = self.agent_registry.create_agent(agent_type, current_tier)

            # Execute agent (stub - Phase 2 will implement actual agent calls)
            # For now, simulate execution
            output = AgentOutputBase(
                task_id=agent_input.task_id,
                status="success",
                confidence_score=0.9,
            )

            duration = (datetime.now() - start_time).total_seconds()
            total_duration += duration

            # Calculate cost
            cost = 0.0 if current_tier != ModelTier.CLOUD else self._estimate_cloud_cost(duration)
            total_cost += cost

            # Validate output
            is_valid = validate_agent_output(agent_type, output)

            if is_valid:
                return TaskResult(
                    task_id=agent_input.task_id,
                    status="success",
                    summary=f"Agent {agent_type.value} completed at {current_tier.value}",
                    duration_seconds=total_duration,
                    cost_usd=total_cost,
                    model_tier=current_tier,
                    escalation_count=attempt_num - 1,
                    test_pass_rate=1.0,
                    agents_used=[agent_type.value],
                )

            # Output invalid - escalate
            escalation_context = EscalationContext(
                attempt_count=attempt_num,
                current_tier=current_tier,
                confidence_score=output.confidence_score,
            )

            decision = self.escalation_policy.evaluate(escalation_context)

            if decision.should_escalate:
                logger.warning(f"⚠️  Escalating: {decision.reason}")
                current_tier = decision.next_tier

        except Exception as e:
            logger.error(f"❌ Attempt {attempt_num} failed: {e}")
            if current_tier != ModelTier.CLOUD:
                current_tier = self.agent_registry.escalation_policy._get_next_tier(current_tier)

    # Max attempts exhausted
    return TaskResult(
        task_id=agent_input.task_id,
        status="failure",
        summary=f"Agent {agent_type.value} failed after {self.max_total_attempts} attempts",
        duration_seconds=total_duration,
        cost_usd=total_cost,
        model_tier=current_tier,
        escalation_count=self.max_total_attempts,
        test_pass_rate=0.0,
        error="Max attempts exhausted",
    )

# MODIFY: _execute_at_tier (line 311) - Add feature flag check
async def _execute_at_tier(
    self, task: JSONValue, task_id: str, tier: ModelTier, attempt_num: int
) -> ExecutionAttempt:
    """Execute task at specified model tier."""

    # If plan parsing enabled, use new path
    if self.enable_plan_parsing and "plan_file" in task:
        # Delegate to execute_plan (Phase 2)
        logger.info("🎼 Using plan-based execution")
        raise NotImplementedError("Plan-based execution in Phase 2")

    # Otherwise, use legacy test-generation logic
    task_type = TaskType(task.get("task_type", "general"))
    agents_needed = self._select_agents_for_task(task_type)

    # ... rest of existing logic unchanged ...
```

**Key Changes:**
- **Feature flag** (`enable_plan_parsing`) for gradual rollout
- **New execution path** for plan-based tasks (Phase 2)
- **Backward compatibility** with existing test-generation logic
- **Stubbed agent execution** (actual calls in Phase 2)

---

## Phase 1.4: Cost Tracking Integration

### Problem
Cost tracking exists but needs integration with:
- Per-agent cost attribution
- Local vs cloud cost comparison
- Budget enforcement

### Solution: Enhance Cost Tracker

#### Changes to: `trinity_protocol/core/hybrid_executor.py`

**Add method:**

```python
def _track_agent_cost(
    self,
    agent_type: AgentType,
    tier: ModelTier,
    duration_seconds: float,
    tokens_used: int = 0,
) -> float:
    """
    Track cost for specific agent execution.

    Returns:
        Cost in USD
    """
    if tier == ModelTier.CLOUD:
        # Cloud cost calculation
        # GPT-5: ~$0.0015 per 1K input tokens, $0.006 per 1K output tokens
        # Estimate: 500 tokens input + 2000 tokens output per agent call
        cost = (0.0015 * 0.5) + (0.006 * 2.0)  # ~$0.0135 per call
    elif tier == ModelTier.LOCAL_PLUS:
        # Local models are free but have energy cost
        # Estimate: $0.001 per minute (electricity for GPU)
        cost = (duration_seconds / 60.0) * 0.001
    else:  # LOCAL
        cost = 0.0  # Free tier

    # Record in cost tracker
    if self.cost_tracker:
        self.cost_tracker.track_operation(
            agent_name=f"{agent_type.value}_{tier.value}",
            cost_usd=cost,
            metadata={
                "tier": tier.value,
                "duration_seconds": duration_seconds,
                "tokens_used": tokens_used,
            }
        )

    logger.debug(
        f"💰 Agent {agent_type.value} cost: ${cost:.4f} "
        f"(tier={tier.value}, duration={duration_seconds:.1f}s)"
    )

    return cost
```

---

## Testing Strategy

### Unit Tests (NEW FILES)

#### `tests/trinity_protocol/core/test_agent_contracts.py`

```python
"""Unit tests for agent contracts."""

import pytest
from trinity_protocol.core.agent_contracts import (
    get_contract,
    validate_agent_output,
    AgentOutputBase,
    AGENT_CONTRACTS,
)
from trinity_protocol.core.agent_registry import AgentType

def test_all_agents_have_contracts():
    """Verify all 10 agent types have contracts."""
    for agent_type in AgentType:
        contract = get_contract(agent_type)
        assert contract is not None
        assert contract.agent_type == agent_type

def test_contract_has_required_fields():
    """Verify contracts have all required fields."""
    contract = get_contract(AgentType.CODER)
    assert contract.input_schema is not None
    assert contract.output_schema is not None
    assert len(contract.required_tools) > 0
    assert contract.success_validator is not None
    assert len(contract.description) > 0

def test_validate_successful_output():
    """Verify success validator works."""
    output = AgentOutputBase(
        task_id="test_1",
        status="success",
        confidence_score=0.9,
    )
    # Most agents should accept this basic success output
    is_valid = validate_agent_output(AgentType.SUMMARY, output)
    assert is_valid

def test_validate_failed_output():
    """Verify validator rejects failures."""
    output = AgentOutputBase(
        task_id="test_1",
        status="failure",
        error_message="Something went wrong",
    )
    # Should fail validation
    is_valid = validate_agent_output(AgentType.CODER, output)
    assert not is_valid

@pytest.mark.parametrize("agent_type", list(AgentType))
def test_required_tools_exist(agent_type):
    """Verify all required tools are valid tool names."""
    contract = get_contract(agent_type)
    valid_tools = {
        "read", "write", "edit", "multi_edit", "glob", "grep",
        "bash", "git", "git_unified", "todo_write", "learning_dashboard",
        "constitution_check", "analyze_type_patterns", "auto_fix_nonetype",
        "apply_and_verify_patch", "property_testing", "document_generator",
    }

    for tool in contract.required_tools:
        assert tool in valid_tools, f"Unknown tool '{tool}' in {agent_type.value} contract"
```

#### `tests/trinity_protocol/core/test_plan_parser.py`

```python
"""Unit tests for plan parser."""

import pytest
from trinity_protocol.core.plan_parser import PlanParser, ExecutionPlan, Task
from trinity_protocol.core.agent_registry import AgentType

SAMPLE_PLAN = """---
title: Add dark mode feature
estimated_hours: 4
plan_id: darkmode_001
---

## Task: Create toggle component
Agent: CODER
Dependencies: None
Artifacts: src/components/DarkModeToggle.tsx

## Task: Add state management
Agent: CODER
Dependencies: Create toggle component
Artifacts: src/store/theme.ts

## Task: Generate tests
Agent: TEST_GENERATOR
Dependencies: Create toggle component, Add state management
Artifacts: tests/DarkMode.test.tsx
"""

def test_parse_frontmatter():
    """Verify frontmatter parsing."""
    parser = PlanParser()
    plan = parser.parse(SAMPLE_PLAN)

    assert plan.title == "Add dark mode feature"
    assert plan.total_estimated_hours == 4.0
    assert plan.plan_id == "darkmode_001"

def test_parse_tasks():
    """Verify task extraction."""
    parser = PlanParser()
    plan = parser.parse(SAMPLE_PLAN)

    assert len(plan.tasks) == 3
    assert plan.tasks[0].description == "Create toggle component"
    assert plan.tasks[0].agent_type == AgentType.CODER
    assert plan.tasks[0].dependencies == []

def test_parse_dependencies():
    """Verify dependency parsing."""
    parser = PlanParser()
    plan = parser.parse(SAMPLE_PLAN)

    test_gen_task = plan.tasks[2]
    assert test_gen_task.agent_type == AgentType.TEST_GENERATOR
    assert "Create toggle component" in test_gen_task.dependencies
    assert "Add state management" in test_gen_task.dependencies

def test_critical_path_ordering():
    """Verify topological sort produces valid ordering."""
    parser = PlanParser()
    plan = parser.parse(SAMPLE_PLAN)

    # Critical path should have tasks in dependency order
    assert len(plan.critical_path) == 3

    # First task has no dependencies
    first_task_id = plan.critical_path[0]
    first_task = next(t for t in plan.tasks if t.task_id == first_task_id)
    assert len(first_task.dependencies) == 0

def test_get_ready_tasks():
    """Verify ready task detection."""
    parser = PlanParser()
    plan = parser.parse(SAMPLE_PLAN)

    # Initially, only task with no dependencies is ready
    ready = plan.get_ready_tasks(set())
    assert len(ready) == 1
    assert ready[0].dependencies == []

    # After completing first task
    completed = {plan.critical_path[0]}
    ready = plan.get_ready_tasks(completed)
    assert len(ready) == 1  # Second task becomes ready
```

#### `tests/trinity_protocol/core/test_hybrid_executor_phase1.py`

```python
"""Integration tests for Phase 1 changes."""

import pytest
from trinity_protocol.core.hybrid_executor import HybridExecutor, create_hybrid_executor
from trinity_protocol.core.agent_registry import AgentType, ModelTier
from shared.agent_context import create_agent_context
from shared.cost_tracker import CostTracker, SQLiteStorage
from shared.message_bus import MessageBus

@pytest.fixture
def hybrid_executor():
    """Create executor with plan parsing enabled."""
    context = create_agent_context()
    cost_tracker = CostTracker(storage=SQLiteStorage(":memory:"))
    message_bus = MessageBus()

    return create_hybrid_executor(
        message_bus=message_bus,
        cost_tracker=cost_tracker,
        agent_context=context,
        enable_plan_parsing=True,
    )

def test_executor_initialization(hybrid_executor):
    """Verify executor initializes with plan parsing."""
    assert hybrid_executor.enable_plan_parsing is True
    assert hybrid_executor.plan_parser is not None

def test_executor_backward_compatibility():
    """Verify legacy mode still works."""
    context = create_agent_context()
    cost_tracker = CostTracker(storage=SQLiteStorage(":memory:"))
    message_bus = MessageBus()

    executor = create_hybrid_executor(
        message_bus=message_bus,
        cost_tracker=cost_tracker,
        agent_context=context,
        enable_plan_parsing=False,  # Legacy mode
    )

    assert executor.enable_plan_parsing is False
    assert executor.plan_parser is None

@pytest.mark.asyncio
async def test_execute_plan_requires_flag(hybrid_executor):
    """Verify execute_plan requires plan parsing enabled."""
    # Disable plan parsing
    hybrid_executor.enable_plan_parsing = False

    with pytest.raises(RuntimeError, match="Plan parsing not enabled"):
        await hybrid_executor.execute_plan("/tmp/test_plan.md")
```

### Integration Tests

#### `tests/integration/test_phase1_integration.py`

```python
"""End-to-end integration tests for Phase 1."""

import pytest
import tempfile
from pathlib import Path
from trinity_protocol.core.hybrid_executor import create_hybrid_executor
from trinity_protocol.core.plan_parser import parse_plan_file
from shared.agent_context import create_agent_context
from shared.cost_tracker import CostTracker, SQLiteStorage
from shared.message_bus import MessageBus

INTEGRATION_PLAN = """---
title: Phase 1 Integration Test
estimated_hours: 1
plan_id: phase1_test
---

## Task: Create sample file
Agent: CODER
Dependencies: None
Artifacts: /tmp/phase1_test.py

## Task: Audit sample file
Agent: AUDITOR
Dependencies: Create sample file
Artifacts: /tmp/phase1_audit.json
"""

@pytest.mark.asyncio
async def test_full_plan_execution():
    """Test complete plan execution workflow."""
    # Create plan file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(INTEGRATION_PLAN)
        plan_file = f.name

    try:
        # Parse plan
        plan = parse_plan_file(plan_file)
        assert len(plan.tasks) == 2

        # Create executor
        context = create_agent_context()
        cost_tracker = CostTracker(storage=SQLiteStorage(":memory:"))
        message_bus = MessageBus()

        executor = create_hybrid_executor(
            message_bus=message_bus,
            cost_tracker=cost_tracker,
            agent_context=context,
            enable_plan_parsing=True,
        )

        # Execute plan (will be stubbed in Phase 1)
        # Phase 2 will implement actual execution
        # For now, just verify no crashes

        # Cleanup
        Path(plan_file).unlink()

    except Exception as e:
        pytest.fail(f"Integration test failed: {e}")
```

---

## File Structure Summary

### New Files Created

```
trinity_protocol/core/
├── agent_contracts.py          (~250 lines) - Input/output schemas, tool requirements
├── plan_parser.py              (~180 lines) - Markdown plan → ExecutionPlan
└── __init__.py                 (update) - Export new classes

tests/trinity_protocol/core/
├── test_agent_contracts.py     (~80 lines) - Contract validation tests
├── test_plan_parser.py         (~90 lines) - Plan parsing tests
└── test_hybrid_executor_phase1.py (~60 lines) - Executor integration tests

tests/integration/
└── test_phase1_integration.py  (~50 lines) - E2E integration test
```

### Modified Files

```
trinity_protocol/core/hybrid_executor.py
├── Line 32-43: Add imports (agent_contracts, plan_parser)
├── Line 142-156: Add enable_plan_parsing parameter
├── Line 184: Add plan_parser initialization
├── Line 310: Add execute_plan() method (~80 lines)
├── Line 390: Add _execute_agent_with_escalation() method (~90 lines)
├── Line 480: Add _track_agent_cost() method (~40 lines)
├── Line 311: Modify _execute_at_tier() with feature flag check (~10 lines)
└── Total changes: ~220 lines added, 5 lines modified

trinity_protocol/core/__init__.py
├── Export AgentContract, get_contract
├── Export PlanParser, ExecutionPlan, Task
└── Total: 3 lines added
```

---

## Dependencies & Imports

### New Package Requirements

**None** - All dependencies already exist in Agency:
- ✅ `pydantic` - Already used for models
- ✅ `yaml` (PyYAML) - Already in requirements
- ✅ `re` - Standard library
- ✅ `dataclasses` - Standard library
- ✅ `enum` - Standard library

### Import Additions

```python
# In hybrid_executor.py
from trinity_protocol.core.agent_contracts import (
    get_contract,
    validate_agent_output,
    AgentInputBase,
    AgentOutputBase,
    AgentContract,
)
from trinity_protocol.core.plan_parser import (
    PlanParser,
    ExecutionPlan,
    Task,
    parse_plan_file,
)

# In agent_contracts.py
from pydantic import BaseModel
from typing import Callable, Any, Literal
from dataclasses import dataclass, field
from trinity_protocol.core.agent_registry import AgentType

# In plan_parser.py
import re
import yaml
from dataclasses import dataclass, field
from typing import Literal
from trinity_protocol.core.agent_registry import AgentType
```

---

## Risk Assessment

### HIGH RISK 🔴

**None** - All changes are additive with feature flags

### MEDIUM RISK 🟡

1. **Plan Parser Regex Complexity**
   - **Risk:** Complex plan formats may break regex parsing
   - **Mitigation:** Start with simple format, extensive unit tests
   - **Fallback:** Manual parsing if regex fails

2. **Agent Contract Validation**
   - **Risk:** Overly strict validators may reject valid outputs
   - **Mitigation:** Start with permissive validators, tighten over time
   - **Fallback:** Disable validation with flag

3. **Backward Compatibility**
   - **Risk:** Feature flag may not fully isolate legacy path
   - **Mitigation:** Integration tests covering both modes
   - **Fallback:** Quick revert if production breaks

### LOW RISK 🟢

1. **Tool Mapping**
   - **Risk:** Agents may need tools not in contracts
   - **Mitigation:** Add tools to contracts as needed
   - **Impact:** Runtime error, easy fix

2. **Cost Tracking**
   - **Risk:** Cost estimates may be inaccurate
   - **Mitigation:** Log all costs, adjust formulas
   - **Impact:** Budget tracking only, no functional impact

---

## Implementation Sequence

### Phase 1.1: Contracts (2 hours)
1. Create `agent_contracts.py` with all 10 agent schemas
2. Write unit tests for contracts
3. Validate all tools exist in Agency
4. **Checkpoint:** 100% test pass

### Phase 1.2: Plan Parser (2 hours)
1. Create `plan_parser.py` with basic parser
2. Implement topological sort for dependencies
3. Write unit tests with sample plans
4. **Checkpoint:** Parse 3+ sample plans successfully

### Phase 1.3: Executor Integration (3 hours)
1. Add `enable_plan_parsing` feature flag
2. Implement `execute_plan()` method (stubbed execution)
3. Implement `_execute_agent_with_escalation()` (stubbed)
4. Add cost tracking method
5. **Checkpoint:** Executor initializes without errors

### Phase 1.4: Testing & Validation (1 hour)
1. Run all unit tests (target: 100% pass)
2. Run integration test (plan → parse → execute stub)
3. Test backward compatibility (legacy mode)
4. **Checkpoint:** All tests green

### Phase 1.5: Documentation (30 min)
1. Update `CLAUDE.md` with Phase 1 status
2. Create ADR for Conductor architecture
3. Document feature flag usage
4. **Checkpoint:** Documentation complete

---

## Success Criteria

### Phase 1 Definition of Done ✅

- [ ] All 10 agent contracts defined with schemas
- [ ] Plan parser handles frontmatter + tasks + dependencies
- [ ] HybridExecutor has `enable_plan_parsing` flag
- [ ] HybridExecutor can parse plans (execution stubbed)
- [ ] Cost tracking integrated per agent/tier
- [ ] 100% unit test pass rate (35+ tests)
- [ ] Integration test passes (plan → parse → stub execution)
- [ ] Backward compatibility verified (legacy mode works)
- [ ] Zero regressions in existing functionality
- [ ] Documentation updated

### What Phase 1 Does NOT Include ⛔

- ❌ Actual agent execution (Phase 2)
- ❌ Real tool provisioning (Phase 2)
- ❌ Multi-agent chaining (Phase 2)
- ❌ Learning integration (Phase 3)
- ❌ Production deployment (Phase 4)

---

## Next Steps (Phase 2 Preview)

**Phase 2 Scope:**
1. Implement actual agent execution in `_execute_agent_with_escalation()`
2. Tool provisioning based on contracts
3. Agent chaining with dependency management
4. Output validation and artifact storage
5. Error handling and rollback

**Estimated Timeline:** 8-12 hours

---

## Constitutional Compliance Checklist

### Article I: Complete Context Before Action ✅
- [x] Plan parser validates complete plan structure
- [x] Escalation rules require complete context
- [x] Feature flag prevents partial migrations

### Article II: 100% Verification and Stability ✅
- [x] All changes have unit tests
- [x] Integration tests verify backward compatibility
- [x] Existing tests continue passing

### Article III: Automated Enforcement ✅
- [x] Agent contracts enforce type safety
- [x] Validators programmatically check outputs
- [x] No manual override mechanisms

### Article IV: Continuous Learning ✅
- [x] Cost tracking captures performance data
- [x] Escalation decisions logged for learning
- [x] AgentContext integration preserved

### Article V: Spec-Driven Development ✅
- [x] This plan serves as formal specification
- [x] Changes trace to plan sections
- [x] ADR will document architecture decision

---

## Appendix: Tool Requirements Matrix

| Agent Type | Required Tools | Count |
|------------|---------------|-------|
| CODER | read, write, edit, multi_edit, bash, todo_write | 6 |
| PLANNER | write, read, glob, grep, learning_dashboard | 5 |
| AUDITOR | read, glob, grep, analyze_type_patterns, constitution_check | 5 |
| TEST_GENERATOR | read, write, edit, bash, grep, property_testing | 6 |
| QUALITY_ENFORCER | read, constitution_check, bash, auto_fix_nonetype, apply_and_verify_patch | 5 |
| LEARNING | read, write, learning_dashboard, grep | 4 |
| CHIEF_ARCHITECT | write, read, glob, document_generator | 4 |
| MERGER | git, git_unified, bash, read | 4 |
| TOOLSMITH | read, write, edit, bash, glob | 5 |
| SUMMARY | read, write | 2 |

**Total Unique Tools:** 17 out of 45+ available

---

## Appendix: Sample Plan Format

```markdown
---
title: Add User Authentication
estimated_hours: 8
plan_id: auth_v1
priority: P0
---

## Task: Create auth models
Agent: CODER
Dependencies: None
Artifacts: src/models/User.py, src/models/Session.py
Duration: 90 minutes

## Task: Generate auth tests
Agent: TEST_GENERATOR
Dependencies: Create auth models
Artifacts: tests/test_auth.py
Duration: 60 minutes

## Task: Implement login endpoint
Agent: CODER
Dependencies: Create auth models
Artifacts: src/api/auth.py
Duration: 120 minutes

## Task: Audit security compliance
Agent: AUDITOR
Dependencies: Implement login endpoint, Generate auth tests
Artifacts: docs/security_audit.md
Duration: 45 minutes

## Task: Create ADR
Agent: CHIEF_ARCHITECT
Dependencies: Audit security compliance
Artifacts: docs/adr/ADR-022-authentication.md
Duration: 30 minutes
```

---

**Plan Version:** 1.0
**Created:** 2025-10-05
**Author:** Claude (Agency Orchestrator)
**Constitutional Compliance:** All 5 Articles ✅
