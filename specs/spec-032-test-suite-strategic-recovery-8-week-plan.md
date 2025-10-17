# Specification: Test Suite Strategic Recovery - 8-Week Plan

**Spec ID**: spec-032
**Created**: 2025-10-17
**Status**: READY FOR EXECUTION
**Complexity**: CRITICAL (8-Week Initiative)
**Owner**: Master-Architect (PrimeA Orchestrator)

---

## 🎯 Strategic Objectives

Transform Agency OS test suite from **"tactically excellent, strategically incomplete"** to **production-grade 95% confidence** through systematic gap closure, CI stabilization, and constitutional compliance.

### Primary Goals

1. **Clean & Green Main Branch** - 100% CI pass rate on GitHub main
2. **Merge Recent Work** - Integrate 4 local commits + 2 open PRs functionally
3. **Close Audit Gaps** - Fix 4 P0 blockers + 8 P1 gaps identified in Master-Architect audit
4. **8-Week Roadmap Completion** - Deliver Phases 1-4 from audit recommendations

---

## 📊 Current State Analysis

### Git State (2025-10-17)

**Local Branch**: `fix/test-suite-top-3-blockers`
**Status**: 4 uncommitted local commits ahead of origin/main

```
Local Commits (Not Pushed):
- 0691b239: chore: Update specs, models, missions, and config for test recovery
- 3805b339: docs: Add comprehensive Master-Architect test suite audit
- f8fc26be: feat: Fix orchestrator and ML classifier for 100% test compatibility
- 8808188d: fix: Achieve 100% test pass rate (5,804/5,804 tests passing)

GitHub Main (origin/main):
- 453ec9c4: feat: Add GitHub Pro setup for constitutional compliance

Open PRs:
- PR #91: feat: Tiered Spec Review for Two-Stage Checkpoint (Leap 7)
- PR #90: docs: Add /primeA workflow integration for branch protection
```

**Issue**: GitHub main CI is red (Update Backlog workflow failures)

### Test Suite State

**Metrics**:
- Tests: 5,804 passing locally (100% pass rate)
- Runtime: 3.9 minutes
- Files: 292 test files
- Skipped: 164 tests

**Master-Architect Audit Grade**: B+ (82/100) - Production Ready with Critical Gaps

### Identified Gaps

**4 P0 Blockers** ($200K+ risk each):
1. Zero NECESSARY markers (ADR-011 violation)
2. No code coverage metrics (unknown risk surface)
3. /primeccc workflow untested (claimed 93% efficiency, zero E2E tests)
4. Article IV VectorStore disabled in tests (constitutional violation)

**8 P1 High-Priority** ($50-100K risk each):
5. Agent communication untested (5 tests for 10 agents)
6. Memory architecture gaps (Anthropic Memory Tool untested)
7. Constitutional enforcement partial (Articles I-II covered, III-V minimal)
8. E2E workflow coverage <1% (29 tests vs 5,804 unit)
9. Fixture dependency unknown (6-layer conftest hierarchy)
10. Realistic test data missing (all synthetic mocks)
11. Performance baselines missing (no load tests)
12. Security testing minimal (7 tests, no penetration)

**200+ Bloat Issues** (technical debt):
- 200 tests recommended for deletion
- 69 tests waste 89s with time.sleep()
- test_chief_architect_agent.py: bloat score 5,207 (369 mocks!)

---

## 🏗️ Strategic Architecture

### Three-Phase Approach

```
Phase 0: Stabilization (Days 1-5)
├─ Stabilize main branch CI
├─ Merge recent work (PRs + commits)
├─ Validate 100% pass rate baseline
└─ Create branch protection rules

Phase 1-2: Critical Gaps (Weeks 1-4)
├─ Week 1: P0 Blocker #1-2 (NECESSARY markers, coverage)
├─ Week 2: P0 Blocker #3-4 (/primeccc tests, Article IV)
├─ Week 3: P1 Gap #5-6 (agent comm, memory)
└─ Week 4: P1 Gap #7-8 (constitutional, E2E)

Phase 3-4: Production Hardening (Weeks 5-8)
├─ Week 5-6: Security + stress testing
├─ Week 7: Bloat cleanup (delete 200 tests)
└─ Week 8: Documentation + ADR synthesis
```

### Task Graph Decomposition

**56 Total Tasks**:
- 8 Spec tasks (requirements definition)
- 24 Code tasks (implementation)
- 24 Test tasks (verification - every Code task has Test)

**Execution Layers** (topological sort):
- Layer 0: Stabilization (5 tasks, parallel)
- Layer 1: P0 Blockers (12 tasks, 3 batches)
- Layer 2: P1 Gaps (16 tasks, 4 batches)
- Layer 3: Hardening (15 tasks, 3 batches)
- Layer 4: Finalization (8 tasks, 2 batches)

