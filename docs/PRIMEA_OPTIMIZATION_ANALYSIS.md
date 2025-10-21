# /primeA Optimization Analysis

**Focus Areas**: Reliability, Stability, TRM-7M Integration, Efficiency, User Value

**Date**: 2025-10-14

---

## Executive Summary

The `/primeA` documentation is **comprehensive and well-designed**, but the **actual implementation has significant gaps**. The orchestrator command file describes a vision of full automation, but many critical components are **documented but not implemented**.

**Current State**: 20% implemented (documentation ✅, code ❌)

**Gap Analysis**: 10 major implementation gaps identified

**Recommendation**: Build foundation incrementally (8 Leap missions to full implementation)

---

## 1. Critical Gaps (Reliability & Stability)

### Gap 1.1: Task Graph Model Missing ⚠️ **CRITICAL**
**Status**: Documented extensively, **NOT IMPLEMENTED**

**Current**:
- `.claude/commands/primeA.md` references `shared/models/task_graph.py` (400+ lines)
- Pydantic validation described in detail
- Topological sort algorithm mentioned
- **File doesn't exist** ❌

**Impact**:
- Task graphs are **ad-hoc JSON** (no validation)
- No automatic DAG validation (circular dependencies possible)
- No cost estimation
- Manual task ordering (no topological sort)

**Fix Required**:
```python
# File: shared/models/task_graph.py
from pydantic import BaseModel, field_validator
from typing import Literal

class Task(BaseModel):
    id: str
    title: str
    type: Literal["Spec", "Code", "Test"]
    tier: Literal["Tier 1", "Tier 2"]
    agent: str
    description: str
    dependencies: list[str]
    acceptance_criteria: list[str] = []
    estimated_tokens: int = 3000

    @field_validator('dependencies')
    def validate_dependencies_exist(cls, v, info):
        # Check all dependencies are valid task IDs
        pass

class TaskGraph(BaseModel):
    mission: str
    phases: list[Phase]

    def topological_sort(self) -> list[list[Task]]:
        """Return DAG layers for parallel execution"""
        pass

    def validate_dag(self) -> Result[None, str]:
        """Check for circular dependencies"""
        pass
```

**Estimated Effort**: 4-6 hours, $12-16 USD

---

### Gap 1.2: Completion Validator Not Integrated ⚠️ **HIGH PRIORITY**
**Status**: Files exist, **NOT INTEGRATED** into orchestrator

**Current**:
- `tools/orchestrator/completion_validator.py` exists ✅
- `tests/tools/orchestrator/test_completion_validator.py` exists (39 tests) ✅
- **STEP 6.5 not implemented in actual orchestrator** ❌
- No enforcement mechanism

**Impact**:
- 90% conclusion incident can still occur
- No automatic validation before execution report
- Pattern (ADR-032) documented but not enforced

**Fix Required**:
```python
# In actual orchestrator implementation
from tools.orchestrator.completion_validator import CompletionValidator

# STEP 6.5: Before STEP 7 (execution report)
validator = CompletionValidator(
    task_results=task_results,
    todos=todos,
    spec_criteria=spec_criteria
)

validation = validator.validate()
if validation.is_err():
    # Block STEP 7, return to STEP 4
    raise ValidationError(validation.unwrap_err())
```

**Estimated Effort**: 2-3 hours, $6-8 USD

---

### Gap 1.3: Error Recovery Missing ⚠️ **HIGH PRIORITY**
**Status**: Documented, **NOT IMPLEMENTED**

**Current**:
- Exponential backoff retry mentioned
- Idempotency keys referenced
- Checkpoint/resume described
- **No actual implementation** ❌

**Impact**:
- Task failures abort entire mission (no resilience)
- Timeout = total loss (no retry with 2x, 3x, 10x)
- Long missions can't resume from checkpoint

**Fix Required**:
```python
# File: tools/orchestrator/retry_controller.py
class RetryController:
    def execute_with_retry(
        self,
        task: Task,
        max_retries: int = 3,
        backoff_multiplier: float = 2.0
    ) -> Result[TaskResult, str]:
        """
        Execute task with exponential backoff.
        Retries: 1x, 2x, 4x, 8x (up to 10x max)
        """
        pass
```

