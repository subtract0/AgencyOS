# TEST SUITE CLEANUP CHECKLIST
**Generated**: 2025-10-17
**Target Completion**: 7 days
**Expected ROI**: -200 tests, -800 lines, -15s runtime, +18 health score points

---

## IMMEDIATE DELETIONS (Day 1 - 2 hours)

### ✅ Task 1: Delete Duplicate File (5 min)
**File**: `tests/test_chief_architect_agent_simple.py`
**Reason**: Complete duplicate of test_chief_architect_agent.py
**Impact**: -3 tests, -150 lines, -39 mocks

```bash
git rm tests/test_chief_architect_agent_simple.py
git commit -m "refactor: Remove duplicate test_chief_architect_agent_simple.py

- Complete duplicate of test_chief_architect_agent.py
- 3 tests with avg 13 mocks each, no unique value
- ROI: -150 lines, reduce churn

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### ✅ Task 2: Delete "Not Implemented" Skipped Tests (15 min)

#### 2.1: Delete test_agent_loader.py tests (3 min)
```bash
# File: tests/test_agent_loader.py
# Delete: test_parse_frontmatter_with_valid_yaml
# Reason: AgentLoader not implemented, no GitHub issue

# Option A: Delete entire file if only has skipped tests
git rm tests/test_agent_loader.py

# Option B: Remove specific test if file has other tests
# Use Edit tool to remove test function
```

#### 2.2: Delete TDD RED phase tests (5 min)
```bash
# File: tests/test_quality_signal_collector.py
# Delete: test_valid_quality_signals_all_fields_populated
# Reason: TDD RED phase, >7 days old

# File: tests/test_misclassification_detector.py
# Delete: test_detected_issue_valid_creation
# Reason: TDD RED phase, >7 days old

# Action: Either implement within 24 hours or delete
```

#### 2.3: Delete Trinity Protocol incomplete tests (5 min)
```bash
# File: tests/trinity_protocol/test_pattern_detector_ambient.py
# Delete: 2 tests (test_detect_recurring_topic_threshold, test_full_conversation_pattern_flow)
# Reason: Feature not implemented

# File: tests/trinity_protocol/test_parameter_tuning.py
# Delete: 3 tests (all CLI parameter tests)
# Reason: CLI parameters not added to parser

# File: tests/unit/tools/test_mutation_testing.py
# Delete: ENTIRE FILE
# Reason: mutation_testing module not implemented
git rm tests/unit/tools/test_mutation_testing.py
```

**Deletion Summary**:
- test_agent_loader.py (if applicable)
- test_mutation_testing.py (entire file)
- 2 tests from test_pattern_detector_ambient.py
- 3 tests from test_parameter_tuning.py
- 2 tests from test_quality_signal_collector.py, test_misclassification_detector.py

**Total**: ~12 tests deleted

---

### ✅ Task 3: Delete 20 Highest-Mock Tests from test_chief_architect_agent.py (30 min)

**Target Tests** (all have 11-16 mocks, no assertions):

1. test_factory_with_different_contexts (16 mocks)
2. test_factory_returns_fresh_instance (15 mocks)
3. test_agent_creation_with_defaults (14 mocks)
4. test_tools_folder_configuration (14 mocks)
5. test_agent_creation_without_context (14 mocks)
6. test_factory_parameter_combinations (14 mocks)
7. test_tools_folder_path_errors (12 mocks)
8. test_agent_creation_with_custom_parameters (11 mocks)
9. test_agent_tools_configuration (11 mocks)
10. test_agent_memory_integration (11 mocks)
11. test_instructions_file_selection (11 mocks)
12. test_hooks_integration (11 mocks)
13. test_agent_description_strategic_leadership (11 mocks)
14. test_agent_description_triggers (11 mocks)
15. test_agent_description_capabilities (11 mocks)
16. test_agent_description_authority (11 mocks)
17. test_agent_description_usage_guidance (11 mocks)
18. test_agent_description_metadata (11 mocks)
19. test_agent_description_yaml_validity (11 mocks)
20. test_agent_description_triggers_uppercase (11 mocks)

**Execution**:
```bash
# Use Edit tool to remove these 20 test functions
# Search for each function name and delete function body + decorators
# Keep: Integration tests that validate real agent behavior (5-10 tests)

