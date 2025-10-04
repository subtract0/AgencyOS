# ADR-021 Implementation Checklist

## Constitutional Amendment: Article II Section 2.4 - Test Isolation Exception

**Status**: Proposed - Awaiting @am approval
**Timeline**: 7 weeks (phased rollout)
**Impact**: 128 mock usages to categorize, 100% constitutional compliance target

---

## Phase 1: Amendment Ratification (Week 1)

### Constitutional Changes
- [ ] **Add Section 2.4 to `constitution.md`**
  - Insert after Article II Section 2.3
  - Copy text from `AMENDMENT-Article-II-Section-2.4.md`
  - Update constitution version number
  - Set effective date after @am approval

- [ ] **Update ADR Index**
  - [x] Add ADR-021 entry to `docs/adr/ADR-INDEX.md`
  - [x] Update "Last Updated" date
  - [ ] Mark as "Accepted" once @am approves

- [ ] **Communication to Agents**
  - [ ] Update all agent instructions (10 agents)
  - [ ] Add Section 2.4 reference to agent constitutional compliance sections
  - [ ] Update `.claude/quick-ref/constitution-checklist.md`
  - [ ] Add test tier decision tree to quick references

### Approval Gate
- [ ] **@am approval required** for constitutional amendment
  - Review ADR-021 full text
  - Review amendment text in `AMENDMENT-Article-II-Section-2.4.md`
  - Approve test tier boundaries (unit/integration/e2e)
  - Approve 7-week implementation timeline

---

## Phase 2: Enforcement Infrastructure (Week 2)

### Pytest Fixture Enhancements
- [ ] **Add `enforce_mock_boundary` fixture to `tests/conftest.py`**
  - Automatically inspect test source for mocks
  - Block E2E tests with `MagicMock`, `create_autospec`, `@patch`
  - Provide clear constitutional violation messages
  - Reference ADR-021 in error output

```python
# Example implementation
@pytest.fixture(autouse=True)
def enforce_mock_boundary(request):
    """Enforce Article II Section 2.4: Test Isolation Exception."""
    test_markers = [m.name for m in request.node.iter_markers()]
    test_path = str(request.node.fspath)

    # Determine test tier
    if "e2e" in test_markers or "/e2e/" in test_path:
        tier = "e2e"
    elif "integration" in test_markers or "/integration/" in test_path:
        tier = "integration"
    else:
        tier = "unit"

    # E2E tests: No mocks allowed
    if tier == "e2e":
        test_source = inspect.getsource(request.function)
        forbidden_patterns = ["MagicMock", "create_autospec", "patch", "mock.Mock"]
        violations = [p for p in forbidden_patterns if p in test_source]

        if violations:
            pytest.fail(
                f"CONSTITUTIONAL VIOLATION - Article II Section 2.4:\n"
                f"E2E tests must use real implementations. Found: {violations}\n"
                f"Resolution: Move to tests/integration/ or remove mocks\n"
                f"See ADR-021 for guidance."
            )

    yield  # Run the test
```

### Pre-commit Hook Enhancement
- [ ] **Update `.git/hooks/pre-commit`** (or `.pre-commit-config.yaml`)
  - Add E2E mock detection check
  - Block commits with mocks in `tests/e2e/`
  - Provide clear error messages with ADR-021 reference

```bash
#!/bin/bash
# .git/hooks/pre-commit addition

echo "Validating Article II Section 2.4 compliance..."

# Check for mocks in E2E tests
E2E_MOCK_VIOLATIONS=$(grep -r "MagicMock\|create_autospec\|@patch\|mock.Mock" tests/e2e/ --include="*.py" 2>/dev/null || true)

if [ -n "$E2E_MOCK_VIOLATIONS" ]; then
    echo "❌ CONSTITUTIONAL VIOLATION: Article II Section 2.4"
    echo "E2E tests must not use mocks. Found violations:"
    echo "$E2E_MOCK_VIOLATIONS"
    echo ""
    echo "Resolution: Move tests to tests/integration/ or remove mocks"
    echo "See docs/adr/ADR-021-test-isolation-exception.md for guidance"
    exit 1
fi

echo "✅ Article II Section 2.4: Compliant"
```