**Estimated Effort**: 6-8 hours, $16-20 USD

---

## 2. Quality Gates (Reliability)

### Gap 2.1: Slop Immunity Missing ⚠️ **MEDIUM PRIORITY**
**Status**: Documented (STEP 3.5), **NOT IMPLEMENTED**

**Current**:
- 50+ lines of documentation in primeA.md
- SlopGuardian class described
- Auto-rewrite loop detailed
- **`tools/orchestrator/slop_guardian.py` doesn't exist** ❌

**Impact**:
- No quality check on mission descriptions
- Vague tasks ("make it better") can proceed
- No pre-flight validation

**Fix Required**:
```python
# File: tools/orchestrator/slop_guardian.py
class SlopGuardian:
    def evaluate_mission(self, description: str) -> SlopVerdict:
        """
        Score 0-5:
        - ≥3.5: ACCEPT (proceed)
        - 2.0-3.4: REVISE (auto-rewrite)
        - <2.0: REJECT (halt with feedback)
        """
        pass
```

**Estimated Effort**: 4-5 hours, $10-14 USD

---

### Gap 2.2: Budget Guard Missing ⚠️ **MEDIUM PRIORITY**
**Status**: Documented (STEP 3.6), **NOT IMPLEMENTED**

**Current**:
- Budget limits described ($100/day, $10/mission)
- --force override mentioned
- Audit trail integration described
- **`tools/orchestrator/budget_guard.py` doesn't exist** ❌

**Impact**:
- No cost protection
- Expensive missions can proceed unchecked
- No daily spend tracking

**Fix Required**:
```python
# File: tools/orchestrator/budget_guard.py
class BudgetGuard:
    def check_budget(
        self,
        estimated_cost: float,
        limits: BudgetLimits,
        force: bool = False
    ) -> Result[None, str]:
        """Block if cost exceeds limits (unless --force)"""
        pass
```

**Estimated Effort**: 3-4 hours, $8-12 USD

---

## 3. TRM-7M Integration (Efficiency)

### Gap 3.1: TRM-7M Validator Missing ⚠️ **HIGH VALUE**
**Status**: Extensively documented, **NOT IMPLEMENTED**

**Current**:
- 200+ lines of TRM-7M documentation
- 4 checkpoints described (DAG, types, edge cases, lint)
- 10-100x speedup claimed
- **`trinity_protocol/core/trm_validator.py` doesn't exist** ❌
- Checkpoints 1-4 not implemented

**Impact**:
- No DAG validation (circular dependencies possible)
- No type constraint checking before tests
- No edge case inference
- No lint pre-validation
- Missing 40-60% churn reduction benefit

**Fix Required**:
```python
# File: trinity_protocol/core/trm_validator.py
class TRMValidator:
    async def validate_and_refine(
        self,
        task: ReasoningTask
    ) -> Result[ValidationResult, str]:
        """
        TRM-7M validation with 16 refinement steps.
        Fallback to Python if TRM unavailable.
        """
        pass

# STEP 3.1: DAG Validation
validation = await trm_validator.validate_dag(task_graph)

# STEP 5.1: Type Constraint Validation
validation = await trm_validator.validate_types(code_file)

# STEP 5.2: Edge Case Inference
edge_cases = await trm_validator.infer_edge_cases(test_task)

# STEP 5.3: Lint Pre-Validation
lint_issues = await trm_validator.validate_lint(code_file)
```

**Estimated Effort**: 12-16 hours, $30-40 USD (complex)

**Value**: 40-60% churn reduction = $40-60 saved per mission (ROI in 1 mission)

---

## 4. Automation (User Value)

### Gap 4.1: Automatic Task Graph Generation Missing ⚠️ **HIGH VALUE**
**Status**: Documented, **NOT IMPLEMENTED**

**Current**:
- "Spawn planner agent to generate task graph" (documented)
- Natural language → JSON conversion described
- **No actual integration with planner agent** ❌
- Task graphs are **manually created**

**Impact**:
- User provides intent: "implement JWT auth"
- **No automatic task graph generation**
- Must manually create JSON (defeats automation)

