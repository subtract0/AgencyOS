# Specification: Foundation Automation Test Coverage Strategy

**ID**: SPEC-030
**Status**: Draft
**Created**: 2025-10-14
**Updated**: 2025-10-14
**Owner**: Planner Agent
**Related ADRs**: ADR-027 (Two-Stage TDD), ADR-032 (Autonomous Completion Protocol)
**Related Tools**: `tools/orchestrator/unified_primea_orchestrator.py`

---

## Goals

### User Goals
1. **Reliability**: Foundation automation workflow (`/primeA`) executes with 100% reliability from natural language intent to merged PR
2. **Constitutional Compliance**: All 5 constitutional articles enforced automatically at every workflow stage
3. **Zero Regressions**: Test suite prevents workflow degradation as new features are added
4. **Fast Feedback**: Test execution completes in <5 minutes for full suite, <30s for unit tests

### System Goals
1. **Comprehensive Coverage**: All workflow paths tested (E2E, git validation, backlog selection, flags, gates, fallbacks)
2. **NECESSARY Pattern Compliance**: Every test category follows Normal, Edge, Constraints, Error, Security, Scale, Asynchronous, Retry, Yield pattern
3. **Isolation**: Tests run independently without cross-test pollution or shared state
4. **Performance**: Test suite scales to 500+ tests without exceeding 10-minute execution time

---

## Non-Goals

1. **Full Integration Testing**: Not testing actual GitHub API calls (mock only)
2. **Local Model Integration**: Not testing Ollama/TRM validation (separate test suite)
3. **UI Testing**: Not testing Kanban visualization server (out of scope)
4. **Load Testing**: Not testing concurrent orchestrator instances (single instance only)

---

## Personas

### Persona 1: Foundation Automation Developer
- **Context**: Extending `/primeA` with new workflow features (e.g., worktree isolation, PR templates)
- **Need**: Test coverage that catches regressions in existing workflow steps while allowing feature additions
- **Interaction**: Runs `pytest tests/orchestrator/test_unified_primea_orchestrator.py -v` before committing changes

### Persona 2: Quality Enforcer Agent
- **Context**: Validating constitutional compliance during autonomous execution
- **Need**: Comprehensive test coverage that validates all 5 articles are enforced at each workflow gate
- **Interaction**: Queries VectorStore for test coverage patterns before proposing workflow modifications

### Persona 3: CI/CD Pipeline
- **Context**: Automated validation on every PR to main branch
- **Need**: Fast, reliable test suite that blocks merges when constitutional violations are introduced
- **Interaction**: Executes `pytest tests/orchestrator/ --run-all` and enforces 100% pass rate (Article II)

---

## Acceptance Criteria

### Functional Criteria

#### 1. E2E Natural Language → PR Flow
- [ ] **E2E-001**: Natural language intent → task graph generation → validation → execution → PR creation (happy path)
- [ ] **E2E-002**: Intent with `--two-stage` flag → spec generation → user approval → TDD execution → PR creation
- [ ] **E2E-003**: Intent with `--no-pr` flag → execution completes without PR creation
- [ ] **E2E-004**: Intent with `--plan-only` flag → graph generation → save to file → exit (no execution)
- [ ] **E2E-005**: Explicit graph file (`--graph missions/test.json`) → validation → execution → PR creation
- [ ] **E2E-006**: Auto-selection from backlog → highest priority task → execution → PR creation
- [ ] **E2E-007**: Invalid intent (slop immunity failure) → auto-rewrite loop (3 attempts) → halt with feedback
- [ ] **E2E-008**: Budget exceeded → halt with cost breakdown → suggest `--force` override

#### 2. Backlog Auto-Selection Mechanism
- [ ] **BACKLOG-001**: Parse `~/.agency/memories/agency_backlog/test_suite_gaps.md` → extract priority tasks
- [ ] **BACKLOG-002**: Select highest priority `Ready` task (not `Blocked`/`Locked`)
- [ ] **BACKLOG-003**: Graceful fallback when backlog file doesn't exist → prompt user for intent
- [ ] **BACKLOG-004**: Empty backlog → prompt user for intent
- [ ] **BACKLOG-005**: Malformed backlog file → log warning → fallback to manual intent

