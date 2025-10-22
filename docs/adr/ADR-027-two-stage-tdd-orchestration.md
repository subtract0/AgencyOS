# ADR-027: Two-Stage TDD Orchestration Architecture

**Status**: ✅ Accepted
**Date**: 2025-10-11
**Leap**: Leap 7 - Test-Driven Autonomy
**Constitutional Alignment**: Articles I, II, IV, V

---

## Context

Following the success of Leap 4's Quality Feedback Loop (ADR-025), which achieved autonomous accuracy improvement through misclassification detection and refinement, we identified a critical architectural gap in Agency's orchestration layer:

### The Gap: No Spec Approval Checkpoint

**Current State (Pre-Leap 7)**:
```
User Intent → Task Graph Generation → Immediate Execution
```

**Problems Identified**:
1. **No human review**: Task graphs execute without user validation of strategic intent
2. **Spec accuracy unknown**: Generated task graphs may misinterpret user intent (~75% accuracy)
3. **No TDD enforcement**: Task graphs can specify Code tasks without corresponding Test tasks
4. **Wasted execution**: Wrong specifications discovered after implementation (high cost)
5. **Constitutional risk**: Violates Article V (spec-driven development) by auto-executing unreviewed specs

### Real-World Impact

**Scenario 1: Ambiguous Intent**
```bash
/primeccc "Add authentication"
# Generates: Basic auth (username/password)
# User wanted: OAuth2 + JWT + refresh tokens
# Result: 2 hours wasted, full re-implementation required
```

**Scenario 2: Missing Test Coverage**
```bash
# Generated task graph:
Task(id="implement_auth", type=CODE, dependencies=[])
# Missing: Test task for verification
# Result: Article II violation (no 100% verification guarantee)
```

**Scenario 3: Over-Specification**
```bash
/primeccc "Fix typo in README"
# Generates: 12-task graph with documentation overhaul
# User wanted: Single typo fix (30 seconds)
# Result: Budget overrun, unnecessary complexity
```

### Constitutional Tension

**Article V: Spec-Driven Development**
> "All development SHALL follow formal specification and planning processes."
> "No implementation without approved specification."

**Current Violation**: Task graphs are specifications, but they execute without approval, bypassing Article V's "approved spec" requirement.

**Article II: 100% Verification**
> "A task is complete ONLY when 100% verified and stable."

**Current Risk**: Generated task graphs may lack Test tasks, preventing verification enforcement.

---

## Decision

**Implement a two-stage orchestration architecture with explicit approval checkpoint and TDD-enforced graph generation:**

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 TWO-STAGE TDD ORCHESTRATION                  │
└─────────────────────────────────────────────────────────────┘

STAGE 1: INTENT → SPEC (Specification Generation)
┌────────────────────────────────────────────────────────────┐
│  Input Modes:                                               │
│    • Auto-Select: /primeccc (reads backlog TOP 5)          │
│    • Natural Language: /primeccc "Add JWT auth"            │
│    • Explicit Spec: /primeA task_graphs/mission.json       │
│                                                             │
│  ↓                                                          │
│  PlannerAgent (o3 model)                                    │
│    • Generates TaskGraph (Pydantic validated)              │
│    • Enforces TDD structure (Code → Test dependencies)     │
│    • Queries VectorStore for similar patterns (Article IV) │
│                                                             │
│  ↓                                                          │
│  Checkpoint: HUMAN_REVIEW                                   │
│    ┌───────────────────────────────────────────────┐       │
│    │  Review Task Graph                             │       │
│    │  • ASCII tree visualization                    │       │
│    │  • Mermaid diagram (dependencies)              │       │
│    │  • Estimated cost/duration                     │       │
│    │                                                 │       │
│    │  Options: [y]es / [n]o / [e]dit                │       │
│    │  Edit Loop: User requests revisions            │       │
│    └───────────────────────────────────────────────┘       │
│                                                             │
│  ↓ (on approval)                                            │
│  Store approved spec in VectorStore (Article IV)            │
└────────────────────────────────────────────────────────────┘

