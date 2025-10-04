# ADR-021: Test Isolation Exception - The Mock/Real Boundary

## Status
**Proposed** - 2025-10-04

## Context

### The Constitutional Tension
Agency's Constitution Article II mandates "100% Verification and Stability" with explicit requirements:
- Section 2.2: "Tests MUST verify REAL functionality, not simulated behavior"
- Section 2.2: "No Simulation in Production" amendment (2025-10-02)

However, the codebase contains **128 usages of `create_mock_agent`** across test files, creating a direct constitutional violation. This creates a fundamental tension:

1. **Article II requires real behavior verification** - production code must be tested against actual implementations
2. **Test pyramid requires fast unit tests** - mocks enable sub-second feedback loops
3. **Integration tests need real components** - to verify actual system behavior
4. **Current state: No clear boundary** - causing constitutional violations and confusion

### Evidence of the Problem

**Violations by the Numbers:**
- 128 `create_mock_agent` usages across 5 files
- Tests in `/tests/*.py` (root) with no categorization
- Automatic timeout enforcement (2s unit, 10s integration, 30s e2e) via `conftest.py`
- 163 explicit test category markers (`@pytest.mark.unit/integration/e2e`)
- **BUT**: No enforcement of mock usage boundaries

**Example Constitutional Violation:**
```python
# tests/test_handoffs_minimal.py - Line 8-19
def create_mock_agent(name: str, with_handoff: bool = True) -> MagicMock:
    """Create a properly mocked Agent instance."""
    mock_agent = create_autospec(Agent, instance=True)
    mock_agent.name = name
    # ... 11 more lines of mock behavior
    return mock_agent
```

This violates Article II Section 2.2: "Tests MUST verify REAL functionality, not simulated behavior."

### Test Architecture Context

Current state-of-the-art test architecture (from `tests/conftest.py`):
- **Auto-categorization** by directory structure (`/unit/`, `/integration/`, `/e2e/`)
- **Automatic timeouts**: 2s (unit), 10s (integration), 30s (e2e)
- **Slow test tracking**: Auto-logs tests >1s for optimization
- **Three-tier pyramid**: Unit (fast) → Integration (real) → E2E (full system)

**Missing**: Enforcement of mock usage boundaries aligned with test categories.

## Decision

**Amend Constitution Article II with Section 2.4: Test Isolation Exception to establish clear, enforceable boundaries for mock usage based on test categorization.**

### Article II Section 2.4: Test Isolation Exception

The following amendment is added to Constitution Article II after Section 2.3:

---

**Section 2.4: Test Isolation Exception**

**Foundational Principle**: Fast feedback requires isolation; Real verification requires actual behavior. Both are constitutional requirements when applied to the correct test tier.

**Test Tier Boundaries (The Mock/Real Boundary):**

1. **Unit Tests (`tests/unit/` or `@pytest.mark.unit`)**
   - **PURPOSE**: Fast feedback on isolated logic (<2 seconds)
   - **MOCKS PERMITTED**: External dependencies (agents, APIs, databases, file systems)
   - **MUST BE REAL**: The component under test itself
   - **ENFORCEMENT**: Automatic 2-second timeout forces mock usage
   - **CONSTITUTIONAL COMPLIANCE**: Mocks are tools for isolation, not simulation of production behavior

2. **Integration Tests (`tests/integration/` or `@pytest.mark.integration`)**
   - **PURPOSE**: Verify component interactions with real implementations (<10 seconds)
   - **MOCKS PROHIBITED**: Components being integrated (agents, tools, repositories)
   - **MOCKS PERMITTED**: True external dependencies (cloud APIs, paid services)
   - **ENFORCEMENT**: Must use real Agency components (shared context, VectorStore, etc.)
   - **CONSTITUTIONAL COMPLIANCE**: Article II verification of real behavior applies here

3. **E2E Tests (`tests/e2e/` or `@pytest.mark.e2e`)**
   - **PURPOSE**: Full system verification (<30 seconds)
   - **MOCKS PROHIBITED**: ALL internal components
   - **MOCKS PERMITTED**: Only unavoidable external services (with explicit justification)
   - **ENFORCEMENT**: Must use production configuration paths
   - **CONSTITUTIONAL COMPLIANCE**: Absolute Article II compliance - zero simulation

**Decision Criteria (When in doubt):**

