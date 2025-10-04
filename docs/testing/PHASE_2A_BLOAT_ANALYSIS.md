# Test Suite Bloat Analysis - Phase 2A

**Generated**: 2025-10-03 22:07:48

## Executive Summary

- **Total tests analyzed**: 2,965 (across 153 test files)
- **Bloat identified**: 731 tests (24.7%)
- **Estimated removal**: 731 tests
- **Remaining tests**: 2,234 tests (Mars-ready)
- **Runtime improvement**: ~296s → ~223s (1.33x faster)
- **Lines of test code**: 72,209 lines total (22,847 bloat lines to remove)
- **Test files**: 153 → 118 files (-23% file count)

## Bloat Categories

### 1. Experimental Features (DELETE)

**Impact**: 35 files, 731 tests

- `tests/test_bash_tool_infrastructure.py` (79 tests, 946 lines) - Experimental/Trinity/DSPy/Archived
- `tests/dspy_agents/test_auditor_agent.py` (70 tests, 1139 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_pattern_detector.py` (59 tests, 955 lines) - Experimental/Trinity/DSPy/Archived
- `tests/dspy_agents/test_planner_agent.py` (49 tests, 942 lines) - Experimental/Trinity/DSPy/Archived
- `tests/dspy_agents/test_code_agent.py` (48 tests, 1297 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_project_models.py` (46 tests, 1220 lines) - Experimental/Trinity/DSPy/Archived
- `tests/dspy_agents/test_toolsmith_agent.py` (41 tests, 983 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_executor_agent.py` (38 tests, 1098 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_witness_agent.py` (38 tests, 1421 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_architect_agent.py` (35 tests, 999 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_preference_learning.py` (28 tests, 701 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_conversation_context.py` (24 tests, 386 lines) - Experimental/Trinity/DSPy/Archived
- `tests/test_learning_loop_integration.py` (23 tests, 704 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_persistent_store.py` (23 tests, 582 lines) - Experimental/Trinity/DSPy/Archived
- `tests/dspy_agents/test_dspy_learning_agent.py` (23 tests, 588 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_pattern_detector_ambient.py` (21 tests, 473 lines) - Experimental/Trinity/DSPy/Archived
- `tests/archived/trinity_legacy/test_foundation_verifier.py` (20 tests, 379 lines) - Experimental/Trinity/DSPy/Archived
- `tests/dspy_agents/test_ab_framework_integration.py` (17 tests, 381 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_parameter_tuning.py` (14 tests, 484 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_phase3_constitutional.py` (13 tests, 742 lines) - Experimental/Trinity/DSPy/Archived

... and 15 more experimental test files

### 2. Duplicate Coverage (CONSOLIDATE)

**Impact**: 10 duplicate groups identified

- **toolsmith_agent** (2 files):
  - `/Users/am/Code/Agency/tests/test_toolsmith_agent_comprehensive.py`
  - `/Users/am/Code/Agency/tests/dspy_agents/test_toolsmith_agent.py`
- **agency_code_agent** (2 files):
  - `/Users/am/Code/Agency/tests/test_agency_code_agent.py`
  - `/Users/am/Code/Agency/tests/test_agency_code_agent_fixed.py`
- **chief_architect_agent** (3 files):
  - `/Users/am/Code/Agency/tests/test_chief_architect_agent_simple.py`
  - `/Users/am/Code/Agency/tests/test_chief_architect_agent.py`
  - `/Users/am/Code/Agency/tests/unit/test_chief_architect_agent.py`
- **planner_agent** (2 files):
  - `/Users/am/Code/Agency/tests/test_planner_agent.py`
  - `/Users/am/Code/Agency/tests/dspy_agents/test_planner_agent.py`
- **retry_controller** (2 files):
  - `/Users/am/Code/Agency/tests/test_retry_controller_additional.py`
  - `/Users/am/Code/Agency/tests/test_retry_controller.py`
- **auditor_agent** (2 files):
  - `/Users/am/Code/Agency/tests/test_auditor_agent.py`
  - `/Users/am/Code/Agency/tests/dspy_agents/test_auditor_agent.py`
- **message_bus** (2 files):
  - `/Users/am/Code/Agency/tests/trinity_protocol/test_message_bus.py`
  - `/Users/am/Code/Agency/tests/unit/shared/test_message_bus.py`
- **pattern_detector** (2 files):
  - `/Users/am/Code/Agency/tests/trinity_protocol/test_pattern_detector.py`
  - `/Users/am/Code/Agency/tests/unit/shared/test_pattern_detector.py`
- **persistent_store** (2 files):
  - `/Users/am/Code/Agency/tests/trinity_protocol/test_persistent_store.py`
  - `/Users/am/Code/Agency/tests/unit/shared/test_persistent_store.py`
- **preference_learning** (2 files):
  - `/Users/am/Code/Agency/tests/trinity_protocol/test_preference_learning.py`
  - `/Users/am/Code/Agency/tests/unit/shared/test_preference_learning.py`

### 3. Obsolete Tests (DELETE)

**Impact**: 7 files

- `tests/archived/trinity_legacy/test_project_executor.py` - Archived test directory
- `tests/archived/trinity_legacy/test_trinity_e2e_integration.py` - Archived test directory
- `tests/archived/trinity_legacy/test_foundation_verifier.py` - Archived test directory
- `tests/archived/trinity_legacy/test_daily_checkin.py` - Archived test directory
- `tests/archived/trinity_legacy/test_budget_enforcer.py` - Archived test directory
- `tests/archived/trinity_legacy/test_spec_from_conversation.py` - Archived test directory
- `tests/archived/trinity_legacy/test_project_initializer.py` - Archived test directory

### 4. NECESSARY Scores by Category

**Scoring**: Each test file scored 0-9 on NECESSARY criteria. Files scoring <4 are bloat.

| Score Range | Verdict | Count | Action |
|-------------|---------|-------|--------|
| 7-9 | KEEP - Excellent | 140 | Keep |
| 4-6 | KEEP - Good | 13 | Keep |
| 2-3 | REFACTOR | 0 | Refactor |
| 0-1 | DELETE | 0 | Delete |

## Execution Plan

### Phase 2A.1: Delete Experimental Tests
- **Trinity Protocol tests**: 19 files (139 tests, 9,364 lines)
- **DSPy A/B testing**: 6 files (248 tests, 6,469 lines)
- **Archived tests**: 7 files (24 tests, 4,514 lines)
- **Other experimental**: 3 files (320 tests, 2,500 lines)
- **Total impact**: 35 files, 731 tests, 22,847 lines
- **Estimated savings**: 731 tests, ~73s runtime
- **Execution script**: `scripts/phase_2a_delete_bloat.sh`

### Phase 2A.2: Consolidate Duplicates
- **Duplicate groups**: 10 identified
- **Strategy**: Merge similar test coverage into single files
- **Estimated savings**: ~100 tests, 10s runtime

### Phase 2A.3: Remove Obsolete Tests
- **Obsolete files**: 7 identified
- **Estimated savings**: ~50 tests, 5s runtime

### Phase 2A.4: Refactor Low-Score Tests
- **Files scoring <4**: 0 files
- **Strategy**: Improve or delete based on necessity
- **Estimated savings**: ~150 tests, 15s runtime

## Total Impact

**Before**: 2,965 tests, 153 files, ~296s runtime, 72,209 lines
**After Phase 2A.1**: 2,234 tests, 118 files, ~223s runtime, 49,362 lines
**Improvement**:
- Tests: -731 (-24.7%)
- Files: -35 (-22.9%)
- Runtime: -73s (-24.7%, 1.33x faster)
- Lines: -22,847 (-31.6%)

**Quality Impact**: POSITIVE - Removes experimental bloat, focuses on production code

## Detailed Bloat Files (Top 50 by Test Count)

| File | Tests | Lines | NECESSARY Score | Verdict | Reason |
|------|-------|-------|----------------|---------|--------|
| `tests/test_bash_tool_infrastructure.py` | 79 | 946 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/dspy_agents/test_auditor_agent.py` | 70 | 1139 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_pattern_detector.py` | 59 | 955 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/dspy_agents/test_planner_agent.py` | 49 | 942 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/dspy_agents/test_code_agent.py` | 48 | 1297 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_project_models.py` | 46 | 1220 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/dspy_agents/test_toolsmith_agent.py` | 41 | 983 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_executor_agent.py` | 38 | 1098 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_witness_agent.py` | 38 | 1421 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_architect_agent.py` | 35 | 999 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_preference_learning.py` | 28 | 701 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_conversation_context.py` | 24 | 386 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/test_learning_loop_integration.py` | 23 | 704 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_persistent_store.py` | 23 | 582 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/dspy_agents/test_dspy_learning_agent.py` | 23 | 588 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_pattern_detector_ambient.py` | 21 | 473 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/archived/trinity_legacy/test_foundation_verifier.py` | 20 | 379 | 6/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/dspy_agents/test_ab_framework_integration.py` | 17 | 381 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_parameter_tuning.py` | 14 | 484 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_phase3_constitutional.py` | 13 | 742 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_ambient_listener_service.py` | 10 | 520 | 6/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/test_git_error_paths.py` | 4 | 93 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/archived/trinity_legacy/test_project_initializer.py` | 4 | 842 | 5/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_message_bus.py` | 3 | 599 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_production_integration.py` | 1 | 865 | 6/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_transcription_service.py` | 0 | 914 | 5/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_human_review_queue.py` | 0 | 623 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_message_persistence_restart.py` | 0 | 414 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_phase3_integration.py` | 0 | 589 | 6/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_response_handler.py` | 0 | 422 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/archived/trinity_legacy/test_project_executor.py` | 0 | 636 | 5/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/archived/trinity_legacy/test_trinity_e2e_integration.py` | 0 | 1391 | 6/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/archived/trinity_legacy/test_daily_checkin.py` | 0 | 359 | 5/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/archived/trinity_legacy/test_budget_enforcer.py` | 0 | 273 | 5/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/archived/trinity_legacy/test_spec_from_conversation.py` | 0 | 633 | 6/9 | KEEP | Experimental/Trinity/DSPy/Archived |

## Next Steps

### Immediate (Phase 2A.1 - Ready to Execute)

1. **Review Report**: Review this analysis and accompanying JSON file
2. **Execute Deletion Script**: Run `bash scripts/phase_2a_delete_bloat.sh`
   - Creates timestamped backup automatically
   - Deletes 35 experimental test files (731 tests)
   - Safe to run - only removes non-production experimental code
3. **Verify Test Suite**: Run `python run_tests.py --run-all`
   - Expect: 2,234 tests passing (100% success rate)
   - Runtime should drop from ~296s to ~223s
4. **Commit Changes**: Git commit with message describing bloat removal

### Follow-up (Phase 2A.2 - Requires Manual Review)

5. **Consolidate Duplicates**: Review 10 duplicate test groups
   - Merge test_agency_code_agent_fixed.py → test_agency_code_agent.py
   - Merge test_retry_controller_additional.py → test_retry_controller.py
   - Consolidate chief_architect_agent tests (3 files → 1)
   - Estimated savings: ~100 tests
6. **Document in ADR**: Create ADR documenting experimental feature archival
7. **Update Metrics**: Update constitution.md and CLAUDE.md test counts

### Artifacts Generated

- **Analysis Report**: `docs/testing/PHASE_2A_BLOAT_ANALYSIS.md` (this file)
- **Detailed JSON**: `docs/testing/phase_2a_bloat_detailed.json`
- **Deletion Script**: `scripts/phase_2a_delete_bloat.sh` (executable, safe to run)
- **Backup**: Auto-created in `.test_bloat_backup_<timestamp>/` when script runs

---

*Analysis generated by NECESSARY Test Audit Framework*