# After deletion, verify tests still pass:
pytest tests/test_chief_architect_agent.py -v
```

**Expected Result**: 34 tests → 14 tests, ~800 lines saved

---

## IMMEDIATE FIXES (Day 2 - 30 min)

### ✅ Task 4: Fix Flaky Meta-Tests (5 min)

**File**: `tests/tools/ci_monitor/test_constitutional_compliance.py`
**Tests**:
- test_article_ii_all_tests_pass
- test_constitutional_compliance_zero_violations

**Problem**: Meta-tests time out in parallel execution

**Solution 1: Mark as Serial** (Recommended)
```python
import pytest

@pytest.mark.serial  # Run sequentially, not in parallel
def test_article_ii_all_tests_pass():
    # ... existing test code ...

@pytest.mark.serial
def test_constitutional_compliance_zero_violations():
    # ... existing test code ...
```

**Solution 2: Increase Timeout**
```python
@pytest.mark.timeout(120)  # Increase from default 60s
def test_article_ii_all_tests_pass():
    # ... existing test code ...
```

**Solution 3: Delete if No Value**
```bash
# If meta-testing adds no real value, delete both tests
# Ask: "Do these tests catch real bugs, or just test the test runner?"
```

---

### ✅ Task 5: Mock time.sleep() in test_chaos_testing.py (15 min)

**File**: `tests/unit/tools/test_chaos_testing.py`
**Problem**: 12 sleeps across 25 tests = ~12s runtime
**Solution**: Mock time.sleep()

```python
# Add to tests/unit/tools/test_chaos_testing.py

import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_sleep(monkeypatch):
    """Mock time.sleep() to eliminate timing dependencies."""
    monkeypatch.setattr("time.sleep", lambda x: None)

# Alternative: Use freezegun for time mocking
from freezegun import freeze_time

@pytest.fixture(autouse=True)
def freeze_time_for_tests():
    """Freeze time to eliminate sleep dependencies."""
    with freeze_time("2025-10-17 12:00:00"):
        yield
```

**Verification**:
```bash
# Before: ~12s runtime
pytest tests/unit/tools/test_chaos_testing.py --durations=0

# After: <1s runtime (12s saved)
pytest tests/unit/tools/test_chaos_testing.py --durations=0
```

---

## VERIFICATION (Day 3 - 10 min)

### ✅ Task 6: Run Full Test Suite
```bash
# Ensure 100% pass rate after deletions
python run_tests.py --run-all

# Expected results:
# - Fewer tests (5,804 → ~5,600)
# - Faster runtime (3.9min → ~3.7min)
# - 100% pass rate maintained
# - Fewer skipped tests (105 → ~90)
```

### ✅ Task 7: Verify Metrics Improvement
```bash
# Re-run bloat analysis
python /tmp/analyze_test_complexity.py > /tmp/test_complexity_after.json

# Compare before/after
python << 'EOF'
import json

with open('/tmp/test_complexity_analysis.json') as f:
    before = json.load(f)
with open('/tmp/test_complexity_after.json') as f:
    after = json.load(f)

print("BEFORE:")
print(f"  Tests: {before['summary']['total_tests']}")
print(f"  Heavy mocks: {before['summary']['heavy_mocks']}")
print(f"  Sleepy tests: {before['summary']['sleepy_tests']}")
print(f"  Skipped: {before['summary']['skipped_tests']}")

print("\nAFTER:")
print(f"  Tests: {after['summary']['total_tests']}")
print(f"  Heavy mocks: {after['summary']['heavy_mocks']}")
print(f"  Sleepy tests: {after['summary']['sleepy_tests']}")
print(f"  Skipped: {after['summary']['skipped_tests']}")

