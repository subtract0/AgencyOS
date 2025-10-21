# Trinity Protocol - Quick Reference

## Module Overview

**Primary Purpose**: Constitutional compliance orchestration and execution framework with adaptive model routing, quality feedback loops, and memory-aware scheduling.

**Core Architecture**: HybridExecutor orchestrates task execution across three model tiers (P1/P2/P3), learns from execution history via quality feedback, and enforces constitutional compliance at every step.

**Key Innovations**:
- **Leap 3**: Adaptive Model Router (96% cost reduction)
- **Leap 4**: Quality Feedback Loop (85%→90% routing accuracy)
- **Leap 6**: Production Hardening (slop immunity, deterministic batching)
- **Leap 8**: TRM-7M Recursive Reasoning Validation (40-60% churn reduction)

**Strategic Value**: Trinity Protocol is the execution backbone of Agency OS - all autonomous operations flow through this framework.

---

## When to Use This Module

**Use Trinity Protocol when:**
- Executing task graphs with constitutional compliance requirements
- Need adaptive model routing (cost optimization via P1/P2/P3 classification)
- Require quality feedback learning (misclassification detection and refinement)
- Building custom orchestrators that need execution infrastructure
- Integrating safety validators and guardrails

**Do NOT use directly for:**
- User-facing commands (use `/primeA` or `/primeccc` instead)
- Simple single-task execution (use direct agent invocation)
- Manual code implementation (Trinity is for automation)

**Decision Tree**:
```
Need autonomous execution?
├─ Task graph with multiple phases? → Trinity Protocol (HybridExecutor)
├─ Single task? → Direct agent invocation
└─ User-facing workflow? → PrimeA orchestrator (uses Trinity internally)

Need cost optimization?
├─ Adaptive routing required? → Trinity Protocol (AdaptiveModelRouter)
└─ Fixed model? → Standard agent execution

Need quality improvement?
├─ Learn from mistakes? → Trinity Protocol (QualityFeedbackLoop)
└─ Static execution? → Standard workflow
```

---

## Core Components

### **1. HybridExecutor** (`core/hybrid_executor.py`)
**Purpose**: Orchestrates task graph execution with memory-aware scheduling and quality feedback.

**Key Features**:
- Topological DAG traversal with parallel batching
- Memory-aware worker calculation (3 workers local model, 10 cloud-only)
- Exponential backoff retry with idempotency keys
- Deterministic task ordering (stable across runs)
- Real-time monitoring and telemetry

**When to Use**: Every task graph execution flows through HybridExecutor.

### **2. AdaptiveModelRouter** (`core/adaptive_model_router.py`)
**Purpose**: Intelligently routes tasks to optimal model tier (P1/P2/P3) based on complexity and learning.

**Key Features**:
- Three-tier classification (P1 gpt-5, P2 gpt-4o/local, P3 local)
- Skill evolution tracking (384-dim feature vectors)
- VectorStore-backed learning (confidence ≥0.6 patterns)
- 96% cost reduction vs all-gpt-5 baseline

**When to Use**: Automatically invoked by HybridExecutor for every task.

### **3. QualityFeedbackCollector** (`core/quality_feedback.py`)
**Purpose**: Detects misclassifications and refines routing rules via VectorStore learning.

**Key Signals**:
- Test failures (task classified too low)
- Code churn (excessive retries, wrong tier)
- Timing deviation (actual vs expected duration)
- User feedback (explicit correction)

**When to Use**: Automatically integrated into HybridExecutor execution hooks.

### **4. SafetyValidator** (`core/safety_validator.py`)
**Purpose**: Pre-execution safety checks (budget limits, slop immunity, constitutional compliance).

**When to Use**: Every task graph passes through validation before execution.

### **5. AmbientListenerService** (`ambient_listener_service.py`)
**Purpose**: Real-time monitoring dashboard for live execution visibility.

**When to Use**: Optional - enable for debugging or production monitoring.

---

## Dependencies

