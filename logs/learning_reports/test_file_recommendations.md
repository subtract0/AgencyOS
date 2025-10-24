# Test Suite File-Level Recommendations

## DELETE (100% Recommendation)

| File | Lines | Reason | Action |
|------|-------|--------|--------|
| `tests/test_example.py` | 100 | Placeholder (only comments, no tests) | DELETE |
| `tests/test_agency_code_agent_fixed.py` | ~500 | "Fixed" version (fix merged to main, old test remains) | DELETE |
| `tests/test_chief_architect_agent_simple.py` | 189 | Redundant with comprehensive version (1,732 lines) | DELETE |

**Total Savings**: 789 lines  
**Test Loss**: 0 (duplicates)  
**Effort**: 5 minutes  
**Risk**: None

---

## CONSOLIDATE INTO ONE FILE (High Priority)

### Group 1: retry_controller (3 files, 1,483 lines)

**Current State**:
- `tests/test_retry_controller.py` (517 lines) - Root level
- `tests/unit/shared/test_retry_controller.py` (524 lines) - Unit tests
- `tests/tools/ci_monitor/test_retry_controller.py` (442 lines) - Tool-specific

**Consolidation Plan**:
1. Keep `tests/unit/shared/test_retry_controller.py` as canonical unit test
2. Keep tool-specific tests in `tests/tools/ci_monitor/test_retry_controller.py`
3. Delete `tests/test_retry_controller.py` (redundant root version)
4. Merge any unique tests from root into unit/ or tool-specific

**Expected Savings**: ~400-500 lines  
**Test Loss**: 0  
**Effort**: 30 minutes  
**Complexity**: Medium

---

### Group 2: ollama_health_check (2 files, 859 lines)

**Current State**:
- `tests/test_ollama_health_check.py` (300 lines) - Basic version
- `tests/test_ollama_health_check_comprehensive.py` (559 lines) - Comprehensive version

**Consolidation Plan**:
1. Keep `tests/test_ollama_health_check_comprehensive.py` (better name/coverage)
2. Delete `tests/test_ollama_health_check.py` (basic version is redundant)
3. Verify comprehensive version covers all basic test cases
4. Update imports if referenced elsewhere

**Expected Savings**: ~300 lines  
**Test Loss**: 0  
**Effort**: 15 minutes  
**Complexity**: Low

---

### Group 3: timeout_wrapper (2 files)

**Current State**:
- `tests/test_timeout_wrapper.py` - Root level
- `tests/unit/shared/test_timeout_wrapper.py` (524 lines) - Unit tests

**Consolidation Plan**:
1. Keep `tests/unit/shared/test_timeout_wrapper.py` (proper location)
2. Delete `tests/test_timeout_wrapper.py` (root version is in wrong directory)
3. Verify unit version has all coverage

**Expected Savings**: ~150-200 lines  
**Test Loss**: 0  
**Effort**: 10 minutes  
**Complexity**: Low

---

### Group 4: chief_architect_agent (3 files, 2,196 lines)

**Current State**:
- `tests/test_chief_architect_agent.py` (1,732 lines) - Comprehensive
- `tests/test_chief_architect_agent_simple.py` (189 lines) - Simplified
- `tests/unit/test_chief_architect_agent.py` (275 lines) - Unit version

**Consolidation Plan**:
1. Keep `tests/test_chief_architect_agent.py` (comprehensive, high value)
2. Delete `tests/test_chief_architect_agent_simple.py` (redundant simple version)
3. Delete `tests/unit/test_chief_architect_agent.py` (unit version redundant)
4. Note: These are HIGH VALUE tests - only consolidate if duplication confirmed

**Expected Savings**: ~450 lines  
**Test Loss**: 0  
**Effort**: 30 minutes (verify coverage first)  
**Complexity**: Medium

---

### Group 5: session_checkpoint (2 files)

**Current State**:
- `tests/test_session_checkpoint.py`
- `tests/test_session_checkpoint_new.py`

**Consolidation Plan**:
1. FIRST: Review both files to understand "_new" suffix
2. If "_new" is complete replacement: Delete old version, rename "_new" to canonical
3. If "_new" has additional tests: Merge into one file
4. Unclear status - need manual verification

**Expected Savings**: ~300+ lines (if consolidated)  
**Test Loss**: 0  
**Effort**: 20 minutes (review first)  
**Complexity**: Medium

---

### Group 6: spec_generator (2 files)

**Current State**:
- `tests/test_spec_generator.py` - Root level
- `tests/orchestrator/test_spec_generator.py` - Orchestrator tests

**Consolidation Plan**:
1. Verify if testing different layers (unit vs integration)
2. If same scope: Consolidate into one file
3. If different scope: Keep separate but clarify documentation
4. Unclear scope - need manual verification