#### 3. Git Validation (Phase 0)
- [ ] **GIT-001**: Execution on `main` branch → halt with Article III violation message
- [ ] **GIT-002**: Execution on `master` branch → halt with Article III violation message
- [ ] **GIT-003**: Execution on feature branch (`feat/*`, `fix/*`, `docs/*`) → pass validation
- [ ] **GIT-004**: Not in git repository → log warning → continue (non-blocking)
- [ ] **GIT-005**: Worktree isolation validation → separate working directory per execution
- [ ] **GIT-006**: Detached HEAD state → halt with guidance to checkout branch

#### 4. Flag Behavior
- [ ] **FLAG-001**: `--two-stage` routes to `TwoStageOrchestrator` (bypasses legacy workflow)
- [ ] **FLAG-002**: `--plan-only` generates graph → saves to `/tmp/task_graph_*.json` → exits
- [ ] **FLAG-003**: `--visualize` enables Mermaid DAG + ASCII tree output
- [ ] **FLAG-004**: `--auto-pr` creates PR automatically on completion (default behavior)
- [ ] **FLAG-005**: `--no-pr` skips PR creation (manual review mode)
- [ ] **FLAG-006**: `--force` overrides budget limits → logs to audit trail
- [ ] **FLAG-007**: `--help` displays comprehensive help text → exits
- [ ] **FLAG-008**: Invalid flag combination (e.g., `--plan-only --auto-pr`) → error with suggestions

#### 5. Constitutional Gates (Articles I-V Enforcement)
- [ ] **GATE-001**: **Article I** - Incomplete graph generation → retry with 2x timeout → eventually halt
- [ ] **GATE-002**: **Article I** - Timeout during TRM validation → retry with 3x timeout → Python fallback
- [ ] **GATE-003**: **Article II** - Tests fail during execution → halt at STEP 6.5 completion validator
- [ ] **GATE-004**: **Article II** - 90% task completion → block STEP 7 execution report → continue until 100%
- [ ] **GATE-005**: **Article III** - TRM DAG validation detects circular dependencies → halt with cycle details
- [ ] **GATE-006**: **Article III** - Slop immunity score <3.5 → auto-rewrite loop → halt if 3 attempts fail
- [ ] **GATE-007**: **Article III** - Budget exceeded without `--force` → halt with cost breakdown
- [ ] **GATE-008**: **Article III** - Main branch detection → halt with branch protection violation
- [ ] **GATE-009**: **Article IV** - VectorStore query before planning → apply learnings (confidence ≥0.6)
- [ ] **GATE-010**: **Article IV** - Pattern storage after success → VectorStore update with tags
- [ ] **GATE-011**: **Article V** - Missing acceptance criteria in spec → validation error
- [ ] **GATE-012**: **Article V** - Task graph doesn't trace to spec → validation error

#### 6. Graceful Fallbacks
- [ ] **FALLBACK-001**: VectorStore unavailable → log warning → continue (non-blocking)
- [ ] **FALLBACK-002**: TRM validator unavailable → Python DAG validation fallback
- [ ] **FALLBACK-003**: Slop Guardian LLM timeout → fallback verdict (score 3.5, ACCEPT)
- [ ] **FALLBACK-004**: Local model unavailable → cloud API routing for all tasks
- [ ] **FALLBACK-005**: GitHub API rate limit → exponential backoff retry (2x, 3x, up to 10x)
- [ ] **FALLBACK-006**: Pre-commit hook failure in worktree → `--no-verify` bypass (tests validated in CI)
- [ ] **FALLBACK-007**: Memory Tool unavailable → session-only memory (no cross-conversation persistence)

### Non-Functional Criteria