---

## 📋 Detailed Task Breakdown

### PHASE 0: STABILIZATION (Days 1-5) - 5 Tasks

**Goal**: Achieve clean main branch + merge recent work

#### Task 0.1: Diagnose Main CI Failures
**Type**: Code
**Tier**: Tier 1 (Complex)
**Agent**: auditor
**Dependencies**: []

**Description**:
Investigate why "Update Backlog" workflow is failing on GitHub main (5 consecutive failures).

**Acceptance Criteria**:
- Root cause identified (workflow file, permissions, backlog format)
- Fix strategy documented
- No side effects on other workflows

**Files**:
- `.github/workflows/*.yml`
- `~/.agency/memories/agency_backlog/*.md`

---

#### Task 0.2: Fix Main CI Workflow
**Type**: Code
**Tier**: Tier 2 (Moderate)
**Agent**: coder
**Dependencies**: [task_0_1]

**Description**:
Apply fix for "Update Backlog" workflow failure. May require workflow file changes, backlog format updates, or GitHub Action permissions.

**Acceptance Criteria**:
- Workflow runs successfully on main
- No breaking changes to backlog functionality
- All other workflows unaffected

---

#### Task 0.3: Test CI Fix
**Type**: Test
**Tier**: Tier 2
**Agent**: test_generator
**Dependencies**: [task_0_2]
**Verification Target**: task_0_2

**Description**:
Create integration test for backlog workflow to prevent future CI failures.

**Acceptance Criteria**:
- Test validates workflow trigger conditions
- Test catches invalid backlog markdown
- Test runs in <10s

---

#### Task 0.4: Create PR for Local Commits
**Type**: Code
**Tier**: Tier 2
**Agent**: merger
**Dependencies**: [task_0_3]

**Description**:
Push local commits to GitHub and create PR for `fix/test-suite-top-3-blockers` branch.

**Commits to Push**:
1. fix: Achieve 100% test pass rate (5,804/5,804)
2. feat: Fix orchestrator and ML classifier compatibility
3. docs: Add Master-Architect test suite audit
4. chore: Update specs, models, missions

**Acceptance Criteria**:
- Branch pushed to origin
- PR created with comprehensive description
- CI triggered and passing
- Linked to audit documents

---

#### Task 0.5: Merge All Open PRs
**Type**: Code
**Tier**: Tier 2
**Agent**: merger
**Dependencies**: [task_0_4]

**Description**:
Sequentially merge PRs to main after CI validation:
1. PR #90: /primeA workflow integration (branch protection docs)
2. PR #91: Tiered Spec Review (Leap 7 feature)
3. PR (new): Test suite fixes (4 commits from task_0_4)

**Acceptance Criteria**:
- All PRs merged to main
- No merge conflicts
- Main branch CI green after each merge
- All tests passing on main (5,804/5,804)

**Post-Merge Validation**:
```bash
git checkout main
git pull origin main
python run_tests.py --run-all
# Expected: 5,804 passed, 0 failed
```

---

### PHASE 1: P0 BLOCKER #1-2 (Week 1) - 8 Tasks

**Goal**: NECESSARY markers + code coverage

#### Task 1.1: Spec NECESSARY Marker Strategy
**Type**: Spec
**Tier**: Tier 1
**Agent**: planner
**Dependencies**: [task_0_5]

**Description**:
Design auto-classification strategy to apply NECESSARY markers to 5,804 existing tests.

**ADR Reference**: ADR-011 (NECESSARY Pattern Constitutional Requirement)

**Marker Categories**:
- **Normal**: Happy path, valid inputs
- **Edge**: Boundary conditions, empty inputs
- **Security**: Auth, injection, CSRF
- **Spec**: Acceptance criteria validation
- **Accessibility**: A11y compliance
- **Resilience**: Timeouts, retries, fallbacks
- **Year-round**: Date/time edge cases

**Acceptance Criteria**:
- Classification rules for 7 NECESSARY categories
- AST-based auto-detection heuristics
- Confidence scoring per classification
- Dry-run mode for validation

**Deliverable**: `specs/spec-033-necessary-marker-auto-classification.md`

---

#### Task 1.2: Implement NECESSARY Classifier
**Type**: Code
**Tier**: Tier 2
**Agent**: coder
**Dependencies**: [task_1_1]

**Description**:
Build Python script to auto-classify and apply NECESSARY markers using AST parsing.

