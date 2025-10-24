# Specification: V5 Calibration Fix - Achieve 15-20% HIGH Classification

**Spec ID**: spec-v5-calibration-fix
**Version**: 1.0
**Date**: 2025-10-24
**Author**: PrimeA Orchestrator
**Status**: Draft - Awaiting User Approval

---

## Executive Summary

Fix the V5 empirical test value scoring system to achieve the target 15-20% HIGH classification rate by regenerating the runtime cache from pytest execution, converting it to V5 format, verifying V5_FULL mode activation, and running a complete test suite audit with validated classifications.

**Current State**: V5_PARTIAL mode with heuristic runtime estimates → 0% classifications (incomplete/buggy audit)
**Target State**: V5_FULL mode with empirical runtime data → 15-20% HIGH classification
**Impact**: Accurate test value assessment for prioritization and cleanup decisions

---

## Background & Context

### Current Situation Analysis

Based on analysis of existing documentation and audit reports:

1. **V5 Implementation Status**: ✅ Complete (all 10 phases implemented, 74 files committed, 137 tests at 96% pass rate)

2. **Runtime Cache Status**:
   - File exists: `.audit/runtime_cache.json` (38KB)
   - **Issue**: Corrupted or invalid format (JSON parse error, missing `duration_seconds` field)
   - **Result**: V5 system falls back to V5_PARTIAL mode with heuristics

3. **Most Recent Audit** (2025-10-24 00:17):
   - **Mode**: V5_PARTIAL (heuristic runtime estimates)
   - **Tests Analyzed**: 5,587
   - **Classifications**: 0% HIGH, 0% MEDIUM, 0% LOW (incomplete/buggy)
   - **Warning**: "Runtime cache not found, using heuristic estimates"

4. **Historical Success** (2025-10-24 earlier):
   - **Mode**: V5_FULL with 287 tests
   - **Result**: 16.0% HIGH classification ✅ (within 15-20% target)
   - **Source**: JUnit XML from pytest execution

### Root Cause

The current `.audit/runtime_cache.json` file is corrupted (invalid JSON format, missing required fields). This causes:
- V5 system cannot load empirical runtime data
- Falls back to V5_PARTIAL mode with heuristic estimates
- Incomplete audit execution (0% classifications suggest code bug when cache is invalid)

### Success Evidence

Previous successful V5_FULL calibration proves the system works when:
1. Valid runtime cache is generated from pytest JUnit XML output
2. Cache is properly converted to V5 format with metadata structure
3. All required fields are present (`duration_seconds`, `source`, `timestamp`)

---

## Goals & Objectives

### Primary Goal
Restore V5_FULL mode operation with 15-20% HIGH classification rate using empirical runtime data from full test suite execution.

### Secondary Goals
1. **Data Quality**: Generate runtime cache from actual pytest execution (not estimates)
2. **Format Validation**: Ensure cache format matches V5 schema requirements
3. **Classification Accuracy**: Verify HIGH classification distribution is within 15-20% target range
4. **Audit Completeness**: Run full test suite audit (5,500+ tests) with validated classifications
5. **Documentation**: Update calibration results with full test suite metrics

---

## Personas & Use Cases

### Persona 1: Test Quality Engineer
**Need**: Accurate test value classifications to prioritize test maintenance
**Pain Point**: Cannot trust heuristic estimates (too many false positives)
**Success Criteria**: 15-20% HIGH classification based on real execution data

### Persona 2: CI/CD Maintainer
**Need**: Identify slow tests causing pipeline bottlenecks
**Pain Point**: Heuristics don't reflect actual test runtime
**Success Criteria**: Runtime penalties correctly applied based on empirical data

### Persona 3: Development Team
**Need**: Focus test cleanup efforts on truly low-value tests
**Pain Point**: Cannot differentiate between valuable and redundant tests
**Success Criteria**: Clear LOW/MEDIUM/HIGH classifications with supporting evidence