**Expected Savings**: 200-500 lines (if consolidated)  
**Test Loss**: 0  
**Effort**: 20 minutes (review first)  
**Complexity**: Medium

---

### Group 7: git_validation (2 files)

**Current State**:
- `tests/test_git_validation.py` - Root level
- `tests/foundation_automation/test_git_validation.py` - Automation tests

**Consolidation Plan**:
1. Verify if testing different contexts (core vs automation)
2. If same scope: Consolidate
3. If different scope: Keep separate with clear documentation
4. Unclear relationship - need manual verification

**Expected Savings**: 200-500 lines (if consolidated)  
**Test Loss**: 0  
**Effort**: 20 minutes (review first)  
**Complexity**: Medium

---

### Group 8: agent_registry (2 files)

**Current State**:
- `tests/test_agent_registry.py` - Root level
- `tests/trinity_protocol/core/test_agent_registry.py` - Trinity protocol

**Consolidation Plan**:
1. Verify if testing same or different agent registry implementations
2. If same: Consolidate into trinity_protocol directory
3. If different: Keep separate with clear documentation
4. Unclear scope - need manual verification

**Expected Savings**: 150-300 lines (if consolidated)  
**Test Loss**: 0  
**Effort**: 15 minutes (review first)  
**Complexity**: Low

---

## REMOVE DUPLICATE FIXTURES (Fixture Deduplication)

### Location: `/tests/conftest.py` vs `/tests/unit/conftest.py` vs `/tests/fixtures/conftest.py`

#### mock_agent_context (DEFINED 3 TIMES - CRITICAL)

**Location 1**: `tests/conftest.py` (line 233)
```python
@pytest.fixture
def mock_agent_context():
    import uuid
    from datetime import datetime
    context = Mock()
    # ... implementation
```

**Location 2**: `tests/unit/conftest.py` (line 19) - REMOVE
```python
@pytest.fixture
def mock_agent_context():
    context = Mock()
    # ... implementation
```

**Location 3**: `tests/fixtures/conftest.py` (line 37) - DEPRECATED
```python
@pytest.fixture
def mock_agent_context():
    # ... implementation
```

**Action**: 
1. Keep Location 1 (`tests/conftest.py`) - global version
2. DELETE Location 2 (`tests/unit/conftest.py`)
3. DELETE Location 3 (`tests/fixtures/conftest.py`) - marked deprecated

**Expected Savings**: 30-50 lines  
**Improvement**: Eliminates test pollution from fixture shadowing  
**Effort**: 10 minutes  
**Risk**: Low (verify no overrides needed)

---

### Other Duplicate Fixtures

| Fixture | Locations | Action | Savings |
|---------|-----------|--------|---------|
| `mock_openai_client` | conftest.py, fixtures/conftest.py | Keep one, remove duplicate | 20 lines |
| `temp_file` | conftest.py, fixtures/conftest.py | Use pytest's `tmp_path` | 30 lines |
| `temp_workspace` | conftest.py, fixtures/conftest.py | Use pytest's `tmp_path` | 25 lines |
| `mock_environment_vars` / `isolated_test_env` | conftest.py (2 versions) | Merge into single fixture | 30 lines |

**Total Fixture Savings**: ~130-155 lines  
**Total Effort**: 45 minutes  
**Risk**: Low

---

## REORGANIZE ROOT-LEVEL TESTS (Major Refactoring)

### Critical Issue