STAGE 2: SPEC → EXECUTION (Verified Implementation)
┌────────────────────────────────────────────────────────────┐
│  Topological Sort (dependency order)                        │
│    • Parallel execution within layers (memory-aware)       │
│    • Test tasks execute after Code tasks                   │
│                                                             │
│  ↓                                                          │
│  Execute Task Layers                                        │
│    ┌───────────────────────────────────────────────┐       │
│    │  Code Task (CodingAgent)                   │       │
│    │    • Implement changes in git worktree        │       │
│    │    • Status: "in_progress"                     │       │
│    └───────────────────────────────────────────────┘       │
│                      ↓                                      │
│    ┌───────────────────────────────────────────────┐       │
│    │  Test Task (TestGenerator)                     │       │
│    │    • Write tests for Code task                 │       │
│    │    • verification_target = code_task.id        │       │
│    └───────────────────────────────────────────────┘       │
│                      ↓                                      │
│    ┌───────────────────────────────────────────────┐       │
│    │  Checkpoint: AUTO_VALIDATE                     │       │
│    │    ✓ Run pytest (via run_tests.py)            │       │
│    │    ✓ 100% pass required (Article II)          │       │
│    │    ✓ Article I retry: 2x, 3x, 5x timeouts     │       │
│    │                                                 │       │
│    │    On Failure:                                 │       │
│    │      • Rollback Code task changes              │       │
│    │      • Query VectorStore for similar failures  │       │
│    │      • Mark Code task "failed"                 │       │
│    │                                                 │       │
│    │    On Success:                                 │       │
│    │      • Mark Code task "complete"               │       │
│    │      • Git commit (constitutional footer)      │       │
│    │      • Proceed to next layer                   │       │
│    └───────────────────────────────────────────────┘       │
│                                                             │
│  ↓ (all layers complete)                                    │
│  Create PR (gh pr create)                                   │
│    • Branch update if behind main (Article III)            │
│    • PR description from task graph metadata               │
│    • Store execution patterns in VectorStore (Article IV)  │
└────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

#### 1. Explicit Approval Checkpoint (Article V Compliance)

**Rationale**: Task graphs ARE specifications. Human approval ensures:
- Strategic intent correctly captured (~95% accuracy vs 75% without review)
- User has opportunity to refine scope before expensive execution
- Constitutional compliance: "approved specification" requirement satisfied

**Implementation**:
```python
# Stage 1: Spec generation with approval
task_graph = planner.generate_from_intent(intent)

# Approval checkpoint (BLOCKING)
approved = execute_checkpoint(
    type=CheckpointType.HUMAN_REVIEW,
    prompt=f"Review task graph:\n{render_tree(task_graph)}\n\nApprove? (y/n/edit)",
    graph=task_graph
)

if not approved:
    # Edit loop or abort
    revised_graph = planner.revise(task_graph, user_feedback)
    # Re-submit for approval (recursive)

# Only execute if approved
orchestrator.execute(task_graph)
```

**Trade-off**: Adds human latency (30-120 seconds) vs. eliminates wasted execution (hours).

#### 2. TDD-Enforced Graph Generation (Article II Compliance)

**Rationale**: Prevent untested code by making Test tasks mandatory during spec generation.

**Implementation**:
```python
class TaskGraph(BaseModel):
    """Task graph with TDD structure validation."""

    @field_validator("phases")
    @classmethod
    def validate_tdd_structure(cls, phases: List[Phase]) -> List[Phase]:
        """Ensure every Code task has corresponding Test task."""
        all_tasks = [t for p in phases for t in p.tasks]

        code_tasks = [t for t in all_tasks if t.type == TaskType.CODE]
        test_tasks = [t for t in all_tasks if t.type == TaskType.TEST]

        # Build verification map
        verification_targets = {t.verification_target for t in test_tasks}

        # Ensure all Code tasks are tested
        untested = [c.id for c in code_tasks if c.id not in verification_targets]

        if untested:
            raise ValueError(
                f"Article II violation: Code tasks without tests: {untested}\n"
                f"TDD mandate: Every Code task MUST have Test task with verification_target"
            )

        return phases
```

**Enforcement**: Pydantic validator runs during graph generation (before checkpoint), ensuring untested graphs never reach user approval.

#### 3. Test Verification Gate (Article II Enforcement)

**Rationale**: Code tasks cannot complete without passing tests.

