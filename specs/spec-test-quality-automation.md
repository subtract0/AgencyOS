# Specification: Test Quality Automation System

**Date**: 2025-10-24
**Status**: DRAFT (Stage 1 - Awaiting Approval)
**Type**: Complex Feature (Automation + Quality)
**Estimated Effort**: 3-4 hours
**Constitutional Articles**: II (Verification), III (Enforcement), IV (Learning)

---

## Executive Summary

Automate the V5 empirical test value auditor to continuously identify and safely delete low-value tests, improving test suite quality while maintaining constitutional compliance.

**Current State**:
- V5 auditor exists but requires manual execution
- One deletion candidate identified (`test_mocking_hell`, score 5.2)
- Revert scripts created manually
- No automation or CI/CD integration

**Target State**:
- Automated audit execution (on-demand, scheduled, CI/CD)
- Safe deletion workflow with backup + revert mechanisms
- Quality metrics dashboard and reporting
- Constitutional compliance enforced (Article III: no auto-deletion without review)

---

## Context

### Problem Statement

**V5 Auditor Capabilities Underutilized**:
- 10-phase empirical scoring system complete (ADR-034)
- 8 empirical dimensions (runtime, CI failures, git churn, mocks, etc.)
- Manual execution only → low adoption, inconsistent usage
- No integration with development workflow

**Quality Debt Accumulation**:
- 1 confirmed low-value test (`test_mocking_hell`: 12 mocks, 120 LOC, 2 assertions)
- Potential candidates undiscovered (requires full audit run)
- No systematic process for identifying/removing low-value tests
- Test suite grows without quality gates

**Safety Concerns**:
- Manual deletion risky (potential for breaking changes)
- Revert scripts created ad-hoc (no standardized process)
- No audit trail for deletions
- Constitutional Article III: manual review required (no auto-deletion)

### Success Metrics

**Automation**:
- ✅ V5 audit runs in <5 minutes (full 1,762-test suite)
- ✅ Audit triggers automatically (PR, daily, on-demand)
- ✅ Results viewable in dashboard/report

**Quality**:
- ✅ 15-20% HIGH classification (currently 98% in V5_PARTIAL mode)
- ✅ Runtime cache generated and used (V5_FULL mode)
- ✅ Deletion candidates identified with confidence scores

**Safety**:
- ✅ 100% backup before deletion (git commit, revert script)
- ✅ Manual review required for all deletions (Article III)
- ✅ Rollback possible with single command
- ✅ Audit trail logged to VectorStore (Article IV)

---

## Goals

### Primary Goals

1. **Automate V5 Audit Execution**
   - CLI command for on-demand audits
   - CI/CD integration (GitHub Actions workflow)
   - Scheduled audits (daily/weekly via cron or GitHub Actions)

2. **Safe Deletion Workflow**
   - Identify deletion candidates (threshold: score < 10.0)
   - Generate backup commit before deletion
   - Create revert script automatically
   - Require manual approval before deletion (Article III)
   - Log deletions to VectorStore for institutional memory

3. **Quality Metrics & Reporting**
   - Classification distribution dashboard
   - Trend analysis over time
   - Deletion impact metrics (LOC removed, coverage change)
   - False positive tracking (deleted tests that should have been kept)

### Secondary Goals

4. **Runtime Cache Automation**
   - Generate runtime cache during audit (no separate step)
   - Update cache incrementally (only changed tests)
   - Cache validation (detect stale/corrupt data)

5. **Constitutional Compliance**
   - Article II: 100% test pass before deletion
   - Article III: No auto-deletion (manual review gate)
   - Article IV: Store patterns to VectorStore
   - Audit trail for all quality actions

---

## Personas

### Primary Users

**1. Development Team (Everyday Use)**
- **Need**: Know test quality without manual audit runs
- **Use Case**: PR checks show quality regression warnings
- **Success**: "I see test quality metrics in every PR"

**2. Quality Engineers (Proactive Maintenance)**
- **Need**: Systematically remove low-value tests
- **Use Case**: Weekly audit → identify candidates → review → delete
- **Success**: "Test suite quality improves 5% per month"

