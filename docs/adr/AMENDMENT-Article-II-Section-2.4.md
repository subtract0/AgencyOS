# Constitutional Amendment: Article II Section 2.4 - Test Isolation Exception

## Summary

**Amendment Type**: Addition to Constitution Article II
**Status**: Proposed - Awaiting @am approval
**Date**: 2025-10-04
**ADR**: ADR-021 (full decision record)

## Problem Solved

**Constitutional Tension**: Article II requires "tests MUST verify REAL functionality, not simulated behavior" BUT fast TDD requires mocks for unit tests. Current codebase has 128 `create_mock_agent` usages with no clear constitutional guidance.

**Resolution**: Establish test tier boundaries where mocks are constitutionally permitted (unit tests) vs. prohibited (integration/e2e tests).

## Amendment Text

Add to `constitution.md` after Article II Section 2.3:

```markdown
### Section 2.4: Test Isolation Exception (ADR-021)

#### Foundational Principle
Fast feedback requires isolation; Real verification requires actual behavior. Both are constitutional requirements when applied to the correct test tier.

#### Test Tier Boundaries

**Unit Tests** (`tests/unit/` or `@pytest.mark.unit`):
- **Purpose**: Fast feedback on isolated logic (<2 seconds)
- **Mocks Permitted**: External dependencies (agents, APIs, databases, file systems)
- **Must Be Real**: The component under test itself
- **Constitutional Status**: Mocks are tools for isolation, not simulation of production behavior

**Integration Tests** (`tests/integration/` or `@pytest.mark.integration`):
- **Purpose**: Verify component interactions with real implementations (<10 seconds)
- **Mocks Prohibited**: Agency components (agents, tools, repositories)
- **Mocks Permitted**: True external dependencies (cloud APIs, paid services)
- **Constitutional Status**: Article II verification of real behavior applies here

**E2E Tests** (`tests/e2e/` or `@pytest.mark.e2e`):
- **Purpose**: Full system verification (<30 seconds)
- **Mocks Prohibited**: ALL internal components
- **Mocks Permitted**: Only unavoidable external services (with explicit justification)
- **Constitutional Status**: Absolute Article II compliance - zero simulation

#### Enforcement
```python
# Pre-commit validation
if test_tier == "e2e" and has_mocks(test_file):
    raise ConstitutionalViolation(
        "Article II Section 2.4: E2E tests must use real implementations"
    )
```

See ADR-021 for complete decision rationale and implementation guidance.
```

## Decision Criteria (Quick Reference)

```python
# When can I use mocks?
def is_mock_allowed(component: str, test_tier: str) -> bool:
    # Never mock the component under test
    if component == "component_under_test":
        return False

    # Unit tests: Mock external dependencies
    if test_tier == "unit":
        return component in ["external_dependency", "api", "database", "agent"]

    # Integration tests: Mock only true externals
    if test_tier == "integration":
        return component in ["cloud_api", "paid_service"]

    # E2E tests: No mocks (Article II absolute)
    if test_tier == "e2e":
        return False  # Rare exceptions require explicit justification

    return False  # Default: Use real implementation
```

## Migration Impact

| Category | Current State | Target State |
|----------|--------------|--------------|
| Mock usages | 128 (unclear constitutional status) | 128 (categorized by tier) |
| Constitutional violations | Unknown | 0 |
| Unit test speed | <2s (with mocks) | <2s (mocks preserved) |
| Integration test speed | <2s (mocked, not real) | <10s (real behavior) |
| E2E test speed | N/A (few exist) | <30s (zero mocks) |

## Implementation Phases

### Phase 1: Amendment Ratification (Week 1)
- [ ] Add Section 2.4 to `constitution.md`
- [ ] Update `docs/adr/ADR-INDEX.md` with ADR-021
- [ ] Communicate amendment to all agents
- [ ] Approval from @am required

### Phase 2: Enforcement Infrastructure (Week 2)
- [ ] Add `enforce_mock_boundary` fixture to `tests/conftest.py`
- [ ] Enhance pre-commit hook with E2E mock detection
- [ ] Add CI pipeline check for Section 2.4 compliance
- [ ] Create tier directories (`tests/unit/`, `tests/integration/`, `tests/e2e/`)