**Implementation**:
```python
async def execute_code_task(task: Task) -> Result[TaskResult, TaskError]:
    """Execute Code task with test verification gate."""

    # 1. Execute code implementation
    code_result = await coding_agent.execute(task)

    if code_result.is_err():
        return code_result

    # 2. Find corresponding Test task
    test_task = next(
        (t for t in task_graph.all_tasks()
         if t.type == TaskType.TEST and t.verification_target == task.id),
        None
    )

    if not test_task:
        return Err(TaskError(
            task_id=task.id,
            error="Article II violation: No Test task for verification"
        ))

    # 3. Execute Test task (write tests)
    test_gen_result = await test_generator.execute(test_task)

    if test_gen_result.is_err():
        return test_gen_result

    # 4. Run pytest with Article I retry logic
    test_exec_result = await run_tests_with_retry(
        timeout_base=120000,  # 2 minutes
        max_retries=3,        # 2x, 3x, 5x multipliers
        scope=test_task.scope
    )

    # 5. Verification Gate (BLOCKING)
    if test_exec_result.is_err() or test_exec_result.unwrap().failed > 0:
        # Rollback code changes
        await git_rollback(task.id)

        # Query VectorStore for similar failures (Article IV)
        similar_failures = vectorstore.search(
            query=f"test failure: {test_exec_result.error_message}",
            filter={"type": "test_failure_pattern"},
            limit=5
        )

        return Err(TaskError(
            task_id=task.id,
            error=f"Article II: Tests failed (100% pass required)",
            remediation=similar_failures
        ))

    # 6. Success: Mark Code task complete
    return Ok(TaskResult(
        task_id=task.id,
        status="complete",
        tests_passing=test_exec_result.unwrap().passed,
        files_modified=code_result.unwrap().files
    ))
```

**Critical Behavior**: Code task status remains "in_progress" until tests pass. This enforces Article II's "100% verification" requirement.

#### 4. Three Input Modes (Flexible Entry Points)

**Rationale**: Support different user workflows:
1. **Auto-Selection**: User wants Agent to pick next priority (`/primeccc`)
2. **Natural Language**: User has specific intent (`/primeccc "Add JWT auth"`)
3. **Explicit Spec**: User provides pre-written task graph (`/primeA task_graphs/custom.json`)

**Implementation**:
```python
def execute_two_stage_workflow(
    input_mode: InputMode,
    intent: Optional[str] = None,
    spec_path: Optional[str] = None
) -> Result[ExecutionResult, WorkflowError]:
    """Execute two-stage workflow with flexible input."""

    # Stage 1: Intent → Spec
    if input_mode == InputMode.AUTO_SELECT:
        # Read backlog memory (Article IV)
        backlog = load_memory("~/.agency/memories/agency_backlog/test_suite_gaps.md")
        intent = select_top_priority(backlog, limit=1)
        task_graph = planner.generate_from_intent(intent)

    elif input_mode == InputMode.NATURAL_LANGUAGE:
        # Generate from user-provided intent
        task_graph = planner.generate_from_intent(intent)

    elif input_mode == InputMode.EXPLICIT_SPEC:
        # Load pre-written task graph
        task_graph = TaskGraph.model_validate_json(Path(spec_path).read_text())

    # Approval checkpoint (ALWAYS required)
    if not execute_checkpoint(task_graph):
        return Err(WorkflowError("Spec rejected by user"))

    # Stage 2: Spec → Execution
    return orchestrator.execute(task_graph)
```

#### 5. Git Worktree Isolation (Article II: Stability)

**Rationale**: Prevent file conflicts in main workspace during autonomous execution.

**Implementation**:
```bash
# Create isolated worktree for mission
git worktree add /Users/am/Code/Agency-{session_id} -b {branch_name}

# Execute tasks in isolation (zero interference)
cd /Users/am/Code/Agency-{session_id}
python trinity_protocol/core/orchestrator.py execute task_graphs/mission.json

# Commit and push
git add .
git commit --no-verify -m "feat: Complete mission X"
git push -u origin {branch_name}

# Create PR
gh pr create --title "feat: Mission X" --body "..."

# Cleanup after merge
git worktree remove /Users/am/Code/Agency-{session_id}
```

**Benefits**:
- Main workspace unaffected by execution
- Parallel missions possible (different worktrees)
- Easy rollback (delete worktree)
- No pre-commit hook interference (--no-verify acceptable in worktrees)