**3. CI/CD Pipeline (Automation)**
- **Need**: Block PRs that add low-value tests
- **Use Case**: Pre-merge quality gate (reject score < 8.0)
- **Success**: "No low-value tests merged to main"

### Secondary Users

**4. Architects (Strategic Oversight)**
- **Need**: Track test quality trends over time
- **Use Case**: Quarterly review of quality metrics
- **Success**: "We reduced test suite by 20% without coverage loss"

---

## Acceptance Criteria

### Phase 1: Automation Infrastructure (Must Have)

1. **CLI Command**
   ```bash
   python scripts/test_audit_automation.py --mode audit
   # Expected: Generates report in <5 minutes
   ```

2. **Runtime Cache Generation**
   ```bash
   python scripts/test_audit_automation.py --mode audit
   # Automatically generates .audit/runtime_cache.json
   # Upgrades V5_PARTIAL → V5_FULL mode
   ```

3. **Quality Report Generated**
   ```bash
   cat .audit/test_quality_report.json | jq '.distribution'
   # Expected: {"HIGH": "15-20%", "MEDIUM": "55-60%", "LOW": "20-25%"}
   ```

### Phase 2: Deletion Workflow (Must Have)

4. **Identify Candidates**
   ```bash
   python scripts/test_audit_automation.py --mode identify --threshold 10.0
   # Outputs: .audit/candidates_to_delete.txt
   # Format: file::test_name, score, reason
   ```

5. **Backup Before Deletion**
   ```bash
   python scripts/test_audit_automation.py --mode delete --candidates .audit/candidates.txt
   # Step 1: Creates git commit (backup)
   # Step 2: Generates revert script (revert_TIMESTAMP.sh)
   # Step 3: Prompts for manual approval (Article III)
   ```

6. **Revert Script Functional**
   ```bash
   bash revert_TIMESTAMP.sh
   # Expected: All deleted tests restored in <1 second
   ```

### Phase 3: CI/CD Integration (Should Have)

7. **GitHub Actions Workflow**
   ```yaml
   # .github/workflows/test-quality-audit.yml
   # Runs on: PR, daily schedule
   # Posts comment with quality metrics
   ```

8. **Pre-Merge Quality Gate**
   ```bash
   # PR checks fail if:
   # - New test score < 8.0
   # - Quality distribution regresses >5%
   ```

9. **Audit Trail Logging**
   ```bash
   # All deletions logged to VectorStore
   # Queryable: context.search_memories(["test_deletion"])
   ```

### Phase 4: Metrics & Reporting (Nice to Have)

10. **Quality Dashboard**
    ```bash
    cat .audit/quality_dashboard.html
    # Shows: trend charts, distribution, deletion history
    ```

11. **False Positive Tracking**
    ```bash
    # Track tests deleted then restored
    # Metric: false_positive_rate < 20%
    ```

---

## Test Plan (NECESSARY Pattern Compliance)

### Normal Cases

**N1: Successful Audit Execution**
- **Given**: 1,762 tests in suite, runtime cache exists
- **When**: Run `python scripts/test_audit_automation.py --mode audit`
- **Then**:
  - Report generated in <5 minutes
  - V5_FULL mode active
  - Classification: 15-20% HIGH

**N2: Deletion Candidate Identification**
- **Given**: Audit complete, threshold = 10.0
- **When**: Run `--mode identify --threshold 10.0`
- **Then**:
  - Candidates file created
  - Each entry has score, reason, LOC
  - Sorted by score (lowest first)

**N3: Safe Deletion with Backup**
- **Given**: Candidates identified, manual approval given
- **When**: Run `--mode delete --candidates .audit/candidates.txt`
- **Then**:
  - Git commit created (backup)
  - Revert script generated
  - Tests deleted from files
  - Tests still pass (100%)

### Edge Cases

**E1: No Runtime Cache (First Run)**
- **Given**: `.audit/runtime_cache.json` missing
- **When**: Run `--mode audit`
- **Then**:
  - pytest executed automatically
  - Runtime cache generated
  - Audit continues with V5_FULL mode

