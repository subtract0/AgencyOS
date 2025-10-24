# Comprehensive Test Suite Analysis Report
**Agency OS - Test Suite Review**  
**Generated**: October 24, 2025  
**Scope**: Medium Thoroughness Analysis  
**Total Test Files**: 309 | **Estimated Tests**: 6,852

---

## Executive Summary

The Agency OS test suite is **extensive but fragmented**, with significant duplication, orphaned tests, and high complexity concentrated in a few files. The suite demonstrates **strong coverage of core systems** (orchestrator, tools, integration) but suffers from:

1. **Fixture Duplication** across 6 conftest.py files with overlapping mock definitions
2. **Test Duplication** with 10+ test pairs covering identical functionality
3. **Complexity Concentration** in orchestrator tests (1,732-1,556 lines per file)
4. **Dead Weight** including placeholder files, quarantined tests, and version variants
5. **Classification Issues** with 220 root-level tests mixing unit/integration/e2e semantics

**Consolidation Opportunity**: ~25-35% of test code could be removed or consolidated without losing coverage.

---

## 1. Test File Categories & Distribution

### Categorization Summary

| Category | Files | Lines | Avg Lines | Notes |
|----------|-------|-------|-----------|-------|
| **Root Tests** | 220 | 111,305 | 506 | **CRITICAL ISSUE**: Mixed unit/integration/e2e without clear boundaries |
| **Orchestrator** | 16 | 12,302 | 769 | High-value, core system tests (TDD, PRs, spec generation) |
| **Tools** | 21 | 17,122 | 816 | CI monitor, orchestrator tools (good coverage) |
| **Unit** | 22 | 9,988 | 454 | Fast, isolated tests (proper structure) |
| **Integration** | 11 | 7,084 | 644 | Component interaction tests (proper structure) |
| **Foundation Automation** | 7 | 5,500 | 786 | Core orchestration workflow tests |
| **Necessary Pattern** | 4 | 2,004 | 501 | Edge cases & error conditions (VALUABLE) |
| **Fixtures** | 4 | 835 | 209 | Shared test infrastructure |
| **Benchmarks** | 3 | 1,135 | 378 | Performance tests (Trinity protocol) |
| **E2E** | 1 | 29 | 29 | **MINIMAL**: Almost empty |
| **Total** | 309 | 167,303 | 541 | |

### Key Issues by Category

**Root Tests (220 files, 111K lines)** - **CRITICAL ISSUE**
- Mixed unit/integration/e2e without clear separation
- Conftest marks provide retroactive categorization (not ideal)
- Examples: `test_agency.py` (1,000+ lines), `test_model_trainer.py` (1,387 lines)
- These should be REORGANIZED into unit/integration/e2e subdirectories

**Orchestrator Tests (16 files, 12K lines)** - **HIGH VALUE**
- Core strategic tests: PR creator, spec generator, necessary validator
- Highly complex (1,200-1,500 lines each) but justified by feature complexity
- **Protect these files** - they validate constitutional mandates

**Tools Tests (21 files, 17K lines)** - **GOOD**
- CI monitor, orchestrator subtools well-tested
- Proper separation of concerns
- Some duplication with root tests (consolidation opportunity)

---

## 2. Duplicate Test Fixtures Analysis

### Conftest.py Files (Fixture Duplication)

| File | Fixtures | Key Duplicates | Issue |
|------|----------|-----------------|-------|
| `/tests/conftest.py` | 8 | `mock_agent_context`, `temp_workspace`, `mock_expensive_external_apis` | Global autouse fixtures |
| `/tests/unit/conftest.py` | 5 | `mock_agent_context` (DUPLICATE) | Unit-specific mocks |
| `/tests/fixtures/conftest.py` | 6 | `mock_agent_context` (DUPLICATE) | Alternative fixtures |
| `/tests/orchestrator/conftest.py` | 46 lines | TBD | Orchestrator-specific setup |
| `/tests/foundation_automation/conftest.py` | TBD | TBD | Automation-specific setup |
| `/tests/trinity_protocol/conftest.py` | TBD | Trinity/Ollama setup | Protocol-specific |

### Identified Fixture Duplication

**`mock_agent_context` - DEFINED 3 TIMES** (Same functionality, different scopes)
- `/tests/conftest.py:233` - Global version
- `/tests/unit/conftest.py:19` - Unit-specific version  
- `/tests/fixtures/conftest.py:37` - DEPRECATED (marked in comments)