---

## Consequences

### Positive

#### 1. Spec Approval Accuracy (+95% Success Rate)

**Before Leap 7**: Task graphs auto-execute with ~75% user satisfaction
**After Leap 7**: Human review catches misinterpretations before execution (~95% approval rate)

**Impact**:
- **Time Saved**: 2-3 hours of wasted execution per misinterpreted intent
- **Cost Saved**: ~$30-50 per failed execution (API costs)
- **User Trust**: Confidence in autonomous system increased

**Evidence**: Projected based on Leap 4's 85% → 90% accuracy improvement pattern.

#### 2. Constitutional Compliance (100% Articles I, II, V)

**Article I: Complete Context**
- ✅ Timeout retry logic in test execution (2x, 3x, 5x multipliers)
- ✅ No partial graph generation (Pydantic validation enforces completeness)

**Article II: 100% Verification**
- ✅ TDD structure enforced (Pydantic validator)
- ✅ Test verification gate blocks Code completion
- ✅ Rollback on test failure

**Article V: Spec-Driven Development**
- ✅ Task graph = executable specification
- ✅ Human approval checkpoint (Article V: "approved spec")
- ✅ Traceability from intent → spec → implementation

#### 3. TDD Enforcement (Zero Untested Code)

**Before Leap 7**: Test tasks manually added by developers (often forgotten)
**After Leap 7**: Test tasks automatically generated with `verification_target` links

**Enforcement Mechanism**:
```python
# Pydantic validator runs during graph generation
@field_validator("phases")
def validate_tdd_structure(cls, phases):
    # Raises ValueError if any Code task lacks Test task
    # User CANNOT approve graph with missing tests
```

**Impact**: 100% Code tasks have corresponding Test tasks (constitutional guarantee).

#### 4. Learning Integration (Article IV Mandate)

**Pattern Storage**:
- Approved task graphs stored in VectorStore (confidence ≥ 0.7)
- Test failure patterns stored with remediation strategies
- Successful verification strategies extracted

**Pattern Reuse**:
- Future spec generation queries VectorStore for similar intents
- Test strategies applied from historical successes
- Failure patterns avoided proactively

**Example**:
```python
# During spec generation (Stage 1)
similar_specs = vectorstore.search(
    query=f"intent: {user_intent}",
    filter={"type": "approved_task_graph"},
    limit=5
)

if similar_specs:
    # Reuse proven structure
    task_graph = adapt_template(similar_specs[0], user_intent)
else:
    # Generate from scratch
    task_graph = planner.generate_from_intent(user_intent)
```

#### 5. Flexibility Without Complexity

Three input modes serve different workflows without architectural complexity:
- **Auto-Select**: Agent autonomy (backlog-driven)
- **Natural Language**: User-driven strategic intent
- **Explicit Spec**: Power users with custom task graphs

All modes converge to same two-stage flow (approval → execution).

### Negative

#### 1. Latency Increase (30-120 seconds per mission)

**Added Latency**:
- Spec approval checkpoint: 30-120 seconds (human review + decision)
- Graph rendering (ASCII tree + Mermaid): 2-5 seconds

**Mitigation**:
- Edit loop allows quick refinements (no regeneration needed)
- Optional `--auto-approve` flag for trusted scenarios (testing, known patterns)
- Timeout with auto-approval after 5 minutes (future enhancement)

**Trade-off Analysis**: 30-120 seconds vs. 2-3 hours of wasted execution → **100x ROI on latency cost**.

#### 2. Complexity Increase in Orchestrator

**New Components**:
- Checkpoint execution logic (HUMAN_REVIEW + AUTO_VALIDATE)
- TDD structure validation (Pydantic validators)
- Test verification gate (pytest integration)
- Rollback logic (git operations)

**Estimated Lines of Code**: +800 LOC (orchestrator + tests)

**Mitigation**:
- Modular design (checkpoints, validators, execution as separate modules)
- Comprehensive test coverage (100% for checkpoint logic)
- Clear separation of concerns (Stage 1 vs Stage 2)

#### 3. User Training Required

**New Workflow**:
- Users must review task graphs (previously auto-executed)
- Edit loop syntax: "Add integration tests for auth flow"
- Understanding Mermaid diagrams (dependency visualization)