```python
# Decision tree for mock usage
def is_mock_allowed(component: str, test_tier: str) -> bool:
    """
    Constitutional mock usage decision tree.

    Returns True if mocking is permitted, False otherwise.
    """
    # Rule 1: Never mock the component under test
    if component == "component_under_test":
        return False  # Article II: Must test real functionality

    # Rule 2: Test tier determines boundary
    if test_tier == "unit":
        # Unit tests: Mock external dependencies for speed
        return component in ["external_dependency", "api", "database", "agent"]

    elif test_tier == "integration":
        # Integration tests: Mock only true externals
        return component in ["cloud_api", "paid_service", "third_party_api"]

    elif test_tier == "e2e":
        # E2E tests: Mock nothing (Article II absolute compliance)
        return component in ["unavoidable_external"]  # Rare exceptions only

    # Default: When in doubt, use real implementation (Article II)
    return False
```

**Enforcement Mechanism:**

```python
# tests/conftest.py addition
@pytest.fixture(autouse=True)
def enforce_mock_boundary(request):
    """
    Enforce Article II Section 2.4: Test Isolation Exception.

    Validates mock usage against test tier boundaries.
    """
    test_markers = [m.name for m in request.node.iter_markers()]
    test_path = str(request.node.fspath)

    # Determine test tier
    if "e2e" in test_markers or "/e2e/" in test_path:
        tier = "e2e"
    elif "integration" in test_markers or "/integration/" in test_path:
        tier = "integration"
    else:
        tier = "unit"

    # E2E tests: No mocks allowed (Article II absolute compliance)
    if tier == "e2e":
        # Inspect test for MagicMock, create_autospec usage
        test_source = inspect.getsource(request.function)
        forbidden_patterns = ["MagicMock", "create_autospec", "patch", "mock.Mock"]

        violations = [p for p in forbidden_patterns if p in test_source]
        if violations:
            pytest.fail(
                f"CONSTITUTIONAL VIOLATION - Article II Section 2.4:\n"
                f"E2E tests must use real implementations. Found: {violations}\n"
                f"Move to tests/integration/ if mocking is necessary."
            )

    yield  # Run the test
```

**Pre-commit Hook Enhancement:**

```bash
#!/bin/bash
# .git/hooks/pre-commit addition

echo "Validating Article II Section 2.4 compliance..."

# Check for mocks in E2E tests
E2E_MOCK_VIOLATIONS=$(grep -r "MagicMock\|create_autospec\|@patch" tests/e2e/ --include="*.py" 2>/dev/null || true)

if [ -n "$E2E_MOCK_VIOLATIONS" ]; then
    echo "❌ CONSTITUTIONAL VIOLATION: Article II Section 2.4"
    echo "E2E tests must not use mocks. Found violations:"
    echo "$E2E_MOCK_VIOLATIONS"
    echo ""
    echo "Resolution: Move tests to tests/integration/ or remove mocks"
    exit 1
fi

echo "✅ Article II Section 2.4: Compliant"
```

---

## Rationale

### Why This Amendment Is Necessary

1. **Resolves Constitutional Paradox**: Allows fast unit tests without violating "real behavior" mandate
2. **Clear Enforcement**: Test tier determines mock legality - no ambiguity
3. **Preserves Test Speed**: Unit tests remain <2s with mocks
4. **Guarantees Real Verification**: Integration/E2E enforce Article II absolutely
5. **Aligns with Industry Standards**: Follows test pyramid best practices
6. **Backward Compatible**: Existing test structure already supports tiers

### Analysis of Alternatives Considered

#### Alternative 1: Ban All Mocks Everywhere
- **Pros**: Absolute Article II compliance, no ambiguity
- **Cons**: Unit tests become slow (>10s), defeats TDD fast feedback
- **Why Rejected**: Destroys test pyramid, makes TDD impractical

#### Alternative 2: Allow Mocks Everywhere
- **Pros**: Maximum test speed, developer convenience
- **Cons**: Violates Article II, tests become meaningless green checkmarks
- **Why Rejected**: Constitutional violation, defeats purpose of testing

#### Alternative 3: Manual Developer Judgment
- **Pros**: Flexibility, case-by-case decisions
- **Cons**: Inconsistent enforcement, constitutional drift over time
- **Why Rejected**: Violates Article III (Automated Enforcement)

#### Alternative 4: This Amendment (Test Tier Boundaries)
- **Pros**: Fast unit tests + real verification, automated enforcement, clear rules
- **Cons**: Requires test reorganization (128 mock usages to migrate)
- **Why Accepted**: Balances Article II with practical TDD, enforceable by automation