### Phase 3: Test Migration (Weeks 3-6)
- [ ] Audit 128 mock usages and categorize by tier
- [ ] Move tests to appropriate tier directories
- [ ] Replace prohibited mocks with real implementations
- [ ] Verify 100% constitutional compliance

### Phase 4: Documentation (Week 7)
- [ ] Update `CLAUDE.md` with Section 2.4 guidance
- [ ] Create testing guide: "When to Mock, When to Use Real"
- [ ] Update agent instructions with tier-specific examples
- [ ] Add ADR-021 reference to all relevant documentation

## Example Migration

### Before (Constitutional Violation)
```python
# tests/test_handoffs_minimal.py (root, unclear tier)
def create_mock_agent(name: str) -> MagicMock:
    mock_agent = create_autospec(Agent, instance=True)
    # ... Article II violation: mocking without tier boundary
    return mock_agent

async def test_coder_handoff_to_planner_minimal():
    mock_coder = create_mock_agent("AgencyCodeAgent")  # Violation
    mock_planner = create_mock_agent("PlannerAgent")   # Violation
```

### After (Constitutional Compliance)

**Option A - Unit Test (Fast Feedback):**
```python
# tests/unit/test_handoff_mechanism.py
@pytest.mark.unit
async def test_handoff_message_serialization():
    """Unit test: Message structure (mocks OK for agents)."""
    mock_coder = create_mock_agent("AgencyCodeAgent")  # OK: External to message logic
    message = HandoffMessage(from_agent=mock_coder, ...)
    assert message.serialize() == expected_format
```

**Option B - Integration Test (Real Behavior):**
```python
# tests/integration/test_agent_handoffs.py
@pytest.mark.integration
async def test_real_coder_to_planner_handoff():
    """Integration test: Real agent handoff (Article II compliance)."""
    real_coder = AgencyCodeAgent()  # Real implementation
    real_planner = PlannerAgent()   # Real implementation
    result = await real_coder.handoff_to(real_planner, "Task delegated")
    assert result.success  # Verifying REAL behavior
```

**Option C - E2E Test (Full System):**
```python
# tests/e2e/test_agency_workflow.py
@pytest.mark.e2e
async def test_complete_agency_workflow():
    """E2E test: Full agency workflow (zero mocks - Article II absolute)."""
    agency = Agency.from_config("production_config.yaml")  # Real system
    result = await agency.run("Implement feature with handoffs")
    assert result.all_agents_coordinated  # Real system verification
```

## Benefits

1. **Resolves Constitutional Paradox**: Allows fast unit tests without violating Article II
2. **Clear Enforcement**: Test tier determines mock legality - zero ambiguity
3. **Preserves TDD Speed**: Unit tests remain <2s with mocks
4. **Guarantees Real Verification**: Integration/E2E enforce Article II absolutely
5. **Automated Compliance**: Pre-commit + pytest fixtures prevent violations
6. **Industry Alignment**: Follows test pyramid best practices

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Tests become too slow | Keep unit test coverage high (>70%), optimize integration tests |
| Unclear tier boundaries | Decision tree codified, pre-commit validation enforces |
| Over-reliance on mocks | Require matching integration test for every mocked scenario |
| Migration overhead | 7-week phased rollout, automated migration tooling |

## Success Metrics

- **Constitutional Compliance**: 100% of tests compliant with Section 2.4
- **Test Speed**: Unit <2s, Integration <10s, E2E <30s (95th percentile)
- **Migration Progress**: 100% complete by Week 6
- **Zero Violations**: Pre-commit blocks all Section 2.4 violations

## Approval Required

**Constitutional Authority**: @am

**Questions for Approval:**
1. Accept Article II Section 2.4 amendment as written?
2. Approve 7-week phased implementation timeline?
3. Authorize enforcement infrastructure deployment (Week 2)?
4. Any modifications to test tier boundaries or decision criteria?

## References

- **ADR-021**: Full architectural decision record
- **Constitution Article II**: Original 100% verification mandate
- **tests/conftest.py**: Current test tier auto-categorization infrastructure
- **Test Pyramid**: Martin Fowler's testing strategy architecture

---

**Next Step**: Await @am approval to proceed with Phase 1 (Amendment Ratification)

*"In isolation we test logic; In integration we verify reality; In E2E we prove production-readiness."*
