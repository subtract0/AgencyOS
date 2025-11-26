# Test Suite Bloat Analysis - Phase 2A

**Generated**: 2025-11-24 02:41:35

## Executive Summary

- **Total tests**: 5,767
- **Bloat identified**: 492 tests (8.5%)
- **Estimated removal**: 492 tests
- **Remaining tests**: 5,275 tests
- **Runtime improvement**: 577s → 528s (1.1x faster)
- **Lines of test code**: 169,239 lines

## Bloat Categories

### 1. Experimental Features (DELETE)

**Impact**: 24 files, 492 tests

- `tests/trinity_protocol/core/test_escalation_rules.py` (52 tests, 1187 lines) - Experimental/Trinity/DSPy/Archived
- `tests/test_bash_validation.py` (46 tests, 478 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/core/test_agent_registry.py` (39 tests, 743 lines) - Experimental/Trinity/DSPy/Archived
- `tests/test_v5_integration.py` (38 tests, 670 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_executor_agent.py` (38 tests, 1112 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/core/test_hybrid_executor.py` (32 tests, 1448 lines) - Experimental/Trinity/DSPy/Archived
- `tests/property/test_property_based.py` (30 tests, 455 lines) - Experimental/Trinity/DSPy/Archived
- `tests/unit/tools/test_tool_cache.py` (27 tests, 544 lines) - Experimental/Trinity/DSPy/Archived
- `tests/test_generate_deletion_pr.py` (23 tests, 599 lines) - Experimental/Trinity/DSPy/Archived
- `tests/test_init_ollama_model.py` (22 tests, 340 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/core/test_orchestrator_hybrid_integration.py` (22 tests, 907 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_pattern_detector_ambient.py` (21 tests, 489 lines) - Experimental/Trinity/DSPy/Archived
- `tests/fixtures/test_constitutional_test_agents.py` (21 tests, 316 lines) - Experimental/Trinity/DSPy/Archived
- `tests/test_overnight_integration.py` (19 tests, 879 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/core/test_hybrid_executor_generalized.py` (17 tests, 724 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_parameter_tuning.py` (14 tests, 499 lines) - Experimental/Trinity/DSPy/Archived
- `tests/tools/ci_monitor/test_constitutional_compliance.py` (11 tests, 733 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_docker_ollama_fixture.py` (7 tests, 97 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/core/test_executor_prompts.py` (5 tests, 173 lines) - Experimental/Trinity/DSPy/Archived
- `tests/trinity_protocol/test_docker_ollama_usage_example.py` (4 tests, 122 lines) - Experimental/Trinity/DSPy/Archived

... and 4 more experimental test files

### 2. Duplicate Coverage (CONSOLIDATE)

**Impact**: 8 duplicate groups identified

- **git_validation** (2 files):
  - `/Users/am/Code/AgencyOS/tests/test_git_validation.py`
  - `/Users/am/Code/AgencyOS/tests/foundation_automation/test_git_validation.py`
- **ollama_health_check** (2 files):
  - `/Users/am/Code/AgencyOS/tests/test_ollama_health_check_comprehensive.py`
  - `/Users/am/Code/AgencyOS/tests/test_ollama_health_check.py`
- **timeout_wrapper** (2 files):
  - `/Users/am/Code/AgencyOS/tests/test_timeout_wrapper.py`
  - `/Users/am/Code/AgencyOS/tests/unit/shared/test_timeout_wrapper.py`
- **retry_controller** (4 files):
  - `/Users/am/Code/AgencyOS/tests/test_retry_controller_additional.py`
  - `/Users/am/Code/AgencyOS/tests/test_retry_controller.py`
  - `/Users/am/Code/AgencyOS/tests/unit/shared/test_retry_controller.py`
  - `/Users/am/Code/AgencyOS/tests/tools/ci_monitor/test_retry_controller.py`
- **spec_generator** (2 files):
  - `/Users/am/Code/AgencyOS/tests/test_spec_generator.py`
  - `/Users/am/Code/AgencyOS/tests/orchestrator/test_spec_generator.py`
- **agent_registry** (2 files):
  - `/Users/am/Code/AgencyOS/tests/test_agent_registry.py`
  - `/Users/am/Code/AgencyOS/tests/trinity_protocol/core/test_agent_registry.py`
- **verification_gate** (2 files):
  - `/Users/am/Code/AgencyOS/tests/test_test_verification_gate.py`
  - `/Users/am/Code/AgencyOS/tests/orchestrator/test_verification_gate.py`
- **chief_architect_agent** (2 files):
  - `/Users/am/Code/AgencyOS/tests/test_chief_architect_agent.py`
  - `/Users/am/Code/AgencyOS/tests/unit/test_chief_architect_agent.py`

### 3. Obsolete Tests (DELETE)

**Impact**: 0 files


### 4. NECESSARY Scores by Category

**Scoring**: Each test file scored 0-9 on NECESSARY criteria. Files scoring <4 are bloat.

| Score Range | Verdict | Count | Action |
|-------------|---------|-------|--------|
| 7-9 | KEEP - Excellent | 300 | Keep |
| 4-6 | KEEP - Good | 12 | Keep |
| 2-3 | REFACTOR | 0 | Refactor |
| 0-1 | DELETE | 0 | Delete |

## Execution Plan

### Phase 2A.1: Delete Experimental Tests
- **Trinity Protocol tests**: 19 files (~150 tests)
- **DSPy A/B testing**: 6 files (~80 tests)
- **Archived tests**: 7 files (~50 tests)
- **Estimated savings**: ~280 tests, 28s runtime

### Phase 2A.2: Consolidate Duplicates
- **Duplicate groups**: 8 identified
- **Strategy**: Merge similar test coverage into single files
- **Estimated savings**: ~100 tests, 10s runtime

### Phase 2A.3: Remove Obsolete Tests
- **Obsolete files**: 0 identified
- **Estimated savings**: ~50 tests, 5s runtime

### Phase 2A.4: Refactor Low-Score Tests
- **Files scoring <4**: 0 files
- **Strategy**: Improve or delete based on necessity
- **Estimated savings**: ~150 tests, 15s runtime

## Total Impact

**Before**: 5,767 tests, ~577s runtime
**After**: 5,275 tests, ~528s runtime
**Improvement**: 8.5% reduction, 1.1x faster

## Detailed Bloat Files (Top 50 by Test Count)

| File | Tests | Lines | NECESSARY Score | Verdict | Reason |
|------|-------|-------|----------------|---------|--------|
| `tests/trinity_protocol/core/test_escalation_rules.py` | 52 | 1187 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/test_bash_validation.py` | 46 | 478 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/core/test_agent_registry.py` | 39 | 743 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/test_v5_integration.py` | 38 | 670 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_executor_agent.py` | 38 | 1112 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/core/test_hybrid_executor.py` | 32 | 1448 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/property/test_property_based.py` | 30 | 455 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/unit/tools/test_tool_cache.py` | 27 | 544 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/test_generate_deletion_pr.py` | 23 | 599 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/test_init_ollama_model.py` | 22 | 340 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/core/test_orchestrator_hybrid_integration.py` | 22 | 907 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_pattern_detector_ambient.py` | 21 | 489 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/fixtures/test_constitutional_test_agents.py` | 21 | 316 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/test_overnight_integration.py` | 19 | 879 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/core/test_hybrid_executor_generalized.py` | 17 | 724 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_parameter_tuning.py` | 14 | 499 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/tools/ci_monitor/test_constitutional_compliance.py` | 11 | 733 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_docker_ollama_fixture.py` | 7 | 97 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/core/test_executor_prompts.py` | 5 | 173 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/test_docker_ollama_usage_example.py` | 4 | 122 | 8/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/unit/shared/test_message_bus.py` | 4 | 722 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/integration/test_remove_intentional_delays.py` | 0 | 583 | 6/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/foundation_automation/test_e2e_natural_language_flow.py` | 0 | 1183 | 7/9 | KEEP | Experimental/Trinity/DSPy/Archived |
| `tests/trinity_protocol/core/test_orchestrator_hybrid_executor_integration.py` | 0 | 161 | 6/9 | KEEP | Experimental/Trinity/DSPy/Archived |

## Next Steps

1. **Review & Approve**: Review this analysis and approve deletion strategy
2. **Execute Deletions**: Remove experimental and obsolete tests
3. **Consolidate Duplicates**: Merge duplicate test coverage
4. **Re-run CI**: Verify 100% pass rate on remaining tests
5. **Update Metrics**: Document new test suite metrics

---

*Analysis generated by NECESSARY Test Audit Framework*