#### Performance Targets
- [ ] **PERF-001**: E2E flow (intent → PR) completes in <120s for simple tasks (≤5 task graph nodes)
- [ ] **PERF-002**: Backlog auto-selection completes in <2s
- [ ] **PERF-003**: Git validation completes in <50ms per check
- [ ] **PERF-004**: Constitutional gate validation (all 5 articles) completes in <3s total
- [ ] **PERF-005**: Individual integration test completes in <5s (95th percentile)
- [ ] **PERF-006**: Memory overhead <500MB for full workflow execution

#### Quality Criteria
- [ ] **QUALITY-001**: Test coverage >95% for `unified_primea_orchestrator.py`
- [ ] **QUALITY-002**: Zero linting errors in test files (`ruff check tests/orchestrator/`)
- [ ] **QUALITY-003**: All test names follow `test_<step>_<scenario>_<expected_outcome>` pattern
- [ ] **QUALITY-004**: Fixtures documented with docstrings explaining purpose and usage
- [ ] **QUALITY-005**: No hardcoded paths (use `tmp_path` fixture for file operations)
- [ ] **QUALITY-006**: 100% type coverage (all test functions have return type annotations)

### Constitutional Compliance Checklist

- [ ] **Article I**: Complete context gathered for all test scenarios (no mocked execution states)
- [ ] **Article II**: 100% test pass rate before spec approval (no skipped/xfail tests)
- [ ] **Article III**: Automated enforcement validated (no manual bypass mechanisms in tests)
- [ ] **Article IV**: VectorStore query/storage patterns tested and validated
- [ ] **Article V**: Spec traceability demonstrated (task graph → spec acceptance criteria)

---

## Dependencies

### Specifications
- **SPEC-027**: Two-Stage TDD Orchestration (spec approval checkpoint)
- **SPEC-032**: Autonomous Completion Protocol (STEP 6.5 validation)

### ADRs
- **ADR-001**: Complete Context Before Action (Article I enforcement)
- **ADR-002**: 100% Verification and Stability (Article II enforcement)
- **ADR-003**: Automated Merge Enforcement (Article III enforcement)
- **ADR-004**: Continuous Learning (Article IV VectorStore integration)
- **ADR-007**: Spec-Driven Development (Article V workflow)
- **ADR-027**: Two-Stage TDD Orchestration (spec → approval → execution)
- **ADR-032**: Autonomous Completion Protocol (STEP 6.5 validation gate)

### Existing Test Files
- `tests/orchestrator/test_unified_primea_orchestrator.py` (1,050 lines, 50 tests)
- `tests/tools/orchestrator/test_completion_validator.py` (39 tests, 100% pass)
- `tests/tools/orchestrator/test_tdd_graph_generator.py` (TDD graph generation)

### External Tools
- `pytest>=8.0.0` (test framework)
- `pytest-asyncio>=0.21.0` (async test support)
- `pytest-mock>=3.12.0` (mocking framework)
- `pytest-timeout>=2.2.0` (timeout enforcement)

---

## Test Plan (NECESSARY Pattern Breakdown)

### Test Suite Organization

```
tests/orchestrator/
├── test_unified_primea_orchestrator.py         # E2E orchestrator tests (50 existing)
├── test_foundation_automation_e2e.py           # NEW: Full E2E workflow tests
├── test_foundation_automation_git_validation.py # NEW: Phase 0 git validation
├── test_foundation_automation_backlog.py       # NEW: Backlog auto-selection
├── test_foundation_automation_flags.py         # NEW: Flag behavior tests
├── test_foundation_automation_gates.py         # NEW: Constitutional gate tests
├── test_foundation_automation_fallbacks.py     # NEW: Graceful fallback tests
└── fixtures/
    ├── task_graphs.py                          # Reusable task graph fixtures
    ├── mock_services.py                        # VectorStore/GitHub API mocks
    └── test_data.py                            # Sample intents, backlog files
```

### NECESSARY Coverage by Test Suite

#### 1. E2E Flow Tests (`test_foundation_automation_e2e.py`)

**Normal Operation (N)**:
- ✅ Natural language intent → graph → validation → execution → PR (E2E-001)
- ✅ Auto-selection from backlog → execution → PR (E2E-006)
- ✅ Explicit graph file → execution → PR (E2E-005)

