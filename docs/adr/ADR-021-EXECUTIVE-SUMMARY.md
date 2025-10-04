# ADR-021: Test Isolation Exception - Executive Summary

## The Problem (One Sentence)

Agency Constitution Article II requires "tests MUST verify REAL functionality, not simulated behavior" BUT our codebase has 128 `create_mock_agent` usages with no constitutional guidance, creating a fundamental tension between fast TDD and real verification.

## The Solution (One Sentence)

Amend Constitution Article II with Section 2.4 to establish test tier boundaries where mocks are constitutionally permitted (unit tests for speed) vs. prohibited (integration/e2e for real verification).

---

## Decision Summary

### Amendment: Article II Section 2.4 - Test Isolation Exception

**Test Tier Boundaries:**

| Tier | Directory | Purpose | Mocks Allowed? | Timeout | Constitutional Status |
|------|-----------|---------|----------------|---------|----------------------|
| **Unit** | `tests/unit/` | Fast isolated logic | External dependencies only | <2s | Mocks are isolation tools |
| **Integration** | `tests/integration/` | Component interactions | True externals only (APIs) | <10s | Article II applies here |
| **E2E** | `tests/e2e/` | Full system verification | NO MOCKS | <30s | Article II absolute |

**Key Principle**: Test tier determines mock legality. Fast feedback (unit) + Real verification (integration/e2e) = Both constitutional.

---

## Impact at a Glance

### Before Amendment
- 128 mock usages with unclear constitutional status
- Article II violation ambiguity
- No enforcement of mock boundaries
- Tests fast but may verify simulated behavior

### After Amendment
- 128 mock usages categorized by tier (100% compliant)
- Clear constitutional guidance: test tier determines legality
- Automated enforcement (pre-commit + pytest + CI)
- Unit tests fast (<2s), integration/e2e verify real behavior

---

## Implementation Timeline

| Phase | Duration | Key Milestone |
|-------|----------|---------------|
| **Phase 1: Ratification** | Week 1 | @am approval, constitution updated |
| **Phase 2: Enforcement** | Week 2 | Pre-commit hooks, pytest fixtures, CI checks |
| **Phase 3: Migration** | Weeks 3-6 | 128 tests categorized, moved, real implementations |
| **Phase 4: Documentation** | Week 7 | Guides, agent instructions, templates |

**Total**: 7 weeks from approval to full compliance

---

## Decision Criteria (Quick Reference)

```python
# When can I use mocks?
def is_mock_allowed(component, test_tier):
    # NEVER mock the component under test
    if component == "component_under_test":
        return False

    # Unit tests: Mock externals for speed
    if test_tier == "unit":
        return component in ["agent", "api", "database", "file_system"]

    # Integration tests: Mock only true externals
    if test_tier == "integration":
        return component in ["cloud_api", "paid_service"]

    # E2E tests: NO MOCKS (Article II absolute)
    if test_tier == "e2e":
        return False

    # Default: Use real implementation (Article II)
    return False
```

---

## Example Migration

### Before (Constitutional Violation)
```python
# tests/test_handoffs_minimal.py (unclear tier)
def create_mock_agent(name: str) -> MagicMock:
    mock_agent = create_autospec(Agent, instance=True)
    # ... Article II violation: no tier boundary
    return mock_agent

async def test_coder_handoff():
    mock_coder = create_mock_agent("AgencyCodeAgent")  # Violation
    mock_planner = create_mock_agent("PlannerAgent")   # Violation
```

### After (Constitutional Compliance)

**Option A - Unit Test:**
```python
# tests/unit/test_handoff_mechanism.py
@pytest.mark.unit
async def test_handoff_message_serialization():
    mock_coder = create_mock_agent("AgencyCodeAgent")  # OK: External to message logic
    message = HandoffMessage(from_agent=mock_coder, ...)
    assert message.serialize() == expected  # <2s, isolated
```

**Option B - Integration Test:**
```python
# tests/integration/test_agent_handoffs.py
@pytest.mark.integration
async def test_real_coder_to_planner_handoff():
    real_coder = AgencyCodeAgent()  # Real implementation
    real_planner = PlannerAgent()   # Real implementation
    result = await real_coder.handoff_to(real_planner, "Task")
    assert result.success  # <10s, real behavior
```