### CI Pipeline Enhancement
- [ ] **Add GitHub Actions workflow step**
  - Check constitutional compliance before running tests
  - Fail fast on Section 2.4 violations
  - Report violation details in CI logs

```yaml
# .github/workflows/test.yml addition
- name: Validate Article II Section 2.4 Compliance
  run: |
    echo "Checking for mocks in E2E tests..."
    if grep -r "MagicMock\|create_autospec\|@patch" tests/e2e/ --include="*.py"; then
      echo "::error::Constitutional violation: E2E tests must not use mocks (Article II Section 2.4)"
      echo "::error::See docs/adr/ADR-021-test-isolation-exception.md"
      exit 1
    fi
    echo "✅ Article II Section 2.4 compliant"
```

### Directory Structure
- [ ] **Create test tier directories** (if not exist)
  - `tests/unit/` - Fast isolated tests (<2s)
  - `tests/integration/` - Component interaction tests (<10s)
  - `tests/e2e/` - Full system tests (<30s)
  - Add README.md to each directory explaining tier purpose

---

## Phase 3: Test Migration (Weeks 3-6)

### Week 3: Audit and Categorization
- [ ] **Audit all 128 `create_mock_agent` usages**
  - Identify files with mock usage
  - Categorize each test by purpose:
    - Unit: Testing isolated logic (message serialization, data structures)
    - Integration: Testing component interactions (agent handoffs, tool usage)
    - E2E: Testing full system workflows (complete agency operations)

- [ ] **Create migration tracking spreadsheet**
  - Columns: File, Test Function, Current State, Target Tier, Migration Status
  - Track progress: Not Started, In Progress, Migrated, Verified

### Week 4-5: Migrate Tests to Tier Directories
- [ ] **Move unit tests to `tests/unit/`**
  - Keep mocks for external dependencies
  - Ensure component under test uses real implementation
  - Verify <2s timeout constraint
  - Add `@pytest.mark.unit` marker (if not auto-categorized)

- [ ] **Move integration tests to `tests/integration/`**
  - Replace `create_mock_agent` with real `AgencyCodeAgent()`, `PlannerAgent()`, etc.
  - Keep mocks for true external dependencies (cloud APIs)
  - Verify <10s timeout constraint
  - Add `@pytest.mark.integration` marker

- [ ] **Move/create E2E tests in `tests/e2e/`**
  - Remove ALL mocks
  - Use production configuration
  - Test complete workflows end-to-end
  - Verify <30s timeout constraint
  - Add `@pytest.mark.e2e` marker

### Week 6: Verification and Cleanup
- [ ] **Run full test suite with enforcement enabled**
  - Verify 100% constitutional compliance
  - No pre-commit blocks
  - No pytest fixture failures
  - No CI pipeline violations

- [ ] **Fix any test failures from migration**
  - Integration tests may fail when switching from mocks to real implementations
  - Fix underlying bugs revealed by real behavior testing
  - Do NOT weaken assertions to make tests pass (Article II)

- [ ] **Clean up deprecated mock utilities**
  - Archive or document `create_mock_agent` for unit test use only
  - Add warnings about constitutional boundaries
  - Update mock utility docstrings with ADR-021 reference

---

## Phase 4: Documentation Update (Week 7)

### Constitutional Documentation
- [ ] **Update `CLAUDE.md`**
  - Add Section 2.4 to "Constitutional Quick Guide"
  - Add test tier decision tree to "Quick Reference Card"
  - Update "Code Quality Checklist" with mock usage guidelines

- [ ] **Create testing guide: `docs/guides/when-to-mock-when-to-use-real.md`**
  - Explain test tier philosophy
  - Provide decision tree with examples
  - Show before/after migration examples
  - Reference ADR-021 for deep dive

### Agent Instructions
- [ ] **Update all 10 agent instruction files**
  - Add Section 2.4 to constitutional compliance sections
  - Include test tier decision criteria
  - Reference ADR-021 in test generation guidance

Agents to update:
  - [ ] `agency_code_agent/instructions.md`
  - [ ] `planner_agent/instructions.md`
  - [ ] `auditor_agent/instructions.md`
  - [ ] `quality_enforcer_agent/instructions.md`
  - [ ] `chief_architect_agent/instructions.md`
  - [ ] `test_generator_agent/instructions.md`
  - [ ] `learning_agent/instructions.md`
  - [ ] `merger_agent/instructions.md`
  - [ ] `toolsmith_agent/instructions.md`
  - [ ] `work_completion_summary_agent/instructions.md`

