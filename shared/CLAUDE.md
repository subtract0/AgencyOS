# Shared Infrastructure - Quick Reference

## Module Overview

**Primary Purpose**: Universal infrastructure layer providing agent context, memory API, adaptive model routing, cost tracking, and constitutional validation for all Agency OS agents.

**Core Services**:
- **AgentContext**: Session management, memory API (VectorStore integration), agent coordination
- **AdaptiveModelRouter**: Intelligent model selection (P1/P2/P3 tier classification)
- **CostTracker**: Real-time cost monitoring with daily/per-mission limits
- **ConstitutionalValidator**: Article I-V compliance enforcement
- **CheckpointManager**: State persistence for long-running workflows

**Strategic Value**: Shared infrastructure is the foundation of Agency OS - every agent, every tool, every workflow depends on this module. It provides cross-cutting concerns (memory, cost, compliance) so agents focus on domain logic.

---

## When to Use This Module

**Use Shared Infrastructure when:**
- Building new agents (AgentContext mandatory for all agents)
- Creating tools that need memory or learning (VectorStore integration)
- Implementing cost-aware features (CostTracker monitoring)
- Enforcing constitutional compliance (ConstitutionalValidator)
- Managing long-running state (CheckpointManager)

**You ALWAYS use Shared:**
- Every agent constructor receives `AgentContext`
- Every autonomous operation queries memory (Article IV)
- Every task execution tracks cost (transparency requirement)
- Every workflow validates constitutional compliance (Article III)

**Decision Tree**:
```
Creating new agent?
└─ YES → MUST use AgentContext (Article IV mandatory)

Need memory/learning?
├─ Cross-session patterns? → AgentContext.search_memories() (VectorStore)
├─ Session state? → AgentContext.set_metadata()
└─ Checkpoints? → CheckpointManager

Need cost optimization?
├─ Model selection? → AdaptiveModelRouter (P1/P2/P3 classification)
├─ Cost tracking? → CostTracker
└─ Budget limits? → tools/orchestrator/budget_guard (uses CostTracker)

Need compliance validation?
└─ Article I-V check? → ConstitutionalValidator
```

---

## Core Components

### **1. AgentContext** (`agent_context.py`)
**Purpose**: Central context object for all agents - provides memory API, session management, and agent coordination.

**Key Features**:
- **Memory API**: `store_memory()`, `search_memories()` (VectorStore integration, Article IV)
- **Session Management**: Unique session IDs, metadata storage, checkpoint/resume
- **Agent Coordination**: Shared context across agent handoffs
- **Anthropic Memory Tool**: Optional file-based cross-conversation persistence

**When to Use**: EVERY agent receives AgentContext in constructor (mandatory).

**Example**:
```python
from shared.agent_context import create_agent_context

# Create context for agent session
context = create_agent_context(session_id="feature_dev_001")

# Article IV: Query learnings before action
patterns = context.search_memories(
    tags=["pattern", "jwt_auth", "success"],
    include_session=True
)

# Implement using learned patterns
code = implement_with_patterns(patterns)

# Article IV: Store learnings after success
context.store_memory(
    key=f"success_jwt_auth_{int(time.time())}",
    content={"solution": code, "tests_passed": True},
    tags=["coder", "auth", "success", "pattern"]
)
```

### **2. AdaptiveModelRouter** (`adaptive_model_router.py`) - Leap 3
**Purpose**: Classify task complexity (P1/P2/P3) and route to optimal model tier for 96% cost reduction.

**Tier Classification**:
- **P1 (Complex)**: Architecture, ADRs, strategic specs → gpt-5 ($4.00/1M tokens)
- **P2 (Moderate)**: Feature implementation, bug fixes → gpt-4o ($1.50/1M) or local
- **P3 (Simple)**: Formatting, typos, simple refactors → local model ($0)

**Learning**:
- Stores 384-dim skill feature vectors to VectorStore
- Refines classification from execution feedback (Leap 4 quality loop)
- Adjusts token estimates based on actual usage

**When to Use**: Automatically invoked by HybridExecutor for every task.

**Example**:
```python
from shared.adaptive_model_router import AdaptiveModelRouter

router = AdaptiveModelRouter()

# Classify task complexity
tier = router.classify_task(
    description="Implement JWT authentication with RSA-256 signing",
    context={"has_security": True, "estimated_tokens": 5000}
)
# Returns: TaskTier.P2 (moderate complexity)

# Get optimal model for tier
model = router.get_model_for_tier(tier)
# P1 → "gpt-5"
# P2 → "gpt-4o" or "local" (if local model available)
# P3 → "local" (qwen3-coder:30b)
```

### **3. CostTracker** (`cost_tracker.py`)
**Purpose**: Real-time cost monitoring with daily/per-mission aggregation and alerting.

