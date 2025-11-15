# Spec: Mission 3 - Self-Healing Agent

**Date**: 2025-11-15
**Status**: Draft
**Priority**: P0 (Critical Path - Metaproductivity 2.0)
**Estimated Effort**: 10-14 hours
**Prerequisites**: Mission 0 (CMP scaffolding), Mission 1 (Foundation), Mission 2 (Learning Coach)

---

## Goals

**Primary Goal**: Implement an autonomous agent that detects failing tests, generates fixes using CladeSelector-chosen configurations, creates PRs, and learns from human feedback via CMP reinforcement signals.

**Success Criteria**:
1. SelfHealingAgent detects failing tests from `test-results/*.json`
2. CladeSelector (ε-greedy bandit) chooses optimal clade configuration
3. Agent generates fix, creates autogen/* PR with CMP metadata
4. auto_supervise_hook (Mission 2) records outcome as CmpEvent
5. CladeSelector evolves: high-approval clades exploited, low-approval clades avoided
6. 100% test coverage (TDD): tests written FIRST, implementation SECOND

**Non-Goals**:
- Manual test fixing (agent is autonomous)
- 100% auto-approval rate (human judgment is the ground truth)
- Fixing non-test code (scope: test failures only)

---

## Personas

### **Persona 1: Autonomous Developer**
**Goal**: Fix failing tests 24/7 without human intervention
**Pain Points**:
- Test suite has 50-200 failures (3.7% failure rate)
- Manual fixing is time-consuming and context-switching
- No systematic learning from past fixes
**Needs**:
- Automatic detection of failing tests
- Intelligent clade selection (model + prompt + strategy)
- PR creation with traceability metadata

### **Persona 2: Human Reviewer**
**Goal**: Approve/reject autonomous PRs efficiently
**Pain Points**:
- Need to understand what fix was attempted
- Want to see agent's reasoning (which clade, why)
- Need confidence that bad clades won't be reused
**Needs**:
- Clear PR metadata (clade_id, task_type, failure description)
- Transparent bandit decision (explore vs exploit)
- CMP feedback loop ensures learning

### **Persona 3: System Architect**
**Goal**: Maximize metaproductivity via reinforcement learning
**Pain Points**:
- Don't know which model/prompt/strategy combinations work best
- No data-driven clade optimization
- Expensive to run experiments manually
**Needs**:
- CMP event tracking (approval/rejection signals)
- CladeSelector bandit algorithm (ε-greedy)
- Clade score evolution over time

---

## Functional Requirements

### **FR1: Test Failure Detection**
**As an** Autonomous Developer
**I want to** detect failing tests from test results JSON
**So that** I can prioritize which failures to fix

**Acceptance Criteria**:
- ✅ Read `test-results/full-suite-final.json` (pytest-json-report format)
- ✅ Parse failures: extract test name, file, line number, error message
- ✅ Filter out skipped tests (only fix failures)
- ✅ Return list of `TestFailure` objects (dataclass with typed fields)
- ✅ Handle missing/malformed JSON gracefully (Result<T,E> pattern)

**Test Coverage**:
- Unit test: Parse valid JSON with 3 failures → returns 3 TestFailure objects
- Unit test: Parse JSON with 0 failures → returns empty list
- Unit test: Parse malformed JSON → returns Err(ParseError)
- Unit test: Missing JSON file → returns Err(FileNotFound)

---

### **FR2: Clade Configuration Registry**
**As a** System Architect
**I want to** define available clade configurations
**So that** CladeSelector can choose from valid options

**Acceptance Criteria**:
- ✅ Define clade format: `<agent_id>::<model_name>::<prompt_profile>::<strategy>`
- ✅ Create `CladeConfig` dataclass (agent_id, model_name, prompt_profile, strategy)
- ✅ Registry: `SELF_HEALING_CLADES: list[CladeConfig]` with 3-5 variations
- ✅ Example clades:
  - `"self_healer_v1::gpt-5::prompt_full_context::strategy_careful"` (high-quality, slow)
  - `"self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal"` (fast, minimal changes)
  - `"self_healer_v1::gpt-5-mini::prompt_terse::strategy_quick"` (cheap, quick fixes)

**Test Coverage**:
- Unit test: Registry has 3+ clades
- Unit test: All clades follow format validation (regex: `^\w+::\w+::\w+::\w+$`)
- Unit test: build_clade_id() from CladeConfig → correct string format

---

### **FR3: CladeSelector Integration**
**As an** Autonomous Developer
**I want to** use epsilon-greedy bandit to select the best clade
**So that** I balance exploration (try new clades) and exploitation (use proven clades)

**Acceptance Criteria**:
- ✅ Import `CladeSelector` from `agency_memory.learning`
- ✅ Initialize with `CmpStore` (load historical events)
- ✅ Call `selector.select_clade(task_type="self_heal", available_clades=..., epsilon=0.1)`
- ✅ Default epsilon=0.1 (10% explore, 90% exploit)
- ✅ Return selected clade_id string

**Test Coverage**:
- Unit test (mocked CmpStore): epsilon=1.0 → always explores (random selection)
- Unit test (mocked CmpStore with events): epsilon=0.0 → always exploits (highest score)
- Unit test (mocked CmpStore): epsilon=0.1 → ~10% explore, ~90% exploit (over 100 trials)

---

### **FR4: Fix Generation**
**As an** Autonomous Developer
**I want to** generate a fix for a failing test using the selected clade
**So that** I can create a PR with the proposed solution

**Acceptance Criteria**:
- ✅ Input: `TestFailure`, `CladeConfig`
- ✅ Build prompt from clade's `prompt_profile`:
  - `prompt_full_context`: Include test file, implementation file, error traceback
  - `prompt_small_diff_v1`: Include only test function and error message
  - `prompt_terse`: Include only error message
- ✅ Call LLM (model from clade) with prompt
- ✅ Parse LLM response → extract code changes (file path + new content)
- ✅ Validate: changes only affect test file or related implementation
- ✅ Return `FixProposal` dataclass (files_changed: dict[str, str], reasoning: str)

**Test Coverage**:
- Unit test (mocked LLM): Full context prompt → returns valid fix
- Unit test (mocked LLM): Small diff prompt → returns minimal fix
- Unit test (mocked LLM): LLM returns invalid response → returns Err(InvalidFix)
- Integration test: Real LLM call with real test failure → generates compilable Python

---

### **FR5: PR Creation with CMP Metadata**
**As a** Human Reviewer
**I want to** see PR metadata (clade_id, task_type, memory_ids) in PR body
**So that** auto_supervise_hook can track outcomes

**Acceptance Criteria**:
- ✅ Create branch: `autogen/selfheal-<agent_id>-<model>-<prompt>-<strategy>-<short_id>`
- ✅ Commit fix with message: `fix: [self_heal] Fix <test_name> using <clade_id>`
- ✅ PR body includes HTML comments:
  ```html
  <!-- agent_id: self_healer_v1 -->
  <!-- clade_id: self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal -->
  <!-- task_type: self_heal -->
  <!-- memory_ids: ["mem_001", "mem_002"] -->
  ```
- ✅ PR title: `[self_heal] Fix <test_name>`
- ✅ PR description: Include test failure, fix reasoning, clade used

**Test Coverage**:
- Unit test: build_pr_metadata() → returns correct HTML comments
- Unit test: build_branch_name() → follows format `autogen/selfheal-...-<short_id>`
- Integration test (dry-run): Create PR on test repo → metadata parseable by auto_supervise_hook

---

### **FR6: End-to-End Self-Healing Workflow**
**As a** System Architect
**I want to** run the full self-healing loop
**So that** the agent autonomously fixes tests and learns from outcomes

**Acceptance Criteria**:
- ✅ Entry point: `tools/self_healing_agent.py --max-fixes=5`
- ✅ Workflow:
  1. Detect failures (FR1)
  2. For each failure (up to `--max-fixes`):
     a. Select clade (FR3)
     b. Generate fix (FR4)
     c. Create PR (FR5)
     d. Record memory_ids (store fix attempt in VectorStore)
  3. Exit when: max-fixes reached OR no failures left
- ✅ Logging: INFO-level logs for each step (clade selected, fix generated, PR created)
- ✅ Error handling: Continue to next failure if one fix fails (don't crash)

**Test Coverage**:
- Integration test (dry-run, no actual PR creation): 3 failures → 3 fixes generated
- Integration test (dry-run): 0 failures → agent exits gracefully
- Integration test (mocked PR creation): 5 failures, --max-fixes=2 → creates 2 PRs only

---

## Non-Functional Requirements

### **NFR1: Performance**
- Detect 100 failures in <5 seconds (JSON parsing)
- Select clade in <500ms (CmpStore query + scoring)
- Generate fix in <30 seconds (LLM call, depends on model)
- Create PR in <10 seconds (git operations)

### **NFR2: Reliability**
- Result<T,E> pattern for all error-prone operations
- Retry LLM calls 2x on timeout (Article I: Complete Context)
- Never lose CMP metadata (HTML comments are append-only)

### **NFR3: Constitutional Compliance**
- **Article I**: Retry on timeout (2x, 3x, up to 10x) for LLM calls
- **Article II**: 100% test pass rate required before PR creation
- **Article III**: Auto-enforce quality (no manual overrides for CMP metadata)
- **Article IV**: Store fix attempts in VectorStore (memory_ids in PR metadata)
- **Article V**: This spec defines the implementation (spec-driven)
- **Article VI**: TDD mandatory (tests written FIRST, RED → GREEN → REFACTOR)

### **NFR4: Test-Driven Development (TDD Protocol)**
**RED PHASE** (Tests Written FIRST):
1. Write failing test for TestFailureDetector
2. Write failing test for CladeSelector integration
3. Write failing test for FixGenerator
4. Write failing test for PR creation
5. Write failing E2E integration test
6. **Verify all tests FAIL** (if they pass, tests are wrong)

**GREEN PHASE** (Implementation):
7. Implement TestFailureDetector → tests pass
8. Implement CladeSelector integration → tests pass
9. Implement FixGenerator → tests pass
10. Implement PR creation → tests pass
11. Implement E2E workflow → tests pass

**REFACTOR PHASE** (Code Quality):
12. Extract duplicated code
13. Improve type safety (no Dict[Any, Any])
14. Add docstrings
15. **Verify tests STILL pass**

---

## Technical Architecture

### **Components**

```
tools/self_healing_agent.py        # CLI entry point
├─ SelfHealingAgent (class)
│  ├─ detect_failures() -> list[TestFailure]
│  ├─ run_healing_loop(max_fixes: int) -> list[PRResult]
│  └─ _heal_one_failure(failure: TestFailure) -> Result[PRResult, HealError]
│
├─ TestFailureDetector (class)
│  ├─ load_test_results(json_path: str) -> Result[TestResults, ParseError]
│  └─ extract_failures(results: TestResults) -> list[TestFailure]
│
├─ FixGenerator (class)
│  ├─ __init__(clade_config: CladeConfig)
│  ├─ generate_fix(failure: TestFailure) -> Result[FixProposal, FixError]
│  └─ _build_prompt(failure: TestFailure, profile: str) -> str
│
└─ PRWorkflow (class)
   ├─ create_branch(clade_id: str, short_id: str) -> str
   ├─ commit_fix(proposal: FixProposal, message: str) -> None
   ├─ create_pr(metadata: PRMetadata) -> Result[PRResult, GitError]
   └─ build_pr_body(failure: TestFailure, proposal: FixProposal, clade_id: str) -> str
```

### **Data Models**

```python
@dataclass
class TestFailure:
    """Represents a single failing test."""
    test_name: str              # e.g., "test_validation_error"
    file_path: str              # e.g., "tests/test_validation.py"
    line_number: int            # Line where test is defined
    error_type: str             # e.g., "AssertionError", "AttributeError"
    error_message: str          # Full traceback or error message
    test_code: str | None       # Optional: test function source code

@dataclass
class CladeConfig:
    """Clade configuration for self-healing."""
    agent_id: str               # e.g., "self_healer_v1"
    model_name: str             # e.g., "gpt-5", "qwen-32b"
    prompt_profile: str         # e.g., "prompt_full_context", "prompt_small_diff_v1"
    strategy: str               # e.g., "strategy_careful", "strategy_minimal"

    def to_clade_id(self) -> str:
        """Build clade_id string."""
        return f"{self.agent_id}::{self.model_name}::{self.prompt_profile}::{self.strategy}"

@dataclass
class FixProposal:
    """Generated fix for a test failure."""
    files_changed: dict[str, str]  # {file_path: new_content}
    reasoning: str                 # LLM's explanation of the fix
    clade_id: str                  # Clade that generated this fix

@dataclass
class PRMetadata:
    """Metadata for PR creation."""
    agent_id: str
    clade_id: str
    task_type: str               # "self_heal"
    memory_ids: list[str]        # VectorStore memory IDs
    test_failure: TestFailure
    fix_proposal: FixProposal

@dataclass
class PRResult:
    """Result of PR creation."""
    pr_id: int                   # GitHub PR number
    branch_name: str             # autogen/* branch
    url: str                     # PR URL
```

### **Clade Registry (Initial)**

```python
SELF_HEALING_CLADES = [
    CladeConfig(
        agent_id="self_healer_v1",
        model_name="gpt-5",
        prompt_profile="prompt_full_context",
        strategy="strategy_careful"
    ),
    CladeConfig(
        agent_id="self_healer_v1",
        model_name="qwen-32b",
        prompt_profile="prompt_small_diff_v1",
        strategy="strategy_minimal"
    ),
    CladeConfig(
        agent_id="self_healer_v1",
        model_name="gpt-5-mini",
        prompt_profile="prompt_terse",
        strategy="strategy_quick"
    ),
]
```

---

## Integration with Mission 0-2

### **Mission 0 (CMP Scaffolding)**
- **CladeSelector**: Used in FR3 to select optimal clade
- **CmpStore**: Loaded by CladeSelector to query historical events
- **CmpEvent**: Created by auto_supervise_hook (Mission 2) when PR is closed

### **Mission 1 (Foundation)**
- **AgentContext**: Used to store fix attempts in VectorStore (memory_ids)
- **agent_id, clade_id, task_type**: Injected into PR metadata

### **Mission 2 (Learning Coach)**
- **auto_supervise_hook.py**: Parses PR metadata, creates CmpEvent
- **GitHub workflow**: Triggers on PR close (approved/rejected signal)
- **CmpStore**: Records event to `data/cmp_events.jsonl`

### **Feedback Loop**
1. SelfHealingAgent creates PR with clade_id metadata
2. Human reviews PR → approves (merge) or rejects (close without merge)
3. auto_supervise_hook detects PR close → extracts clade_id → creates CmpEvent
4. CmpEvent written to CmpStore → `reinforcement_signal: "approved"` or `"rejected"`
5. Next run: CladeSelector queries CmpStore → scores clades → exploits high-approval clades

---

## Test Plan

### **Unit Tests** (tests/test_self_healing_agent.py)

**TestFailureDetector**:
- ✅ `test_load_valid_json()` → returns TestResults
- ✅ `test_load_missing_file()` → returns Err(FileNotFound)
- ✅ `test_load_malformed_json()` → returns Err(ParseError)
- ✅ `test_extract_failures_3_failures()` → returns 3 TestFailure objects
- ✅ `test_extract_failures_0_failures()` → returns empty list
- ✅ `test_extract_failures_skips_skipped_tests()` → ignores skipped tests

**CladeSelector Integration**:
- ✅ `test_select_clade_explore()` → epsilon=1.0 → random selection
- ✅ `test_select_clade_exploit()` → epsilon=0.0 → highest score
- ✅ `test_select_clade_epsilon_distribution()` → epsilon=0.1 → ~10% explore

**FixGenerator**:
- ✅ `test_build_prompt_full_context()` → includes test file, impl file, traceback
- ✅ `test_build_prompt_small_diff()` → includes only test function + error
- ✅ `test_build_prompt_terse()` → includes only error message
- ✅ `test_generate_fix_valid_response()` → returns FixProposal
- ✅ `test_generate_fix_invalid_llm_response()` → returns Err(InvalidFix)

**PRWorkflow**:
- ✅ `test_build_branch_name()` → `autogen/selfheal-...-<short_id>`
- ✅ `test_build_pr_body()` → includes HTML comment metadata
- ✅ `test_build_pr_metadata()` → correct agent_id, clade_id, task_type

### **Integration Tests** (tests/test_self_healing_agent_integration.py)

**End-to-End Workflow (Dry-Run)**:
- ✅ `test_e2e_3_failures_3_fixes()` → Detect 3, generate 3, create 3 PRs (dry-run)
- ✅ `test_e2e_0_failures()` → Agent exits gracefully
- ✅ `test_e2e_max_fixes_limit()` → 5 failures, --max-fixes=2 → creates 2 PRs only
- ✅ `test_e2e_one_fix_fails_continues()` → 3 failures, 1 fix fails → creates 2 PRs

**CMP Feedback Loop**:
- ✅ `test_cmp_feedback_approved_pr()` → Create PR → simulate merge → verify CmpEvent created
- ✅ `test_cmp_feedback_rejected_pr()` → Create PR → simulate close → verify CmpEvent created
- ✅ `test_cmp_feedback_clade_learning()` → 10 PRs (8 approved, 2 rejected) → verify clade score evolution

---

## Implementation Phases

### **Phase 1: TDD - Write Tests FIRST** (Estimated: 2-3 hours)
1. Create `tests/test_self_healing_agent.py`
2. Write 15-20 unit tests (all FAILING initially)
3. Create `tests/test_self_healing_agent_integration.py`
4. Write 5-7 integration tests (all FAILING initially)
5. **Verify all tests FAIL** (RED phase complete)

### **Phase 2: Core Implementation** (Estimated: 4-6 hours)
6. Implement `TestFailureDetector` → unit tests pass
7. Implement `CladeSelector` integration → tests pass
8. Implement `FixGenerator` → tests pass
9. Implement `PRWorkflow` → tests pass
10. Implement `SelfHealingAgent.run_healing_loop()` → E2E tests pass
11. **Verify all tests PASS** (GREEN phase complete)

### **Phase 3: Refactoring & Polish** (Estimated: 2-3 hours)
12. Extract common patterns (e.g., prompt building)
13. Add comprehensive docstrings
14. Type safety audit (no Dict[Any, Any])
15. Logging improvements (INFO-level for each step)
16. **Verify tests STILL pass** (REFACTOR phase complete)

### **Phase 4: Manual Validation** (Estimated: 1-2 hours)
17. Run on real failing tests from test suite
18. Verify PR metadata parseable by auto_supervise_hook
19. Test CladeSelector evolution (approve 2 PRs, reject 1 PR, verify scores)
20. Update METAPRODUCTIVITY_2.0_STATUS.md with Mission 3 completion

---

## Acceptance Checklist

Before marking Mission 3 as COMPLETE, verify:

- [ ] All unit tests pass (15-20 tests in test_self_healing_agent.py)
- [ ] All integration tests pass (5-7 tests in test_self_healing_agent_integration.py)
- [ ] TDD protocol followed (tests written FIRST, all failed initially)
- [ ] `tools/self_healing_agent.py --help` works
- [ ] `tools/self_healing_agent.py --max-fixes=1 --dry-run` generates fix
- [ ] CladeSelector integration verified (epsilon-greedy working)
- [ ] PR metadata parseable by auto_supervise_hook (HTML comments)
- [ ] CMP feedback loop verified (CmpEvent created on PR close)
- [ ] Clade score evolution verified (approved clades score higher)
- [ ] Constitutional compliance (Articles I-VI)
- [ ] Documentation updated (METAPRODUCTIVITY_2.0_STATUS.md)

---

## Future Enhancements (Post-Mission 3)

- **Mission 4**: Backlog Agent (uses same CMP infrastructure)
- **Mission 5**: Night Shift & Auto-Recovery (24/7 execution)
- **Clade Registry Expansion**: Add more prompt profiles, strategies
- **Multi-Agent Coordination**: Self-healing + backlog agents cooperate
- **Revert Detection**: Auto-detect reverted PRs → reinforce negative signal

---

**Specification Status**: Draft → Ready for Implementation
**Next Step**: Phase 1 (Write Tests FIRST - TDD RED Phase)