**E2: Empty Candidates List**
- **Given**: No tests score below threshold
- **When**: Run `--mode identify --threshold 5.0`
- **Then**:
  - Candidates file created but empty
  - Message: "No deletion candidates found"
  - Exit code 0 (success)

**E3: Test Failures After Deletion**
- **Given**: Deletion candidate removed
- **When**: pytest run shows failures
- **Then**:
  - Deletion aborted
  - Revert script executed automatically
  - Error logged to VectorStore

### Security Cases

**S1: Manual Approval Required (Article III)**
- **Given**: Deletion candidates identified
- **When**: Run `--mode delete` without `--approve` flag
- **Then**:
  - Interactive prompt shown
  - No deletion without explicit "yes"
  - Audit trail logs approval timestamp

**S2: Revert Script Validation**
- **Given**: Revert script generated
- **When**: Run `bash revert_TIMESTAMP.sh`
- **Then**:
  - Git reset to backup commit
  - All deleted tests restored
  - Test suite passes (100%)

**S3: Audit Trail Immutability**
- **Given**: Deletion executed
- **When**: VectorStore queried for deletion history
- **Then**:
  - All deletions logged with timestamp, user, reason
  - Logs immutable (append-only)
  - Constitutional compliance verified

---

## Implementation Notes

### Architecture

```
test_audit_automation.py
├── AuditOrchestrator
│   ├── run_audit() → Generates quality report
│   ├── generate_runtime_cache() → pytest + cache conversion
│   └── validate_results() → Check V5_FULL mode, distribution
│
├── DeletionWorkflow
│   ├── identify_candidates(threshold) → Parse audit results
│   ├── create_backup() → git commit + revert script
│   ├── request_approval() → Interactive prompt (Article III)
│   └── execute_deletion() → Remove tests, verify tests pass
│
└── MetricsReporter
    ├── generate_report() → JSON + HTML dashboard
    ├── log_to_vectorstore() → Store patterns (Article IV)
    └── track_trends() → Compare historical audits
```

### Dependencies

**Existing V5 Components** (Reuse):
- `scripts/test_value_audit_v5.py` - Core auditor
- `scripts/convert_junit_to_cache.py` - Runtime cache generator
- `weights.yaml` - Scoring configuration

**New Components** (Build):
- `scripts/test_audit_automation.py` - Main orchestrator
- `.github/workflows/test-quality-audit.yml` - CI/CD integration
- `scripts/deletion_workflow.py` - Safe deletion manager
- `scripts/quality_dashboard.py` - Metrics reporter

### Configuration

**weights.yaml** (Existing):
```yaml
scoring:
  deletion_threshold: 10.0  # Tests below this score are candidates
  quality_gate_threshold: 8.0  # PR check fails for new tests below this

automation:
  runtime_cache_path: .audit/runtime_cache.json
  audit_report_path: .audit/test_quality_report.json
  candidates_path: .audit/candidates_to_delete.txt

safety:
  require_manual_approval: true  # Article III compliance
  create_backup_commit: true
  generate_revert_script: true
  verify_tests_after_deletion: true  # Article II compliance
```

---

## Non-Functional Requirements

### Performance
- **Audit execution**: <5 minutes for 1,762 tests
- **Runtime cache generation**: <3 minutes (pytest execution)
- **Dashboard rendering**: <2 seconds

### Reliability
- **Test pass rate**: 100% after deletion (Article II)
- **Revert success rate**: 100% (backup always works)
- **False positive rate**: <20% (deleted tests rarely need restoration)

### Maintainability
- **Code reuse**: 80% (leverage existing V5 components)
- **Documentation**: Usage guide + troubleshooting
- **Logging**: All actions logged to VectorStore

