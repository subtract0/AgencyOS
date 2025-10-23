# ADR-033: Value-First Testing Philosophy

**Status**: Accepted
**Date**: 2025-10-23
**Deciders**: @am
**Constitutional Authority**: Article VII (Amendment 2025-10-23)

---

## Context

After running marathon test audit V4 on 1,200 tests, we discovered a fundamental problem:
- **6,554 tests** in the codebase (not 5,408 as thought)
- **162,177 lines** of test code
- V4 wanted to ADD 2,000+ more tests (to "fix gaps")
- **Result**: 8,000+ tests, 30+ minute CI/CD, high maintenance burden

**The Real Problem**: We're optimizing for the WRONG metric.
- ❌ **Wrong goal**: Comprehensive coverage (NECESSARY pattern: 9 categories)
- ✅ **Right goal**: High-value tests that catch REAL bugs

**Key Insight**: You can have 100% confidence with 2,500 well-designed tests. You CANNOT have 100% confidence with 6,554 poorly-designed tests.

---

## Decision

**We adopt VALUE-FIRST TESTING as Constitutional Law (Article VII):**

### Core Principle
**Quality > Quantity. Integration > Unit. Behavior > Implementation.**

### Target State
- **2,000-3,000 HIGH-VALUE tests** (down from 6,554)
- **70% integration, 30% unit** (proper test pyramid)
- **<15 minute CI/CD** (down from 30+)
- **>0.5 bugs detected per test per year**

### Test Value Scoring
```python
test_value = (
    bug_detection_score * 10 +      # 0-10: Real bugs caught
    critical_path_score * 5 +        # 0-10: Tests core logic
    integration_score * 3 -          # 0-10: Tests real components
    runtime_penalty * 0.1 -          # Penalty for slow tests
    maintenance_burden * 2           # Penalty for fragile tests
)

# Categories:
# HIGH (>20): KEEP - Integration, critical path, security
# MEDIUM (10-20): REVIEW - Consolidate or improve
# LOW (<10): DELETE - Mocking hell, implementation details
```

### Test Classification

**DELETE (40% of suite)**:
- Mocking hell (>10 mocks, <3 assertions)
- Implementation detail tests (test HOW, not WHAT)
- Redundant tests (same behavior 5 ways)
- "Just in case" tests (never happen scenarios)

**KEEP (30% of suite)**:
- Integration tests (real components)
- E2E tests (complete workflows)
- Critical path tests (core business logic)
- Security tests (auth, injection, XSS)

**CONSOLIDATE (30% of suite)**:
- Parameterize similar tests (20 → 1)
- Merge overlapping coverage
- Convert to property-based tests

---

## Rationale

### Why This Is Better

**Before (Coverage-First)**:
- 6,554 tests
- Many test implementation details (break on refactor)
- Mocking hell (mock everything, test nothing)
- 30+ minute CI/CD
- 100+ tests break per refactor

**After (Value-First)**:
- 2,500 tests (62% reduction)
- Test behavior, not implementation
- Real components, not mocks
- 10-15 minute CI/CD (3x faster)
- 20 tests break per refactor (5x less maintenance)

### The Testing Pyramid

**Current State (Inverted - BAD)**:
```
        /\
       /UI\         ← 100 e2e tests
      /    \
     /Integ.\       ← 500 integration tests
    /        \
   /   Unit   \     ← 5,954 unit tests (TOO MANY!)
  /____________\
```

**Target State (Proper - GOOD)**:
```
  /\
 /UI\              ← 100 e2e tests
/____\
/Integ\            ← 1,500 integration tests (INCREASE!)
/______\
/ Unit  \          ← 900 unit tests (REDUCE 85%!)
/________\
```

### Economic Impact

**Time Investment**:
- V4 approach (add 2,000 tests): 150+ hours
- Pruning approach (delete 4,000 tests): 14 hours

**Maintenance Savings** (annual):
- Fewer tests breaking on refactor: ~200 hours/year saved
- Faster CI/CD feedback: ~100 hours/year saved
- **Total**: ~300 hours/year saved (~$30k-60k)

**Bug Detection** (improved):
- More integration tests = catch more real bugs
- Less implementation testing = fewer false failures
- **Result**: BETTER bug detection with FEWER tests

---

## Consequences

### Positive

1. **Faster Development**:
   - 10-15 min CI/CD (down from 30+)
   - Less time fixing broken tests after refactors
   - Faster feedback loops

2. **Better Bug Detection**:
   - Integration tests catch real bugs
   - Security tests catch vulnerabilities
   - E2E tests catch workflow bugs

3. **Lower Maintenance**:
   - 20 tests break per refactor (not 100+)
   - Less time reviewing test failures
   - Easier to understand test suite

4. **Constitutional Enforcement**:
   - Article VII mandates value-first testing
   - Test generators must create high-value tests
   - Pre-commit hooks reject low-value tests

### Negative

1. **Initial Effort**:
   - 14 hours to audit + delete + consolidate
   - Manual review of deletion candidates
   - Some risk of over-deleting (mitigated by manual review)

2. **Cultural Shift**:
   - Developers used to "more tests = better"
   - Need to train on "value > coverage"
   - May resist deleting their tests

3. **Measurement Complexity**:
   - Value scoring is heuristic-based
   - Not as simple as "100% coverage"
   - Need new metrics (bug detection rate, test suite health)