**Fix Required**:
```python
# STEP 2: Automatic task graph generation
from agents.planner_agent import PlannerAgent

planner = PlannerAgent()
task_graph_json = planner.generate_task_graph(
    intent="implement JWT authentication",
    context=context
)

task_graph = TaskGraph.model_validate_json(task_graph_json)
```

**Estimated Effort**: 6-8 hours, $16-20 USD

**Value**: Enables true "/primeA 'task'" workflow (current gap!)

---

### Gap 4.2: Automatic PR Creation Missing ⚠️ **HIGH VALUE**
**Status**: Now documented as default, **NOT IMPLEMENTED**

**Current**:
- `--auto-pr` is now default (docs updated today)
- STEP 7 describes PR creation
- **No automatic PR creation code** ❌
- Must manually spawn merger agent

**Impact**:
- User expects: `/primeA "task"` → automatic PR
- **Reality**: Manual PR creation still required
- Breaks documented workflow

**Fix Required**:
```python
# STEP 7: Automatic PR creation (if not --no-pr)
if not args.get("no_pr"):
    from agents.merger_agent import MergerAgent

    merger = MergerAgent()
    pr_url = merger.create_pr(
        title=f"feat: {graph.mission}",
        body=generate_pr_body(graph, execution_results),
        base="main",
        head=current_branch
    )

    print(f"✅ PR created: {pr_url}")
    print(f"🔄 CI running... (gh pr checks to monitor)")
```

**Estimated Effort**: 4-5 hours, $10-14 USD

**Value**: Completes documented "/clear → /primeA" automation

---

### Gap 4.3: Automatic Branch Creation Missing ⚠️ **HIGH VALUE**
**Status**: Documented in task graphs, **NOT IMPLEMENTED**

**Current**:
- Documentation says: "Phase 0: create_feature_branch task"
- **Task graphs don't auto-generate this** ❌
- Manual branch creation still required