---

## Acceptance Criteria

### Phase 1: Runtime Cache Generation ✅ (if not already done)
- [ ] **AC1.1**: JUnit XML file generated from pytest execution (`.audit/junit.xml`)
- [ ] **AC1.2**: JUnit XML contains execution data for 5,500+ tests
- [ ] **AC1.3**: Total runtime data captured (setup + call + teardown phases)
- [ ] **AC1.4**: File size reasonable (~50-100KB for 5,500+ tests)

**Verification**:
```bash
ls -lh .audit/junit.xml
# Expected: ~50-100KB file exists
xmllint --format .audit/junit.xml | grep -c "testcase"
# Expected: 5,500+ test cases
```

### Phase 2: V5 Format Conversion ✅
- [ ] **AC2.1**: Runtime cache file created at `.audit/runtime_cache.json`
- [ ] **AC2.2**: Cache format matches V5 schema (nested structure with metadata)
- [ ] **AC2.3**: All entries have required fields: `duration_seconds`, `source`, `timestamp`
- [ ] **AC2.4**: Metadata includes: `version`, `source`, `test_count`
- [ ] **AC2.5**: Test count in metadata matches actual entries (5,500+)

**V5 Schema**:
```json
{
  "version": "1.0",
  "source": "junitxml",
  "test_count": 5587,
  "runtimes": {
    "tests/path/to/test.py::test_name": {
      "duration_seconds": 0.123,
      "source": "junitxml",
      "timestamp": "2025-10-24T12:00:00"
    }
  }
}
```

**Verification**:
```bash
python3 -c "import json; d=json.load(open('.audit/runtime_cache.json')); print(f\"Tests: {d['test_count']}, Version: {d['version']}, Entries: {len(d['runtimes'])}\")"
# Expected: Tests: 5587, Version: 1.0, Entries: 5587
```

### Phase 3: V5_FULL Mode Verification ✅
- [ ] **AC3.1**: Verification script confirms V5_FULL mode is active
- [ ] **AC3.2**: Runtime cache loads successfully (no parse errors)
- [ ] **AC3.3**: HIGH classification rate is 15-20% (based on top percentile runtime)
- [ ] **AC3.4**: Runtime percentiles calculated correctly (P80, P85, P90)
- [ ] **AC3.5**: No warnings about missing runtime data

**Verification**:
```bash
python3 scripts/verify_v5_calibration.py
# Expected output:
# ✅ V5 Calibration VERIFIED
# HIGH classification: 16.0% (target: 15.0-20.0%)
# Runtime penalties correctly applied
```

### Phase 4: Full Test Suite Audit ✅
- [ ] **AC4.1**: Test value audit completes for all 5,500+ tests
- [ ] **AC4.2**: Audit metadata shows `scoring_version: "V5_FULL"`
- [ ] **AC4.3**: Audit metadata shows `runtime_source: "junitxml"`
- [ ] **AC4.4**: No warnings in audit metadata
- [ ] **AC4.5**: Classification distribution matches target:
  - HIGH (>20 score): 15-20% (~840-1,120 tests)
  - MEDIUM (10-20 score): 55-60% (~3,070-3,350 tests)
  - LOW (<10 score): 20-25% (~1,115-1,395 tests)
- [ ] **AC4.6**: Audit report generated at `audit_reports/test_value_audit_*.json`
- [ ] **AC4.7**: Candidate lists generated (delete, consolidate, high-value)

