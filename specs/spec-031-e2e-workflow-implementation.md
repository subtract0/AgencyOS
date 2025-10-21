# Specification: E2E Workflow Function Implementation

**ID**: SPEC-031
**Status**: Draft
**Created**: 2025-10-16
**Updated**: 2025-10-16
**Owner**: AgencyOS Agent
**Related Specs**: SPEC-030 (Foundation Automation Test Coverage)
**Related ADRs**: ADR-027 (Two-Stage TDD), ADR-032 (Autonomous Completion Protocol)

---

## Stage 1: Specification Approval

### Executive Summary

This specification defines the implementation of E2E workflow functions for the UnifiedPrimeAOrchestrator, following the test coverage strategy outlined in SPEC-030. We will implement 15 RED-phase tests first (TDD Article VI mandate), then create the necessary orchestrator methods to make them pass.

The implementation focuses on creating comprehensive E2E workflow test coverage with the NECESSARY pattern, ensuring all workflow paths from natural language intent to PR creation are thoroughly tested.

---

## Goals

### User Goals
1. **Complete E2E Testing**: Full workflow validation from intent → task graph → validation → execution → PR
2. **TDD Compliance**: Tests written FIRST (RED phase), implementation SECOND (GREEN phase)
3. **Constitutional Enforcement**: All 5 articles validated at each workflow gate
4. **Foundation Automation**: Phase 0 git validation, backlog selection, flag handling

### System Goals
1. **NECESSARY Pattern**: All test categories covered (Normal, Edge, Constraints, Error, Security, Scale, Async, Retry, Yield)
2. **Test Isolation**: No cross-test pollution, fixtures with automatic cleanup
3. **Performance Targets**: E2E <120s, backlog selection <2s, git validation <50ms
4. **Coverage Target**: >95% code coverage for orchestrator module

---

## Acceptance Criteria

### RED Phase (Tests First)
- [ ] Create `test_foundation_automation_e2e.py` with 8 E2E workflow tests
- [ ] Create `test_foundation_automation_backlog.py` with 5 backlog selection tests
- [ ] Create `test_foundation_automation_git_validation.py` with 6 git validation tests
- [ ] Create `test_foundation_automation_flags.py` with 8 flag behavior tests
- [ ] Create `test_foundation_automation_gates.py` with 12 constitutional gate tests
- [ ] Create `test_foundation_automation_fallbacks.py` with 7 graceful fallback tests
- [ ] All 46 tests MUST FAIL initially (RED phase requirement)

### GREEN Phase (Implementation)
- [ ] Implement `_auto_select_from_backlog()` method in orchestrator
- [ ] Implement `_validate_git_workflow()` method for Phase 0
- [ ] Implement `_parse_intent()` for natural language processing
- [ ] Implement `_handle_flags()` for flag parsing and routing
- [ ] Implement `_execute_e2e_workflow()` main orchestration method
- [ ] Implement fallback handlers for each external dependency
- [ ] All 46 tests MUST PASS after implementation

### REFACTOR Phase (Optimization)
- [ ] Extract common patterns to fixtures
- [ ] Optimize performance bottlenecks
- [ ] Add comprehensive docstrings
- [ ] Ensure no code duplication

---

## Implementation Plan

### Phase 1: Test File Structure Creation (RED)

```python
# tests/orchestrator/test_foundation_automation_e2e.py
class TestFoundationAutomationE2E:
    """E2E workflow tests following NECESSARY pattern."""

    def test_e2e_001_natural_language_to_pr_happy_path(self):
        """E2E-001: Natural language intent → PR creation."""
        assert False  # RED phase

    def test_e2e_002_two_stage_workflow_with_approval(self):
        """E2E-002: --two-stage flag with spec approval."""
        assert False  # RED phase

    def test_e2e_003_no_pr_flag_skips_pr_creation(self):
        """E2E-003: --no-pr flag validation."""
        assert False  # RED phase

    # ... 5 more tests
```

### Phase 2: Orchestrator Method Implementation (GREEN)

```python
# tools/orchestrator/unified_primea_orchestrator.py

async def _auto_select_from_backlog(self) -> Result[str, BacklogError]:
    """
    Parse backlog file and select highest priority task.

    Returns:
        Ok(intent): Selected task description
        Err(BacklogError): If no tasks available or file error
    """
    backlog_path = Path.home() / ".agency/memories/agency_backlog/test_suite_gaps.md"

    if not backlog_path.exists():
        self.logger.warning(f"Backlog file not found: {backlog_path}")
        return Err(BacklogError("No backlog file found"))

    # Parse markdown for priority tasks
    # Select first Ready task by priority
    # Return task description as intent

async def _validate_git_workflow(self) -> Result[None, GitValidationError]:
    """
    Phase 0: Validate git branch compliance (Article III).

    Checks:
    - Not on main/master branch
    - Feature branch pattern (feat/*, fix/*, etc.)
    - Repository exists
    """
    # Implementation per SPEC-030 requirements

async def _execute_e2e_workflow(
    self,
    intent: Optional[str] = None,
    graph_file: Optional[str] = None,
    flags: Dict[str, Any] = None
) -> Result[ExecutionResult, ExecutionError]:
    """
    Main E2E orchestration method.

    Workflow:
    1. Phase 0: Git validation
    2. Step 2: Parse input (auto-select/intent/graph)
    3. Step 3: Validate (TRM, Slop, Budget)
    4. Step 5: Execute DAG
    5. Step 6.5: Completion validation
    6. Final: PR creation (unless --no-pr)
    """
    # Complete implementation following SPEC-030
```