**Problem**: 220 test files in `tests/` root directory without clear classification:
- Mixed unit and integration tests
- Conftest applies markers retroactively (not ideal)
- Makes understanding test scope difficult
- Hinders CI pipeline filtering (can't easily run only unit tests)

### Solution

**Reorganize into proper directory structure**:

```
tests/
├── unit/              (Fast, isolated tests)
│   ├── test_*.py      (Move ~80-100 unit tests here)
│   └── shared/
│       └── test_*.py
├── integration/       (Component interaction tests)
│   ├── test_*.py      (Move ~50-80 integration tests here)
│   └── ci_monitor/
│       └── test_*.py
├── e2e/              (End-to-end tests)
│   └── test_*.py     (Currently only 1 file - needs expansion)
├── orchestrator/     (Keep as-is - well-structured)
├── foundation_automation/ (Keep as-is - well-structured)
└── necessary/        (Keep as-is - well-structured)
```

### Migration Process

1. **Phase 1**: Identify root tests that should be in unit/integration
   - Use conftest markers to guide categorization
   - Example: Tests with `pytest.mark.unit` → move to `tests/unit/`
   - Example: Tests with `pytest.mark.integration` → move to `tests/integration/`

2. **Phase 2**: Move files with minimal changes
   - Update import paths if needed (rare - paths relative to project root)
   - Verify conftest fixtures are accessible

3. **Phase 3**: Verify CI filtering works
   - Test: `pytest tests/unit/ -v` (should run only unit tests)
   - Test: `pytest tests/integration/ -v` (should run only integration tests)
   - Test: `pytest tests/e2e/ -v` (should run only E2E tests)

### Expected Impact

- **Savings**: 0 lines (reorganization only)
- **Clarity**: Massive improvement in test structure
- **CI Efficiency**: Can now efficiently skip categories
- **Maintainability**: Clear boundaries improve debugging
- **Effort**: 4-8 hours (large refactoring)

---

## EXPAND E2E TEST SUITE (Severely Underdeveloped)

### Current State

- Only 1 E2E test file: `tests/e2e/test_e2e_router_agency_integration.py`
- File size: 29 lines (barely a test)
- Coverage: Minimal (3-4 assertions on mocked data)

### Recommendation

**Build comprehensive E2E test suite** (~7K lines to match integration tests):

1. End-to-end workflow tests:
   - Full task execution pipeline
   - Multi-agent coordination
   - Learning loop integration
   - PR creation workflow

2. Real system integration:
   - Against actual Ollama (if available)
   - Full memory store operations
   - Git workflow validation

3. Failure scenarios:
   - Network interruptions
   - Resource exhaustion
   - Concurrent operations

### Estimated Effort

- 2-4 days of test development
- Should result in ~7,000 lines of E2E tests
- Worth the investment for coverage validation

---

## SPLIT VERY LARGE TEST FILES (If Maintainability Suffers)

### Files to Consider Splitting (Only if debugging becomes hard)

| File | Lines | Suggested Split |
|------|-------|-----------------|
| `test_chief_architect_agent.py` | 1,732 | agent_basic, agent_adrs, agent_validation |
| `test_pattern_extraction.py` | 1,443 | happy_path, edge_cases, ml_features |
| `test_model_trainer.py` | 1,387 | basic, retraining, validation |

### Rationale for Keeping Large Files

- **Pro**: Easy to understand complete test scope in one place
- **Pro**: All tests currently passing - splitting risks introducing bugs
- **Con**: Harder to navigate 1,700 line files
- **Decision**: Only split if:
  - Debugging becomes difficult
  - Related tests frequently need independent modification
  - Test count exceeds 50 tests per file

### If You Do Split

**Example**: `test_chief_architect_agent.py` → 3 files

1. `test_chief_architect_agent_basic.py` - Core functionality
2. `test_chief_architect_agent_adrs.py` - ADR generation
3. `test_chief_architect_agent_validation.py` - Input validation

Ensure common setup is shared (use conftest fixtures, don't duplicate)

---

## Summary of Actions by Priority

### Priority 1 - Delete (15 min, 789 lines saved)
- [ ] Delete `test_example.py`
- [ ] Delete `test_agency_code_agent_fixed.py`
- [ ] Delete `test_chief_architect_agent_simple.py`

### Priority 2 - Remove Duplicate Fixtures (45 min, 150 lines saved)
- [ ] Remove `mock_agent_context` from `tests/unit/conftest.py`
- [ ] Remove `mock_agent_context` from `tests/fixtures/conftest.py`
- [ ] Consolidate other duplicate fixtures

### Priority 3 - Consolidate Test Pairs (2 hours, 1,200+ lines saved)
- [ ] Consolidate `retry_controller` (3 files → 2)
- [ ] Consolidate `ollama_health_check` (2 files → 1)
- [ ] Consolidate `timeout_wrapper` (2 files → 1)
- [ ] Clarify `session_checkpoint` (2 files → 1)
- [ ] Review `spec_generator`, `git_validation`, `agent_registry` pairs

### Priority 4 - Reorganize Root Tests (4-8 hours, massive clarity improvement)
- [ ] Move unit tests from `tests/` root to `tests/unit/`
- [ ] Move integration tests from `tests/` root to `tests/integration/`
- [ ] Verify CI filtering works correctly

### Priority 5 - Expand E2E Tests (2-4 days, ~7K new lines)
- [ ] Build comprehensive E2E test suite
- [ ] Test full workflows with real systems
- [ ] Add failure scenario coverage

---

## Files to ABSOLUTELY PROTECT

Do NOT consolidate or delete these high-value test files:

```
tests/orchestrator/test_pr_creator.py (1,502 lines)
tests/orchestrator/test_necessary_validator.py (1,402 lines)
tests/orchestrator/test_spec_generator.py (1,288 lines)
tests/integration/test_autonomous_audit_loop.py (benchmark)
tests/tools/ci_monitor/test_fix_generator.py (1,556 lines)
tests/tools/ci_monitor/test_feedback_loop_orchestrator.py (1,103 lines)
tests/necessary/ (4 files, 2K lines total)
```

These tests validate constitutional compliance and core system behavior.