**Verification**:
```bash
# Run audit
python3 scripts/test_value_audit.py

# Check metadata
python3 -c "
import json, glob
files = sorted(glob.glob('audit_reports/test_value_audit_*.json'))
d = json.load(open(files[-1]))
m = d['metadata']
s = d['summary']
print(f\"Version: {m['scoring_version']}\")
print(f\"Runtime: {m['runtime_source']}\")
print(f\"Warnings: {m.get('warnings', [])}\")
print(f\"HIGH: {s['HIGH']['count']} ({s['HIGH']['percentage']:.1f}%)\")
print(f\"MEDIUM: {s['MEDIUM']['count']} ({s['MEDIUM']['percentage']:.1f}%)\")
print(f\"LOW: {s['LOW']['count']} ({s['LOW']['percentage']:.1f}%)\")
"
# Expected:
# Version: V5_FULL
# Runtime: junitxml
# Warnings: []
# HIGH: 900 (16.1%)
# MEDIUM: 3200 (57.3%)
# LOW: 1487 (26.6%)
```

### Phase 5: Documentation Update ✅
- [ ] **AC5.1**: `V5_CALIBRATION_RESULTS.md` updated with full test suite metrics
- [ ] **AC5.2**: Document includes runtime distribution analysis (5,500+ tests)
- [ ] **AC5.3**: Document includes HIGH classification verification
- [ ] **AC5.4**: Constitutional compliance section updated

---

## Test Plan (NECESSARY Pattern)

### Test Coverage Matrix

#### Normal Path (Happy Path) - Required Tests
1. **test_runtime_cache_generation_success**
   - Given: Valid pytest execution with JUnit XML output
   - When: `convert_junit_to_cache.py` processes the file
   - Then: Runtime cache created with correct format and all entries

2. **test_v5_full_mode_activation**
   - Given: Valid runtime cache file exists
   - When: `verify_v5_calibration.py` runs
   - Then: Confirms V5_FULL mode, 15-20% HIGH classification

3. **test_full_audit_execution**
   - Given: V5_FULL mode active
   - When: `test_value_audit.py` runs
   - Then: All 5,500+ tests classified, distribution matches targets

#### Edge Cases - Required Tests
4. **test_corrupted_cache_recovery**
   - Given: Corrupted `.audit/runtime_cache.json`
   - When: System attempts to load cache
   - Then: Falls back to V5_PARTIAL gracefully, logs warning

5. **test_missing_cache_regeneration**
   - Given: No runtime cache file exists
   - When: Cache generation script runs
   - Then: Creates new cache from JUnit XML

6. **test_empty_junit_xml_handling**
   - Given: JUnit XML file with 0 test cases
   - When: Conversion script runs
   - Then: Creates valid cache with 0 entries, logs warning

7. **test_partial_junit_xml_data**
   - Given: JUnit XML missing some test runtime data
   - When: Conversion script runs
   - Then: Includes available data, logs skipped entries

#### Constraints (Type/Domain Validation) - Required Tests
8. **test_runtime_cache_schema_validation**
   - Validate cache has required top-level keys: `version`, `source`, `test_count`, `runtimes`
   - Validate each runtime entry has: `duration_seconds`, `source`, `timestamp`
   - Validate `duration_seconds` is float >= 0
   - Validate `test_count` matches number of runtime entries

9. **test_classification_distribution_bounds**
   - Validate HIGH percentage is between 15.0% and 20.0%
   - Validate MEDIUM + HIGH + LOW = 100% (within 0.1% tolerance)
   - Validate all scores are non-negative floats

#### Error Handling - Required Tests
10. **test_junit_xml_parse_failure**
    - Given: Malformed XML file
    - When: Conversion script attempts to parse
    - Then: Returns error with clear message, doesn't crash

11. **test_cache_write_permission_error**
    - Given: No write permissions for `.audit/` directory
    - When: Cache generation attempts to write file
    - Then: Returns error with permission details

12. **test_audit_script_timeout**
    - Given: Audit script runs for >30 minutes
    - When: Timeout threshold reached
    - Then: Script terminates gracefully, saves partial results

#### Security - Required Tests
13. **test_cache_file_permissions**
    - Validate `.audit/runtime_cache.json` has correct permissions (644)
    - Validate no sensitive data in cache (only test IDs and durations)

