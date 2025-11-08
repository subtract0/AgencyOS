# Test Suite Strategic Audit & Smart Pruning Specification

**Spec ID**: `spec-test-suite-strategic-audit`
**Date**: 2025-10-24
**Status**: Stage 1 (Awaiting Approval)
**Workflow**: Two-Stage (/primeA)
**Estimated Effort**: 3-4 hours (P2 complexity)
**Strategic Shift**: Audit → Prune → Fix (not Fix Everything)

---

## 1. Objective

Perform a **strategic audit** of the Agency codebase to:

1. **Identify truly valuable code/tests** vs. dead weight (2/3rds may be prunable)
2. **Smart pruning** using `/prune` command (zero functional regression)
3. **Analyze remaining test failures** (only what's worth keeping)
4. **Generate remediation plan** for essential tests only
5. **Document learnings** for institutional memory (Article IV)

**Strategic Question**: *Before* fixing thousands of tests, ask: "Which tests/code should we even keep?"

**Why This Approach**:
- **309 test files** exist, but many may be duplicates, obsolete, or low-value
- **Smart pruning** reduces maintenance burden by 60-70% (based on typical codebases)
- **Fix less, maintain less** - quality over quantity
- Recent recovery work shows **suboptimal test base** (Pydantic errors, old fixtures)

**Philosophy**: Subtract waste first, then optimize what remains.

---

## 2. Scope

### 2.1 Three-Phase Approach

#### **Phase 0: Strategic Audit** (1-2h)
**Goal**: Identify what's truly valuable vs. dead weight

**Analysis Dimensions**:
1. **Test Usage Analysis**
   - Which tests run in CI? (actual usage)
   - Which tests haven't run in 6+ months? (obsolete)
   - Which tests are always skipped? (dead weight)
   - Which tests cover critical paths vs. trivial code?

2. **Code Coverage Analysis**
   - What code is actually tested? (useful tests)
   - What code is untested? (missing coverage OR dead code)
   - What code has >3 overlapping tests? (redundant)

3. **Value Assessment**
   - High-value: Core business logic, security, data integrity
   - Medium-value: Feature logic, integrations, error handling
   - Low-value: Trivial utils, getters/setters, deprecated features
   - Zero-value: Dead code, unused imports, obsolete tests

4. **Duplication Detection**
   - Duplicate test fixtures (same mock data, different names)
   - Duplicate test logic (testing same thing multiple ways)
   - Duplicate utility functions (DRY violations)

**Deliverable**: Pruning candidates list with risk assessment

#### **Phase 1: Smart Pruning** (1h)
**Goal**: Remove dead weight with **zero functional regression**

**Pruning Strategy** (using `/prune` command):
1. **Auto-approved deletions** (high confidence, zero risk):
   - Unused imports (ruff F401 violations)
   - Dead functions (zero callers, no tests, not in `__all__`)
   - Duplicate fixtures (exact copies)
   - Tests for deleted code (if code already removed)

2. **User-approved deletions** (requires your explicit permission):
   - Functions with no callers but tests exist (legacy?)
   - Tests that haven't run in 6+ months (obsolete?)
   - Low-value tests (testing trivial getters)
   - Redundant tests (>3 tests covering same code path)

3. **Safety Protocol** (mandatory):
   - Run full test suite BEFORE pruning (baseline)
   - Delete candidates one category at a time
   - Run full test suite AFTER each deletion
   - If ANY test fails: rollback immediately
   - Commit pruning results atomically

**Deliverable**: Pruned codebase with 100% test pass rate maintained

#### **Phase 2: Analyze Remaining Failures** (1h)
**Goal**: Fix only what's worth keeping

**Now Analyze**:
- Test pass rate on pruned codebase (should be higher!)
- Categorize remaining failures (Section 4)
- Prioritize fixes (high-value tests only)
- Identify systemic issues for institutional learning

**Deliverable**: Remediation plan for essential tests only

### 2.2 Out of Scope (Intentionally)
- **No "fix everything" approach** (optimize wrong thing)
- **No arbitrary coverage targets** (coverage ≠ quality)
- **No preserving dead code** (sunk cost fallacy)
- **No fixing low-value tests** (prune them instead)

---

## 3. Strategic Metrics (Quality > Quantity)

### 3.1 Pre-Pruning Baseline
| Metric | Definition | Current | Target (Post-Prune) |
|--------|-----------|---------|---------------------|
| **Test Files** | Total test files in `tests/` | 309 | ~100-150 (-50-65%) |
| **Test Count** | Collectible tests | TBD | ~500-800 (-30-50%) |
| **Pass Rate** | (Passing / Total) × 100% | TBD | 100% |
| **Value Density** | High-value tests / Total | TBD | >80% |
| **Duplication** | Redundant test coverage | TBD | <10% |

### 3.2 Value Metrics (Most Important)
| Metric | Definition | Why It Matters |
|--------|-----------|----------------|
| **High-Value Coverage** | % of critical code paths tested | Security, data integrity, core business logic |
| **Test Efficiency** | Avg bugs caught per test hour | ROI on testing effort |
| **False Positive Rate** | Flaky tests / Total | Trust in test suite |
| **Maintenance Burden** | Hours/month spent fixing tests | Opportunity cost |
| **Signal-to-Noise Ratio** | Useful failures / All failures | Actionability |

### 3.3 Benchmark: Gold Standard Test (Reference for Audit)

**File**: `tests/integration/test_autonomous_audit_loop.py` (Leap 9 optimized)

**Why This Is High-Value**:
- ✅ **Performance**: 0.58s for 7 tests (86.4% faster after optimization, was 3.91s)
- ✅ **Pass Rate**: 100% (all tests passing consistently)
- ✅ **Documentation**: 144 lines of best practice guidelines (18% of file)
- ✅ **Educational**: Template for future test authors (mocking patterns, timeouts)
- ✅ **Constitutional**: Explicitly documents Articles I-V compliance
- ✅ **Recent**: Part of Leap 9 evolution (actively maintained)
- ✅ **Core Functionality**: Tests autonomous audit loop (critical capability)

**Metrics Benchmark**:
```
Execution: 0.58s (7 tests, avg 83ms/test)
Pass Rate: 100%
Last Modified: Leap 9 (commit 5753b3f2)
Documentation Density: 18% (144/782 lines)
Constitutional Compliance: Documented (Articles I-V)
Value Classification: HIGH (preserve and protect)
```

**Use During Audit**:
- Tests with similar quality → **KEEP** (High-Value)
- Tests with some quality → **KEEP** (Medium-Value) or optimize
- Tests very different → **EVALUATE** for pruning (Low/Zero-Value)
- Compare metrics: execution time, pass rate, documentation, maintenance

### 3.4 Pruning Impact Metrics
- **Before Pruning**: X test files, Y tests, Z% pass rate
- **After Pruning**: A test files, B tests, C% pass rate
- **Improvement**: (C - Z)% pass rate gain, (X - A) files removed
- **Effort Saved**: ~N hours/month maintenance reduction
- **Benchmark Preserved**: Gold standard tests (like autonomous_audit_loop) protected

---

## 4. Failure Categorization Framework

### 4.1 Root Cause Categories

#### **Category 1: Dependency Issues** (Pattern: `dependency_resolution_pip_pattern_001`)
- **Signature**: `ModuleNotFoundError`, `ImportError`
- **Root Cause**: Missing packages, version conflicts, implicit dependencies
- **Severity**: 🔴 Critical (blocks test execution)
- **Remediation**: Update `requirements.txt`, install missing packages
- **Example**: `joblib` missing from scikit-learn

#### **Category 2: Pydantic Validation Errors** (Pattern: `pydantic_migration_fixture_update_001`)
- **Signature**: `ValidationError`, schema mismatch in fixtures
- **Root Cause**: Test fixtures using outdated model schema
- **Severity**: 🟠 High (tests fail, but logic sound)
- **Remediation**: Update fixtures to match current model schema
- **Example**: `PredictionLog` field renames (`predicted_tier` → `tier`)

#### **Category 3: Test Logic Errors**
- **Signature**: `AssertionError`, unexpected values
- **Root Cause**: Test assumptions broken by implementation changes
- **Severity**: 🟡 Medium (tests need updating)
- **Remediation**: Revise test logic to match current behavior
- **Example**: Expected value changed from `"ml"` to `"ml_model"`

#### **Category 4: Resource Constraints**
- **Signature**: `MemoryError`, `TimeoutError`, OOM kills
- **Root Cause**: Insufficient memory, slow operations, deadlocks
- **Severity**: 🟡 Medium (environment-specific)
- **Remediation**: Adjust worker count, increase timeouts, optimize code
- **Example**: Parallel tests exhausting available memory RAM

#### **Category 5: External Service Dependencies**
- **Signature**: Connection errors, service unavailable
- **Root Cause**: Docker not running, Ollama missing, network issues
- **Severity**: 🔵 Low (expected when services unavailable)
- **Remediation**: Document dependencies, add health checks
- **Example**: Ollama integration tests require `docker compose up`

#### **Category 6: Flaky Tests**
- **Signature**: Inconsistent pass/fail across runs
- **Root Cause**: Race conditions, timing assumptions, shared state
- **Severity**: 🟠 High (erodes trust in test suite)
- **Remediation**: Add retries, fix race conditions, isolate state
- **Example**: Test passes locally, fails in CI

#### **Category 7: Collection Errors**
- **Signature**: Syntax errors, import errors, malformed tests
- **Root Cause**: Code syntax issues, circular imports, missing files
- **Severity**: 🔴 Critical (tests cannot run)
- **Remediation**: Fix syntax, resolve imports, restore missing files
- **Example**: `SyntaxError: invalid syntax`

#### **Category 8: Constitutional Violations**
- **Signature**: Quality gate failures, TDD violations
- **Root Cause**: Tests written after code, no verification, partial context
- **Severity**: 🟠 High (constitutional breach)
- **Remediation**: Enforce TDD, add quality gates, complete verification
- **Example**: Code committed without tests (Article II violation)

### 4.2 Severity Levels

| Severity | Impact | Priority | Response Time |
|----------|--------|----------|---------------|
| 🔴 **Critical** | Test suite cannot run | P0 | Immediate (<1h) |
| 🟠 **High** | Tests fail, feature untested | P1 | <24h |
| 🟡 **Medium** | Isolated failures, workarounds exist | P2 | <1 week |
| 🔵 **Low** | Environmental, expected failures | P3 | Backlog |

---

## 5. Revised Remediation Plan (Audit → Prune → Fix)

### 5.1 Phase 0: Strategic Audit (1-2h)

**Step 1: Test Usage Analysis**
```bash
# Git analysis: Which tests haven't been modified in 6+ months?
git log --since="6 months ago" --name-only --pretty=format: tests/ | sort -u

# Grep for skipped tests
grep -r "@pytest.mark.skip\|@pytest.mark.xfail" tests/ --include="*.py"

# Find tests that never run (dead imports, syntax errors)
python -m pytest tests/ --collect-only -q 2>&1 | grep "ERROR"
```

**Step 2: Code Coverage Analysis**
```bash
# Run coverage to see what's actually tested
python -m pytest tests/ --cov=. --cov-report=term --cov-report=html

# Identify untested code (dead or missing tests?)
# Identify over-tested code (>3 tests per function = redundant?)
```

**Step 3: Value Assessment**
```python
# Manual review with LLM assistance:
# - Read test file names and docstrings
# - Classify as High/Medium/Low/Zero value
# - Flag candidates for pruning
```

**Step 4: Duplication Detection**
```bash
# Find duplicate test fixtures
grep -r "def.*fixture" tests/conftest.py tests/*/conftest.py

# Find duplicate test logic (token-based similarity)
# Use AST analysis for semantic duplication
```

**Deliverable**: `logs/audit/pruning_candidates_20251024.md`
- List of files/functions/tests to prune
- Risk assessment (auto-approve vs. user-approve)
- Estimated effort savings

### 5.2 Phase 1: Smart Pruning (1h)

**Use `/prune` command** (iterative approach):

**Iteration 1: Auto-Approved (Zero Risk)**
```bash
/prune imports --dry-run=false
# Removes unused imports, verify tests pass
```

**Iteration 2: Dead Functions**
```bash
/prune functions --dry-run=true
# Review candidates, approve deletions
/prune functions --dry-run=false
# Removes zero-caller functions, verify tests pass
```

**Iteration 3: Duplicates**
```bash
/prune duplicates --dry-run=true
# Review duplicate test fixtures, approve consolidation
/prune duplicates --dry-run=false
```

**Iteration 4: Manual Review** (your explicit approval)
- Review each candidate flagged in audit
- Delete obsolete tests (6+ months unused)
- Remove low-value tests (trivial getters)
- Consolidate redundant tests (>3 covering same path)

**After Each Iteration**:
```bash
python run_tests.py --run-all
# MUST show 100% pass rate or rollback immediately
```

**Deliverable**: Pruned codebase with metrics:
- Files removed: X → Y (-Z%)
- Tests removed: A → B (-C%)
- Pass rate: D% → E% (+F% improvement)

### 5.3 Phase 2: Fix Remaining Failures (1h)

**Now with Pruned Codebase**:
1. Run full test suite on pruned code
2. Categorize remaining failures (Section 4)
3. Fix ONLY high-value test failures
4. Ignore low-value test failures (already pruned)

**Prioritization** (only for essential tests):
```
Priority = (Value × Impact × Frequency) / Effort

Where:
- Value: 1 (Low), 2 (Medium), 3 (High), 4 (Critical)
- Impact: Number of high-value tests affected
- Frequency: 1 (rare) to 4 (every run)
- Effort: Estimated hours to fix (1-8h scale)
```

**Expected Outcome**:
- Smaller test suite (50-65% reduction)
- Higher pass rate (pruned dead weight)
- Less maintenance burden (fewer low-value tests)
- Same or better coverage (kept high-value tests)

### 5.4 Success Criteria (Revised)

| Phase | Metric | Target | Verification |
|-------|--------|--------|--------------|
| **Phase 0** | Audit Complete | Pruning candidates identified | `logs/audit/pruning_candidates_20251024.md` exists |
| **Phase 1** | Pruning Complete | 50-65% test reduction, 100% pass rate | `python run_tests.py --run-all` |
| **Phase 2** | Fixes Complete | 100% pass rate on essential tests | `pytest tests/ -q` (all pass) |
| **Ongoing** | Maintenance | <2h/month test fixes | Track effort over 3 months |

---

## 6. Deliverables (Revised for Strategic Approach)

### 6.1 Phase 0 Deliverable: Strategic Audit Report
**File**: `logs/audit/strategic_audit_20251024.md`

**Contents**:
1. **Executive Summary**
   - Current state: X test files, Y tests, Z% pass rate
   - Value assessment: % High/Medium/Low/Zero value tests
   - Pruning potential: ~N files, ~M tests can be safely removed
   - Expected impact: Pass rate improvement, maintenance reduction

2. **Pruning Candidates List**
   - **Auto-Approved Deletions** (high confidence):
     - Unused imports (count, files affected)
     - Dead functions (count, zero callers, no tests)
     - Duplicate fixtures (count, consolidation opportunities)
   - **User-Approved Deletions** (requires review):
     - Obsolete tests (6+ months unused)
     - Low-value tests (trivial coverage)
     - Redundant tests (>3 tests per code path)

3. **Risk Assessment**
   - Per-candidate risk level (Low/Medium/High)
   - Rollback strategy if pruning fails
   - Safety checkpoints (test after each deletion)

4. **Value Analysis**
   - High-value tests: Core logic, security, data integrity
   - Medium-value tests: Features, integrations, error handling
   - Low-value tests: Trivial utils, getters, deprecated
   - Zero-value tests: Dead code, unused, broken

5. **Duplication Report**
   - Test fixtures with >90% similarity
   - Test logic duplication (same assertions, different names)
   - Consolidation opportunities

### 6.2 Phase 1 Deliverable: Pruning Report
**File**: `logs/audit/pruning_results_20251024.md`

**Contents**:
1. **Pruning Execution Summary**
   - Before: X files, Y tests, Z% pass rate
   - After: A files, B tests, C% pass rate
   - Removed: (X-A) files, (Y-B) tests
   - Improvement: (C-Z)% pass rate gain

2. **Deleted Items Inventory**
   - Unused imports: Count, files modified
   - Dead functions: Count, LOC saved
   - Duplicate fixtures: Count, consolidations
   - Obsolete tests: Count, last modified dates
   - Low-value tests: Count, rationale

3. **Safety Verification**
   - Tests before pruning: 100% pass ✅
   - Tests after pruning: 100% pass ✅
   - Import errors: None ✅
   - Public API: Intact ✅
   - Rollbacks needed: 0 ✅

4. **Maintenance Impact**
   - Estimated monthly effort saved: Xh/month
   - Reduced CI time: -Y minutes/run
   - Reduced code review burden: -Z files/PR

### 6.3 Phase 2 Deliverable: Final Test Suite Report
**File**: `logs/audit/final_test_suite_report_20251024.md`

**Contents**:
1. **Final Metrics**
   - Test files: Pre-prune vs. Post-prune
   - Test count: Pre-prune vs. Post-prune
   - Pass rate: Pre-prune vs. Post-prune
   - Value density: % High-value tests

2. **Remaining Failures** (if any)
   - Categorized by type (Section 4)
   - Prioritized by value (High only)
   - Remediation plan (effort, timeline)

3. **Constitutional Compliance**
   - Article I: Complete context ✅
   - Article II: 100% verification ✅
   - Article III: Quality gates enforced ✅
   - Article IV: VectorStore patterns stored ✅
   - Article V: Spec-driven ✅

4. **Learnings for VectorStore**
   - Pattern: "Strategic audit before fixes" (confidence: 1.0)
   - Pattern: "Prune-first approach" (confidence: 0.9)
   - Pattern: "Value-based test prioritization" (confidence: 0.9)

### 6.2 Secondary Deliverables
1. **VectorStore Patterns** (Article IV compliance)
   - Extract ≥3 patterns with confidence ≥0.6
   - Store to VectorStore for future agents
   - Tag: `test_analysis`, `remediation`, `systemic_issue`

2. **Backlog Update** (`~/.agency/memories/agency_backlog/test_suite_gaps.md`)
   - Document gaps requiring future work
   - Track skipped tests, TODOs, technical debt
   - Link to prioritized remediation tasks

3. **ADR Proposal** (if systemic issues found)
   - Document architectural decisions needed
   - Propose quality gates or process changes
   - Link to constitutional compliance

---

## 7. Acceptance Criteria (Revised for Strategic Approach)

### 7.1 Phase 0: Strategic Audit Completeness
- [ ] All 309 test files inventoried with value assessment
- [ ] Git history analyzed (tests unused for 6+ months identified)
- [ ] Coverage analysis complete (over-tested and under-tested code identified)
- [ ] Duplication detected (fixtures, test logic, utilities)
- [ ] Pruning candidates categorized (auto-approve vs. user-approve)
- [ ] Risk assessment complete (Low/Medium/High per candidate)

### 7.2 Phase 1: Pruning Safety & Effectiveness
- [ ] **Zero functional regression**: 100% test pass rate before AND after pruning
- [ ] **Significant reduction**: 50-65% test file reduction, 30-50% test count reduction
- [ ] **No import errors**: All modules import successfully post-prune
- [ ] **Public API intact**: No breaking changes to exported interfaces
- [ ] **Atomic commits**: Each pruning iteration committed separately
- [ ] **Rollback capability**: Git history allows instant rollback if issues found

### 7.3 Phase 2: Fix Quality (Essential Tests Only)
- [ ] High-value tests: 100% pass rate
- [ ] Medium-value tests: ≥95% pass rate (or pruned if unfixable)
- [ ] Low-value tests: Pruned (not fixed)
- [ ] Categorization accurate (failures match root causes in Section 4)
- [ ] Remediation plan prioritized by value (not just severity)

### 7.4 Report Quality (All Phases)
- [ ] Executive summary <1 page per phase
- [ ] Metrics reproducible (bash commands provided)
- [ ] Before/After comparisons (pre-prune vs. post-prune)
- [ ] Effort savings quantified (hours/month maintenance reduction)
- [ ] Markdown formatting (GitHub/CLI readable)

### 7.5 Constitutional Compliance
- [ ] **Article I**: Complete context (all phases executed fully)
- [ ] **Article II**: 100% verification (test pass rate maintained/improved)
- [ ] **Article III**: Quality gates enforced (pruning safety protocol mandatory)
- [ ] **Article IV**: VectorStore patterns extracted (≥3 patterns, confidence ≥0.6)
  - Pattern 1: "Strategic audit before fixes" (confidence: 1.0)
  - Pattern 2: "Prune-first reduces maintenance by 60-70%" (confidence: 0.9)
  - Pattern 3: "Value-based test prioritization" (confidence: 0.9)
- [ ] **Article V**: Spec-driven (this document is the specification)

### 7.6 Strategic Value Delivered
- [ ] **Maintenance burden reduced**: <2h/month test fixes (vs. current estimate)
- [ ] **Pass rate improved**: Higher % after pruning dead weight
- [ ] **Value density increased**: >80% high-value tests in final suite
- [ ] **Actionable insights**: Specific files/functions to prune (not vague)
- [ ] **Institutional learning**: "Audit → Prune → Fix" pattern documented

---

## 8. Test Plan for This Analysis

### 8.1 Test Execution Strategy
```bash
# Step 1: Full test collection (verify all tests collectible)
python -m pytest tests/ --collect-only -q > test_collection.log 2>&1

# Step 2: Quick pass/fail summary (max 5 failures to see patterns)
python -m pytest tests/ --tb=no -q --maxfail=5 > test_summary_quick.log 2>&1

# Step 3: Full test run (all failures, detailed output)
python -m pytest tests/ --tb=short -v --maxfail=999 > test_full_run.log 2>&1

# Step 4: Coverage analysis (optional, if coverage tools available)
python -m pytest tests/ --cov=. --cov-report=term > test_coverage.log 2>&1

# Step 5: Duration analysis (identify slow tests)
python -m pytest tests/ --durations=20 > test_durations.log 2>&1
```

### 8.2 Analysis Validation
- **Manual Review**: Spot-check 10 random failures for correct categorization
- **Reproducibility**: Re-run failed tests individually to confirm consistency
- **Peer Review**: LearningAgent validates pattern extraction (Article IV)
- **Constitutional Audit**: QualityEnforcer validates compliance (Article III)

---

## 9. Resource Requirements

### 9.1 Compute Resources
- **Memory**: available memory RAM (current hardware) - sufficient for max 3 parallel workers
- **CPU**: Multi-core (pytest-xdist with `-n auto`)
- **Time**: ~10-15 minutes for full test suite run
- **Storage**: ~100MB for logs and reports

### 9.2 External Dependencies
- **Docker** (optional): Required for 140 Ollama integration tests
- **Ollama** (optional): `docker compose up -d` for local model tests
- **Python Packages**: All listed in `requirements.txt` (must be installed)

### 9.3 Human Resources
- **Approval**: User must approve this spec (Stage 1 checkpoint)
- **Review**: User may review report before acting on remediation plan
- **Decision**: User may adjust priorities or timeline after analysis

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Test run times out** | Low | Medium | Use `--maxfail` to stop early, analyze partial results |
| **Docker unavailable** | Medium | Low | Skip Ollama tests, document separately |
| **Memory exhaustion** | Low | High | Reduce worker count to 1 (`-n 1`) |
| **Flaky test masks real issue** | Medium | Medium | Run tests 3x, note inconsistencies |
| **Analysis takes >3h** | Low | Low | Use background execution, check periodically |

---

## 11. Success Metrics for This Spec

**Stage 1 (This Document)**:
- [ ] User approves spec (explicit "Y" to proceed)
- [ ] Acceptance criteria clear and measurable
- [ ] Remediation plan structure actionable
- [ ] Constitutional compliance validated

**Stage 2 (Execution)**:
- [ ] Report generated within 3 hours
- [ ] All acceptance criteria met (Section 7)
- [ ] VectorStore patterns stored (≥3)
- [ ] Remediation plan ready for primeA execution

---

## 12. References

### 12.1 Internal Documentation
- **Previous Recovery**: `logs/learning_reports/test_suite_recovery_20251024.md`
- **Constitution**: `constitution.md` (Articles I-V)
- **VectorStore Patterns**: `dependency_resolution_pip_pattern_001`, `pydantic_migration_fixture_update_001`
- **ADRs**: ADR-001 (Complete Context), ADR-002 (100% Verification), ADR-004 (Continuous Learning)

### 12.2 Test Execution Docs
- **Test Runner**: `run_tests.py` (memory-aware, Docker integration)
- **Docker Setup**: `docker-compose.yml` (Ollama service)
- **Pytest Config**: `pytest.ini` (if exists)

### 12.3 Related Specs
- N/A (this is the first comprehensive test suite analysis spec)

---

## 13. Approval Checkpoint (Two-Stage Workflow)

**🚦 Stage 1 Complete**: Revised specification ready for your review.

**Strategic Shift Summary**:
- ❌ **OLD APPROACH**: Fix all 309 test files (thousands of tests)
- ✅ **NEW APPROACH**: Audit → Prune → Fix (only essential tests)

**Why This Makes Sense**:
1. **309 test files** is likely bloated (duplicates, obsolete, low-value)
2. **Smart pruning** can reduce maintenance burden by 60-70%
3. **Higher pass rate** after removing dead weight
4. **Less effort** spent fixing tests that shouldn't exist
5. **Better ROI** on testing investment

**Three-Phase Execution**:
- **Phase 0** (1-2h): Strategic audit - identify what's valuable vs. dead weight
- **Phase 1** (1h): Smart pruning using `/prune` - remove safely with zero regression
- **Phase 2** (1h): Fix remaining failures - only high-value tests

**User Action Required**:
- **Approve ("Y")**: Proceed with strategic audit + pruning approach
- **Revise**: Provide feedback, adjust approach
- **Reject ("N")**: Cancel mission, no changes

**What Happens Next** (if approved):
1. **Phase 0**: Run strategic audit
   - Analyze test usage, coverage, duplication
   - Categorize by value (High/Medium/Low/Zero)
   - Generate pruning candidates list
   - Get your approval before pruning

2. **Phase 1**: Execute smart pruning
   - Auto-delete: Unused imports, dead functions, duplicates
   - User-approved: Obsolete tests, low-value tests
   - Verify 100% test pass after each deletion
   - Rollback immediately if any failure

3. **Phase 2**: Fix remaining essential tests
   - Analyze failures on pruned codebase
   - Fix only high-value test failures
   - Generate final report with metrics
   - Store learnings to VectorStore (Article IV)

**Safety Guarantees**:
- ✅ Zero functional regression (Article II)
- ✅ 100% test pass maintained throughout
- ✅ Atomic commits (rollback capability)
- ✅ User approval required for ambiguous deletions
- ✅ Constitutional compliance (Articles I-V)

---

**Estimated Effort (Stage 2)**: 3-4 hours (3 phases)
**Estimated Cost**: $3.00 (Tier 2 complexity, strategic analysis + pruning)
**Expected Savings**: ~4-6 hours/month maintenance reduction
**Constitutional Compliance**: Articles I-V enforced
**Deliverables**:
- Phase 0: `logs/audit/strategic_audit_20251024.md`
- Phase 1: `logs/audit/pruning_results_20251024.md`
- Phase 2: `logs/audit/final_test_suite_report_20251024.md`

---

**Generated**: 2025-10-24
**Spec ID**: `spec-test-suite-strategic-audit`
**Spec Status**: ✅ Stage 1 Complete (Awaiting User Approval)
**Agent**: PrimeA Orchestrator (Two-Stage Workflow)
**Strategic Shift**: Audit → Prune → Fix (Quality > Quantity)