**Edge Cases (E)**:
- ✅ Empty intent string → prompt user for clarification
- ✅ Intent with special characters (quotes, newlines) → sanitize and process
- ✅ Graph file with minimal valid structure (1 task) → execute successfully
- ✅ Graph file at maximum complexity (100 tasks, 10 phases) → batch execution

**Constraints (C)**:
- ✅ Intent length ≤10,000 characters (LLM context limit)
- ✅ Graph file size ≤1MB (JSON parsing limit)
- ✅ Task count ≤200 tasks per graph (topological sort limit)

**Error Handling (E)**:
- ✅ Graph generation timeout → retry with 2x timeout (Article I)
- ✅ Planner agent failure → return Err with details
- ✅ Malformed JSON in graph file → validation error with line number

**Security (S)**:
- ✅ Intent injection attempt (malicious JSON in string) → sanitize before LLM
- ✅ Graph file path traversal (`../../etc/passwd`) → reject invalid paths
- ✅ HMAC signature validation for audit logs → verify tamper detection

**Scale (S)**:
- ✅ Large graph (100 tasks) → execution completes within budget (10 min timeout)
- ✅ High parallelism (20 tasks in single layer) → batch execution (3 workers local, 10 cloud)

**Asynchronous (A)**:
- ✅ Concurrent graph validations → no race conditions in validator
- ✅ Parallel task execution → TodoWrite updates synchronized

**Retry Logic (R)**:
- ✅ Transient failure (network timeout) → exponential backoff (2x, 3x, 10x)
- ✅ Permanent failure (invalid API key) → halt after 3 retries

**Yield/Generator (Y)**:
- N/A (no generator patterns in orchestrator)

#### 2. Git Validation Tests (`test_foundation_automation_git_validation.py`)

**Normal Operation (N)**:
- ✅ Feature branch (`feat/test`) → validation passes (GIT-003)
- ✅ Fix branch (`fix/bug-123`) → validation passes
- ✅ Docs branch (`docs/update-readme`) → validation passes

**Edge Cases (E)**:
- ✅ Branch name with special characters (`feat/user-auth-2.0`) → validation passes
- ✅ Very long branch name (255 characters) → validation passes
- ✅ Branch name with Unicode characters → sanitize and validate

**Constraints (C)**:
- ✅ Branch name matches pattern `(feat|fix|docs|refactor|test)/*`
- ✅ Not on protected branches: `main`, `master`, `develop`

**Error Handling (E)**:
- ✅ Execution on `main` branch → halt with Article III message (GIT-001)
- ✅ Detached HEAD state → halt with checkout guidance (GIT-006)
- ✅ Not in git repo → log warning, continue (non-blocking) (GIT-004)

**Security (S)**:
- ✅ Branch name injection (`main; rm -rf /`) → reject with validation error
- ✅ Symlink to protected branch → reject with symlink detection

**Scale (S)**:
- ✅ Git validation <50ms per check (PERF-003)

**Asynchronous (A)**:
- N/A (synchronous git operations)

**Retry Logic (R)**:
- ✅ Git command timeout (slow filesystem) → retry with 2x timeout
- ✅ Git command failure (repo locked) → retry up to 3 times

**Yield/Generator (Y)**:
- N/A

#### 3. Backlog Auto-Selection Tests (`test_foundation_automation_backlog.py`)

**Normal Operation (N)**:
- ✅ Backlog with single task → select and execute (BACKLOG-001)
- ✅ Backlog with multiple tasks → select highest priority (BACKLOG-002)
- ✅ Backlog with mixed statuses (Ready/Blocked/Locked) → select first Ready task

**Edge Cases (E)**:
- ✅ Empty backlog file (0 tasks) → prompt user for intent (BACKLOG-004)
- ✅ All tasks blocked → prompt user for intent
- ✅ Backlog with duplicate priorities → select first occurrence

**Constraints (C)**:
- ✅ Backlog file path: `~/.agency/memories/agency_backlog/test_suite_gaps.md`
- ✅ Task format: `- [ ] Priority N: <task description>`