14. **test_junit_xml_injection_prevention**
    - Given: JUnit XML with malicious test names (path traversal attempts)
    - When: Conversion script processes names
    - Then: Sanitizes paths, prevents directory traversal

#### Scale (Performance) - Required Tests
15. **test_large_test_suite_performance**
    - Given: 5,500+ test runtime entries
    - When: V5 audit runs
    - Then: Completes in <5 minutes, memory usage <500MB

16. **test_runtime_percentile_calculation_accuracy**
    - Given: 5,500+ runtime samples
    - When: Percentiles calculated (P80, P85, P90)
    - Then: Results match numpy.percentile within 1% tolerance

#### Asynchronous (if applicable)
17. **test_concurrent_cache_access**
    - Given: Multiple processes read runtime cache simultaneously
    - When: File locks tested
    - Then: No corruption, all processes get valid data

#### Retry Logic (Article I Resilience)
18. **test_transient_file_lock_retry**
    - Given: Cache file temporarily locked by another process
    - When: Read attempt fails
    - Then: Retries 3 times with exponential backoff

19. **test_network_timeout_retry_for_ci_data**
    - Given: CI failure data fetch times out
    - When: First attempt fails
    - Then: Retries with 2x, 3x timeout multipliers

#### Yield/Generator (if applicable)
20. **test_streaming_junit_xml_parsing**
    - Given: Very large JUnit XML file (>100MB)
    - When: Parsing uses generator/streaming
    - Then: Memory usage remains constant, doesn't load entire file

---

## Implementation Phases

### Phase 1: Runtime Cache Generation (Tier 1)
**Estimated Effort**: 30 minutes
**Estimated Cost**: $0.50 (simple execution task)
**Agent**: Coder (P3 local model)

**Tasks**:
1. Check if `.audit/junit.xml` exists and is recent (<24 hours)
2. If missing or stale, regenerate:
   ```bash
   mkdir -p .audit
   uv run pytest tests/ --junitxml=.audit/junit.xml --tb=no -q
   ```
3. Validate JUnit XML has 5,500+ test entries
4. Verify file is well-formed XML (no parse errors)

**Dependencies**: None
**Acceptance Criteria**: AC1.1, AC1.2, AC1.3, AC1.4

### Phase 2: V5 Format Conversion (Tier 1)
**Estimated Effort**: 30 minutes
**Estimated Cost**: $0.50 (simple conversion task)
**Agent**: Coder (P3 local model)

**Tasks**:
1. Run conversion script:
   ```bash
   python3 scripts/convert_junit_to_cache.py .audit/junit.xml .audit/runtime_cache.json
   ```
2. Validate output format matches V5 schema
3. Verify all required fields present
4. Check test_count matches runtime entries
5. Validate JSON is well-formed (no syntax errors)

**Dependencies**: Phase 1 (requires JUnit XML)
**Acceptance Criteria**: AC2.1, AC2.2, AC2.3, AC2.4, AC2.5

### Phase 3: V5_FULL Mode Verification (Tier 1)
**Estimated Effort**: 15 minutes
**Estimated Cost**: $0.25 (simple verification)
**Agent**: Test Generator (P3 local model)

**Tasks**:
1. Run verification script:
   ```bash
   python3 scripts/verify_v5_calibration.py
   ```
2. Verify exit code is 0 (success)
3. Check HIGH classification is 15-20%
4. Validate runtime percentiles are calculated
5. Confirm no warnings about missing data

**Dependencies**: Phase 2 (requires valid runtime cache)
**Acceptance Criteria**: AC3.1, AC3.2, AC3.3, AC3.4, AC3.5

### Phase 4: Full Test Suite Audit (Tier 2)
**Estimated Effort**: 1 hour
**Estimated Cost**: $1.50 (moderate complexity)
**Agent**: Coder (P2 gpt-4o)

**Tasks**:
1. Run full test value audit:
   ```bash
   python3 scripts/test_value_audit.py
   ```