### Security
- **Manual approval**: Required for all deletions (Article III)
- **Audit trail**: Immutable deletion history
- **Access control**: Deletion requires git push permissions

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **False Positives** (delete valuable tests) | HIGH | MEDIUM | Manual review required (Article III), revert script always available |
| **Runtime Cache Stale** (wrong scores) | MEDIUM | LOW | Cache validation, incremental updates, timestamp checks |
| **Test Failures After Deletion** | HIGH | LOW | 100% test pass required (Article II), auto-revert on failure |
| **CI/CD Performance** (slow PR checks) | MEDIUM | MEDIUM | Cache runtime data, run only on changed tests |
| **Constitutional Violations** (auto-deletion) | CRITICAL | LOW | Mandatory approval gate, VectorStore logging enforced |

---

## Out of Scope

**Explicitly NOT Included**:
- ❌ Auto-deletion without manual approval (violates Article III)
- ❌ Machine learning for test classification (V5 is rule-based)
- ❌ Test generation to replace deleted tests (separate feature)
- ❌ Integration with external quality tools (SonarQube, CodeClimate)
- ❌ Support for non-pytest test frameworks (unittest, nose)

---

## Open Questions

**For User Approval**:

1. **Deletion Threshold**: Confirm 10.0 as threshold (current: 5.2 found 1 test)
   - Lower threshold (8.0) → More candidates
   - Higher threshold (12.0) → Fewer candidates, higher confidence

2. **Automation Frequency**: How often to run audits?
   - Option A: Every PR (slowest, most thorough)
   - Option B: Daily schedule (balanced)
   - Option C: On-demand only (fastest, manual trigger)

3. **CI/CD Integration Priority**: Include in Phase 1 or defer to Phase 2?
   - Phase 1: Automation + deletion workflow
   - Phase 2: CI/CD + dashboard

4. **Manual Review Process**: Who approves deletions?
   - Option A: Any developer (fastest)
   - Option B: Quality engineer only (safest)
   - Option C: Require 2 approvals (slowest, most thorough)

---

## References

**ADRs**:
- ADR-034: Empirical Test Value Scoring (V5 implementation)
- ADR-033: Value-First Testing Philosophy (quality > quantity)
- ADR-002: 100% Verification (Article II)
- ADR-003: Local Enforcement (Article III)

**V5 Documentation**:
- `V5_HANDOFF_COMPLETE.md` - V5 production delivery (87% pass rate)
- `TEST_AUDIT_V5_PLAN.md` - Original 10-phase plan
- `ADR034_TEST_DELIVERY.md` - Test delivery summary

**Existing Scripts**:
- `scripts/test_value_audit_v5.py` - V5 auditor (514 lines)
- `scripts/convert_junit_to_cache.py` - Runtime cache converter
- `weights.yaml` - Scoring configuration

---

## Timeline Estimate

**Phase 1: Automation Infrastructure** (2 hours)
- CLI command for on-demand audits
- Runtime cache automation
- Quality report generation

**Phase 2: Deletion Workflow** (1.5 hours)
- Candidate identification
- Backup + revert script generation
- Manual approval gate

**Phase 3: CI/CD Integration** (1 hour)
- GitHub Actions workflow
- PR quality checks
- Audit trail logging

**Phase 4: Metrics & Reporting** (2 hours, optional)
- Quality dashboard
- Trend analysis
- False positive tracking

**Total**: 4.5-6.5 hours (depending on scope)

---

## Success Criteria Summary

**Must Have** (Minimum Viable Product):
1. ✅ Automated audit execution (<5 min)
2. ✅ Runtime cache generation (V5_FULL mode)
3. ✅ Deletion candidates identified (threshold: 10.0)
4. ✅ Safe deletion workflow (backup + revert)
5. ✅ Manual approval required (Article III)
6. ✅ 100% test pass after deletion (Article II)

**Should Have** (High Value):
7. ✅ CI/CD integration (GitHub Actions)
8. ✅ Audit trail logging (VectorStore)
9. ✅ Quality metrics dashboard

**Nice to Have** (Future Enhancement):
10. ⏭️ Trend analysis over time
11. ⏭️ False positive tracking

---

**Status**: DRAFT - Awaiting User Approval (Stage 1 Complete)
**Next Step**: User reviews specification, approves/revises, then proceeds to Stage 2 (TDD Execution)