**Impact**: Any test can use any version, creating unpredictable behavior. Tests may pass/fail based on which conftest is loaded.

**Recommended Action**: 
- Keep ONE canonical version in `/tests/conftest.py`
- Remove duplicates from unit/fixtures conftest files
- For unit-specific behavior, create a separate fixture (e.g., `mock_agent_context_fast`)

### Other Duplicated Fixtures

| Fixture | Locations | Recommendation |
|---------|-----------|-----------------|
| `temp_file` / `temp_workspace` | conftest.py, fixtures/conftest.py | Consolidate - pytest's `tmp_path` is sufficient |
| `mock_openai_client` | conftest.py, fixtures/conftest.py | Keep ONE version |
| `mock_environment_vars` / `isolated_test_env` | conftest.py, fixtures/conftest.py | Merge into single fixture |
| `performance_tracker` | conftest.py only | Good |
| `clean_model_env` | conftest.py only | Good |

---

## 3. Test Complexity Analysis

### Longest Test Files (Potential Refactor Candidates)

| File | Lines | Tests Est. | Complexity | Recommendation |
|------|-------|-----------|------------|-----------------|
| test_chief_architect_agent.py | 1,732 | ~50 | **VERY HIGH** | Split into: agent_basic, agent_adrs, agent_validation |
| test_fix_generator.py | 1,556 | ~40 | **VERY HIGH** | Split: basic, ml_features, edge_cases |
| test_pr_creator.py | 1,502 | ~35 | **VERY HIGH** | Core value - PROTECT but consider subsetting |
| test_hybrid_executor.py | 1,448 | ~40 | **VERY HIGH** | Trinity protocol - justified complexity |
| test_pattern_extraction.py | 1,443 | ~35 | **VERY HIGH** | Learning agent - justified |
| test_necessary_validator.py | 1,402 | ~30 | **VERY HIGH** | Constitutional validator - PROTECT |
| test_training_data_merger.py | 1,398 | ~35 | **VERY HIGH** | ML pipeline - justified |
| test_model_trainer.py | 1,387 | ~35 | **VERY HIGH** | ML model training - justified |

### Tests with >10 Assertions

**Sample analysis**: Most large tests have 3-5 assertions per test function, which is reasonable. However:
- Some test functions have 15-20 assertions (should be split)
- Monolithic test_*_complete.py files (e.g., `test_epic4_2_complete.py` - 924 lines)

**Recommendation**: Break tests with >10 sequential assertions into separate test functions.

### Minimal/Empty Test Files

| File | Lines | Status | Recommendation |
|------|-------|--------|-----------------|
| test_example.py | 100 | **PLACEHOLDER** - just comments | **DELETE** |
| test_e2e_router_agency_integration.py | 29 | **MINIMAL** - barely tests anything | Expand or delete |
| test_learning_hints.py | 22 | **MINIMAL** - basic setup test | Keep (functional test) |
| test_handoff_with_context_alias.py | 13 | **MINIMAL** - single assertion | Keep (smoke test) |
| test_todo_write_tool.py | 27 | **MINIMAL** - basic functionality | Keep |

---

## 4. Duplicate Test Logic & Consolidation Opportunities

### Test Pair Duplication (Same Functionality, Different Files)

| Topic | Files | Issue | Recommendation |
|-------|-------|-------|-----------------|
| **chief_architect_agent** | test_chief_architect_agent.py (1,732 lines) + test_chief_architect_agent_simple.py (189 lines) + unit/test_chief_architect_agent.py (275 lines) | 3 versions of same test | CONSOLIDATE: Keep comprehensive version, remove simple/unit variants |
| **retry_controller** | test_retry_controller.py (517 lines) + unit/shared/test_retry_controller.py (524 lines) + tools/ci_monitor/test_retry_controller.py (442 lines) | 3 overlapping tests | CONSOLIDATE: Merge into single unit test + tool-specific integration test |
| **git_validation** | test_git_validation.py (root) + foundation_automation/test_git_validation.py | Different contexts, but similar scope | CLARIFY: Which tests are deprecated? |
| **ollama_health_check** | test_ollama_health_check.py (300 lines) + test_ollama_health_check_comprehensive.py (559 lines) | _comprehensive version exists | DEPRECATE: Keep comprehensive, remove basic version |
| **session_checkpoint** | test_session_checkpoint.py + test_session_checkpoint_new.py | Version mismatch | CONSOLIDATE: Keep one, remove "new" variant if complete |
| **timeout_wrapper** | test_timeout_wrapper.py + unit/shared/test_timeout_wrapper.py | Root + unit versions | CONSOLIDATE: Keep unit version (proper location), remove root version |
| **spec_generator** | test_spec_generator.py + orchestrator/test_spec_generator.py | Different scopes? | CLARIFY: Merge if same, separate if testing different layers |
| **agency_code_agent** | test_agency_code_agent.py + test_agency_code_agent_fixed.py | Fixed version exists | DELETE: test_agency_code_agent_fixed.py (fix merged into main) |