### Phase 3: NECESSARY Pattern Coverage

Each test suite covers all 9 NECESSARY categories:

1. **Normal (N)**: Happy path scenarios
2. **Edge (E)**: Boundary conditions
3. **Constraints (C)**: System limits
4. **Error (E)**: Error handling
5. **Security (S)**: Security validations
6. **Scale (S)**: Performance at scale
7. **Async (A)**: Concurrent operations
8. **Retry (R)**: Retry logic
9. **Yield (Y)**: Generator patterns (N/A for orchestrator)

---

## Test Data Requirements

### Fixtures

```python
# tests/orchestrator/fixtures/task_graphs.py
@pytest.fixture
def simple_task_graph():
    """5-task graph for performance testing."""
    return TaskGraph(...)

@pytest.fixture
def complex_task_graph():
    """100-task graph for scale testing."""
    return TaskGraph(...)

# tests/orchestrator/fixtures/mock_services.py
@pytest.fixture
def mock_vector_store():
    """Mock VectorStore with predefined learnings."""
    return create_mock_vector_store(learnings=[...])

@pytest.fixture
def mock_github_api():
    """Mock GitHub CLI for PR tests."""
    return mock_github_api(pr_url="...")
```

### Test Backlog Files

```markdown
# ~/.agency/memories/agency_backlog/test_suite_gaps.md
- [ ] Priority 1: Fix authentication bug
- [ ] Priority 2: Add rate limiting [Blocked]
- [ ] Priority 3: Improve logging [Ready]
```

---

## Performance Requirements

| Operation | Target | Measurement Method |
|-----------|--------|-------------------|
| E2E Simple (5 tasks) | <120s | pytest-benchmark |
| E2E Complex (100 tasks) | <600s | pytest-benchmark |
| Backlog Selection | <2s | pytest-benchmark |
| Git Validation | <50ms | pytest-benchmark |
| Constitutional Gates | <3s | pytest-benchmark |
| Memory Overhead | <500MB | tracemalloc |

---

## Constitutional Compliance

### Article I: Complete Context
- All tests verify complete task execution (no partial states)
- Retry logic tested with exponential backoff
- Timeout handling validated

### Article II: 100% Verification
- All 46 tests MUST pass before implementation approval
- Test coverage >95% enforced
- NECESSARY pattern validation

### Article III: Automated Enforcement
- No manual bypass mechanisms in tests
- All gates tested for enforcement
- Audit trail validation

### Article IV: Continuous Learning
- VectorStore mocks include pattern queries
- Successful patterns stored in fixtures
- Learning integration tested

### Article V: Spec-Driven Development
- This spec drives implementation
- Task graph traces to acceptance criteria
- Two-stage workflow validated

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Flaky Tests | High | Use deterministic mocks, no network calls |
| Test Pollution | High | Isolated fixtures, unique session IDs |
| Performance Regression | Medium | Benchmark tests with strict limits |
| Incomplete Coverage | High | NECESSARY pattern enforcement |

---

## Dependencies

### Python Packages
- pytest>=8.0.0
- pytest-asyncio>=0.21.0
- pytest-mock>=3.12.0
- pytest-timeout>=2.2.0
- pytest-benchmark>=4.0.0

### Existing Modules
- tools/orchestrator/unified_primea_orchestrator.py
- shared/models/task_graph.py
- shared/agent_context.py
- tools/orchestrator/completion_validator.py

---

## Success Criteria

1. **RED Phase Complete**: All 46 tests created and failing
2. **GREEN Phase Complete**: All 46 tests passing
3. **Coverage**: >95% for orchestrator module
4. **Performance**: All benchmarks within targets
5. **Constitutional**: All 5 articles validated

---

## Next Steps

Upon approval of this specification:

1. **Phase 1**: Create test files with RED tests (30 minutes)
2. **Phase 2**: Implement orchestrator methods (2 hours)
3. **Phase 3**: Refactor and optimize (30 minutes)
4. **Phase 4**: Run full test suite validation (10 minutes)
5. **Phase 5**: Create PR with test results

Total estimated time: 3.5 hours

---

**This specification defines the TDD implementation of E2E workflow functions, ensuring constitutional compliance and comprehensive test coverage per SPEC-030.**