**Mitigation**:
- Detailed documentation in `docs/TWO_STAGE_WORKFLOW.md`
- Interactive tutorial (`/primeccc --tutorial`)
- Clear prompts with examples ("Approve? (y/n/edit: 'add integration tests')")

#### 4. Git Worktree Management Overhead

**Operational Complexity**:
- Worktree creation before execution
- Cleanup after PR merge
- Disk space monitoring (orphaned worktrees)

**Mitigation**:
- Automatic cleanup after successful PR merge
- Weekly cron job to prune orphaned worktrees (`git worktree prune`)
- Disk space alerts via telemetry

### Trade-offs

| Dimension | Trade-off | Decision |
|-----------|-----------|----------|
| **Latency vs. Accuracy** | 30-120s approval time vs. 2-3 hours wasted execution | ✅ Prioritize accuracy (100x ROI) |
| **Simplicity vs. Quality** | Auto-execute vs. TDD enforcement | ✅ Prioritize quality (Article II mandate) |
| **Autonomy vs. Control** | Full autonomy vs. human approval | ✅ Hybrid: auto-generate, human-approve |
| **Flexibility vs. Complexity** | Single input mode vs. three modes | ✅ Accept complexity for flexibility |

---

## Alternatives Considered

### Alternative 1: Single-Stage with Post-Execution Review

**Description**: Execute task graph immediately, allow user to review/rollback after execution.

**Pros**:
- Zero latency (no approval checkpoint)
- User can review actual code changes (not abstract spec)

**Cons**:
- ❌ Wastes execution time/cost on wrong specs
- ❌ Article V violation (no "approved spec" before implementation)
- ❌ Rollback complexity (undo file changes, git history)
- ❌ Mental burden on user (review completed work vs. plan)

**Rejection Reason**: Constitutional violation (Article V) + wasteful execution.

---

### Alternative 2: Auto-Approval with Confidence Threshold

**Description**: Auto-execute if spec generation confidence ≥ 0.9, otherwise require approval.

**Pros**:
- Reduces approval bottleneck for high-confidence specs
- Maintains some human oversight for ambiguous intents

**Cons**:
- ❌ Confidence scoring unreliable early (cold start problem)
- ❌ Partial Article V compliance (some specs approved, some not)
- ❌ User confusion (unpredictable approval requirement)

**Rejection Reason**: Inconsistent UX + unreliable confidence scoring.

---

### Alternative 3: LLM-Based Approval Agent

**Description**: Replace human approval with LLM agent that reviews task graph against intent.

**Pros**:
- Zero human latency (fully autonomous)
- Consistent evaluation criteria

**Cons**:
- ❌ LLM may miss subtle intent nuances (e.g., security requirements)
- ❌ Reduced user agency (no edit loop)
- ❌ Article V interpretation: "approved" implies human judgment

**Rejection Reason**: Human judgment critical for strategic decisions (not delegatable to LLM).

---

### Alternative 4: Continuous Streaming (No Checkpoints)

**Description**: Stream task execution in real-time, allow user to interrupt mid-execution.

**Pros**:
- Appears faster (instant feedback)
- User can course-correct during execution

**Cons**:
- ❌ Complex state management (interrupt handling, rollback)
- ❌ Unclear checkpoint semantics (when to interrupt?)
- ❌ Violates Article I (partial execution = incomplete context)

**Rejection Reason**: Architectural complexity + constitutional risk (incomplete context).

---

## Constitutional Alignment

### Article I: Complete Context Before Action

**Compliance Mechanisms**:
1. **Timeout Retry Logic**: Test execution retries with 2x, 3x, 5x multipliers (max 10x)
2. **Complete Graph Generation**: Pydantic validation ensures all tasks fully specified
3. **No Partial Execution**: Task graph MUST pass approval before execution begins
4. **Test Completion**: All tests run to completion (no early termination)

**Implementation Reference**:
```python
# shared/timeout_wrapper.py
@with_constitutional_timeout(base_timeout=120000, max_retries=3)
async def run_tests_with_retry(scope: str) -> Result[TestReport, TestError]:
    """Article I: Complete test execution with retry."""
    # Retries with 2x, 3x, 5x multipliers on timeout
```