**Error Handling (E)**:
- ✅ Backlog file not found → log warning, fallback to manual intent (BACKLOG-003)
- ✅ Malformed task line (missing priority) → log warning, skip task (BACKLOG-005)
- ✅ Backlog file unreadable (permissions) → fallback to manual intent

**Security (S)**:
- ✅ Backlog file path traversal → reject paths outside `~/.agency/memories/`
- ✅ Malicious task description (shell injection) → sanitize before execution

**Scale (S)**:
- ✅ Large backlog (1,000 tasks) → selection completes in <2s (PERF-002)

**Asynchronous (A)**:
- N/A (synchronous file read)

**Retry Logic (R)**:
- ✅ File read timeout (NFS mount) → retry with 2x timeout

**Yield/Generator (Y)**:
- N/A

#### 4. Flag Behavior Tests (`test_foundation_automation_flags.py`)

**Normal Operation (N)**:
- ✅ `--two-stage` → routes to TwoStageOrchestrator (FLAG-001)
- ✅ `--plan-only` → generates graph, saves to file, exits (FLAG-002)
- ✅ `--auto-pr` → creates PR on completion (FLAG-004)
- ✅ `--no-pr` → skips PR creation (FLAG-005)
- ✅ No flags → auto-selects backlog, creates PR (default behavior)

**Edge Cases (E)**:
- ✅ Multiple flags (`--visualize --auto-pr`) → both features enabled
- ✅ Flag order variation (`--auto-pr --visualize`) → same behavior
- ✅ Flag with equals syntax (`--graph=missions/test.json`) → parsed correctly

**Constraints (C)**:
- ✅ `--graph` requires file path argument
- ✅ `--force` only valid with budget guard active

**Error Handling (E)**:
- ✅ Invalid flag (`--invalid`) → error with suggestion (FLAG-008)
- ✅ Conflicting flags (`--plan-only --auto-pr`) → error with explanation
- ✅ Missing required argument (`--graph` without path) → error with usage

**Security (S)**:
- ✅ `--graph` path traversal (`--graph ../../etc/passwd`) → reject invalid paths
- ✅ Flag injection (`--graph "test.json; rm -rf /"`) → sanitize arguments

**Scale (S)**:
- N/A (flag parsing is O(1))

**Asynchronous (A)**:
- N/A (synchronous flag parsing)

**Retry Logic (R)**:
- N/A (no retry needed for flag parsing)

**Yield/Generator (Y)**:
- N/A

#### 5. Constitutional Gate Tests (`test_foundation_automation_gates.py`)

**Normal Operation (N)**:
- ✅ All gates pass → execution proceeds to STEP 7 (GATE-001)
- ✅ TRM DAG validation passes → acyclic graph confirmed (GATE-005)
- ✅ Slop immunity passes (score ≥3.5) → execution continues (GATE-006)
- ✅ Budget guard passes → cost within limits (GATE-007)
- ✅ Completion validator passes → 100% tasks complete (GATE-004)

**Edge Cases (E)**:
- ✅ Slop immunity score exactly 3.5 → pass (boundary condition)
- ✅ Budget exactly at limit → pass (boundary condition)
- ✅ Context usage exactly 80% → no warning (boundary condition)

**Constraints (C)**:
- ✅ TRM validation timeout: 30s (default), 60s (retry)
- ✅ Slop immunity score threshold: ≥3.5
- ✅ Budget daily limit: $100 (default), configurable via env
- ✅ Budget per-mission limit: $10 (default), configurable via metadata

**Error Handling (E)**:
- ✅ TRM unavailable → Python fallback, validation continues (FALLBACK-002)
- ✅ Slop Guardian LLM timeout → fallback verdict (ACCEPT, score 3.5) (FALLBACK-003)
- ✅ Budget exceeded without `--force` → halt with cost breakdown (GATE-007)
- ✅ Incomplete tasks at STEP 6.5 → block STEP 7, continue execution (GATE-004)

**Security (S)**:
- ✅ No manual bypass mechanism for any gate (Article III enforcement)
- ✅ HMAC audit log validation → tamper detection works