**Algorithm**:
```python
def classify_test(test_func_node: ast.FunctionDef) -> List[str]:
    markers = []

    # Heuristics
    if "test_invalid" in test_func_node.name or "test_empty" in test_func_node.name:
        markers.append("necessary_edge")

    if "auth" in test_func_node.name or "permission" in test_func_node.name:
        markers.append("necessary_security")

    if "acceptance_criteria" in extract_docstring(test_func_node):
        markers.append("necessary_spec")

    # Default to Normal if no specific category
    if not markers:
        markers.append("necessary_normal")

    return markers
```

**Acceptance Criteria**:
- Script parses all 292 test files
- Applies markers via AST rewriting
- Preserves existing test decorators
- Generates classification report (confidence scores)
- Dry-run mode validates before applying

**Files**:
- `tools/test_marker_classifier.py` (new)
- `tests/test_marker_classifier.py` (new)

---

#### Task 1.3: Test NECESSARY Classifier
**Type**: Test
**Tier**: Tier 2
**Agent**: test_generator
**Dependencies**: [task_1_2]
**Verification Target**: task_1_2

**Description**:
Validate NECESSARY classifier accuracy and safety.

**Test Cases** (NECESSARY compliant!):
```python
@pytest.mark.necessary_normal
def test_classifier_valid_syntax():
    """Should preserve valid Python syntax after marker injection."""

@pytest.mark.necessary_edge
def test_classifier_empty_file():
    """Should handle empty test files without crashing."""

@pytest.mark.necessary_security
def test_classifier_no_destructive_changes():
    """Should not modify test logic, only add decorators."""
```

**Acceptance Criteria**:
- 20+ tests covering all 7 marker categories
- Edge cases (empty files, malformed syntax, existing markers)
- Performance test (<5s for 5,804 files)

---

#### Task 1.4: Apply NECESSARY Markers to Test Suite
**Type**: Code
**Tier**: Tier 2
**Agent**: coder
**Dependencies**: [task_1_3]

**Description**:
Execute classifier on entire test suite (5,804 tests, 292 files).

**Execution**:
```bash
# Dry-run validation
python tools/test_marker_classifier.py --dry-run --report /tmp/classification_report.json

# Review report (manual checkpoint)
cat /tmp/classification_report.json | jq '.summary'

# Apply markers (Git checkpoint before)
git add -A && git commit -m "chore: Checkpoint before NECESSARY marker application"
python tools/test_marker_classifier.py --apply

# Validate
pytest --collect-only | grep "necessary_" | wc -l
# Expected: 5,804 tests now have markers
```

**Acceptance Criteria**:
- All 5,804 tests marked
- Syntax validated (pytest --collect-only succeeds)
- All tests still pass (100% pass rate maintained)
- Classification report shows confidence scores

**Deliverable**: Git commit with 292 modified test files

---

#### Task 1.5: Spec Code Coverage Strategy
**Type**: Spec
**Tier**: Tier 1
**Agent**: planner
**Dependencies**: [task_1_4]

**Description**:
Design pytest-cov integration with coverage gates and CI integration.

**Acceptance Criteria**:
- Target coverage percentage (70% baseline, 85% goal)
- Exclusion rules (test files, migrations, __init__.py)
- CI/CD integration strategy
- Coverage report format (HTML, terminal, XML for badges)

**Key Decisions**:
- Use `pytest-cov` (industry standard)
- Generate HTML report for browsing
- Fail CI if coverage drops below 70%
- Track coverage trends over time

**Deliverable**: `specs/spec-034-code-coverage-integration.md`

---

#### Task 1.6: Install and Configure pytest-cov
**Type**: Code
**Tier**: Tier 2
**Agent**: coder
**Dependencies**: [task_1_5]

**Description**:
Install pytest-cov, configure coverage settings, integrate with run_tests.py.

**Files**:
- `pyproject.toml` (add pytest-cov config)
- `run_tests.py` (add --coverage flag)
- `.coveragerc` (exclusion rules)
- `.gitignore` (add htmlcov/, .coverage)

**Configuration**:
```toml
# pyproject.toml
[tool.coverage.run]
source = [".", "agency_code_agent", "planner_agent", "tools", "shared"]
omit = ["*/tests/*", "*/__pycache__/*", "*/migrations/*"]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
```

**Acceptance Criteria**:
- pytest-cov installed (pip install pytest-cov)
- Coverage report generated successfully
- HTML report browsable (htmlcov/index.html)
- Terminal report shows per-file coverage

---

#### Task 1.7: Test Coverage Integration
**Type**: Test
**Tier**: Tier 2
**Agent**: test_generator
**Dependencies**: [task_1_6]
**Verification Target**: task_1_6

**Description**:
Validate coverage integration works correctly.

