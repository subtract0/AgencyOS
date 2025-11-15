# Mission 4: Backlog Agent & primeX Orchestrator - Specification

**Date**: 2025-11-15
**Mission**: Metaproductivity 2.0 - Mission 4
**Status**: Draft
**Dependencies**: Missions 0-3 (CMP, Learning Coach, Self-Healing Agent)

---

## 1. Goals & Success Criteria

### Primary Goal
Create an intelligent backlog management system and orchestrator that automatically prioritizes, selects, and executes high-value tasks using CMP learning and prior mission infrastructure.

### Success Criteria

**SC1: Backlog Agent Operational**
- Tracks technical debt, test failures, and feature requests in structured format
- Prioritizes tasks using CMP scores, complexity estimates, and business value
- Auto-selects next-highest-value task when invoked with zero arguments
- Stores task metadata in VectorStore for cross-session learning

**SC2: primeX Orchestrator Functional**
- `/primeX` command integrates all prior missions (M0-M3)
- Accepts zero arguments (auto-select from backlog) or specific task intent
- Orchestrates: Backlog → Self-Healing (M3) → Learning Coach (M2) → CMP (M0)
- Returns PR with verified tests and CMP metadata

**SC3: Quality & Testing**
- 100% test coverage for Backlog Agent
- 100% test coverage for primeX orchestrator
- All tests passing (no regressions in prior missions)
- TDD protocol followed (RED → GREEN → REFACTOR)

**SC4: Documentation & Integration**
- Comprehensive spec (this document)
- Integration guide with existing prime commands
- Updated CLAUDE.md with Mission 4 details
- Completion report with verification

---

## 2. Personas

### P1: Developer (Primary)
**Need**: Automatic prioritization of technical debt and failed tests
**Pain Point**: Manual triage wastes time, unclear what to fix first
**Expectation**: `primeX` command auto-selects and fixes highest-priority issue

### P2: CI System
**Need**: Automated recovery from test failures
**Pain Point**: Broken builds block progress until manual intervention
**Expectation**: Self-healing + backlog integration fixes failures autonomously

### P3: Product Owner
**Need**: Visibility into backlog health and completion velocity
**Pain Point**: No metrics on technical debt reduction
**Expectation**: Backlog agent reports on task completion rates and CMP learning

---

## 3. Functional Requirements

### FR1: Backlog Storage & Persistence
**Requirement**: Backlog Agent must store tasks in structured JSON format with priority queue semantics.

**Acceptance Criteria**:
- Tasks stored in `~/.agency/memories/agency_backlog/tasks.jsonl` (JSONL for append-only ops)
- Each task has: `id`, `title`, `description`, `priority` (P1/P2/P3), `status` (pending/in_progress/completed), `created_at`, `estimated_complexity`, `cmp_related_clade_ids[]`
- Backlog Agent provides CRUD operations: `add_task()`, `get_task()`, `update_task()`, `delete_task()`
- Atomic writes (no corruption on concurrent access)

**Test Coverage**:
- `test_backlog_storage_crud()` - Create, read, update, delete tasks
- `test_backlog_persistence()` - Tasks survive process restarts
- `test_backlog_atomic_writes()` - Concurrent writes don't corrupt data

### FR2: Priority Queue & Task Selection
**Requirement**: Backlog Agent must implement intelligent task selection based on CMP scores, complexity, and business priority.

**Acceptance Criteria**:
- Priority formula: `score = (cmp_avg_score * 0.4) + (business_priority * 0.3) + (1 / estimated_complexity * 0.3)`
- `select_next_task()` returns highest-scoring pending task
- Tasks with P1 priority always selected before P2/P3 (regardless of score)
- Ties broken by `created_at` (oldest first)
- Zero-argument invocation: auto-select next task

**Test Coverage**:
- `test_priority_formula()` - Verify scoring calculation
- `test_p1_always_first()` - P1 tasks always selected first
- `test_tie_breaking()` - Oldest task wins ties
- `test_zero_argument_auto_select()` - Auto-select works correctly

### FR3: CMP Integration
**Requirement**: Backlog Agent must query CMP scores for related clades and use them in prioritization.

**Acceptance Criteria**:
- Tasks can specify `cmp_related_clade_ids` (e.g., ["self_healer_v1::gpt-5::..."])
- `select_next_task()` queries CmpStore for each clade's score
- Average CMP score used in priority formula
- If no clades specified, CMP score = 0.5 (neutral)

**Test Coverage**:
- `test_cmp_score_query()` - Queries CmpStore correctly
- `test_cmp_score_averaging()` - Averages multiple clade scores
- `test_no_clades_defaults_neutral()` - Missing clades → 0.5 score

### FR4: VectorStore Learning
**Requirement**: Backlog Agent must store task completion metadata in VectorStore for cross-session learning.

**Acceptance Criteria**:
- On task completion, store: task details, duration, outcome (success/failure), clade IDs used
- Memory key format: `backlog_task_{task_id}_{timestamp}`
- Tags: ["backlog", "task_completion", task.priority]
- Confidence score based on success rate of similar tasks