**Scale (S)**:
- ✅ Constitutional gate validation completes in <3s total (PERF-004)

**Asynchronous (A)**:
- ✅ Parallel gate validation (TRM + Slop + Budget) → no race conditions

**Retry Logic (R)**:
- ✅ TRM timeout → retry with 2x timeout, fallback to Python (GATE-002)
- ✅ VectorStore query timeout → retry with 3x timeout, fallback to session memory

**Yield/Generator (Y)**:
- N/A

#### 6. Graceful Fallback Tests (`test_foundation_automation_fallbacks.py`)

**Normal Operation (N)**:
- ✅ VectorStore available → queries return learnings (FALLBACK-001)
- ✅ TRM available → DAG validation uses TRM (FALLBACK-002)
- ✅ Slop Guardian available → evaluation returns verdict (FALLBACK-003)

**Edge Cases (E)**:
- ✅ VectorStore partially available (query succeeds, store fails) → log warning, continue
- ✅ TRM latency spike (>5s) → fallback to Python validation

**Constraints (C)**:
- ✅ VectorStore timeout: 10s (default)
- ✅ TRM timeout: 30s (default)
- ✅ GitHub API rate limit: 5000 requests/hour

**Error Handling (E)**:
- ✅ VectorStore unavailable → session-only memory, log warning (FALLBACK-001)
- ✅ TRM model not loaded → Python DAG validation (FALLBACK-002)
- ✅ Slop Guardian LLM timeout → fallback verdict (FALLBACK-003)
- ✅ Local model OOM → cloud API routing for P3 tasks (FALLBACK-004)
- ✅ GitHub API rate limit → exponential backoff (FALLBACK-005)
- ✅ Memory Tool unavailable → session memory only (FALLBACK-007)

**Security (S)**:
- ✅ Fallback mechanisms don't bypass constitutional gates
- ✅ Session memory doesn't persist sensitive data (API keys)

**Scale (S)**:
- ✅ Fallback to Python validation <100ms (vs <10ms TRM)
- ✅ VectorStore fallback doesn't block execution (async query)

**Asynchronous (A)**:
- ✅ Parallel fallback checks (VectorStore + TRM) → no deadlocks

**Retry Logic (R)**:
- ✅ GitHub API 429 → exponential backoff: 2s, 4s, 8s, 16s, 32s (FALLBACK-005)
- ✅ VectorStore transient error → retry 3 times before fallback

**Yield/Generator (Y)**:
- N/A

---

## Test Isolation Strategy

### Fixture Design

#### 1. Agent Context Fixture
```python
@pytest.fixture
def agent_context():
    """Isolated agent context with memory disabled."""
    return create_agent_context(
        session_id=f"test_{uuid.uuid4()}",
        enable_memory=False  # Disable VectorStore for isolation
    )
```

#### 2. Temporary Repository Fixture
```python
@pytest.fixture
def git_repo(tmp_path):
    """Create temporary git repository for testing."""
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path)
    subprocess.run(["git", "checkout", "-b", "feat/test"], cwd=tmp_path)

    return tmp_path
```

#### 3. Mock VectorStore Fixture
```python
@pytest.fixture
def mock_vector_store():
    """Mock VectorStore with predefined learnings."""
    mock_store = MagicMock()
    mock_store.search_memories = MagicMock(return_value=[
        {"pattern": "TDD workflow", "confidence": 0.8},
        {"pattern": "Git validation", "confidence": 0.9},
    ])
    return mock_store
```

#### 4. Mock GitHub API Fixture
```python
@pytest.fixture
def mock_github_api():
    """Mock GitHub API for PR creation tests."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="https://github.com/org/repo/pull/123"
        )
        yield mock_run
```

### Cleanup Protocols

#### Teardown Fixtures
```python
@pytest.fixture
def orchestrator(agent_context, tmp_path):
    """Create orchestrator with automatic cleanup."""
    orch = UnifiedPrimeAOrchestrator(
        context=agent_context,
        repo_path=str(tmp_path),
        enable_todos=False  # Disable TodoWrite for tests
    )

    yield orch

    # Cleanup: Remove temporary files
    if tmp_path.exists():
        shutil.rmtree(tmp_path)
```