print("\nIMPROVEMENT:")
print(f"  Tests: {after['summary']['total_tests'] - before['summary']['total_tests']}")
print(f"  Heavy mocks: {after['summary']['heavy_mocks'] - before['summary']['heavy_mocks']}")
print(f"  Sleepy tests: {after['summary']['sleepy_tests'] - before['summary']['sleepy_tests']}")
print(f"  Skipped: {after['summary']['skipped_tests'] - before['summary']['skipped_tests']}")
EOF
```

---

## COMMIT & DOCUMENT (Day 3 - 15 min)

### ✅ Task 8: Create Summary Commit
```bash
git add -A
git commit -m "refactor: Test suite bloat cleanup - Phase 1 immediate actions

Deleted:
- test_chief_architect_agent_simple.py (duplicate file, 3 tests, 150 lines)
- 12 'not implemented' skipped tests (technical debt)
- 20 high-mock tests from test_chief_architect_agent.py (testing mocks, not behavior)

Fixed:
- 2 flaky meta-tests with @pytest.mark.serial
- 12 sleeps in test_chaos_testing.py (mocked time.sleep)

Impact:
- Tests: 5,804 → ~5,600 (-200, -3.5%)
- Lines: 154,115 → ~153,300 (-800, -0.5%)
- Runtime: 3.9min → ~3.7min (-12s, -5%)
- Skipped: 105 → ~90 (-15, -14%)
- Heavy mocks: 37 → ~17 (-20, -54%)
- Sleepy tests: 69 → ~57 (-12, -17%)
- Health Score: 72 → ~78 (+6 points)

References:
- Analysis: docs/TEST_SUITE_BLOAT_ANALYSIS.md
- Metrics: docs/test-suite-bloat-metrics.json
- Checklist: docs/TEST_SUITE_CLEANUP_CHECKLIST.md

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### ✅ Task 9: Update Tracking Metrics
```bash
# Update test-suite-bloat-metrics.json with actual results
# Document completion in TEST_SUITE_BLOAT_ANALYSIS.md
# Create GitHub issue for Phase 2 (30-day actions)
```

---

## SUCCESS CRITERIA

- [ ] test_chief_architect_agent_simple.py deleted
- [ ] 12 "not implemented" tests deleted
- [ ] 20 high-mock tests deleted from test_chief_architect_agent.py
- [ ] 2 flaky meta-tests fixed with @pytest.mark.serial
- [ ] time.sleep() mocked in test_chaos_testing.py
- [ ] All tests pass (100% success rate)
- [ ] Runtime reduced by >10s
- [ ] Health score improved by >5 points
- [ ] Changes committed with detailed message
- [ ] Metrics updated in tracking JSON

---

## PHASE 2 PREVIEW (Next 30 Days)

**Not included in immediate checklist, but planned:**

1. REFACTOR test_memory_cache.py - remove sleeps (30 min)
2. REFACTOR test_distributed_locks.py - event-based sync (1 hour)
3. REFACTOR test_firestore_learning_persistence.py - split long test (30 min)
4. PARAMETRIZE test_bash_pydantic_validation.py (1 hour)
5. PARAMETRIZE test_git_validation.py (1 hour)

**Expected Impact**: -100 tests, -40s runtime

---

## NOTES

- **Before starting**: Commit current state for rollback safety
- **After each deletion**: Run affected test file to verify no breakage
- **After all deletions**: Run full suite to ensure 100% pass rate
- **Document learnings**: Update bloat prevention strategy in constitution.md

**Estimated Total Time**: 2.5 hours
**Expected ROI**: -200 tests, -800 lines, -15s runtime, +6 health score points

---

**Generated**: 2025-10-17
**Owner**: QualityEnforcerAgent
**Status**: READY FOR EXECUTION