**Test Coverage**:
- `test_vectorstore_storage_on_completion()` - Task completion stores memory
- `test_memory_key_format()` - Verify key format
- `test_memory_tags()` - Verify tags

### FR5: primeX Orchestrator - Zero Argument Auto-Select
**Requirement**: `primeX` command with zero arguments must auto-select the next highest-priority task from backlog.

**Acceptance Criteria**:
- `/primeX` (no args) → calls `BacklogAgent.select_next_task()`
- Displays selected task details to user
- Proceeds with orchestration workflow (FR6)
- Updates task status to `in_progress` before execution

**Test Coverage**:
- `test_primex_zero_args_auto_select()` - Auto-selects from backlog
- `test_primex_updates_status()` - Status changes to in_progress

### FR6: primeX Orchestrator - Full Workflow
**Requirement**: `primeX` must orchestrate all prior missions (M0-M3) to complete the selected task.

**Acceptance Criteria**:
- Workflow: Backlog Agent (select) → Self-Healing Agent (fix) → Learning Coach (extract patterns) → CMP (record event)
- If task is test failure: invoke `SelfHealingAgent.heal_one_failure()`
- If task is feature request: invoke `primeccc` workflow
- On success: update task status to `completed`, store VectorStore memory
- On failure: update task status to `pending`, log error, DO NOT mark complete

**Test Coverage**:
- `test_primex_workflow_test_failure()` - Test failure workflow
- `test_primex_workflow_feature_request()` - Feature request workflow
- `test_primex_success_updates_status()` - Success updates task
- `test_primex_failure_keeps_pending()` - Failure doesn't mark complete

### FR7: primeX Orchestrator - Explicit Task Intent
**Requirement**: `primeX "fix auth bug"` must create ad-hoc task and execute immediately.

**Acceptance Criteria**:
- `/primeX "fix auth bug"` creates temporary task with P2 priority
- Executes workflow immediately (no backlog storage for ad-hoc tasks)
- Still records completion in VectorStore
- Returns PR URL on success

**Test Coverage**:
- `test_primex_explicit_intent()` - Ad-hoc task execution
- `test_primex_explicit_no_backlog_storage()` - No backlog storage for ad-hoc
- `test_primex_explicit_vectorstore_storage()` - VectorStore storage still happens

---

## 4. Data Models

### Task (Pydantic Model)
```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class TaskPriority(str, Enum):
    P1 = "P1"  # Critical (always first)
    P2 = "P2"  # High
    P3 = "P3"  # Normal

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType(str, Enum):
    TEST_FAILURE = "test_failure"
    FEATURE_REQUEST = "feature_request"
    TECH_DEBT = "tech_debt"
    BUG_FIX = "bug_fix"

class Task(BaseModel):
    id: str = Field(..., description="Unique task ID (UUID)")
    title: str = Field(..., description="Short task description")
    description: str = Field(..., description="Detailed task description")
    task_type: TaskType = Field(..., description="Type of task")
    priority: TaskPriority = Field(default=TaskPriority.P2)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    estimated_complexity: int = Field(..., ge=1, le=10, description="1=simple, 10=complex")
    business_value: int = Field(default=5, ge=1, le=10, description="1=low, 10=high")
    cmp_related_clade_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

### BacklogMetrics (Pydantic Model)
```python
class BacklogMetrics(BaseModel):
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_completion_time_hours: float
    p1_count: int
    p2_count: int
    p3_count: int
    oldest_pending_task_age_days: float