#### Worktree Isolation
```python
@pytest.fixture(scope="function")
def worktree_repo(tmp_path):
    """Create isolated worktree for parallel test execution."""
    # Each test gets isolated worktree
    worktree_path = tmp_path / f"worktree_{uuid.uuid4()}"

    subprocess.run([
        "git", "worktree", "add", str(worktree_path), "-b", "test-branch"
    ], check=True)

    yield worktree_path

    # Cleanup: Remove worktree
    subprocess.run(["git", "worktree", "remove", str(worktree_path)], check=True)
```

### No Cross-Test Pollution

#### State Isolation
- Each test gets unique `session_id` for AgentContext
- Temporary directories via `tmp_path` fixture (auto-cleanup)
- Mock services reset between tests (`@pytest.fixture(autouse=True)`)
- No global state mutations (constants only)

#### File System Isolation
- All file operations use `tmp_path` (pytest auto-cleanup)
- Backlog files created in test-specific directories
- Graph files written to `/tmp/task_graph_<uuid>.json`
- No shared state in `~/.agency/` during tests

---

## Performance Test Targets

### Benchmark Tests

#### 1. E2E Performance (`test_performance_e2e.py`)
```python
@pytest.mark.performance
def test_e2e_simple_task_graph_performance(orchestrator, benchmark):
    """Benchmark E2E execution time for simple graph (5 tasks)."""
    result = benchmark(orchestrator.execute, simple_task_graph)

    assert result.is_ok()
    assert benchmark.stats.mean < 120.0  # <120s (PERF-001)
```

#### 2. Backlog Selection Performance
```python
@pytest.mark.performance
def test_backlog_auto_selection_performance(orchestrator, benchmark):
    """Benchmark backlog parsing and selection."""
    result = benchmark(orchestrator._auto_select_from_backlog)

    assert result.is_ok()
    assert benchmark.stats.mean < 2.0  # <2s (PERF-002)
```

#### 3. Git Validation Performance
```python
@pytest.mark.performance
def test_git_validation_performance(orchestrator, git_repo, benchmark):
    """Benchmark git branch validation."""
    result = benchmark(orchestrator._validate_git_workflow)

    assert result.is_ok()
    assert benchmark.stats.mean < 0.05  # <50ms (PERF-003)
```

#### 4. Constitutional Gate Performance
```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_constitutional_gates_performance(orchestrator, simple_task_graph, benchmark):
    """Benchmark all constitutional gate validations."""
    async def run_gates():
        await orchestrator._validate_dag_with_trm(simple_task_graph)
        await orchestrator._check_slop_immunity(simple_task_graph)
        await orchestrator._check_budget(simple_task_graph, force=False)

    result = await benchmark(run_gates)
    assert benchmark.stats.mean < 3.0  # <3s (PERF-004)
```

### Memory Profiling

#### Memory Overhead Test
```python
@pytest.mark.memory
def test_memory_overhead(orchestrator, simple_task_graph):
    """Validate memory usage during execution."""
    import tracemalloc

    tracemalloc.start()
    orchestrator.execute(simple_task_graph)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Memory overhead <500MB (PERF-006)
    assert peak / (1024 ** 2) < 500  # MB
```

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| **Flaky Tests** (network timeouts, race conditions) | High | Medium | Use mocks for external dependencies; retry logic in fixtures; deterministic test execution order |
| **Mock Brittleness** (breaking changes in mocked APIs) | Medium | High | Version-pinned mocks; contract testing; integration tests verify real API contracts quarterly |
| **Performance Regressions** (tests become too slow) | Medium | Medium | Benchmark tests with performance budgets; CI fails if tests exceed time limits; parallelization with pytest-xdist |
| **Test Pollution** (shared state between tests) | High | Low | Isolated fixtures (tmp_path, unique session_id); cleanup teardown; no global mutations |
| **Incomplete Coverage** (missing edge cases) | High | Medium | NECESSARY pattern enforcement; coverage reports (>95% target); quarterly coverage audits |
| **Constitutional Violations** (tests bypass gates) | Critical | Low | Automated constitutional compliance checks in CI; quality enforcer agent reviews test PRs |