### Quick References
- [ ] **Update `.claude/quick-ref/constitution-checklist.md`**
  - Add Article II Section 2.4 checklist item
  - Include test tier decision question

- [ ] **Create `.claude/quick-ref/test-tier-decision-tree.md`**
  - Visual decision tree for mock usage
  - Copy from ADR-021 decision criteria
  - Include common examples

### Test Templates
- [ ] **Create tier-specific test templates**
  - `tests/unit/TEMPLATE_unit_test.py`
  - `tests/integration/TEMPLATE_integration_test.py`
  - `tests/e2e/TEMPLATE_e2e_test.py`
  - Each with appropriate mocking examples and constitutional guidance

---

## Validation Checkpoints

### After Phase 1 (Week 1)
- [ ] @am approval received
- [ ] Constitution updated with Section 2.4
- [ ] All agents aware of amendment

### After Phase 2 (Week 2)
- [ ] Pre-commit hook blocks E2E mocks
- [ ] Pytest fixture enforces boundaries
- [ ] CI pipeline validates compliance
- [ ] Test tier directories exist

### After Phase 3 (Week 6)
- [ ] 100% of 128 mock usages categorized
- [ ] All tests in correct tier directories
- [ ] Full test suite passes with enforcement enabled
- [ ] Zero constitutional violations

### After Phase 4 (Week 7)
- [ ] Documentation complete
- [ ] Agent instructions updated
- [ ] Quick references available
- [ ] Test templates created

---

## Success Metrics (Target State)

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Mock usages categorized | 0/128 | 128/128 | All tests in tier directories |
| Constitutional violations | Unknown | 0 | Pre-commit + CI checks pass |
| Unit test speed (95th %ile) | <2s | <2s | Maintained with mocks |
| Integration test speed | <2s (mocked) | <10s (real) | Real behavior verification |
| E2E test speed | N/A | <30s | Full system validation |
| Test tier compliance | ~50% | 100% | All tests marked/categorized |
| Article II compliance | Ambiguous | 100% | Clear boundaries enforced |

---

## Risk Mitigation Checklist

- [ ] **Tests become too slow**
  - Keep unit test coverage >70%
  - Optimize integration test setup (shared fixtures)
  - Run unit tests locally, integration/e2e in CI

- [ ] **Unclear tier boundaries**
  - Decision tree codified in ADR-021
  - Pre-commit validation enforces
  - Agent instructions updated with guidance

- [ ] **Over-reliance on mocks**
  - Require matching integration test for mocked scenarios
  - Code review checks for excessive unit-only coverage

- [ ] **Migration introduces bugs**
  - Fix bugs, don't weaken tests (Article II)
  - Real behavior may reveal hidden issues (this is good!)
  - Full regression testing after migration

---

## Approval Required

**@am Sign-off Needed:**
- [ ] Article II Section 2.4 amendment text approved
- [ ] 7-week implementation timeline approved
- [ ] Test tier boundaries approved (unit/integration/e2e)
- [ ] Enforcement mechanism approved (pre-commit + pytest)

**Questions for @am:**
1. Any modifications to test tier boundaries?
2. Any concerns about 7-week timeline?
3. Priority for migration (all at once vs. phased by module)?
4. Any specific tests that need special handling?

---

## Next Steps After Approval

1. **Immediate** (Day 1): Update `constitution.md` with Section 2.4
2. **Week 1**: Agent communication and documentation updates
3. **Week 2**: Deploy enforcement infrastructure (pre-commit, pytest, CI)
4. **Week 3-6**: Execute test migration (128 usages)
5. **Week 7**: Finalize documentation and templates
6. **Week 8**: Post-implementation review and lessons learned

---

## References

- **ADR-021**: Full architectural decision record
- **AMENDMENT-Article-II-Section-2.4.md**: Constitutional amendment text
- **Constitution Article II**: Original 100% verification mandate
- **tests/conftest.py**: Current test infrastructure

---

*Last Updated: 2025-10-04*
*Status: Awaiting @am approval to proceed*