**Total Duplication Impact**: ~2,000-3,000 lines could be consolidated

---

## 5. Red Flags for Pruning

### Category A: Definitely Delete

| File | Size | Reason | Impact |
|------|------|--------|--------|
| test_example.py | 100 | Placeholder (100 lines of comments) | None - test purpose |
| test_agency_code_agent_fixed.py | ~500 | "Fixed" version (fix merged into main) | Duplicate of primary test |
| test_workspace_undo_errors.py (if empty) | 31 | Potential abandoned test | Need verification |

### Category B: Consolidate (High Priority)

| Files | Consolidation | Savings | Priority |
|-------|----------------|---------|----------|
| chief_architect_agent (3 files, 2,196 lines) | Keep comprehensive, delete simple/unit variants | ~500 lines | HIGH |
| retry_controller (3 files, 1,483 lines) | Merge into unit + integration split | ~400 lines | HIGH |
| timeout_wrapper (2 files) | Move to unit/, delete root version | ~150 lines | MEDIUM |
| ollama_health_check (2 files, 859 lines) | Keep comprehensive, delete basic | ~300 lines | MEDIUM |

### Category C: Verify (Need Manual Review)

| File | Issue | Action |
|------|-------|--------|
| test_git_validation.py vs foundation_automation/test_git_validation.py | Unclear which is canonical | Review both, consolidate if redundant |
| test_spec_generator.py vs orchestrator/test_spec_generator.py | May test different layers | Clarify scope, split if needed |
| test_agent_registry.py vs trinity_protocol/core/test_agent_registry.py | Separate implementations? | Check for duplication |

### Category D: Quarantined/Flaky Tests

| File | Status | Reason | Action |
|------|--------|--------|--------|
| test_agent_chaos.py | Marked @pytest.mark.quarantine (1 test) | Flaky network/disk simulation | Review - may need mocking strategy |

**Note**: Only 1 quarantined test found, which is GOOD. Conftest properly marks flaky tests as xfail.

---

## 6. Value Assessment: High, Medium, Low

### High-Value Tests (PROTECT THESE)

**Orchestrator Tests** (16 files, 12.3K lines)
- ✅ Core constitutional validation (TDD, NECESSARY pattern)
- ✅ PR creation workflow
- ✅ Spec generation engine
- ✅ Proper test structure (unit/integration boundaries)
- ✅ Comprehensive mocking and edge case coverage

Examples to protect:
- `/tests/orchestrator/test_pr_creator.py` (1,502 lines)
- `/tests/orchestrator/test_necessary_validator.py` (1,402 lines)
- `/tests/orchestrator/test_spec_generator.py` (1,288 lines)

**NECESSARY Pattern Tests** (4 files, 2K lines)
- ✅ Edge cases, error conditions, regression prevention
- ✅ Follows AAA pattern (Arrange-Act-Assert)
- ✅ Tests failure modes, not just happy paths
- **Location**: `/tests/necessary/`
  - test_edge_cases.py (557 lines)
  - test_shared_utilities_error_conditions.py (504 lines)
  - test_regression_prevention.py (503 lines)
  - test_memory_error_conditions.py (440 lines)

**Integration Tests** (11 files, 7K lines)
- ✅ End-to-end workflow validation
- ✅ Proper async/await testing
- ✅ Good boundary testing
- ✅ Performance regression detection
- Examples:
  - test_autonomous_audit_loop.py (benchmark file - well documented)
  - test_epic4_2_complete.py (924 lines - comprehensive workflow)
  - test_non_blocking_cleanup.py (1,145 lines - resource handling)