**Test Cases**:
```python
@pytest.mark.necessary_normal
def test_coverage_report_generated():
    """Should create .coverage file after test run."""

@pytest.mark.necessary_edge
def test_coverage_html_output():
    """Should generate htmlcov/index.html."""

@pytest.mark.necessary_spec
def test_coverage_above_baseline():
    """Should show coverage >70% for acceptance."""
```

**Acceptance Criteria**:
- Coverage report generated after test run
- Baseline coverage measured (document actual %)
- No false negatives (test files excluded)

---

#### Task 1.8: Generate Initial Coverage Report
**Type**: Code
**Tier**: Tier 2
**Agent**: coder
**Dependencies**: [task_1_7]

**Description**:
Run full test suite with coverage and analyze results.

**Execution**:
```bash
python run_tests.py --run-all --coverage
open htmlcov/index.html
```

**Deliverables**:
- Coverage report (HTML + JSON)
- Analysis document: `docs/test-coverage-baseline-2025-10-17.md`
- Identify top 10 uncovered critical files
- Prioritize coverage improvements for Phase 2

**Acceptance Criteria**:
- Baseline coverage documented
- Critical gaps identified (auth, orchestrator, memory)
- Improvement targets set (70% → 85%)

---

### PHASE 2: P0 BLOCKER #3-4 (Week 2) - 10 Tasks

**Goal**: /primeccc E2E tests + Article IV VectorStore enforcement

#### Task 2.1: Spec /primeccc E2E Test Strategy
**Type**: Spec
**Tier**: Tier 1
**Agent**: planner
**Dependencies**: [task_1_8]

**Description**:
Design comprehensive E2E test plan for /primeccc autonomous orchestration workflow.

**Workflow Steps to Test**:
1. Auto-select from backlog (priority queue parsing)
2. Generate task graph (Planner agent)
3. Validate task graph (DAG, Pydantic)
4. Execute phases (parallel agent spawning)
5. Verify completion (all tasks succeeded)
6. Create PR (Merger agent)
7. VectorStore learning (pattern extraction)

**Acceptance Criteria**:
- 20+ E2E test scenarios (happy path + edge cases)
- Test data fixtures (realistic backlog items)
- Mock strategy for expensive operations (GitHub API, LLM calls)
- Performance targets (<5 min per E2E test)

**Deliverable**: `specs/spec-035-primeccc-e2e-testing.md`

---

#### Task 2.2: Create /primeccc E2E Test Fixtures
**Type**: Code
**Tier**: Tier 2
**Agent**: coder
**Dependencies**: [task_2_1]

**Description**:
Build realistic test fixtures for E2E /primeccc workflow.

**Fixtures**:
```python
@pytest.fixture
def sample_backlog_simple():
    """Simple 3-task mission (1 Spec, 1 Code, 1 Test)."""
    return {
        "mission": "Add health check endpoint",
        "priority": 1,
        "complexity": "simple",
        "tasks": [...]
    }

@pytest.fixture
def sample_backlog_complex():
    """Complex 12-task mission (architecture + parallel execution)."""
    return {
        "mission": "Implement JWT authentication",
        "priority": 1,
        "complexity": "complex",
        "tasks": [...]
    }

@pytest.fixture
def mock_planner_agent(monkeypatch):
    """Mock Planner agent to return deterministic task graphs."""
    ...

@pytest.fixture
def mock_github_api(monkeypatch):
    """Mock GitHub PR creation to avoid rate limits."""
    ...
```

**Acceptance Criteria**:
- 5+ backlog fixtures (simple, moderate, complex)
- Mocks for external services (GitHub, OpenAI)
- Fixtures reusable across E2E tests

**Files**:
- `tests/e2e/fixtures/primeccc_fixtures.py` (new)

---

#### Task 2.3: Implement /primeccc E2E Tests (Happy Path)
**Type**: Code
**Tier**: Tier 2
**Agent**: coder
**Dependencies**: [task_2_2]

**Description**:
Build 10 happy-path E2E tests for core /primeccc functionality.

**Test Cases**:
```python
@pytest.mark.e2e
@pytest.mark.necessary_normal
def test_primeccc_auto_select_from_backlog(sample_backlog_simple, mock_planner):
    """Should auto-select highest priority task from backlog."""
    result = primeccc_orchestrator.execute(auto_select=True)
    assert result.is_ok()
    assert result.unwrap().mission == "Add health check endpoint"

@pytest.mark.e2e
@pytest.mark.necessary_normal
def test_primeccc_parallel_execution(sample_backlog_complex):
    """Should execute parallel tasks in batches."""
    result = primeccc_orchestrator.execute(graph=sample_backlog_complex)
    assert result.is_ok()
    assert result.unwrap().tasks_completed == 12
    assert result.unwrap().parallelism_achieved > 3  # At least 3 parallel workers

@pytest.mark.e2e
@pytest.mark.necessary_normal
def test_primeccc_creates_pr_on_success(mock_github_api):
    """Should create GitHub PR after successful execution."""
    result = primeccc_orchestrator.execute(intent="Add feature X", auto_pr=True)
    assert result.is_ok()
    assert mock_github_api.pr_created
```