## Consequences

### Positive

1. **Constitutional Compliance**: Resolves Article I/II tension with mocks
2. **Fast Feedback Loop**: Unit tests remain <2s with mocks
3. **Real Verification**: Integration/E2E guarantee actual behavior validation
4. **Clear Guidelines**: Developers know exactly when mocks are allowed
5. **Automated Enforcement**: Pre-commit + pytest fixtures prevent violations
6. **Test Pyramid Alignment**: Matches industry best practices
7. **Preserves TDD**: Maintains fast Red-Green-Refactor cycles

### Negative

1. **Migration Required**: 128 `create_mock_agent` usages need categorization
2. **Test Reorganization**: Move tests to correct tier directories (`unit/`, `integration/`, `e2e/`)
3. **Initial Slowdown**: Integration tests will be slower than current mocked tests
4. **Learning Curve**: Developers must understand tier boundaries
5. **Duplicate Test Logic**: Some scenarios may need both unit (mocked) and integration (real) tests

### Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tests become too slow | Developer productivity drop | Keep unit test coverage high (>70%), optimize integration tests |
| Unclear tier boundaries | Inconsistent categorization | Decision tree codified, pre-commit validation |
| Over-reliance on mocks | False confidence in unit tests | Require matching integration test for every mocked scenario |
| Test duplication overhead | Maintenance burden | Share test fixtures, use parametrization |

## Implementation Notes

### Phase 1: Amendment Ratification (Week 1)
1. Add Section 2.4 to `constitution.md`
2. Create this ADR-021
3. Update `docs/adr/ADR-INDEX.md`
4. Communicate amendment to all agents

### Phase 2: Enforcement Infrastructure (Week 2)
1. Add `enforce_mock_boundary` fixture to `tests/conftest.py`
2. Enhance pre-commit hook with E2E mock detection
3. Add CI pipeline check for constitutional compliance
4. Create `tests/unit/`, `tests/integration/`, `tests/e2e/` directories (if not exist)

### Phase 3: Test Migration (Weeks 3-6)
1. **Audit Current Tests** (128 mock usages)
   - Categorize each test by purpose (unit/integration/e2e)
   - Identify which mocks are legitimate (external dependencies)
   - Flag which tests need real implementations (Article II violations)

2. **Migrate to Tier Directories**
   - Move unit tests → `tests/unit/`
   - Move integration tests → `tests/integration/`
   - Move e2e tests → `tests/e2e/`

3. **Replace Prohibited Mocks**
   - Integration tests: Replace `create_mock_agent` with real agent instances
   - E2E tests: Remove all mocks, use production setup

4. **Verify Constitutional Compliance**
   - Run full test suite with new enforcement
   - Fix violations until 100% compliant
   - Document any exceptions (with justification)

### Phase 4: Documentation Update (Week 7)
1. Update `CLAUDE.md` with Section 2.4 guidance
2. Create testing guide: "When to Mock, When to Use Real"
3. Add ADR-021 reference to all agent instructions
4. Update test templates with tier-specific examples

### Test Migration Checklist

For each of the 128 mock usages:

```python
# Migration decision tree
def migrate_test(test_file: str, test_function: str):
    """
    1. What is the test's purpose?
       - Isolated logic? → Unit test (mocks OK for externals)
       - Component interaction? → Integration test (mocks for true externals only)
       - Full system flow? → E2E test (no mocks)

    2. What is being mocked?
       - External dependency (API, DB)? → Mock allowed in unit/integration
       - Agency component (agent, tool)? → Must be real in integration/e2e
       - Component under test? → NEVER mock (Article II)

    3. Move to correct directory:
       - tests/unit/ → Keep lightweight mocks
       - tests/integration/ → Replace agent mocks with real instances
       - tests/e2e/ → Remove all mocks

    4. Verify:
       - Test still passes with real implementations
       - Timeout constraints met (2s/10s/30s)
       - Constitutional compliance validated
    """
```

### Example Migration

**Before (Constitutional Violation):**
```python
# tests/test_handoffs_minimal.py (root directory, unclear tier)
def create_mock_agent(name: str) -> MagicMock:
    mock_agent = create_autospec(Agent, instance=True)
    mock_agent.name = name
    return mock_agent

@pytest.mark.asyncio
async def test_coder_handoff_to_planner_minimal():
    mock_coder = create_mock_agent("AgencyCodeAgent")  # Article II violation
    mock_planner = create_mock_agent("PlannerAgent")   # Article II violation
    # ... rest of test
```

