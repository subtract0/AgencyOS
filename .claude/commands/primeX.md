# primeX - Intelligent Task Orchestrator (Mission 4)

**Context**: You are executing the `/primeX` command to orchestrate intelligent task execution from backlog or explicit intent.

## Mission

Orchestrate autonomous task execution using the following workflow:
1. **Task Selection**: Auto-select from backlog OR use explicit intent
2. **Routing**: Route to appropriate execution agent (SelfHealingAgent, PrimeCCC, etc.)
3. **Execution**: Execute task with full workflow (code + tests + verification)
4. **Learning**: Store completion metadata in VectorStore for future optimization

## Usage Modes

### Mode 1: Auto-Select from Backlog (Zero Arguments)
```
/primeX
```

**Behavior**:
- Queries BacklogAgent for next highest-priority pending task
- Priority formula: `(cmp_avg * 0.4) + (business_value/10 * 0.3) + (1/complexity * 0.3)`
- P1 tasks ALWAYS selected before P2/P3 (regardless of score)
- Displays selected task details to user
- Updates task status to `IN_PROGRESS` before execution
- Proceeds with orchestration workflow

### Mode 2: Explicit Task Intent
```
/primeX "Fix authentication bug in login flow"
```

**Behavior**:
- Creates ad-hoc task from intent (NOT stored in backlog)
- Infers task type from keywords:
  - "test", "failing" → TEST_FAILURE
  - "add", "implement", "feature" → FEATURE_REQUEST
  - "refactor", "clean", "debt" → TECH_DEBT
  - Default → BUG_FIX
- Defaults: P2 priority, complexity=5, business_value=5
- Executes immediately (no backlog storage)
- Still stores completion metadata in VectorStore for learning

## Execution Workflow

### For TEST_FAILURE Tasks:
1. Route to SelfHealingAgent (Mission 3)
2. Agent detects failure, selects optimal clade (ε-greedy bandit)
3. Generates fix via LLM
4. Creates PR with CMP metadata
5. On success: Update task to COMPLETED, store VectorStore metadata
6. On failure: Keep task PENDING, log error

### For FEATURE_REQUEST/BUG_FIX/TECH_DEBT Tasks:
1. Route to PrimeCCCAgent (future integration)
2. Scout → Plan → Execute → Deliver workflow
3. TDD-first implementation (tests before code)
4. Constitutional compliance validation (Article I-VI)
5. On success: Update task to COMPLETED, store VectorStore metadata
6. On failure: Keep task PENDING, log error

## Success Criteria

**✅ Task Complete When**:
- All tests passing (100% pass rate)
- PR created with proper metadata
- Task status updated to COMPLETED
- VectorStore metadata stored for learning

**❌ Task Failed When**:
- Tests fail (Article II violation)
- Implementation incomplete
- PR creation fails
- Status remains PENDING (NOT marked complete on failure)

## VectorStore Learning (Article IV)

**MANDATORY**: All task completions (including ad-hoc tasks) store metadata:
- Task details (title, type, complexity, priority)
- Duration (hours)
- Outcome (success/failure)
- CMP-related clade IDs
- Completion timestamp

**Memory Key Format**: `backlog_task_{task_id}_{timestamp}`
**Tags**: `["backlog", "task_completion", priority, task_type]`

## Constitutional Compliance

**Article I**: Complete Context
- All task dependencies identified before execution
- No partial work (complete or keep pending)

**Article II**: 100% Verification
- Tests MUST pass before marking complete
- No merge without 100% test success

**Article III**: Automated Enforcement
- Quality gates enforced (no manual bypass)
- Constitutional validation before PR creation

**Article IV**: Continuous Learning
- VectorStore query BEFORE task selection (learn from past)
- VectorStore store AFTER completion (teach future)

**Article VI**: TDD Protocol
- Tests written BEFORE implementation
- RED → GREEN → REFACTOR cycle mandatory

## Example Execution

### Example 1: Auto-Select from Backlog
```
User: /primeX

Claude:
  🔍 Querying backlog for next highest-priority task...

  Selected Task:
  - ID: abc-123-def
  - Title: Fix failing test_auth_token_validation
  - Type: TEST_FAILURE
  - Priority: P1 (Critical)
  - Complexity: 4/10
  - Business Value: 9/10

  Updating status to IN_PROGRESS...

  🚀 Routing to SelfHealingAgent...
  [SelfHealingAgent execution...]

  ✅ Task completed successfully!
  - PR: https://github.com/org/repo/pull/456
  - Tests: 100% passing (47/47)
  - Duration: 0.8 hours
  - VectorStore metadata stored

  Task status updated to COMPLETED.
```

### Example 2: Explicit Intent
```
User: /primeX "Add JWT authentication support"

Claude:
  📝 Creating ad-hoc task from intent...

  Task Details:
  - Title: Add JWT authentication support
  - Type: FEATURE_REQUEST (inferred from "add")
  - Priority: P2 (default for ad-hoc)
  - Complexity: 5/10 (default)

  🚀 Routing to PrimeCCCAgent...
  [PrimeCCC workflow: Scout → Plan → Execute → Deliver]

  ✅ Task completed successfully!
  - PR: https://github.com/org/repo/pull/457
  - Tests: 100% passing (12/12 new)
  - Duration: 2.3 hours
  - VectorStore metadata stored

  Note: Ad-hoc task not stored in backlog (executed immediately).
```

## Implementation Details

**BacklogStorage**: `tools/backlog_agent.py`
- JSONL persistence: `~/.agency/memories/agency_backlog/tasks.jsonl`
- CRUD operations: add_task(), get_task(), update_task(), delete_task()
- Atomic writes (no corruption on concurrent access)

**PriorityQueue**: `tools/backlog_agent.py`
- CMP-aware scoring algorithm
- Epsilon-greedy clade selection
- Tie-breaking by created_at (oldest first)

**PrimeXOrchestrator**: `tools/primex_orchestrator.py`
- Auto-select or explicit intent routing
- Agent orchestration (SelfHealing, PrimeCCC)
- VectorStore learning integration

**Tests**:
- `tests/test_backlog_agent.py`: 18 tests (100% passing)
- `tests/test_primex.py`: 9 tests (100% passing)

## References

- **Spec**: `specs/spec-mission-4-backlog-primex.md`
- **Mission 3**: SelfHealingAgent (`tools/self_healing_agent.py`)
- **Mission 2**: LearningCoach (pattern extraction)
- **Mission 0**: CmpStore, CladeSelector (ε-greedy bandit)
- **Article IV**: Continuous Learning (VectorStore mandatory)

---

**Now execute the primeX orchestration workflow following the above protocol.**