---

## Implementation Notes

### Pytest Configuration

#### `pytest.ini` Settings
```ini
[pytest]
testpaths = tests/orchestrator
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    performance: Performance benchmark tests
    memory: Memory profiling tests
    integration: Integration tests (require external services)
    unit: Unit tests (fast, no external dependencies)
addopts =
    --strict-markers
    --tb=short
    --verbose
    --cov=tools/orchestrator
    --cov-report=term-missing
    --cov-fail-under=95
timeout = 300
```

#### CI Integration (`.github/workflows/test-foundation-automation.yml`)
```yaml
name: Foundation Automation Tests

on:
  pull_request:
    paths:
      - 'tools/orchestrator/**'
      - 'tests/orchestrator/**'
      - 'specs/spec-030-*.md'

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-asyncio pytest-cov pytest-timeout

      - name: Run unit tests
        run: pytest tests/orchestrator/ -m "not performance and not memory" --cov

      - name: Run performance tests
        run: pytest tests/orchestrator/ -m performance --benchmark-only

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          fail_ci_if_error: true
```

### Mock Configuration

#### VectorStore Mock Pattern
```python
# tests/orchestrator/fixtures/mock_services.py

from unittest.mock import MagicMock

def create_mock_vector_store(learnings: list[dict] = None):
    """Create mock VectorStore with predefined learnings."""
    learnings = learnings or []

    mock_store = MagicMock()
    mock_store.search_memories = MagicMock(return_value=learnings)
    mock_store.store_memory = MagicMock(return_value=True)

    return mock_store
```

#### GitHub API Mock Pattern
```python
# tests/orchestrator/fixtures/mock_services.py

from unittest.mock import patch, MagicMock

@contextmanager
def mock_github_api(pr_url: str = "https://github.com/org/repo/pull/123"):
    """Mock GitHub CLI for PR creation tests."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=pr_url,
            stderr=""
        )
        yield mock_run
```

---

## References

### Specifications
- **SPEC-027**: Two-Stage TDD Orchestration
- **SPEC-032**: Autonomous Completion Protocol

### ADRs
- **ADR-001**: Complete Context Before Action (Article I)
- **ADR-002**: 100% Verification and Stability (Article II)
- **ADR-003**: Automated Merge Enforcement (Article III)
- **ADR-004**: Continuous Learning (Article IV)
- **ADR-007**: Spec-Driven Development (Article V)
- **ADR-027**: Two-Stage TDD Orchestration
- **ADR-032**: Autonomous Completion Protocol

### Existing Test Files
- `tests/orchestrator/test_unified_primea_orchestrator.py` (50 tests, 1,050 lines)
- `tests/tools/orchestrator/test_completion_validator.py` (39 tests, 100% pass)
- `tests/tools/orchestrator/test_tdd_graph_generator.py` (TDD graph generation)

### Tools
- `tools/orchestrator/unified_primea_orchestrator.py` (main orchestrator)
- `tools/orchestrator/completion_validator.py` (STEP 6.5 validation)
- `tools/orchestrator/slop_guardian.py` (quality enforcement)
- `tools/orchestrator/budget_guard.py` (cost enforcement)

### External Documentation
- Pytest documentation: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- pytest-benchmark: https://pytest-benchmark.readthedocs.io/

---

**This specification defines comprehensive test coverage for the foundation automation workflow, ensuring constitutional compliance, reliability, and performance at every stage from natural language intent to merged PR.**

**Next Steps**:
1. Review specification with Quality Enforcer agent
2. Generate implementation plan (`plan-030-foundation-automation-test-coverage.md`)
3. Create TodoWrite task breakdown
4. Implement test suites following NECESSARY pattern
5. Validate >95% coverage and <5 minute execution time