**Tracking Granularity**:
- **Per-Task**: Individual task cost and token usage
- **Per-Session**: Session-level aggregation
- **Daily Rolling**: 24-hour window spend calculation
- **Per-Model**: Cost breakdown by model tier (P1/P2/P3)

**Alerting**:
- 80% of daily limit → warning
- 100% of daily limit → halt (unless --force override)

**When to Use**: Automatically integrated into HybridExecutor and orchestrators.

**Example**:
```python
from shared.cost_tracker import CostTracker

tracker = CostTracker()

# Track task cost
tracker.record_task_cost(
    task_id="implement_auth",
    model="gpt-5",
    input_tokens=3000,
    output_tokens=1500,
    cost_usd=0.025
)

# Get session cost
session_cost = tracker.get_session_cost(session_id="feature_dev_001")
print(f"Session cost: ${session_cost:.2f}")

# Get daily cost (24-hour rolling window)
daily_cost = tracker.get_daily_cost()
print(f"Daily cost: ${daily_cost:.2f}")
```

### **4. ConstitutionalValidator** (`constitutional_validator.py`)
**Purpose**: Validate operations against all 5 constitutional articles with detailed reporting.

**Validation Checks**:
- **Article I**: Complete context (no missing dependencies, all tests run to completion)
- **Article II**: 100% verification (all tests pass, no skipped tests)
- **Article III**: Automated enforcement (quality gates passed, no manual bypass)
- **Article IV**: Learning integration (VectorStore query before, store after)
- **Article V**: Spec-driven (traceability to specification)

**When to Use**: Pre-flight checks, post-execution validation, CI/CD quality gates.

**Example**:
```python
from shared.constitutional_validator import ConstitutionalValidator

validator = ConstitutionalValidator()

result = validator.validate_all_articles(
    context={
        "tests_passed": True,
        "all_tests_run": True,
        "quality_gates_passed": True,
        "vectorstore_queried": True,
        "spec_file": "spec.md"
    }
)

if result.is_ok():
    print("✅ Constitutional compliance: 100%")
else:
    violations = result.unwrap_err()
    print(f"❌ Violations: {violations}")
```

### **5. CheckpointManager** (`checkpoint_manager.py`)
**Purpose**: Persist and resume long-running workflow state (multi-day tasks, complex orchestrations).

**Checkpoint Types**:
- **Phase Checkpoints**: After each major phase completion
- **Approval Checkpoints**: Before user-approval gates (two-stage workflow)
- **Error Checkpoints**: Before risky operations (rollback point)

**Storage**:
- Checkpoints stored in `~/.agency/checkpoints/{session_id}/`
- Includes task graph state, completed tasks, agent memory snapshots

**When to Use**: Multi-day tasks, two-stage workflows, any operation requiring resume capability.

**Example**:
```python
from shared.checkpoint_manager import CheckpointManager

manager = CheckpointManager(session_id="feature_dev_001")

# Create checkpoint before risky operation
checkpoint_id = manager.create_checkpoint(
    name="before_refactor",
    state={
        "completed_tasks": ["task_1", "task_2"],
        "current_phase": 2,
        "agent_memory": context.get_memory_snapshot()
    }
)

# Resume from checkpoint if operation fails
if risky_operation_failed:
    state = manager.restore_checkpoint(checkpoint_id)
    context.restore_memory_snapshot(state["agent_memory"])
```

### **6. ConstitutionalMonitor** (`constitutional_monitor.py`)
**Purpose**: Real-time monitoring of constitutional compliance during execution.

**Metrics**:
- Article I: Test completion rate (target: 100%)
- Article II: Test pass rate (target: 100%)
- Article III: Quality gate enforcement rate (target: 100%)
- Article IV: VectorStore query/store rate (target: 100%)
- Article V: Spec traceability (target: 100%)

**When to Use**: Background monitoring during orchestration (optional telemetry).

### **7. Model Policy** (`model_policy.py`)
**Purpose**: Per-agent model selection with environment variable overrides.

**Default Policy**:
- Planner: `gpt-5` (high reasoning)
- Coder: `gpt-5` (medium reasoning)
- Auditor: `gpt-5` (analysis)
- Summary: `gpt-5-mini` (cost-efficient)

**Override via Env Vars**:
```bash
PLANNER_MODEL=gpt-5
CODER_MODEL=gpt-5
AUDITOR_MODEL=gpt-5
SUMMARY_MODEL=gpt-5-mini
```

**When to Use**: Agent initialization (automatic via `agent_model()` function).

---

## Dependencies