```

---

## 5. Test Plan

### Unit Tests (TDD - Write First)

**Test File**: `tests/test_backlog_agent.py`

#### TestBacklogStorage
- `test_add_task()` - Add task to backlog
- `test_get_task()` - Retrieve task by ID
- `test_update_task()` - Update existing task
- `test_delete_task()` - Delete task
- `test_persistence()` - Tasks survive restarts
- `test_atomic_writes()` - Concurrent writes safe

#### TestPriorityQueue
- `test_priority_formula()` - Score calculation correct
- `test_p1_always_first()` - P1 priority overrides score
- `test_tie_breaking()` - Oldest wins ties
- `test_select_next_task()` - Returns highest-priority task
- `test_empty_backlog()` - select_next_task() returns None

#### TestCMPIntegration
- `test_cmp_score_query()` - Queries CmpStore
- `test_cmp_score_averaging()` - Averages clade scores
- `test_no_clades_neutral()` - Missing clades → 0.5

#### TestVectorStoreIntegration
- `test_store_completion_metadata()` - Stores on completion
- `test_memory_key_format()` - Correct key format
- `test_memory_tags()` - Correct tags

**Test File**: `tests/test_primex.py`

#### TestPrimeXAutoSelect
- `test_zero_args_auto_select()` - Auto-selects from backlog
- `test_updates_task_status()` - Status → in_progress

#### TestPrimeXWorkflow
- `test_workflow_test_failure()` - Test failure flow
- `test_workflow_feature_request()` - Feature request flow
- `test_success_updates_completed()` - Success updates status
- `test_failure_keeps_pending()` - Failure doesn't mark complete

#### TestPrimeXExplicitIntent
- `test_explicit_intent_execution()` - Ad-hoc task works
- `test_explicit_no_backlog_storage()` - No backlog for ad-hoc
- `test_explicit_vectorstore_storage()` - VectorStore still used

### Integration Tests
- `test_primex_end_to_end()` - Full workflow from backlog to PR
- `test_primex_with_self_healing()` - Integration with Mission 3
- `test_primex_with_learning_coach()` - Integration with Mission 2

---

## 6. Implementation Plan

### Phase 1: Backlog Agent Core (8-10 hours)
1. **Data Models** (`shared/models/backlog.py`)
   - Task, TaskPriority, TaskStatus, TaskType, BacklogMetrics

2. **Storage Layer** (`tools/backlog_agent.py`)
   - BacklogStorage class (JSONL persistence)
   - CRUD operations
   - Atomic writes

3. **Tests** (`tests/test_backlog_agent.py`)
   - TestBacklogStorage (6 tests)
   - Run: `pytest tests/test_backlog_agent.py::TestBacklogStorage -v`

### Phase 2: Priority Queue & CMP Integration (6-8 hours)
1. **Priority Queue** (`tools/backlog_agent.py`)
   - Priority formula implementation
   - select_next_task() logic
   - Tie-breaking

2. **CMP Integration**
   - Query CmpStore for clade scores
   - Average scores for prioritization

3. **Tests** (`tests/test_backlog_agent.py`)
   - TestPriorityQueue (5 tests)
   - TestCMPIntegration (3 tests)

### Phase 3: VectorStore Learning (4-6 hours)
1. **Learning Integration** (`tools/backlog_agent.py`)
   - store_completion_metadata() method
   - Memory key/tag format

2. **Tests** (`tests/test_backlog_agent.py`)
   - TestVectorStoreIntegration (3 tests)

### Phase 4: primeX Orchestrator (10-12 hours)
1. **Command Implementation** (`.claude/commands/primeX.md`)
   - Zero-argument auto-select
   - Explicit task intent
   - Workflow orchestration

2. **Integration** (`tools/primex_orchestrator.py`)
   - Integrate with SelfHealingAgent (M3)
   - Integrate with LearningCoach (M2)
   - Integrate with CmpStore (M0)

3. **Tests** (`tests/test_primex.py`)
   - TestPrimeXAutoSelect (2 tests)
   - TestPrimeXWorkflow (4 tests)
   - TestPrimeXExplicitIntent (3 tests)

### Phase 5: Integration & Documentation (4-6 hours)
1. **Integration Tests**
   - End-to-end workflow
   - Mission 2-3 integration

2. **Documentation**
   - CLAUDE.md update
   - Integration guide
   - Completion report

---

## 7. Dependencies

**Required from Prior Missions**:
- Mission 0: CmpStore, CladeSelector, compute_clade_score
- Mission 2: LearningCoach (pattern extraction)
- Mission 3: SelfHealingAgent (test failure fixing)
- Shared: EnhancedMemoryStore (VectorStore), Result pattern

**External Dependencies**:
- `pydantic>=2.0` (data models)
- `pytest>=8.0` (testing)

---

## 8. Success Metrics

| Metric | Target | Verification Method |
|--------|--------|---------------------|
| Test Coverage | 100% | `pytest --cov=tools/backlog_agent --cov=tools/primex_orchestrator` |
| Test Pass Rate | 100% | `pytest tests/test_backlog_agent.py tests/test_primex.py -v` |
| TDD Compliance | 100% | Tests written before implementation |
| Auto-Select Accuracy | >90% | primeX selects correct highest-priority task |
| Workflow Success Rate | >95% | primeX completes tasks without errors |
| Documentation | Complete | Spec, integration guide, completion report |

---

## 9. Risk Mitigation

**Risk 1: Complexity Explosion**
- Mitigation: Start with MVP (test failures only), expand to features later
- Fallback: If too complex, split into Mission 4a (Backlog) and 4b (primeX)

**Risk 2: Integration Issues with M2-M3**
- Mitigation: Write integration tests early
- Fallback: Mock M2-M3 for initial development, integrate incrementally

**Risk 3: Priority Formula Accuracy**
- Mitigation: A/B test priority formula against manual triage
- Fallback: Add manual override flag for debugging

---

## 10. Open Questions

1. **Backlog UI**: CLI-only or add web dashboard? (MVP: CLI-only)
2. **Task Source**: Manual entry only or auto-detect from git/CI? (MVP: Manual + test failures auto-detected)
3. **Multi-Agent Coordination**: primeX runs sequentially or parallel agents? (MVP: Sequential, parallel in M5)

---

**Specification Version**: 1.0
**Last Updated**: 2025-11-15
**Author**: Claude (AgencyOS Mission 4)
**Status**: Ready for Implementation