**After (Constitutional Compliance):**

**Option A - Unit Test (Fast Feedback):**
```python
# tests/unit/test_handoff_mechanism.py
@pytest.mark.unit
async def test_handoff_message_serialization():
    """Unit test: Handoff message structure (mocks OK for agents)."""
    # Mock agents for isolated message testing
    mock_coder = create_mock_agent("AgencyCodeAgent")  # OK: External to message logic
    mock_planner = create_mock_agent("PlannerAgent")   # OK: External to message logic

    message = HandoffMessage(from_agent=mock_coder, to_agent=mock_planner)
    assert message.serialize() == expected_format
```

**Option B - Integration Test (Real Behavior):**
```python
# tests/integration/test_agent_handoffs.py
@pytest.mark.integration
async def test_real_coder_to_planner_handoff():
    """Integration test: Real agent handoff (Article II compliance)."""
    # Use REAL agents (Article II: verify real functionality)
    from agency_code_agent import AgencyCodeAgent
    from planner_agent import PlannerAgent

    real_coder = AgencyCodeAgent()  # Real implementation
    real_planner = PlannerAgent()   # Real implementation

    # Test actual handoff behavior
    result = await real_coder.handoff_to(real_planner, "Task delegated")
    assert result.success
    assert real_planner.received_context == expected_context
```

**Option C - E2E Test (Full System):**
```python
# tests/e2e/test_agency_workflow.py
@pytest.mark.e2e
async def test_complete_agency_workflow():
    """E2E test: Full agency workflow (zero mocks)."""
    # NO MOCKS - Article II absolute compliance
    from agency import Agency

    # Production configuration
    agency = Agency.from_config("production_config.yaml")

    # End-to-end scenario
    result = await agency.run("Implement new feature with handoffs")

    # Verify real system behavior
    assert result.task_completed
    assert result.all_agents_coordinated
    assert len(result.handoff_chain) >= 2  # Coder → Planner → Coder
```

## Metrics and Success Criteria

### Constitutional Compliance Metrics
- **Pre-Amendment**: Article II compliance unclear for 128 mock usages
- **Post-Amendment Target**: 100% compliance across all test tiers

### Test Suite Performance
- **Unit Tests**: Maintain <2s average (95th percentile <5s)
- **Integration Tests**: <10s average (95th percentile <20s)
- **E2E Tests**: <30s average (95th percentile <60s)
- **Full Suite**: <5 minutes total runtime

### Migration Progress
- **Week 2**: Enforcement infrastructure deployed (0 violations allowed)
- **Week 4**: 50% of tests migrated to tier directories
- **Week 6**: 100% of tests migrated and compliant
- **Week 7**: Documentation complete, amendment fully operational

### Quality Indicators
- **Test Categorization**: 100% of tests in tier directories or explicitly marked
- **Mock Justification**: Every mock in integration/e2e has documented justification
- **Real Verification Coverage**: Every feature has at least one integration test with real components

## References

- **Constitution Article II**: 100% Verification and Stability
- **ADR-002**: Original Article II ratification
- **ADR-011**: NECESSARY Pattern for Tests
- **ADR-012**: Test-Driven Development mandate
- **Test Pyramid** (Martin Fowler): Unit → Integration → E2E architecture
- **Growing Object-Oriented Software, Guided by Tests** (Freeman & Pryce): Mock roles, not objects

## Related ADRs

- **ADR-001**: Complete Context Before Action (timeout enforcement aligns with test tiers)
- **ADR-002**: 100% Verification and Stability (this amendment clarifies Section 2.2)
- **ADR-003**: Automated Merge Enforcement (pre-commit hooks enforce this amendment)
- **ADR-012**: Test-Driven Development (fast unit tests preserve TDD workflow)

## Decision Authority

- **Proposed by**: ChiefArchitectAgent
- **Constitutional Authority**: @am (amendment requires explicit approval)
- **Alignment**: Articles I (Complete Context), II (100% Verification), III (Automated Enforcement)

---

## Appendix: Constitutional Amendment Text

**For inclusion in `constitution.md` after Article II Section 2.3:**

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

---

**Status**: Awaiting @am approval for constitutional amendment
**Next Steps**: Upon approval, proceed to Phase 1 implementation
**Review Date**: 2025-11-04 (1 month post-implementation)

*"In isolation we test logic; In integration we verify reality; In E2E we prove production-readiness."*