**Option C - E2E Test:**
```python
# tests/e2e/test_agency_workflow.py
@pytest.mark.e2e
async def test_complete_agency_workflow():
    agency = Agency.from_config("production_config.yaml")  # Real system
    result = await agency.run("Implement feature with handoffs")
    assert result.all_agents_coordinated  # <30s, zero mocks
```

---

## Benefits

1. **Resolves Constitutional Paradox**: Fast unit tests + real verification = both constitutional
2. **Clear Enforcement**: Test tier determines mock legality, zero ambiguity
3. **Preserves TDD Speed**: Unit tests stay <2s with mocks
4. **Guarantees Real Verification**: Integration/E2E enforce Article II absolutely
5. **Automated Compliance**: Pre-commit + pytest prevent violations
6. **Industry Alignment**: Follows test pyramid best practices

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Tests too slow | Keep unit coverage >70%, optimize integration setup |
| Unclear boundaries | Decision tree codified, pre-commit enforces |
| Over-reliance on mocks | Require integration test for every mocked scenario |
| Migration overhead | 7-week phased rollout, 128 tests over 4 weeks |

---

## Metrics and Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Constitutional compliance | 100% | Zero violations in pre-commit/CI |
| Mock usages categorized | 128/128 | All tests in tier directories |
| Unit test speed (95th %ile) | <2s | Maintained with mocks |
| Integration test speed | <10s | Real behavior verification |
| E2E test speed | <30s | Full system validation |
| Article II compliance | 100% | Clear boundaries enforced |

---

## Approval Required

**@am must approve:**
1. Article II Section 2.4 amendment text
2. Test tier boundaries (unit/integration/e2e)
3. 7-week implementation timeline
4. Enforcement mechanism (pre-commit + pytest + CI)

**Questions for @am:**
1. Any modifications to test tier boundaries or timeout constraints?
2. Approve 7-week timeline or prefer faster/slower rollout?
3. Priority: Migrate all tests at once or phase by module?
4. Any tests requiring special handling or exceptions?

---

## Next Steps After Approval

1. **Day 1**: Update `constitution.md` with Section 2.4
2. **Week 1**: Agent communication, documentation updates
3. **Week 2**: Deploy enforcement (pre-commit, pytest, CI)
4. **Weeks 3-6**: Migrate 128 tests to tier directories
5. **Week 7**: Finalize documentation and templates
6. **Week 8**: Post-implementation review

---

## Files Created

1. **`docs/adr/ADR-021-test-isolation-exception.md`** - Full architectural decision record (comprehensive rationale, alternatives, implementation)
2. **`docs/adr/AMENDMENT-Article-II-Section-2.4.md`** - Constitutional amendment text and summary
3. **`docs/adr/ADR-021-implementation-checklist.md`** - 7-week phased implementation checklist
4. **`docs/adr/ADR-021-EXECUTIVE-SUMMARY.md`** - This document (quick reference)
5. **`docs/adr/ADR-INDEX.md`** - Updated with ADR-021 entry

---

## Constitutional Alignment

- **Article I (Complete Context)**: Timeout enforcement aligned with test tiers
- **Article II (100% Verification)**: **PRIMARY** - Section 2.4 clarifies mock boundaries
- **Article III (Automated Enforcement)**: Pre-commit + pytest enforce amendment
- **Article XII (TDD)**: Fast unit tests preserve Red-Green-Refactor workflow

---

## Bottom Line

**Problem**: 128 mocks violate Article II ("verify real functionality") but are needed for fast TDD.

**Solution**: Test tier boundaries make mocks constitutional in unit tests (speed) and prohibited in integration/e2e (real verification).

**Result**: Fast feedback (<2s unit) + Real verification (<10s integration, <30s e2e) + 100% constitutional compliance.

**Timeline**: 7 weeks from approval to full migration.

**Approval Needed**: @am must ratify constitutional amendment.

---

**Recommendation**: APPROVE amendment. Resolves constitutional tension, preserves TDD speed, guarantees real verification, automated enforcement.

---

*Created by: ChiefArchitectAgent*
*Date: 2025-10-04*
*Status: Awaiting @am approval*
*ADR: ADR-021*