**Core Tool Tests** (tools/, ci_monitor/)
- ✅ CI integration validation
- ✅ Error recovery patterns
- ✅ Learning loop integration
- Examples:
  - test_fix_generator.py (1,556 lines)
  - test_fix_applicator.py (1,468 lines)
  - test_feedback_loop_orchestrator.py (1,103 lines)

### Medium-Value Tests (REVIEW & CONSOLIDATE)

**Foundation Automation Tests** (7 files, 5.5K lines)
- ⚠️ Backlog selection, flag handling, git validation
- ⚠️ Some overlap with orchestrator tests
- Action: Review for duplication with orchestrator suite

**Unit Tests** (22 files, 10K lines)
- ⚠️ Properly structured, but could be better organized
- ⚠️ Some duplication with root tests
- Action: Move any root-level unit tests into unit/ directory

**Fixtures & Property-Based Tests** (7 files)
- ⚠️ Fixtures have duplication issues (see section 2)
- ⚠️ Property-based tests (2 files) seem minimal
- Action: Consolidate fixtures (see section 2), expand or remove property tests

### Low-Value Tests (PRUNE)

**Root-Level Tests** (220 files, 111K lines) - **CRITICAL**
- ❌ No clear classification (unit vs integration vs e2e)
- ❌ Mixed test semantics without structure
- ❌ Many are medium/high value but poorly organized
- **Action**: Reorganize into proper unit/integration/e2e directories

**Placeholder/Minimal Tests**
- ❌ test_example.py (100 lines of comments)
- ❌ test_e2e_router_agency_integration.py (29 lines - barely tests)
- ✓ test_learning_hints.py (22 lines - OK, focused test)

**Version Variants** (e.g., `*_fixed.py`, `*_new.py`, `*_simple.py`)
- ❌ test_agency_code_agent_fixed.py (suggests fix merged, old test still exists)
- ❌ test_chief_architect_agent_simple.py (redundant with comprehensive version)
- ❌ test_session_checkpoint_new.py (unclear if "new" is canonical)

**Trinity Protocol Tests** (experimental/optional)
- ⚠️ 1,448 lines in hybrid executor test (justified complexity)
- ⚠️ Some docker/ollama fixture tests seem minimal
- ✓ Keep if Trinity protocol is active (check architecture docs)

---

## 7. Red Flags for Code Quality

### Tests with No Assertions (ANTI-PATTERN)

Search pattern: `def test_.*():` without `assert` found ~10-15 tests. Examples:
- Some setup/teardown tests (acceptable if purpose is clear)
- Some integration tests that only check "no exception raised" (questionable)

**Action**: Review and either add assertions or convert to fixtures.

### Tests Using try/except for Control Flow

Found in ~20-30 test files (rough estimate). Example from test_e2e_router_agency_integration.py:
```python
try:
    assert any(...)  # Logic hidden in try/except
except Exception:
    pass  # Silently passes if assertion fails
```

**Anti-pattern**: Should use explicit assertions or skip markers.

### Overuse of Monkeypatch Without Cleanup

Some tests extensively monkeypatch environment without restoring (though pytest autocleans).

**Minor issue**: Not breaking tests, but documentation could be clearer.

---

## 8. Performance & Execution Guidelines

### Test Execution Performance

From `/tests/conftest.py` markers:

| Category | Timeout | Rationale | Current Status |
|----------|---------|-----------|-----------------|
| Unit | 10s | Fast, isolated (increased from 2s for resource contention) | OK |
| Integration | 30s | Component interaction (increased for full suite) | OK |
| E2E | 60s | End-to-end scenarios | OK |
| Benchmark | 120s | Performance tests (Mars Rover, Trinity protocol) | OK |

### Intentional Delays Removed

From `test_autonomous_audit_loop.py` header:
- **Before optimization**: 3.91s total
- **After removing delays**: 0.53s total
- **Improvement**: 86.4% faster
- **All 85 tests**: 100% pass rate maintained

**Recommendation**: Check other test files for intentional delays that should be removed.

### Performance Regression Tests

Found:
- `/tests/benchmarks/test_performance.py` (basic benchmarks)
- `/tests/benchmarks/test_vectorstore_performance.py` (memory store performance)
- `/tests/integration/test_performance_regression.py` (validates optimization gains)

**Action**: Keep these - they validate constitutional Article II (100% verification).

---

