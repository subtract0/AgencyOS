# Test Baseline Recovery - Phase 0 Failure Tracking

**Mission**: Achieve 6,264/6,264 tests passing (100%)
**Current**: ~5,951/6,264 passing (~95%) - **313 FAILURES**
**Status**: 🔴 CRITICAL - Article II Violation

---

## Recovery Plan (Codex 6-Step)

### Step 1: Full-Suite Run ⏳ IN PROGRESS
- **Command**: `.venv/bin/python run_tests.py --run-all`
- **Output**: `logs/test_run_TIMESTAMP.log`
- **Status**: Running in background (bash_id: bcdf46)

### Step 2: Catalog All Failures ⏸️ PENDING
- Use `pytest --last-failed --durations=20`
- Export to JSON for tracking
- Group by failure type

### Step 3: Triage by Category ⏸️ PENDING
Categories to identify:
- **Config/Skipped**: Missing services (Ollama, Firestore)
- **Import Errors**: Missing dependencies, wrong paths
- **Logic Failures**: Stale fixtures, assertion errors
- **Flaky/Timeouts**: Non-deterministic tests

### Step 4: Fix in Batches ⏸️ PENDING
Priority order:
1. Config/Import issues (unblock many tests at once)
2. Logic regressions (use Regression Guard)
3. Flaky tests (deterministic fixes or quarantine)

### Step 5: Iterate Until Green ⏸️ PENDING
- Fix batch → run affected tests
- Verify no regressions
- Repeat until 100%

### Step 6: Resume Phase 1 ⏸️ PENDING
- Annotate completion in this doc
- Tag: `git tag -f phase0-green`
- Unfreeze Phase 1 tasks

---

## Failure Catalog (Step 2 - In Progress)

### Configuration/Path Errors ✅ BATCH 1 FIXED
**Status**: 20 tests fixed with 1 line change
**File**: `tests/docs/test_claude_md_two_stage.py:187`
**Issue**: Hardcoded path `/Users/am/Code/Agency/CLAUDE.md` (should be `AgencyOS`)
**Fix**: Updated path to `/Users/am/Code/AgencyOS/CLAUDE.md`
**Tests Fixed**:
- 2 FAILED: test_claude_md_file_exists, test_claude_md_is_readable
- 18 ERROR: All tests dependent on claude_md_content fixture

**Impact**: High-impact Config/Import fix - exactly what Codex recommended

### Import Errors
<!-- To be cataloged from remaining failures -->

### Configuration/Skipped Tests
**Known Issues**:
- Ollama not running on localhost:11434 (needs service or skip)
- Firestore tests requiring external service (already ignored in run_tests.py)

### Logic Failures
<!-- To be cataloged from remaining failures -->

### Flaky/Timeout Tests
<!-- To be cataloged from remaining failures -->

---

## Batch Fix Progress

### Batch 1: Config/Path Anti-Pattern Elimination ⏳ IN PROGRESS
- **Status**: ⏳ Significant progress (28+ paths fixed)
- **Root Cause**: Hardcoded absolute paths (/Users/am/Code/Agency/) - anti-pattern
- **Solution**: Dynamic path resolution using Path(__file__) and repo_root fixture
- **Files Fixed**:
  1. ✅ tests/docs/test_claude_md_two_stage.py (20 tests fixed, 1 path evolved)
  2. ✅ tests/tools/ci_monitor/test_constitutional_compliance.py (7 paths evolved)
  3. ✅ tests/test_overnight_orchestrator.py (2 paths evolved to use repo_root fixture)
  4. ✅ tests/conftest.py (added session-scoped repo_root fixture for all tests)
- **Pattern Evolved**: Hardcoded paths → Dynamic resolution (portable, testable, robust)
- **Remaining**: ~20 more paths in integration tests (test_remove_intentional_delays.py, etc.)
- **Time**: ~45 minutes (discovery + pattern evolution + fixes + verification)

### Batch 2: Logic Failures (Priority 2)
- **Status**: Not started
- **Tests Fixed**: 0
- **Tests Remaining**: TBD

### Batch 3: Flaky Tests (Priority 3)
- **Status**: Not started
- **Tests Fixed**: 0
- **Tests Remaining**: TBD

---

## Test Run History

### Run 1: Initial Baseline Discovery
- **Date**: 2025-10-31
- **Result**: ~5,951/6,264 passing (95%)
- **Failures**: ~313 tests
- **Action**: Started recovery mission

### Run 2: Full Suite with Logging (Current)
- **Date**: 2025-10-31
- **Command**: `.venv/bin/python run_tests.py --run-all`
- **Status**: ⏳ Running
- **Log**: `logs/test_run_TIMESTAMP.log`

---

## Coordination Notes (For Both Agents)

### Current State
- **Phase 1**: ❄️ FROZEN - No new reliability work
- **Focus**: 100% test pass rate ONLY
- **Blocking**: All PRs, all commits until green

### Handoff Protocol
- Update this doc after each batch fix
- Run full suite after each update
- Coordinate via this shared document

---

**Last Updated**: 2025-10-31 (Initial creation)
**Next Update**: After Step 1 completes