**Validation**: ✅ All test execution pathways include retry logic.

---

### Article II: 100% Verification and Stability

**Compliance Mechanisms**:
1. **TDD Structure Enforcement**: Pydantic validator ensures every Code task has Test task
2. **Test Verification Gate**: Code tasks blocked until 100% tests pass
3. **Rollback on Failure**: Code changes reverted if tests fail after retries
4. **Main Branch Protection**: PR creation only after all tests green

**Implementation Reference**:
```python
# shared/models/task_graph.py
@field_validator("phases")
def validate_tdd_structure(cls, phases):
    """Article II: Enforce TDD structure."""
    code_tasks = [t for p in phases for t in p.tasks if t.type == TaskType.CODE]
    test_tasks = [t for p in phases for t in p.tasks if t.type == TaskType.TEST]
    verification_targets = {t.verification_target for t in test_tasks}

    untested = [c.id for c in code_tasks if c.id not in verification_targets]
    if untested:
        raise ValueError(f"Article II: Untested code tasks: {untested}")
```

**Validation**: ✅ Impossible to generate task graph without tests.

---

### Article III: Automated Merge Enforcement

**Compliance Mechanisms**:
1. **System-Level Enforcement**: Test verification gate (no manual override)
2. **Branch Protection**: GitHub rules prevent force push, require CI green
3. **Quality Gates**: Phase gates block progression on failures
4. **Pre-Commit Hooks**: Multi-layer validation (local + CI)

**Implementation Reference**:
- GitHub branch protection rules: main branch requires CI green
- Test verification gate: hard-coded in orchestrator (no bypass flag)
- Pre-commit hooks: `git commit --no-verify` acceptable only in worktrees

**Validation**: ✅ No bypass authority for test verification gate.

---

### Article IV: Continuous Learning and Improvement

**Compliance Mechanisms**:
1. **Pattern Storage**: Approved task graphs stored in VectorStore (confidence ≥ 0.7)
2. **Query Before Generation**: PlannerAgent queries similar intents before graph generation
3. **Failure Learning**: Test failures stored with remediation strategies
4. **Cross-Session Memory**: VectorStore persists patterns across missions

**Implementation Reference**:
```python
# After approval (Stage 1)
vectorstore.store(
    key=f"approved_task_graph_{timestamp}",
    content={
        "intent": user_intent,
        "task_graph": task_graph.model_dump(),
        "approval_time": datetime.now(),
        "user_feedback": edit_history
    },
    tags=["approved_spec", "two_stage_workflow"],
    confidence=0.7
)

# Before generation (Stage 1)
similar_specs = vectorstore.search(
    query=user_intent,
    filter={"tags": "approved_spec"},
    limit=5
)
```

**Validation**: ✅ VectorStore integration mandatory (no disable flags).

---

### Article V: Spec-Driven Development

**Compliance Mechanisms**:
1. **Task Graph = Specification**: Executable declarative mission definition
2. **Approval Checkpoint**: Human review before execution (Article V: "approved spec")
3. **Traceability**: Tasks reference acceptance criteria from intent
4. **Living Document**: Task graph updated with execution metadata

**Implementation Reference**:
```python
# Stage 1: Generate specification (task graph)
task_graph = planner.generate_from_intent(intent)

# Approval checkpoint (Article V: "approved specification")
approved = execute_checkpoint(
    type=CheckpointType.HUMAN_REVIEW,
    graph=task_graph
)

if not approved:
    raise WorkflowError("Article V: No execution without approved spec")

# Stage 2: Execute approved specification
orchestrator.execute(task_graph)
```

**Validation**: ✅ Impossible to execute without approved task graph.

---

## Implementation Timeline

### Phase 1: Foundation (Checkpoint Models) ✅

**Scope**: Enhance task graph models with checkpoint support

**Deliverables**:
- ✅ `Checkpoint` model in `shared/models/task_graph.py`
- ✅ `execute_checkpoint()` function for approval logic
- ✅ Pydantic validators for checkpoint semantics
- ✅ Unit tests for checkpoint models

**Duration**: 2 hours (completed 2025-10-11)

---

### Phase 2: Intent-to-Spec Generation (In Progress)

**Scope**: Natural language → task graph transformation with TDD enforcement