**Acceptance Criteria**:
- 10 tests covering core workflow
- All tests pass (green baseline)
- Tests run in <5 min total
- Use NECESSARY markers (necessary_normal)

**Files**:
- `tests/e2e/test_primeccc_workflow.py` (new, 10 tests)

---

#### Task 2.4: Test /primeccc E2E Happy Path
**Type**: Test
**Tier**: Tier 2
**Agent**: test_generator
**Dependencies**: [task_2_3]
**Verification Target**: task_2_3

**Description**:
Validate E2E tests are correctly implemented and passing.

**Meta-Test Cases**:
```python
@pytest.mark.necessary_spec
def test_e2e_tests_exist():
    """Should have at least 10 /primeccc E2E tests."""
    tests = collect_tests("tests/e2e/test_primeccc_workflow.py")
    assert len(tests) >= 10

@pytest.mark.necessary_normal
def test_e2e_tests_use_fixtures():
    """Should reuse fixtures for consistency."""
    # Validate fixtures are imported and used
    ...

@pytest.mark.necessary_resilience
def test_e2e_tests_timeout_protection():
    """Should have timeout markers (<5 min per test)."""
    ...
```

**Acceptance Criteria**:
- E2E tests validated
- All 10 tests passing
- Coverage report shows /primeccc orchestrator covered

---

#### Task 2.5: Implement /primeccc E2E Tests (Edge Cases)
**Type**: Code
**Tier**: Tier 2
**Agent**: coder
**Dependencies**: [task_2_4]

**Description**:
Build 10 edge-case E2E tests for failure scenarios and boundary conditions.

**Test Cases**:
```python
@pytest.mark.e2e
@pytest.mark.necessary_edge
def test_primeccc_empty_backlog():
    """Should fail gracefully when backlog is empty."""
    result = primeccc_orchestrator.execute(auto_select=True)
    assert result.is_err()
    assert "No tasks in backlog" in result.unwrap_err()

@pytest.mark.e2e
@pytest.mark.necessary_edge
def test_primeccc_circular_dependency():
    """Should detect circular dependencies in task graph."""
    graph = create_circular_graph()  # Task A -> B -> C -> A
    result = primeccc_orchestrator.execute(graph=graph)
    assert result.is_err()
    assert "Circular dependency" in result.unwrap_err()

@pytest.mark.e2e
@pytest.mark.necessary_resilience
def test_primeccc_agent_failure_retry():
    """Should retry failed agents with exponential backoff."""
    with mock_agent_failure(agent="coder", fail_count=2):
        result = primeccc_orchestrator.execute(intent="Build feature")
        assert result.is_ok()  # Should succeed after 2 retries
```

**Acceptance Criteria**:
- 10 edge-case tests
- All tests pass
- Use NECESSARY markers (necessary_edge, necessary_resilience)

**Files**:
- `tests/e2e/test_primeccc_edge_cases.py` (new, 10 tests)

---

#### Task 2.6: Test /primeccc E2E Edge Cases
**Type**: Test
**Tier**: Tier 2
**Agent**: test_generator
**Dependencies**: [task_2_5]
**Verification Target**: task_2_5

**Description**:
Validate edge-case tests are robust.

**Acceptance Criteria**:
- All 10 edge-case tests passing
- Edge cases caught and handled gracefully
- Coverage improvement documented

---

#### Task 2.7: Spec Article IV VectorStore Enforcement
**Type**: Spec
**Tier**: Tier 1
**Agent**: planner
**Dependencies**: [task_2_6]

**Description**:
Design strategy to enforce Article IV (VectorStore mandatory) in test suite.

**Current Issue**: Tests disable VectorStore with `USE_ENHANCED_MEMORY=false`

**Proposed Solution**:
1. **Constitutional Gate**: Create pytest plugin that validates Article IV
2. **Separate Test Modes**:
   - Unit tests: VectorStore optional (speed)
   - Integration tests: VectorStore required (realism)
   - E2E tests: VectorStore mandatory (constitutional)
3. **Memory Assertions**: Add explicit VectorStore checks in orchestrator tests