**Impact**:
- Branch protection active (can't push to main)
- **No automatic branch creation**
- User must manually: `git checkout -b feat/...`

**Fix Required**:
```python
# In task graph generation (planner agent)
# Always prepend Phase 0: Git Workflow Setup
phase_0 = Phase(
    id="phase_0_setup",
    title="Git Workflow Setup",
    tasks=[
        Task(
            id="create_feature_branch",
            title="Create feature branch",
            type="Code",
            tier="Tier 2",
            agent="coder",
            description=f"Create and checkout feature branch: feat/{slugify(mission)}",
            dependencies=[],
            acceptance_criteria=[
                "Feature branch created with semantic naming",
                "Checked out to feature branch",
                "Verified not on main branch"
            ]
        )
    ]
)
```

**Estimated Effort**: 2-3 hours, $6-8 USD

**Value**: Enables constitutional Article III compliance automatically

---

## 5. Observability (User Experience)

### Gap 5.1: Real-Time Visualization Missing ⚠️ **MEDIUM VALUE**
**Status**: Documented, **NOT IMPLEMENTED**

**Current**:
- Mermaid DAG generation described
- ASCII tree visualization mentioned
- Live progress tracking documented
- **No actual implementation** ❌

**Impact**:
- No visibility into execution progress
- Can't see which tasks are running
- No ETA for completion

**Fix Required**:
```python
# STEP 4: Real-time visualization
def display_live_progress(graph: TaskGraph, completed_tasks: set[str]):
    """
    Update terminal with:
    - Mermaid DAG (colored by status: green=done, yellow=running, gray=pending)
    - ASCII tree with checkmarks
    - Progress bar: [████░░░░] 50% (6/12 tasks, ~8 min remaining)
    """
    pass
```

**Estimated Effort**: 6-8 hours, $16-20 USD

**Value**: Significantly improves user experience during long missions

---

### Gap 5.2: TodoWrite Auto-Updates Missing ⚠️ **MEDIUM PRIORITY**
**Status**: Documented as "CRITICAL", **NOT AUTOMATED**

**Current**:
- STEP 0: "Initialize TodoWrite" (documented)
- Pattern: "Always update TodoWrite at completion" (confidence 1.0)
- **Manual TodoWrite calls in documentation only** ❌
- No automatic synchronization

**Impact**:
- Todo list out of sync with actual progress
- User sees stale status
- Violates documented pattern (ADR-032)

**Fix Required**:
```python
# Automatic TodoWrite updates in orchestrator
class TaskGraphExecutor:
    def execute_layer(self, layer: list[Task]):
        # Mark phase as in_progress
        self.update_todos(phase_id, status="in_progress")

        # Execute tasks...

        # Mark phase as completed
        self.update_todos(phase_id, status="completed")
```

**Estimated Effort**: 2-3 hours, $6-8 USD

**Value**: Constitutional pattern enforcement (Article IV)

---

## 6. Learning Integration (Efficiency)

### Gap 6.1: Automatic VectorStore Integration Missing ⚠️ **HIGH VALUE**
**Status**: Documented (STEP 6), **NOT AUTOMATED**

**Current**:
- "Query patterns before action" (Article IV)
- "Store patterns after success" (Article IV)
- **Manual agent spawning required** ❌
- No automatic VectorStore queries

**Impact**:
- Patterns stored but not queried
- Institutional learning not applied
- Repeats solved problems (inefficient)

**Fix Required**:
```python
# STEP 2: Before task graph generation
relevant_patterns = context.search_memories(
    tags=["primeA", task_category],
    min_confidence=0.6
)

# STEP 6: After successful execution
context.store_memory(
    key=f"mission_{graph.mission}_{timestamp}",
    content={"patterns": extracted_patterns},
    tags=["primeA", "success", task_category]
)
```

**Estimated Effort**: 4-5 hours, $10-14 USD

**Value**: Enables cross-session learning (exponential improvement)

---

## 7. Architecture Gaps

### Gap 7.1: Two-Stage Orchestrator Missing ⚠️ **MEDIUM PRIORITY**
**Status**: Documented (STEP 2.5), **NOT IMPLEMENTED**

**Current**:
- `--two-stage` flag documented
- Routing logic described
- **`tools/orchestrator/two_stage_orchestrator.py` doesn't exist** ❌

**Impact**:
- --two-stage flag doesn't work
- No spec approval checkpoint
- Documented feature not functional

**Estimated Effort**: 8-10 hours, $20-25 USD

---

### Gap 7.2: Cost Tracking Missing ⚠️ **MEDIUM VALUE**
**Status**: Documented (STEP 7 report), **NOT IMPLEMENTED**

**Current**:
- Per-task cost breakdown described
- Tier routing savings calculated
- **No actual cost tracking** ❌

**Impact**:
- Can't measure actual costs
- Can't verify 96% savings claims
- No visibility into spend

**Estimated Effort**: 4-6 hours, $10-16 USD

---

## Priority Recommendations

### Tier 1: Foundation (Build First) ⚡ **CRITICAL**
Essential for basic functionality:

1. **Task Graph Model** (Gap 1.1) - 4-6 hours
2. **Automatic Task Graph Generation** (Gap 4.1) - 6-8 hours
3. **Automatic Branch Creation** (Gap 4.3) - 2-3 hours
4. **Automatic PR Creation** (Gap 4.2) - 4-5 hours

**Total**: 16-22 hours, $40-55 USD

**Value**: Enables documented "/clear → /primeA 'task'" workflow

---

### Tier 2: Quality & Reliability ⚡ **HIGH PRIORITY**
Critical for production use:

1. **Completion Validator Integration** (Gap 1.2) - 2-3 hours
2. **Error Recovery** (Gap 1.3) - 6-8 hours
3. **Slop Immunity** (Gap 2.1) - 4-5 hours
4. **Budget Guard** (Gap 2.2) - 3-4 hours

**Total**: 15-20 hours, $38-50 USD

**Value**: Prevents 90% conclusion, enables resilience

---

### Tier 3: Efficiency & Learning ⚡ **HIGH VALUE**
Maximize ROI:

1. **TRM-7M Validator** (Gap 3.1) - 12-16 hours
2. **Automatic VectorStore Integration** (Gap 6.1) - 4-5 hours
3. **Cost Tracking** (Gap 7.2) - 4-6 hours

**Total**: 20-27 hours, $50-68 USD

**Value**: 40-60% churn reduction + institutional learning

---

### Tier 4: User Experience ⚡ **MEDIUM VALUE**
Polish and observability:

1. **Real-Time Visualization** (Gap 5.1) - 6-8 hours
2. **TodoWrite Auto-Updates** (Gap 5.2) - 2-3 hours
3. **Two-Stage Orchestrator** (Gap 7.1) - 8-10 hours

**Total**: 16-21 hours, $40-53 USD

**Value**: Significantly improved UX

---

## Suggested Tasks for Next /primeA Round

### Option A: Foundation (Quickest Path to Working System) ✅ **RECOMMENDED**

**Task 1: Core Infrastructure**
```
/primeA "implement task graph model with Pydantic validation, DAG validation, and topological sort (shared/models/task_graph.py) - includes TaskGraph, Phase, Task models with field validators for dependencies, acceptance criteria, and automatic cost estimation"
```

**Task 2: Planner Integration**
```
/primeA "integrate planner agent for automatic task graph generation from natural language intent - includes Phase 0 automatic branch creation, Phase N automatic PR creation, and validation that every Code task has Test dependency"
```

**Task 3: Complete Automation**
```
/primeA "implement automatic branch creation and PR creation in primeA orchestrator - Phase 0 creates feat/task-name branch, final phase creates GitHub PR with comprehensive description (unless --no-pr flag), triggers CI automatically"
```

**Impact**: After these 3 tasks, the documented workflow works:
```bash
/clear
/primeA "implement JWT auth"
# → Automatic branch, spec, tests, code, PR, CI ✅
```

---

### Option B: Quality First (Most Reliable) 🛡️

**Task 1: Quality Gates**
```
/primeA "implement slop immunity (tools/orchestrator/slop_guardian.py) and budget guard (tools/orchestrator/budget_guard.py) with STEP 3.5-3.6 integration - includes pre-flight quality checks, auto-rewrite loop, daily/mission cost limits, and --force override with audit trail"
```

**Task 2: Resilience**
```
/primeA "implement exponential backoff retry controller with checkpoint/resume for primeA task execution - includes idempotency keys, 2x/3x/10x timeout retry (Article I), partial failure recovery, and graceful degradation"
```

**Task 3: Completion Validation**
```
/primeA "integrate completion validator into primeA STEP 6.5 - automatic 6-gate validation before execution report, blocks STEP 7 if validation fails, returns to STEP 4 for incomplete tasks, stores success pattern to VectorStore"
```

**Impact**: Constitutional compliance enforced, production-ready reliability

---

### Option C: Efficiency Maximization (Best ROI) 💰

**Task 1: TRM-7M Infrastructure**
```
/primeA "implement TRM-7M validator (trinity_protocol/core/trm_validator.py) with all 4 checkpoints - includes DAG validation (10-100x faster than Python), type constraint checking, edge case inference, lint pre-validation, and graceful fallback to Python validation"
```

**Task 2: TRM-7M Integration**
```
/primeA "integrate TRM-7M validator into primeA STEPS 3.1 and 5.1-5.3 - automatic DAG validation after task graph generation, type checking after Code tasks, edge case discovery for Test tasks, lint validation before test execution, with auto-fix via QualityEnforcer"
```

**Task 3: Learning Loop**
```
/primeA "implement automatic VectorStore integration in primeA STEPS 2 and 6 - query patterns before task execution (Article IV), store patterns after success with confidence scoring, extract learnings for future missions, propose next mission based on gaps"
```

**Impact**: 40-60% churn reduction ($40-60 saved per mission, ROI in 1 mission)

---

### Option D: End-to-End (Comprehensive) 🚀 **AMBITIOUS**

**Single Mission**:
```
/primeA "implement complete primeA orchestrator with all STEPS 0-7 - includes task graph model, slop immunity, budget guard, automatic task graph generation from planner agent, automatic branch creation, TRM-7M validation (4 checkpoints), completion validator integration, automatic PR creation, TodoWrite auto-updates, and real-time Mermaid visualization" --two-stage
```

**Estimated**: 40-60 hours, $100-150 USD (large mission)

**Impact**: Documented primeA vision becomes reality

**Risk**: Very large scope, recommend Tier 1-3 incremental approach instead

---

## Recommended Execution Order (Incremental Leaps)

**Leap 10: Foundation** (Option A)
- Task graph model
- Planner integration
- Automatic branch + PR creation
- **Result**: Working "/primeA 'task'" automation

**Leap 11: Quality Gates** (Option B)
- Slop immunity + budget guard
- Error recovery
- Completion validator integration
- **Result**: Production-ready reliability

**Leap 12: TRM-7M Integration** (Option C, Task 1-2)
- TRM-7M validator
- 4 checkpoint integration
- **Result**: 40-60% churn reduction

**Leap 13: Learning Loop** (Option C, Task 3)
- Automatic VectorStore integration
- Pattern extraction
- **Result**: Exponential improvement

**Leap 14: User Experience** (Tier 4)
- Real-time visualization
- TodoWrite auto-updates
- **Result**: Polished UX

**Leap 15: Advanced Features**
- Two-stage orchestrator
- Cost tracking
- **Result**: Full feature parity

---

## Expected Outcomes

### After Leap 10 (Foundation) ✅
**User workflow**:
```bash
/clear
/primeA "implement rate limiting middleware"
# → Automatic: branch, spec, tests, code, PR, CI ✅
```

**Gap closure**: 40% (core automation working)

---

### After Leap 11 (Quality) ✅
**Additional capabilities**:
- Slop immunity blocks vague tasks
- Budget guard prevents overspend
- Retry logic handles transient failures
- Completion validator prevents 90% conclusion

**Gap closure**: 65% (production-ready)

---

### After Leap 12 (TRM-7M) ✅
**Additional capabilities**:
- DAG validation (10-100x faster)
- Type checking before tests
- Edge case auto-discovery
- 40-60% churn reduction

**Gap closure**: 85% (highly efficient)

---

### After Leap 13 (Learning) ✅
**Additional capabilities**:
- Automatic pattern application
- Cross-session learning
- Exponential improvement
- Next mission auto-proposals

**Gap closure**: 95% (self-improving)

---

### After Leap 14-15 (Polish) ✅
**Additional capabilities**:
- Real-time progress visualization
- Two-stage workflow
- Cost tracking dashboard

**Gap closure**: 100% (full vision realized)

---

## Summary Table

| Gap | Priority | Effort | Value | Recommended Leap |
|-----|----------|--------|-------|------------------|
| Task Graph Model | CRITICAL | 4-6h | Foundation | Leap 10 |
| Planner Integration | CRITICAL | 6-8h | Foundation | Leap 10 |
| Auto Branch Creation | CRITICAL | 2-3h | Foundation | Leap 10 |
| Auto PR Creation | CRITICAL | 4-5h | Foundation | Leap 10 |
| Completion Validator | HIGH | 2-3h | Reliability | Leap 11 |
| Error Recovery | HIGH | 6-8h | Reliability | Leap 11 |
| Slop Immunity | MEDIUM | 4-5h | Reliability | Leap 11 |
| Budget Guard | MEDIUM | 3-4h | Reliability | Leap 11 |
| TRM-7M Validator | HIGH | 12-16h | Efficiency | Leap 12 |
| VectorStore Integration | HIGH | 4-5h | Learning | Leap 13 |
| Real-Time Visualization | MEDIUM | 6-8h | UX | Leap 14 |
| TodoWrite Auto-Updates | MEDIUM | 2-3h | UX | Leap 14 |
| Two-Stage Orchestrator | MEDIUM | 8-10h | Advanced | Leap 15 |
| Cost Tracking | MEDIUM | 4-6h | Advanced | Leap 15 |

---

## My Recommendation

**Start with Leap 10 (Foundation)**:

```bash
/clear

# Task 1: Core infrastructure (4-6 hours)
/primeA "implement task graph model with Pydantic validation, DAG validation, and topological sort (shared/models/task_graph.py)"

# After Task 1 success:
/clear

# Task 2: Planner integration (6-8 hours)
/primeA "integrate planner agent for automatic task graph generation from natural language intent"

# After Task 2 success:
/clear

# Task 3: Complete automation (6-8 hours)
/primeA "implement automatic branch creation in Phase 0 and automatic PR creation in final phase of task graphs"
```

**Total Leap 10**: 16-22 hours, $40-55 USD

**Result**: Documented "/clear → /primeA 'task'" workflow WORKS! 🎉

Then continue with Leaps 11-15 incrementally for full vision realization.

---

**Last Updated**: 2025-10-14