### Mitigation Strategies

**For Cultural Shift**:
- Make it constitutional (Article VII)
- Show economic benefits (300 hours/year saved)
- Demonstrate improved bug detection

**For Measurement Complexity**:
- Automate value scoring (`test_value_audit.py`)
- Track test suite health score (>80/100 target)
- Monitor bug detection rate (>0.5 bugs/test/year)

**For Over-Deletion Risk**:
- Manual review of top 100 deletion candidates
- Run full test suite after deletions (verify coverage maintained)
- Rollback if critical tests deleted

---

## Implementation

### Tools Created

1. **`scripts/test_value_audit.py`**: Score all tests by value
   - Generates deletion candidates
   - Identifies consolidation opportunities
   - Produces high-value test list

2. **Constitution Article VII**: Value-First Testing Philosophy
   - Mandates 2,000-3,000 high-value tests
   - Defines test classification (KEEP/DELETE/CONSOLIDATE)
   - Enforcement mechanisms (pre-commit hooks)

3. **Test Suite Health Metrics**:
   ```python
   health_score = (
       (integration_test_pct * 0.3) +
       (high_value_test_pct * 0.4) +
       (100 - ci_time_minutes * 2) * 0.2 +
       (bug_detection_rate * 20) * 0.1
   )
   # Target: >80/100
   ```

### Migration Path

**Phase 1: Audit** (Week 1):
```bash
python scripts/test_value_audit.py
# Generates: candidates_to_delete.txt, candidates_to_consolidate.txt
```

**Phase 2: Delete** (Week 2):
- Review top 100 deletion candidates
- Batch delete low-value tests (score <5)
- Verify test suite passes

**Phase 3: Consolidate** (Week 3):
- Parameterize redundant tests
- Merge overlapping tests
- Convert to property-based tests

**Phase 4: Rebalance** (Week 4):
- Add integration tests for critical paths
- Remove unit tests covered by integration
- Achieve 70% integration, 30% unit ratio

### Success Metrics

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| **Test Count** | 6,554 | 2,000-3,000 | Direct count |
| **CI/CD Time** | 30+ min | <15 min | CI logs |
| **Test Pyramid** | Inverted | 70% int, 30% unit | Category count |
| **High-Value %** | ~20% | >50% | Value scores >20 |
| **Low-Value %** | ~40% | <10% | Value scores <10 |
| **Health Score** | ~45/100 | >80/100 | Formula calculation |
| **Bug Detection** | 0.2/test/yr | >0.5/test/yr | Production incident tracking |
| **Maintenance** | 100 tests/refactor | <20 tests/refactor | Git history |

---

## Alternatives Considered

### Alternative 1: V4 Approach (Add 2,000 Tests)
**Description**: Follow V4's roadmap to add Edge, Spec, Cascading coverage to 892 P1 tests.

**Pros**:
- Achieves "comprehensive coverage"
- Satisfies NECESSARY pattern (9 categories)

**Cons**:
- 8,000+ total tests (unsustainable)
- 150+ hours effort
- Slower CI/CD (40+ minutes)
- Higher maintenance burden

**Decision**: REJECTED - Optimizes for wrong metric (coverage, not value)

### Alternative 2: Adjust V4 Threshold
**Description**: Change V4 to require 2+ missing core categories for P1 (instead of 1+).

**Pros**:
- Lower P1 count (~300 tests instead of 892)
- Less overwhelming to implement

**Cons**:
- Still adds tests (doesn't solve bloat problem)
- Still focuses on coverage, not value
- Doesn't address mocking hell, redundancy

**Decision**: REJECTED - Treats symptom, not root cause

### Alternative 3: Status Quo (Keep 6,554 Tests)
**Description**: Do nothing, live with current test suite.

**Pros**:
- Zero effort
- No risk of over-deletion

**Cons**:
- Slow CI/CD continues (30+ minutes)
- High maintenance continues (100+ tests/refactor)
- Many low-value tests waste resources

**Decision**: REJECTED - Technical debt compounds over time

---

## Related ADRs

- **ADR-026**: Test-Driven Autonomy (TDD workflow)
- **ADR-002**: 100% Verification and Stability (quality standards)
- **ADR-023**: Memory-Aware Test Execution (hardware constraints)

**Relationship**: ADR-033 complements ADR-026. ADR-026 defines HOW to write tests (TDD: tests FIRST). ADR-033 defines WHICH tests to write (VALUE-FIRST: integration > unit).

---

## References

- Constitution Article VII: Value-First Testing Philosophy
- `scripts/test_value_audit.py`: Test value scoring implementation
- `TEST_PRUNING_PROPOSAL.md`: Detailed rationale and examples
- `V4_1200_TEST_ANALYSIS.md`: V4 audit results that revealed test bloat

---

## Approval

**Approved by**: @am
**Date**: 2025-10-23
**Constitutional Authority**: Article VII (Amendment 2025-10-23)

**Ratification**: This ADR is now CONSTITUTIONAL LAW. All agents MUST comply with Article VII: Value-First Testing Philosophy.

---

**Summary**: We shift from coverage-first (6,554 tests, many low-value) to value-first (2,500 tests, all high-value). Quality > Quantity. Integration > Unit. Behavior > Implementation. This is now Constitutional Law.