**Acceptance Criteria**:
- Test mode classification (unit vs integration vs E2E)
- VectorStore enforcement strategy per mode
- Backward compatibility (existing tests don't break)

**Deliverable**: `specs/spec-036-article-iv-test-enforcement.md`

---

#### Task 2.8: Implement Article IV Enforcement Plugin
**Type**: Code
**Tier**: Tier 2
**Agent**: coder
**Dependencies**: [task_2_7]

**Description**:
Build pytest plugin to enforce VectorStore usage in E2E/integration tests.

**Plugin Logic**:
```python
# conftest.py
def pytest_runtest_setup(item):
    """Enforce Article IV for E2E and integration tests."""
    if item.get_closest_marker("e2e") or item.get_closest_marker("integration"):
        # Check VectorStore is enabled
        if os.getenv("USE_ENHANCED_MEMORY") != "true":
            pytest.fail(
                "Article IV violation: E2E/integration tests require VectorStore "
                "(USE_ENHANCED_MEMORY=true)"
            )
```

**Acceptance Criteria**:
- Plugin activates for E2E/integration markers
- Unit tests unaffected (can disable VectorStore)
- Clear error message on violation

**Files**:
- `tests/conftest.py` (add plugin)
- `tests/plugins/article_iv_enforcer.py` (new)

---

#### Task 2.9: Test Article IV Enforcement
**Type**: Test
**Tier**: Tier 2
**Agent**: test_generator
**Dependencies**: [task_2_8]
**Verification Target**: task_2_8

**Description**:
Validate Article IV enforcement plugin works correctly.

**Test Cases**:
```python
@pytest.mark.necessary_spec
def test_article_iv_enforced_for_e2e():
    """Should fail E2E tests if VectorStore disabled."""
    with monkeypatch.setenv("USE_ENHANCED_MEMORY", "false"):
        result = pytest.main(["tests/e2e/test_primeccc_workflow.py::test_primeccc_auto_select"])
        assert result == pytest.ExitCode.TESTS_FAILED

@pytest.mark.necessary_normal
def test_article_iv_allows_unit_tests():
    """Should allow unit tests to disable VectorStore (speed)."""
    with monkeypatch.setenv("USE_ENHANCED_MEMORY", "false"):
        result = pytest.main(["tests/unit/test_memory_cache.py"])
        assert result == pytest.ExitCode.OK
```

**Acceptance Criteria**:
- Enforcement validated
- E2E tests blocked without VectorStore
- Unit tests unaffected

---

#### Task 2.10: Enable VectorStore in CI for E2E Tests
**Type**: Code
**Tier**: Tier 2
**Agent**: coder
**Dependencies**: [task_2_9]

**Description**:
Update CI workflows to enable VectorStore for E2E/integration test runs.

**Changes**:
```yaml
# .github/workflows/test.yml
- name: Run E2E Tests
  env:
    USE_ENHANCED_MEMORY: true  # Article IV compliance
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    pytest tests/e2e/ --markers e2e -v
```

**Acceptance Criteria**:
- CI enables VectorStore for E2E tests
- All E2E tests pass in CI
- Article IV enforced (no bypass possible)

---

### PHASE 3: P1 GAPS (Weeks 3-4) - 16 Tasks

**Goal**: Agent communication + memory architecture + constitutional tests

*(Tasks 3.1-3.16 follow same structure as above - Spec → Code → Test pattern)*

**Week 3 Focus** (8 tasks):
- Task 3.1-3.4: Agent communication tests (10 agents × 5 comm patterns = 50 tests)
- Task 3.5-3.8: Memory architecture tests (Anthropic Memory Tool E2E)

**Week 4 Focus** (8 tasks):
- Task 3.9-3.12: Constitutional enforcement (Articles III-V automated tests)
- Task 3.13-3.16: E2E workflow expansion (2x coverage from 29 → 58 tests)

---

### PHASE 4: PRODUCTION HARDENING (Weeks 5-8) - 15 Tasks

**Goal**: Security + stress + bloat cleanup

**Week 5-6: Security & Stress** (9 tasks):
- Task 4.1-4.3: Penetration testing (auth bypass, injection, CSRF)
- Task 4.4-4.6: Load testing (1000 concurrent tasks, memory profiling)
- Task 4.7-4.9: Chaos engineering (network failures, agent crashes)

**Week 7: Bloat Cleanup** (3 tasks):
- Task 4.10: Delete 200 bloated tests (following audit checklist)
- Task 4.11: Refactor time.sleep() (mock time for 69 tests, save 89s)
- Task 4.12: Parametrize duplicate tests (test_bash_pydantic_validation)

**Week 8: Documentation & ADR** (3 tasks):
- Task 4.13: Generate ADR-032 (8-Week Test Suite Recovery)
- Task 4.14: Update test architecture documentation
- Task 4.15: Final validation and handoff

---

## 🎯 Success Criteria

### Phase 0 Completion (Day 5)
- ✅ GitHub main branch CI green (100% pass rate)
- ✅ All PRs merged (3 PRs: #90, #91, test suite fixes)
- ✅ Clean git state (no uncommitted changes)
- ✅ Baseline established (5,804 tests passing locally and in CI)

### Phase 1-2 Completion (Week 2)
- ✅ All 5,804 tests have NECESSARY markers
- ✅ Code coverage baseline documented (>70%)
- ✅ 20 /primeccc E2E tests passing
- ✅ Article IV enforced (VectorStore mandatory in E2E tests)

### Phase 3 Completion (Week 4)
- ✅ 50 agent communication tests
- ✅ Memory architecture E2E validated
- ✅ Constitutional Articles III-V automated enforcement
- ✅ E2E coverage 2x (58 tests vs 29)

### Phase 4 Completion (Week 8)
- ✅ 200 bloated tests deleted
- ✅ 89s runtime saved (time.sleep() mocked)
- ✅ Security tests passing (penetration, load, chaos)
- ✅ ADR-032 published
- ✅ **Final Grade: A (95/100) - Production Ready**

---

## 💰 Investment & ROI

### Effort Breakdown

| Phase | Duration | Engineering Days | Cost Estimate |
|-------|----------|-----------------|---------------|
| Phase 0: Stabilization | 5 days | 3 days | $2,400 |
| Phase 1: P0 #1-2 | 1 week | 5 days | $4,000 |
| Phase 2: P0 #3-4 | 1 week | 5 days | $4,000 |
| Phase 3: P1 Gaps | 2 weeks | 8 days | $6,400 |
| Phase 4: Hardening | 4 weeks | 12 days | $9,600 |
| **Total** | **8 weeks** | **33 days** | **$26,400** |

### Risk Reduction

**Without This Work** (Current State):
- 4 P0 blockers: $800K risk ($200K each)
- 8 P1 gaps: $600K risk ($75K avg)
- Production failures: Unknown (untested workflows)
- **Total Exposure**: $1.4M

**With This Work** (After 8 Weeks):
- P0 risk eliminated: $800K → $0
- P1 risk reduced 80%: $600K → $120K
- Production confidence: 70% → 95%
- **Residual Risk**: $120K

**ROI**: $1.28M risk reduction / $26.4K investment = **48:1 ROI**

---

## 📊 Metrics & KPIs

### Health Score Progression

| Metric | Baseline | Week 2 | Week 4 | Week 8 | Target |
|--------|----------|--------|--------|--------|--------|
| Overall Grade | B+ (82) | B+ (84) | A- (88) | A (95) | A (95) |
| NECESSARY Compliance | F (0) | A (100) | A (100) | A (100) | A (100) |
| Code Coverage | Unknown | C+ (70) | B (78) | A- (85) | A- (85) |
| E2E Coverage | F (0.5%) | C (2%) | B- (3.5%) | B+ (5%) | B+ (5%) |
| Bloat Score | B- (72) | B- (72) | B (78) | A- (88) | A- (88) |

### Test Suite Metrics

| Metric | Baseline | Target (Week 8) | Delta |
|--------|----------|-----------------|-------|
| Total Tests | 5,804 | ~5,850 | +46 (new E2E) - 200 (deleted bloat) = -154 net |
| Pass Rate | 100% | 100% | Maintained |
| Runtime | 3.9 min | 3.0 min | -23% (sleep mocking) |
| Skipped | 164 | <50 | -70% |
| NECESSARY Markers | 0 | 5,850 | +100% |

---

## 🔄 Execution Strategy

### Workflow

1. **Planning Phase** (This Document):
   - ✅ Create comprehensive spec (spec-032)
   - ✅ Generate task graph JSON for primeA execution
   - User approval checkpoint

2. **Execution Phase** (Week 0-8):
   - Deploy primeA orchestrator with `--two-stage` workflow
   - Stage 1: Generate phase-specific specs (spec-033 to spec-036)
   - User approval after each phase
   - Stage 2: Execute task graph with parallel agents
   - Continuous validation (tests pass after each task)

3. **Validation Phase** (Week 8):
   - Final test suite run (100% pass rate)
   - Coverage validation (≥85%)
   - Security audit (penetration tests pass)
   - Grade calculation (≥95/100 = A grade)

### Git Strategy

**Branch Structure**:
```
main (protected, green)
├── feat/necessary-markers (Phase 1, Week 1)
├── feat/code-coverage (Phase 1, Week 1)
├── feat/primeccc-e2e (Phase 2, Week 2)
├── feat/article-iv-enforcement (Phase 2, Week 2)
├── feat/agent-communication (Phase 3, Week 3)
├── feat/memory-architecture (Phase 3, Week 3)
├── feat/constitutional-tests (Phase 3, Week 4)
├── feat/security-hardening (Phase 4, Week 5-6)
└── feat/bloat-cleanup (Phase 4, Week 7)
```

**PR Strategy**:
- 1 PR per week (8 PRs total)
- Each PR requires 100% CI pass
- Squash merge to keep main history clean
- Linked to audit documents and ADRs

---

## 🚨 Risks & Mitigations

### Risk #1: CI Instability on Main
**Likelihood**: High (already red)
**Impact**: Blocks all merges

**Mitigation**:
- Phase 0 highest priority (fix before continuing)
- Root cause analysis (Task 0.1)
- Comprehensive fix validation (Task 0.3)
- Branch protection rules enforce green CI

---

### Risk #2: NECESSARY Marker Classification Errors
**Likelihood**: Medium (auto-classification may misclassify)
**Impact**: Incorrect test categorization

**Mitigation**:
- Dry-run mode with confidence scoring (Task 1.2)
- Manual review of low-confidence classifications (<0.6)
- Iterative refinement (run classifier, review, adjust heuristics)
- Rollback checkpoint (Git commit before applying)

---

### Risk #3: VectorStore Performance in CI
**Likelihood**: Medium (increased latency in E2E tests)
**Impact**: Test runtime increases

**Mitigation**:
- E2E tests use mocked LLM calls (fast)
- VectorStore uses in-memory backend for CI (vs Firestore)
- Timeout protection (<5 min per E2E test)
- Parallel execution disabled for E2E (sequential for stability)

---

### Risk #4: Bloat Deletion Breaks Dependencies
**Likelihood**: Low (200 tests marked for deletion may be needed)
**Impact**: Unexpected test failures

**Mitigation**:
- Comprehensive impact analysis before deletion (Task 4.10)
- Delete in batches (50 tests at a time, validate after each)
- Git checkpoint before each batch
- Rollback strategy (revert batch if failures)

---

## 📚 References

### Audit Documents
- `docs/TEST_SUITE_MASTER_ARCHITECT_COMPREHENSIVE_AUDIT.md` - Primary audit
- `docs/TEST_SUITE_BLOAT_ANALYSIS.md` - Bloat details
- `docs/TEST_SUITE_CLEANUP_CHECKLIST.md` - Deletion guide
- `docs/TEST_ARCHITECTURE_ACTION_PLAN.md` - Phase breakdown
- `docs/test-suite-bloat-metrics.json` - Machine-readable metrics

### ADRs
- ADR-011: NECESSARY Pattern Constitutional Requirement
- ADR-031: Test Suite Strategic Assessment
- ADR-032: 8-Week Test Suite Recovery (to be created)

### Related Specs
- spec-031: E2E Workflow Implementation (Leap 7)
- spec-033: NECESSARY Marker Auto-Classification (to be created)
- spec-034: Code Coverage Integration (to be created)
- spec-035: /primeccc E2E Testing (to be created)
- spec-036: Article IV Test Enforcement (to be created)

---

## 🎯 Next Steps

### Immediate Actions (User Approval Required)

1. **Review This Spec** - Validate strategic approach and task breakdown
2. **Approve Phase 0 Execution** - Authorize CI fix and PR merges (Days 1-5)
3. **Generate Task Graph** - Convert spec to JSON for primeA orchestrator
4. **Execute Phase 0** - Stabilize main branch and merge recent work

### Post-Approval Execution

```bash
# Generate task graph from this spec
/primeA --graph specs/spec-032-test-suite-strategic-recovery-8-week-plan.md --plan-only

# Review task graph (56 tasks, 8-week execution)
cat /tmp/task_graph_*.json | jq '.phases[] | {id, title, tasks: (.tasks | length)}'

# Execute Phase 0 (Stabilization)
/primeA --graph /tmp/task_graph_*.json --phase 0 --auto-pr

# After Phase 0 complete, proceed to Phase 1-2 (Weeks 1-2)
# User approval checkpoint after each phase
```

---

**Prepared By**: Master-Architect (PrimeA Meta-Intelligence)
**Status**: READY FOR USER APPROVAL
**Estimated Completion**: 2025-12-12 (8 weeks from 2025-10-17)
**Success Probability**: 90% (assuming user approval and no external blockers)

---

*"Tactical excellence meets strategic completeness. 8 weeks to production-grade confidence."*