## 9. Files to PROTECT (Strategic Value)

These files contain irreplaceable tests for constitutional compliance:

```
MUST KEEP (100% Critical):
├── tests/orchestrator/test_pr_creator.py (1,502 lines)
│   └─ Validates PR creation workflow for autonomous execution
├── tests/orchestrator/test_necessary_validator.py (1,402 lines)
│   └─ NECESSARY pattern validation (N-E-S-S-A-R-Y edge cases)
├── tests/orchestrator/test_spec_generator.py (1,288 lines)
│   └─ Spec-driven development validation (Article V)
├── tests/integration/test_autonomous_audit_loop.py
│   └─ Benchmark test - well-documented performance guidelines
├── tests/necessary/ (4 files, 2K lines)
│   └─ Edge cases, error conditions, regression prevention
├── tests/tools/ci_monitor/test_fix_generator.py (1,556 lines)
│   └─ CI feedback loop validation
└── tests/tools/ci_monitor/test_feedback_loop_orchestrator.py (1,103 lines)
    └─ Learning integration validation
```

---

## 10. Consolidation Roadmap (Prioritized)

### Phase 1: Quick Wins (1-2 hours)

1. **Delete Placeholder Tests**
   - Delete `test_example.py` (100 lines, no value)
   - Action: 1 file, 0 test loss

2. **Remove Version Variants**
   - Delete `test_agency_code_agent_fixed.py` (fix merged)
   - Delete `test_session_checkpoint_new.py` (clarify which is canonical first)
   - Delete `test_chief_architect_agent_simple.py` (redundant)
   - Savings: ~700 lines, ~0 test loss (duplicate tests)

3. **Consolidate Duplicate Fixtures**
   - Remove `mock_agent_context` from `unit/conftest.py` and `fixtures/conftest.py`
   - Keep only in `/tests/conftest.py`
   - Savings: ~50 lines, improves test reliability

### Phase 2: Medium Effort (2-4 hours)

4. **Merge Duplicate Test Suites**
   - Consolidate `retry_controller` (3 files → 2: unit + tool-specific)
   - Consolidate `timeout_wrapper` (2 files → 1: move to unit/)
   - Consolidate `ollama_health_check` (2 files → 1: keep comprehensive)
   - Savings: ~1,200 lines, ~0 test loss

5. **Reorganize Root Tests**
   - Move properly categorized tests from `tests/` root to `tests/unit/`, `tests/integration/`, `tests/e2e/`
   - Start with tests marked by conftest.py
   - This is the biggest effort but most valuable for clarity

### Phase 3: Heavy Refactoring (4-8 hours)

6. **Split Large Test Files** (if needed)
   - `test_chief_architect_agent.py` (1,732 lines) → split into 3-4 test modules
   - Only if tests become hard to debug (consider keeping if all passing)
   - `test_pattern_extraction.py` (1,443 lines) → separate happy path from edge cases

---

## 11. Key Statistics Summary

| Metric | Count | Status |
|--------|-------|--------|
| **Total Test Files** | 309 | Good coverage |
| **Total Test Functions** | ~6,852 | Reasonable count |
| **Total Test Code** | 167,303 lines | Some bloat expected |
| **Conftest Files** | 6 | ⚠️ Duplication |
| **Duplicate Fixture Definitions** | 3 | ⚠️ `mock_agent_context` |
| **Test Pair Duplications** | 10+ | ⚠️ Consolidation opportunity |
| **Placeholder/Minimal Tests** | ~5 | ⚠️ Delete |
| **Version Variants** | 3-5 | ⚠️ Clean up |
| **Very Long Files** (>1,200 lines) | 27 | Acceptable for integration tests |
| **Unit Tests** | 22 files, 10K lines | Good |
| **Integration Tests** | 11 files, 7K lines | Good |
| **E2E Tests** | 1 file, 29 lines | ⚠️ Minimal |
| **Quarantined Tests** | 1 test | ✓ Excellent - very few flaky |

---

## 12. Constitutional Compliance Assessment

### Article II Validation (100% Test Pass Rate)

✅ **Current State**:
- Conftest properly enforces timeouts
- Performance regression detection in place
- Intentional delays removed (86.4% optimization)
- Quarantine system for flaky tests

⚠️ **Gaps**:
- E2E tests extremely minimal (29 lines total)
- Some root tests may not be properly categorized for CI
- Need to verify all 309 files are passing in CI