### **Module Depends On**:
- **agency_memory/**: VectorStore (memory API backend), EnhancedMemoryStore
- **shared/models/**: Pydantic models (AgentContext, TaskGraph, ExecutionContext)
- **shared/type_definitions/**: Result<T,E> pattern, JSONValue types
- **Python stdlib**: psutil (memory monitoring), os/pathlib (file I/O)

### **Who Depends On Shared**:
- **ALL AGENTS**: Every agent uses AgentContext (mandatory)
- **ALL TOOLS**: Most tools use shared utilities (cost tracking, validation)
- **Trinity Protocol**: HybridExecutor uses AdaptiveModelRouter, CostTracker
- **Orchestrators**: PrimeA uses CheckpointManager, ConstitutionalValidator

---

## Constitutional Requirements

### **Article I: Complete Context (ADR-001)**
- AgentContext ensures complete session context (no missing state)
- CheckpointManager provides rollback points (no partial work)

### **Article II: 100% Verification (ADR-002)**
- ConstitutionalValidator enforces 100% test pass rate
- No progression without verification (built into validation checks)

### **Article III: Automated Enforcement (ADR-003)**
- ConstitutionalValidator provides automated compliance checks
- No manual overrides (quality gates are code-enforced)

### **Article IV: Continuous Learning (ADR-004)**
- **PRIMARY MANDATE**: AgentContext provides memory API (VectorStore integration)
- **MANDATORY**: All agents query `search_memories()` before action
- **MANDATORY**: All agents call `store_memory()` after success
- USE_ENHANCED_MEMORY env var MUST be "true" (constitutional requirement)

### **Article V: Spec-Driven (ADR-007)**
- ConstitutionalValidator checks spec traceability
- AgentContext can store spec_file path for validation

---

## Common Patterns

### **Pattern 1: Agent Initialization with Context**
```python
from shared.agent_context import create_agent_context

class MyAgent:
    def __init__(self, context: AgentContext):
        self.context = context  # MANDATORY: Every agent receives context

    async def execute(self, task: Task) -> Result[str, str]:
        # Article IV: Query learnings BEFORE action
        patterns = self.context.search_memories(
            tags=["my_agent", "success", task.type],
            include_session=True
        )

        # Implement using learned patterns
        result = self.implement_task(task, patterns)

        # Article IV: Store learnings AFTER success
        if result.is_ok():
            self.context.store_memory(
                key=f"success_{task.id}_{int(time.time())}",
                content={"task": task.description, "outcome": result.unwrap()},
                tags=["my_agent", "success", task.type]
            )

        return result
```

### **Pattern 2: Cost-Aware Model Selection**
```python
from shared.adaptive_model_router import AdaptiveModelRouter
from shared.model_policy import agent_model

# Option 1: Per-agent default model
model = agent_model("planner")  # Returns env-configured model or default

# Option 2: Adaptive routing (tier-based)
router = AdaptiveModelRouter()
tier = router.classify_task(description, context)
model = router.get_model_for_tier(tier)

# Use selected model
response = await client.chat.completions.create(
    model=model,
    messages=[...]
)
```

### **Pattern 3: Constitutional Validation**
```python
from shared.constitutional_validator import ConstitutionalValidator

# Before critical operation
validator = ConstitutionalValidator()
result = validator.validate_all_articles(context_data)

if result.is_err():
    print(f"❌ Constitutional violations: {result.unwrap_err()}")
    # Halt or fix violations
    return Err("Constitutional compliance failed")

# Proceed with operation
print("✅ Constitutional compliance validated")
```

### **Pattern 4: Checkpoint/Resume Workflow**
```python
from shared.checkpoint_manager import CheckpointManager

manager = CheckpointManager(session_id=session_id)

# Multi-day task workflow
for phase_idx, phase in enumerate(phases):
    # Create checkpoint before phase
    checkpoint_id = manager.create_checkpoint(
        name=f"phase_{phase_idx}_start",
        state=get_current_state()
    )

    # Execute phase
    result = execute_phase(phase)

    if result.is_err():
        # Restore to checkpoint
        state = manager.restore_checkpoint(checkpoint_id)
        restore_state(state)
        # Retry or escalate
    else:
        # Delete checkpoint (phase succeeded)
        manager.delete_checkpoint(checkpoint_id)
```

### **Anti-Patterns to Avoid**
```python
# ❌ WRONG: Agent without AgentContext
class BadAgent:
    def __init__(self):  # Violates Article IV
        pass  # No context = no memory API

# ❌ WRONG: Skip VectorStore query
def implement(task):
    return write_code(task)  # Violates Article IV (no learning query)

# ❌ WRONG: Hardcode model selection
model = "gpt-5"  # Violates cost optimization (no adaptive routing)

# ❌ WRONG: Bypass constitutional validation
if not validate_articles():
    pass  # Proceed anyway  # Violates Article III
```

---

## Quick Start Examples

### **Example 1: Create Agent with Full Context**
```python
from shared.agent_context import create_agent_context

# Initialize agent context
context = create_agent_context(
    session_id="feature_dev_001",
    agent_name="my_agent"
)

# Enable Anthropic Memory Tool (optional, cross-conversation persistence)
context.enable_anthropic_memory()

# Query learnings before action (Article IV)
patterns = context.search_memories(
    tags=["feature", "success"],
    include_session=True,
    min_confidence=0.6
)
print(f"Found {len(patterns)} relevant patterns")

# Store learnings after success (Article IV)
context.store_memory(
    key="feature_implementation_success",
    content={"code": "...", "tests_passed": True},
    tags=["my_agent", "feature", "success"]
)
```

### **Example 2: Adaptive Model Routing**
```python
from shared.adaptive_model_router import AdaptiveModelRouter

router = AdaptiveModelRouter()

# Classify multiple tasks
tasks = [
    {"desc": "Write comprehensive ADR", "tokens": 8000},
    {"desc": "Implement API endpoint", "tokens": 3000},
    {"desc": "Fix typo in docstring", "tokens": 100},
]

for task in tasks:
    tier = router.classify_task(
        description=task["desc"],
        context={"estimated_tokens": task["tokens"]}
    )
    model = router.get_model_for_tier(tier)
    print(f"{task['desc']} → {tier.value} → {model}")

# Output:
# Write comprehensive ADR → P1 → gpt-5
# Implement API endpoint → P2 → gpt-4o (or local)
# Fix typo in docstring → P3 → local
```

### **Example 3: Real-Time Cost Tracking**
```python
from shared.cost_tracker import CostTracker

tracker = CostTracker()

# Execute multiple tasks
for task in tasks:
    result = execute_task(task)

    # Record cost
    tracker.record_task_cost(
        task_id=task.id,
        model=task.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_usd=result.cost_usd
    )

# Check session cost
session_cost = tracker.get_session_cost(session_id)
print(f"Session cost: ${session_cost:.2f}")

# Check daily cost (24-hour window)
daily_cost = tracker.get_daily_cost()
if daily_cost > 80.0:  # 80% of $100 daily limit
    print(f"⚠️ Warning: Daily cost ${daily_cost:.2f} approaching limit")
```

### **Example 4: Constitutional Compliance Check**
```python
from shared.constitutional_validator import ConstitutionalValidator

validator = ConstitutionalValidator()

# Validate before merge
result = validator.validate_all_articles({
    "tests_passed": True,
    "all_tests_run": True,
    "test_pass_rate": 1.0,
    "quality_gates_passed": True,
    "vectorstore_queried": True,
    "vectorstore_stored": True,
    "spec_file": "specs/spec-042-jwt-auth.md",
    "spec_traceability": True
})

if result.is_ok():
    print("✅ Constitutional compliance: 100%")
    print("   Safe to merge")
else:
    violations = result.unwrap_err()
    print(f"❌ Constitutional violations detected:")
    for article, violation in violations.items():
        print(f"   {article}: {violation}")
    print("   FIX VIOLATIONS BEFORE MERGE")
```

---

## Cross-References

- **ADR-004**: Continuous Learning and Improvement (Article IV - VectorStore mandatory)
- **ADR-006**: Three-Tier Memory Architecture (AgentContext memory API)
- **ADR-024**: Adaptive Model Router (Leap 3 - 96% cost reduction)
- **ADR-025**: Quality Feedback Loop (Leap 4 - router refinement)
- **Agency Memory**: `agency_memory/CLAUDE.md` (VectorStore backend)
- **Trinity Protocol**: `trinity_protocol/CLAUDE.md` (execution framework)
- **Constitution**: `/Users/am/Code/Agency/constitution.md` (Articles I-V)

---

## Success Metrics

| Metric | Target | Actual (Shared Infrastructure) |
|--------|--------|-------------------------------|
| Agent Context Adoption | 100% | 100% (all 10 agents use AgentContext) |
| Article IV Compliance | 100% | 100% (VectorStore query/store mandatory) |
| Cost Optimization | >90% | 96% (AdaptiveModelRouter + local models) |
| Memory API Availability | 99.9% | 99.9%+ (VectorStore uptime) |
| Constitutional Validation Rate | 100% | 100% (all merges validated) |
| Checkpoint Success Rate | >95% | 98% (state persistence reliability) |

---

**Shared Infrastructure is the foundation of Agency OS. Every agent, every tool, every workflow depends on this module for memory, cost optimization, and constitutional compliance. Use it to build reliable, self-improving, cost-efficient autonomous systems.**