2. Wait for completion (may take 5-10 minutes for 5,500+ tests)
3. Verify audit report generated
4. Validate metadata shows V5_FULL mode
5. Check classification distribution matches targets
6. Review candidate lists (delete, consolidate, high-value)

**Dependencies**: Phase 3 (requires V5_FULL mode active)
**Acceptance Criteria**: AC4.1, AC4.2, AC4.3, AC4.4, AC4.5, AC4.6, AC4.7

### Phase 5: Documentation Update (Tier 1)
**Estimated Effort**: 30 minutes
**Estimated Cost**: $0.50 (simple documentation)
**Agent**: Summary (P3 gpt-5-mini)

**Tasks**:
1. Update `V5_CALIBRATION_RESULTS.md` with new metrics
2. Include runtime distribution for 5,500+ tests
3. Document HIGH classification verification
4. Add constitutional compliance notes
5. Update troubleshooting section if issues found

**Dependencies**: Phase 4 (requires completed audit)
**Acceptance Criteria**: AC5.1, AC5.2, AC5.3, AC5.4

---

## Risk Assessment & Mitigation

### Risk 1: Pytest Execution Timeout (Probability: Medium, Impact: Medium)
**Description**: Running pytest on 5,500+ tests may timeout or hang
**Mitigation**:
- Use `--tb=no` to disable tracebacks (faster execution)
- Use `-q` for quiet mode (less output overhead)
- Set reasonable timeout: `--timeout=120` per test
- Run in background if needed, monitor with `ps aux | grep pytest`

### Risk 2: Runtime Cache Format Incompatibility (Probability: Low, Impact: High)
**Description**: Converted cache doesn't match expected V5 schema
**Mitigation**:
- Validate schema immediately after conversion
- Test with sample data first (10-20 tests)
- Rollback to known-good cache if validation fails
- Add schema validation tests to prevent regressions

### Risk 3: Classification Distribution Drift (Probability: Low, Impact: Medium)
**Description**: Full test suite HIGH percentage drifts outside 15-20% range
**Mitigation**:
- Verify with smaller sample first (287 tests previously worked)
- If drift occurs, check for new slow tests added recently
- Review weights.yaml configuration (may need tuning)
- Use grid search tuner to re-optimize if needed

### Risk 4: Incomplete Audit Execution (Probability: Low, Impact: High)
**Description**: Audit script fails midway through 5,500+ test analysis
**Mitigation**:
- Implement checkpoint/resume mechanism (save partial progress)
- Add progress logging every 500 tests
- Set memory limits to prevent OOM crashes
- Retry failed tests with exponential backoff (Article I)

---

## Success Metrics

### Primary Metrics (Must Achieve)
1. **V5_FULL Mode Active**: ✅ runtime_source = "junitxml" (not "heuristic")
2. **HIGH Classification Rate**: ✅ 15.0% <= HIGH% <= 20.0% (target: 16.0%)
3. **Audit Completeness**: ✅ 100% of tests analyzed (5,500+/5,500+)
4. **No Warnings**: ✅ metadata.warnings = [] (empty list)

### Secondary Metrics (Should Achieve)
5. **MEDIUM Classification Rate**: 55-60% (~3,070-3,350 tests)
6. **LOW Classification Rate**: 20-25% (~1,115-1,395 tests)
7. **Runtime Accuracy**: P90 runtime within ±10% of actual execution time
8. **Audit Performance**: Completes in <5 minutes for 5,500+ tests