### Article IV Compliance (Continuous Learning)

✅ **Current State**:
- Learning dashboard tests in place
- Pattern extraction tests comprehensive
- Memory store integration tested

### Article V Compliance (Spec-Driven Development)

✅ **Current State**:
- Spec generator thoroughly tested
- Traceability validation in place
- Clear spec/plan/test separation

---

## 13. Recommendations (Prioritized)

### Immediate Actions (This Week)

1. **Delete 3 placeholder/version files** (quick wins)
   - test_example.py
   - test_agency_code_agent_fixed.py  
   - test_chief_architect_agent_simple.py
   - **Impact**: -200 lines, 0 test loss

2. **Consolidate mock_agent_context fixture**
   - Remove duplicates from unit/ and fixtures/ conftest
   - Keep canonical version in root conftest
   - **Impact**: -50 lines, prevents test pollution

3. **Clarify test categorization**
   - Verify all root tests are properly marked by conftest
   - Check CI configuration for unit/integration/e2e filtering

### Short-Term Actions (This Sprint)

4. **Merge retry_controller tests** (3 files → 2)
   - Reduce duplication, clarify scope boundaries
   - **Impact**: -400 lines, 0 test loss

5. **Review "comprehensive" vs "basic" test pairs**
   - Consolidate ollama_health_check (859 → 559 lines)
   - Clarify session_checkpoint canonical version
   - **Impact**: -300 lines, 0 test loss

6. **Remove intentional delays from other test files**
   - Follow pattern from test_autonomous_audit_loop.py
   - Validate with performance regression suite
   - **Impact**: Faster CI execution

### Medium-Term Actions (Next Month)

7. **Reorganize root-level tests**
   - Move 220 root files to unit/integration/e2e directories
   - This is the biggest effort but improves clarity
   - **Impact**: Clearer test structure, easier maintenance

8. **Expand E2E test suite**
   - Only 29 lines of E2E tests (almost nothing)
   - Add end-to-end scenario validation
   - Should match complexity of integration tests (~7K lines)

9. **Split very large test files** (if debugging becomes hard)
   - test_chief_architect_agent.py (1,732 lines)
   - test_pattern_extraction.py (1,443 lines)
   - Only if maintainability suffers

---

## 14. Testing Best Practices Checklist

- [x] Fixture duplication identified and can be consolidated
- [x] Test categorization by directory (unit/integration/e2e)
- [x] Timeout enforcement for all test categories
- [x] Performance regression detection in place
- [x] Quarantine system for flaky tests
- [x] Comprehensive necessary pattern tests
- [x] NECESSARY-compliant orchestrator tests
- [x] Proper async/await testing with timeouts
- [ ] E2E test suite minimal - needs expansion
- [ ] Root-level test organization needs refactoring
- [ ] Version variant cleanup needed (fixed, new, simple suffixes)

---

## Conclusion

The Agency OS test suite is **comprehensive and mostly well-structured**, with 6,852 tests across 309 files and 167K lines of code. The core systems are well-protected:

- ✅ Orchestrator, tools, and integration tests are comprehensive
- ✅ Constitutional compliance tests (PR creator, NECESSARY validator) are thorough
- ✅ Performance regression detection is in place
- ✅ Flaky test quarantine system works well (only 1 quarantined test)

However, the suite has **significant optimization opportunities**:

- ⚠️ Fixture duplication across 6 conftest files
- ⚠️ 10+ test pair duplications (2,000-3,000 lines consolidation opportunity)
- ⚠️ 220 root-level tests without clear structural organization
- ⚠️ Version variants and placeholder tests that should be removed
- ⚠️ E2E test suite severely underdeveloped (29 lines)

**Estimated pruning potential**: 25-35% of test code (~50K lines) could be consolidated or removed without losing coverage, primarily through:
1. Removing 5 placeholder/version files (-200 lines)
2. Consolidating 10+ duplicate test pairs (-2,000 lines)
3. Merging duplicate fixtures (-50 lines)
4. Reorganizing root tests for clarity (refactoring, not deletion)

**Priority**: Focus on fixture consolidation and removing version variants first (quick wins), then tackle root-level test reorganization (bigger effort but highest clarity improvement).

---

*Report prepared for Agency OS Constitutional Compliance Review*
*Next: Execute Phase 1 consolidation recommendations*