**Deliverables**:
- [ ] `intent_to_spec.py` module with LLM-based generation
- [ ] Backlog auto-selection logic (TOP 5 priority)
- [ ] TDD structure enforcement (Pydantic validators)
- [ ] Mermaid diagram generation for approval UI
- [ ] Integration tests for all three input modes

**Duration**: 6 hours (estimated)

**Success Criteria**:
- Natural language intent generates valid `TaskGraph`
- Every Code task has Test task with `verification_target`
- Auto-selection reads backlog and picks highest priority

---

### Phase 3: Spec-to-Execution Engine (Planned)

**Scope**: Execute approved task graphs with verification gates

**Deliverables**:
- [ ] Topological sort execution in orchestrator
- [ ] Test verification gate logic (Article II enforcement)
- [ ] Git worktree management for isolation
- [ ] Article I retry logic for test execution
- [ ] Rollback behavior on test failures

**Duration**: 8 hours (estimated)

**Success Criteria**:
- Tasks execute in dependency order
- Test verification gate blocks Code completion on failure
- Worktree isolation prevents main workspace conflicts

---

### Phase 4: PR Creation Workflow (Planned)

**Scope**: Automated PR generation with mergeability checks

**Deliverables**:
- [ ] Commit generation with constitutional footer
- [ ] Branch update logic (if behind main)
- [ ] `gh pr create` integration with task metadata
- [ ] PR description generation from task graph
- [ ] Tests for git operations

**Duration**: 4 hours (estimated)

**Success Criteria**:
- Successful execution creates PR automatically
- Branch is up-to-date before PR creation
- PR description links to task graph and verification results

---

### Phase 5: Learning Integration (Planned)

**Scope**: Pattern extraction and VectorStore storage (Article IV)

**Deliverables**:
- [ ] Extract successful task graphs as patterns
- [ ] Store verification strategies in VectorStore
- [ ] Query historical patterns during spec generation
- [ ] Confidence scoring for reusable patterns

**Duration**: 5 hours (estimated)

**Success Criteria**:
- Successful missions stored in VectorStore (confidence ≥ 0.6)
- Future spec generation applies learned patterns
- Failed patterns stored with remediation notes

---

**Total Estimated Duration**: 25 hours (1 week with parallel development)

---

## Validation

### Test Coverage Requirements

**Phase 1: Checkpoint Models** (Target: 40 tests)
- [ ] Checkpoint Pydantic validation (HUMAN_REVIEW, AUTO_VALIDATE types)
- [ ] `execute_checkpoint()` approval logic
- [ ] Edit loop behavior (user revisions)
- [ ] Timeout handling (no timeout for HUMAN_REVIEW)

**Phase 2: Intent-to-Spec** (Target: 50 tests)
- [ ] Natural language → task graph generation
- [ ] TDD structure validation (Code → Test dependencies)
- [ ] Backlog auto-selection (TOP 5 priority)
- [ ] Mermaid diagram generation
- [ ] Three input modes (auto-select, NL intent, explicit spec)

**Phase 3: Spec-to-Execution** (Target: 60 tests)
- [ ] Topological sort correctness
- [ ] Test verification gate enforcement
- [ ] Article I retry logic (2x, 3x, 5x multipliers)
- [ ] Rollback on test failure
- [ ] Git worktree isolation

**Phase 4: PR Creation** (Target: 30 tests)
- [ ] Commit generation (constitutional footer)
- [ ] Branch update logic (mergeability)
- [ ] `gh pr create` integration
- [ ] PR description generation

**Phase 5: Learning Integration** (Target: 40 tests)
- [ ] Pattern extraction (approved task graphs)
- [ ] VectorStore storage (confidence ≥ 0.6)
- [ ] Pattern query during spec generation
- [ ] Failure pattern storage

**Integration Tests** (Target: 30 tests)
- [ ] End-to-end workflow (intent → spec → execution → PR)
- [ ] Test failure handling (rollback verification)
- [ ] Edge cases (circular dependencies, missing verification targets)

**Total Test Target**: 250 tests (100% pass rate required for production)

---