### Validation Commands
```bash
# Metric 1: V5_FULL mode
python3 -c "import json, glob; d=json.load(open(sorted(glob.glob('audit_reports/test_value_audit_*.json'))[-1])); print(d['metadata']['scoring_version'])"
# Expected: V5_FULL

# Metric 2: HIGH classification rate
python3 -c "import json, glob; d=json.load(open(sorted(glob.glob('audit_reports/test_value_audit_*.json'))[-1])); print(f\"{d['summary']['HIGH']['percentage']:.1f}%\")"
# Expected: 15.0% - 20.0%

# Metric 3: Audit completeness
python3 -c "import json, glob; d=json.load(open(sorted(glob.glob('audit_reports/test_value_audit_*.json'))[-1])); print(d['summary']['total_tests'])"
# Expected: 5587 (or current total)

# Metric 4: No warnings
python3 -c "import json, glob; d=json.load(open(sorted(glob.glob('audit_reports/test_value_audit_*.json'))[-1])); print(d['metadata'].get('warnings', []))"
# Expected: []
```

---

## Constitutional Requirements

### Article I: Complete Context Before Action
- **Requirement**: All 5,500+ tests executed to completion (no timeouts)
- **Validation**: JUnit XML shows complete execution data for all tests
- **Implementation**: Use `--timeout=120` per test, retry on timeout (2x, 3x, 10x)

### Article II: 100% Verification and Stability
- **Requirement**: V5 calibration verified with actual pytest execution data
- **Validation**: 15-20% HIGH classification rate confirmed by verification script
- **Implementation**: All tests in this spec must pass before completion

### Article III: Automated Local Enforcement
- **Requirement**: Quality gates enforced locally (no manual overrides)
- **Validation**: Schema validation runs automatically on cache conversion
- **Implementation**: Fail fast on invalid cache format, don't proceed to audit

### Article IV: Continuous Learning and Improvement
- **Requirement**: VectorStore query for V5 calibration patterns before starting
- **Validation**: Store successful patterns after completion (cache generation, conversion)
- **Implementation**: Query learnings for similar "runtime cache", "V5 calibration" tasks

### Article V: Spec-Driven Development
- **Requirement**: This specification is the contract for implementation
- **Validation**: All acceptance criteria met before marking complete
- **Implementation**: Trace all code changes back to AC items in this spec

---

## Dependencies & Prerequisites

### System Requirements
- Python 3.12+ (for pytest execution)
- `uv` package manager (for isolated test runs)
- 5GB free disk space (for JUnit XML and audit reports)
- 2GB free memory (for audit script execution)

### File Dependencies
- **Input**: `tests/` directory with 5,500+ test files
- **Output**: `.audit/junit.xml`, `.audit/runtime_cache.json`
- **Scripts**: `scripts/convert_junit_to_cache.py`, `scripts/verify_v5_calibration.py`, `scripts/test_value_audit.py`

### Configuration Dependencies
- `weights.yaml` (V5 scoring weights configuration)
- `.audit/failure_history.sqlite` (CI failure data, optional)
- Git history (for churn analysis, optional)

---

## Rollback Plan

### Rollback Trigger Conditions
1. Runtime cache conversion produces invalid JSON
2. V5 verification shows HIGH% outside 10-25% range (major drift)
3. Audit script crashes or produces 0% classifications
4. Any constitutional violation detected

### Rollback Steps
1. **Restore Previous Cache**:
   ```bash
   cp .audit/runtime_cache.json.backup .audit/runtime_cache.json
   ```

2. **Revert to V5_PARTIAL Mode**:
   ```bash
   rm .audit/runtime_cache.json
   # System will auto-fallback to heuristics
   ```

3. **Use Known-Good Results**:
   - Previous successful audit: `audit_reports/test_value_audit_20251023_*.json`
   - Known-good cache: `.audit/runtime_cache.json` (from commit 39dc5a95)

4. **Report Failure**:
   - Create issue in `~/.agency/memories/agency_backlog/v5_calibration_issues.md`
   - Document failure mode, logs, error messages
   - Store failure pattern to VectorStore for learning

---

## Next Steps After Completion

### Immediate (Required)
1. ✅ Verify V5_FULL mode is stable (run audit 2-3 times, check consistency)
2. ✅ Update `.gitignore` to exclude `.audit/runtime_cache.json` (local dev data)
3. ✅ Document V5 usage in `docs/TEST_ADR034_USAGE.md`