### **Module Depends On**:
- **shared/**: AgentContext, AdaptiveModelRouter, ConstitutionalValidator, CostTracker
- **agency_memory/**: VectorStore (quality feedback storage), EnhancedMemoryStore
- **shared/models/**: TaskGraph, ExecutionContext, QualitySignal Pydantic models
- **tools/orchestrator/**: BudgetGuard, SlopGuardian (safety validators)

### **Who Depends On Trinity**:
- **PrimeA Orchestrator**: Uses HybridExecutor for task graph execution
- **PrimeCCC**: Legacy orchestrator also uses Trinity execution
- **All Autonomous Workflows**: Constitutional execution requires Trinity
- **LearningAgent**: Extracts patterns from Trinity execution telemetry

---

## Constitutional Requirements

### **Article I: Complete Context (ADR-001)**
- HybridExecutor retries tasks with exponential backoff (2x, 3x, 10x timeouts)
- No partial layer execution (all tasks in batch must complete)
- Idempotency keys prevent duplicate execution on retry

### **Article II: 100% Verification (ADR-002)**
- Test tasks have `verification_target` field (links to Code task)
- HybridExecutor fails layer if any test fails (no progression to next layer)
- Quality gates enforced before layer transition

### **Article III: Automated Enforcement (ADR-003)**
- SafetyValidator runs before execution (no manual bypass)
- Budget limits enforced (--force override logged to audit trail)
- Slop immunity mandatory (score ≥3.5 or auto-rewrite)

### **Article IV: Continuous Learning (ADR-004)**
- **MANDATORY**: QualityFeedbackCollector stores patterns to VectorStore after execution
- AdaptiveModelRouter queries VectorStore before task routing
- Misclassifications auto-refine routing rules (confidence ≥0.6)

### **Article V: Spec-Driven (ADR-007)**
- Task graphs validated against TaskGraph Pydantic schema
- All tasks have acceptance_criteria field
- Spec tasks required for complex features (P1 tier)

---

## Common Patterns

### **Pattern 1: HybridExecutor Invocation**
```python
from trinity_protocol.core.hybrid_executor import HybridExecutor
from shared.models.task_graph import TaskGraph

# Load validated task graph
graph = TaskGraph.model_validate_json(graph_json)

# Create executor with memory-aware config
executor = HybridExecutor(
    use_local_model=True,  # Enable local model for P3 tasks
    max_workers=3,         # Memory-safe for M4 Pro 48GB
    enable_quality_feedback=True  # Article IV learning
)

# Execute task graph (returns Result<ExecutionReport, ExecutionError>)
result = await executor.execute(graph)

if result.is_ok():
    report = result.unwrap()
    print(f"✅ Completed {report.tasks_completed}/{report.total_tasks}")
else:
    error = result.unwrap_err()
    print(f"❌ Execution failed: {error.message}")
```

### **Pattern 2: Adaptive Model Routing**
```python
from shared.adaptive_model_router import AdaptiveModelRouter

router = AdaptiveModelRouter()

# Classify task complexity (returns P1/P2/P3)
tier = router.classify_task(
    description="Implement JWT authentication with RSA-256",
    context={"has_security": True, "estimated_tokens": 5000}
)

# Get optimal model for tier
model = router.get_model_for_tier(tier)
# P1 → gpt-5
# P2 → gpt-4o or local (if available)
# P3 → local (qwen3-coder:30b)
```

### **Pattern 3: Quality Feedback Integration**
```python
from trinity_protocol.core.quality_feedback import QualityFeedbackCollector

collector = QualityFeedbackCollector()

# After task execution, collect signals
signals = collector.collect_signals(
    task_id="implement_auth",
    actual_tier="P2",
    test_passed=False,  # Misclassification signal
    actual_duration_s=300,
    expected_duration_s=120,
    code_churn_count=5
)

# Store to VectorStore for learning (Article IV)
collector.store_feedback(signals, confidence=0.8)
```

### **Pattern 4: Memory-Aware Scheduling**
```python
import psutil
from tools.memory_aware_test_runner import get_safe_worker_count

# Check available memory before execution
mem = psutil.virtual_memory()
available_gb = mem.available / (1024 ** 3)

# Calculate safe worker count
use_local = os.getenv("USE_LOCAL_MODEL", "true").lower() == "true"
worker_count = get_safe_worker_count()
# Returns:
# - 1 worker if <10GB available (critical)
# - 3 workers if local model ON + <15GB (safe for M4 Pro 48GB)
# - 10 workers if cloud-only + >20GB (full parallelism)

executor = HybridExecutor(max_workers=worker_count)
```

### **Anti-Patterns to Avoid**
```python
# ❌ WRONG: Bypass safety validators
executor = HybridExecutor(skip_validation=True)  # Violates Article III

# ❌ WRONG: Ignore quality feedback
executor = HybridExecutor(enable_quality_feedback=False)  # Violates Article IV

# ❌ WRONG: Execute partial layers
executor.execute_tasks(layer[:2])  # Violates Article I (complete context)

# ❌ WRONG: Proceed after test failure
if test_failed:
    executor.continue_anyway()  # Violates Article II (100% verification)
```

---

## Quick Start Examples

### **Example 1: Execute Task Graph with Quality Feedback**
```python
from trinity_protocol.core.hybrid_executor import HybridExecutor
from shared.models.task_graph import TaskGraph

# Load task graph (from PrimeA or custom source)
graph = TaskGraph.model_validate_json(graph_json)

# Execute with Trinity Protocol
executor = HybridExecutor(
    use_local_model=True,
    max_workers=3,
    enable_quality_feedback=True
)

result = await executor.execute(graph)

if result.is_ok():
    report = result.unwrap()
    print(f"""
    ✅ Execution Complete
    - Tasks: {report.tasks_completed}/{report.total_tasks}
    - Cost: ${report.actual_cost_usd:.2f}
    - Misclassifications: {report.misclassifications_detected}
    - Patterns Stored: {report.patterns_stored}
    """)
```

### **Example 2: Monitor Execution with Ambient Listener**
```bash
# Terminal 1: Start ambient listener service
python -m trinity_protocol.ambient_listener_service --port 8080

# Terminal 2: Execute task graph (Trinity sends telemetry)
/primeA --graph missions/leap_7.json --visualize

# Browser: http://localhost:8080 (real-time DAG visualization)
```

### **Example 3: Custom Orchestrator Using Trinity**
```python
from trinity_protocol.core.hybrid_executor import HybridExecutor
from shared.agent_context import create_agent_context

async def custom_orchestrator(intent: str):
    # Phase 1: Generate task graph (Planner agent)
    context = create_agent_context("custom_orchestrator")
    graph = await generate_task_graph(intent)

    # Phase 2: Validate graph (Trinity validators)
    from tools.orchestrator.graph import validate_task_graph
    validation = validate_task_graph(graph)
    if validation.is_err():
        return validation

    # Phase 3: Execute with Trinity Protocol
    executor = HybridExecutor(
        use_local_model=True,
        enable_quality_feedback=True
    )
    result = await executor.execute(graph)

    # Phase 4: Extract learnings (Article IV)
    if result.is_ok():
        context.store_memory(
            key=f"orchestration_{intent}",
            content={"success": True, "cost": result.unwrap().actual_cost_usd},
            tags=["orchestrator", "success", "trinity"]
        )

    return result
```

---

## Cross-References

- **ADR-024**: Adaptive Model Router (Leap 3 - 96% cost reduction)
- **ADR-025**: Quality Feedback Loop (Leap 4 - 85%→90% accuracy)
- **ADR-026**: Test-Driven Autonomy (Leap 7 - TDD enforcement)
- **ADR-031**: Test Suite Recovery (Leap 9 - memory-aware execution)
- **Leap 3 Docs**: `docs/leap_3_complete.md`
- **Leap 4 Docs**: `docs/leap_4_complete.md`
- **Constitution**: `/Users/am/Code/Agency/constitution.md` (Articles I-V)
- **PrimeA Orchestrator**: `.claude/agents/primea_orchestrator.md`
- **Shared Infrastructure**: `shared/CLAUDE.md`

---

## Success Metrics

| Metric | Target | Actual (Trinity Protocol) |
|--------|--------|---------------------------|
| Cost Reduction | >90% | 96% (vs all-gpt-5 baseline) |
| Routing Accuracy | >85% | 90% (Leap 4 quality feedback) |
| Execution Success Rate | >95% | 97%+ (exponential backoff retry) |
| Memory Safety | 100% | 100% (no OOM crashes on M4 Pro) |
| Article IV Compliance | 100% | 100% (VectorStore learning mandatory) |
| Churn Reduction (Leap 8) | >40% | 40-60% (TRM-7M validation) |

---

**Trinity Protocol is the constitutional execution backbone of Agency OS. All autonomous operations - from PrimeA orchestration to quality feedback learning - flow through this framework. Use it to build reliable, cost-optimized, self-improving autonomous systems.**