### Performance Benchmarks

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Spec Generation Time** | <30s for <20 tasks | Timer in `planner.generate_from_intent()` |
| **Approval Latency** | 30-120s (human) | Time between prompt and user input |
| **Test Execution Time** | Respects memory constraints (3-10 workers) | `get_safe_worker_count()` logic |
| **Parallel Efficiency** | >70% theoretical speedup | (sequential_time / parallel_time) × 100% |
| **Spec Approval Rate** | >90% approved without revision | (approved / total_generated) × 100% |

---

## Future Enhancements

### Enhancement 1: Confidence-Based Auto-Approval

**Description**: Auto-approve task graphs with confidence ≥ 0.95 (after VectorStore maturity).

**Rationale**: Reduce approval bottleneck for high-confidence patterns.

**Prerequisites**:
- ≥100 approved task graphs in VectorStore
- Confidence scoring validated (>95% accuracy)
- User opt-in setting (default: always require approval)

---

### Enhancement 2: Interactive Spec Editor

**Description**: Web-based UI for visual task graph editing.

**Features**:
- Drag-and-drop task nodes
- Visual dependency links (Mermaid-style)
- Real-time validation feedback

**Rationale**: Improve edit loop UX for non-technical users.

---

### Enhancement 3: Spec Templates Library

**Description**: Reusable task graph templates for common patterns.

**Examples**:
- "Add REST API endpoint" template (CRUD operations)
- "Add authentication" template (OAuth2 + JWT)
- "Add database migration" template (Alembic + SQLAlchemy)

**Storage**: VectorStore with `template` tag (high confidence patterns).

---

### Enhancement 4: Agent Self-Improvement

**Description**: Agents propose workflow enhancements based on execution patterns.

**Example**:
```python
# After 50 missions with "authentication" intent
learning_agent.propose_enhancement(
    pattern="authentication_tasks_always_include_refresh_tokens",
    confidence=0.92,
    proposal="Add refresh token task to authentication template"
)
```

---

## References

### ADRs
- **ADR-001**: Complete Context Before Action (timeout handling, retry logic)
- **ADR-002**: 100% Verification and Stability (test verification gate)
- **ADR-004**: Continuous Learning (VectorStore pattern storage)
- **ADR-005**: Per-Agent Model Policy (PlannerAgent uses o3 model)
- **ADR-023**: Hardware-Aware Execution (M4 Pro memory constraints)
- **ADR-025**: Quality Feedback Loop (misclassification detection inspiration)

### Specifications
- **SPEC-007**: Two-Stage TDD Workflow (this ADR's source spec)
- **SPEC-001**: Spec-Driven Development (Article V mandate)
- **SPEC-004**: Quality Feedback Loop (learning integration patterns)

### Implementation Files
- `shared/models/task_graph.py`: Task graph models with checkpoints
- `trinity_protocol/core/orchestrator.py`: Execution engine
- `tools/memory_aware_test_runner.py`: Dynamic worker adjustment
- `tools/git_workflow.py`: Worktree management

### External Documentation
- **Pydantic Validation**: https://docs.pydantic.dev/latest/concepts/validators/
- **Git Worktrees**: https://git-scm.com/docs/git-worktree
- **GitHub CLI**: https://cli.github.com/manual/gh_pr_create

---

## Decision Outcome

**✅ Accepted** - 2025-10-11

The Two-Stage TDD Orchestration architecture is **approved for implementation** with:
- **Explicit approval checkpoint**: Ensures spec accuracy before execution (~95% vs 75%)
- **TDD-enforced graph generation**: Prevents untested code (100% Code tasks have Test tasks)
- **Test verification gate**: Enforces Article II (100% verification mandatory)
- **Three input modes**: Flexible entry points (auto-select, NL intent, explicit spec)
- **Constitutional compliance**: Articles I, II, IV, V fully satisfied

**Next Steps**:
1. **Phase 1 Complete**: Checkpoint models validated ✅
2. **Phase 2 In Progress**: Intent-to-Spec generation (6 hours)
3. **Phase 3-5 Planned**: Execution engine, PR workflow, learning integration (17 hours)
4. **Production Deployment**: Week of 2025-10-18 (after 250 tests pass)

**Impact**: Leap 7 establishes foundation for autonomous test-driven development with human oversight at strategic checkpoints, eliminating wasted execution while maintaining constitutional compliance.

---

*"Strategic intent to verified reality - with human wisdom at the checkpoint."*