### Short-Term (Optional, High Value)
4. Add `verify_v5_calibration.py` to CI checks (fail if HIGH% drifts >5%)
5. Schedule periodic cache refresh (weekly pytest run via cron/GitHub Actions)
6. Create monitoring dashboard for classification drift over time

### Long-Term (Optional, Strategic)
7. Integrate manual labeling tool (sample 50-100 tests for ground truth)
8. Run grid search tuner to optimize weights.yaml based on labels
9. Execute test cleanup workflow (delete LOW value tests, consolidate duplicates)
10. Measure impact: test suite runtime reduction, maintenance hours saved

---

## Appendix A: V5 Three-Tier Fallback System

```
┌──────────────────────────────────────────────────────┐
│ V5_FULL (Target - All Empirical Data)               │
├──────────────────────────────────────────────────────┤
│ ✅ Runtime: Actual pytest durations                  │
│ ✅ CI Failures: SQLite database                      │
│ ✅ Git Churn: Repository analysis                    │
│ ✅ Weights: weights.yaml configuration               │
│ Result: 15-20% HIGH (optimal calibration)           │
└──────────────────────────────────────────────────────┘
                    ↓ (missing runtime data)
┌──────────────────────────────────────────────────────┐
│ V5_PARTIAL (Current Mode - PROBLEM)                 │
├──────────────────────────────────────────────────────┤
│ ❌ Runtime: Heuristic estimates (keywords)           │
│ ✅ CI Failures: SQLite database                      │
│ ✅ Git Churn: Repository analysis                    │
│ ✅ Weights: weights.yaml configuration               │
│ Result: 0% classifications (incomplete/buggy)       │
└──────────────────────────────────────────────────────┘
                    ↓ (no empirical data)
┌──────────────────────────────────────────────────────┐
│ V4_FALLBACK (Legacy)                                 │
├──────────────────────────────────────────────────────┤
│ All heuristic-based scoring                          │
│ Result: 74% HIGH (original V4 behavior)              │
└──────────────────────────────────────────────────────┘
```

**This Spec Targets**: V5_PARTIAL → V5_FULL upgrade

---

## Appendix B: Historical Context

### Previous Successful Calibration (2025-10-24 00:49)
- **Test Suite**: 287 tests (subset)
- **Mode**: V5_FULL
- **Runtime Source**: junitxml
- **HIGH Classification**: 16.0% (46/287 tests)
- **Result**: ✅ Within 15-20% target range

### Current Failed State (2025-10-24 02:50)
- **Test Suite**: 5,587 tests (full suite)
- **Mode**: V5_PARTIAL
- **Runtime Source**: heuristic
- **HIGH Classification**: 0% (0/5,587 tests)
- **Result**: ❌ Incomplete audit, corrupted cache

**Goal**: Replicate previous success with full test suite (5,587 tests)

---

## Approval Checkpoint

**This specification must be approved before proceeding to Stage 2 (TDD execution).**

**Reviewer Questions**:
1. Are the acceptance criteria clear and measurable?
2. Is the 15-20% HIGH classification target appropriate?
3. Should we include manual labeling/tuning phases in this mission?
4. Any concerns about risk assessment or rollback plan?
5. Approve to proceed to TDD execution? (YES/NO/REVISE)

**Estimated Total Effort**: 2.5 hours
**Estimated Total Cost**: $3.25 (mixed P1/P2/P3 routing)
**Expected Outcome**: V5_FULL mode with 15-20% HIGH classification for 5,500+ test suite

---

**Status**: ⏸️ PAUSED - Awaiting User Approval
**Next Action**: User reviews spec, approves/rejects/requests revisions
**After Approval**: Execute Stage 2 (TDD workflow: tests first, implementation second, verify, PR)
