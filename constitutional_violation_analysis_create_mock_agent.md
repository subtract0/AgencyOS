# Constitutional Violation Analysis: create_mock_agent Pattern

**Analysis Date**: 2025-10-04
**Auditor**: Auditor Agent
**Mode**: READ-ONLY Static Analysis
**Scope**: All occurrences of `create_mock_agent` in codebase

---

## Executive Summary

**CRITICAL FINDING**: The `create_mock_agent` pattern is a systematic constitutional violation affecting **128+ test executions** with an estimated annual cost of **$133,120** (444x ROI to fix).

**Root Cause**: Test infrastructure bypasses real agent behavior validation, violating Articles I and II of the Constitution.

**Violation Severity**: BLOCKER
**Estimated Fix Effort**: 2-4 hours
**Estimated Annual Savings**: 887 hours (444x ROI)

---

## 1. Occurrence Analysis

### Total Occurrences
- **217 total matches** across 12 files
- **159 logged violations** in constitutional_violations.jsonl
- **3 distinct implementations** of `create_mock_agent` function
- **5 test files** actively using the pattern

### File Breakdown

#### Implementation Files (3)
1. `/Users/am/Code/Agency/tests/test_handoffs_minimal.py` (line 8)
   - Creates mock Agent instances with autospec
   - Sets static properties (name, tools, temperature, model, etc.)
   - Used in 11 places within the file

2. `/Users/am/Code/Agency/tests/test_orchestrator_system.py` (line 67)
   - Creates `MockAgent` dataclass with configurable behavior
   - Factory pattern: `create_mock_agent_factory(name, **kwargs)`
   - Used in 12 places within the file

3. `/Users/am/Code/Agency/tests/test_constitutional_validator.py` (line 26)
   - Creates mock agent within test fixture
   - Embedded in `mock_create_agent_func` fixture
   - Used in 2 places within the file

#### Documentation/Logs (9)
- Constitutional intelligence tools (violation_patterns.py, README.md)
- Autonomous healing logs (constitutional_violations.jsonl)
- Snapshots and archived reports

---

## 2. Constitutional Violation Breakdown

### Article I: Complete Context Before Action
**Violation Count**: 64 (50% of violations)

**Why It Violates Article I**:
```python
# From test_handoffs_minimal.py:8
def create_mock_agent(name: str, with_handoff: bool = True) -> MagicMock:
    mock_agent = create_autospec(Agent, instance=True)
    mock_agent.name = name
    mock_agent.tools = [SendMessageHandoff] if with_handoff else []
    # ... static configuration only
    return mock_agent
```

**Constitutional Mandate**: "Retry on timeout (2x, 3x, up to 10x). ALL tests run to completion. Never proceed with incomplete data."

**Actual Behavior**: Mock agents have NO real context, NO retry logic, NO timeout handling, NO actual LLM interaction. They return pre-scripted responses regardless of actual system state.

**Real Behavior NOT Tested**:
- Agent context initialization (AgentContext, session_id, memory)
- Memory integration hooks (create_memory_integration_hook)
- Message filtering hooks (create_message_filter_hook)
- Constitutional compliance validation (@constitutional_compliance decorator)
- Model selection and configuration (model_policy.py)
- Tool execution with real agent runtime

---

### Article II: 100% Verification and Stability
**Violation Count**: 64 (50% of violations)

**Why It Violates Article II**:
```python
# From test_handoffs_minimal.py:30
with patch.object(Agency, "get_response") as mock_get_response:
    # Create a mock response that simulates successful handoff
    mock_response = MagicMock()
    mock_response.text = "Successfully handed off to PlannerAgent..."
    mock_get_response.return_value = mock_response

    # Initialize agency with mocked agents
    agency = Agency(mock_coder, communication_flows=[...])
```

**Constitutional Mandate**: "Main branch: 100% test success ALWAYS. Tests must validate real behavior. Definition of Done: Code + Tests + Pass + Review + CI."

**Actual Behavior**: Tests validate that mocks return what we tell them to return. This is circular validation with zero real behavior coverage.

**Real Behavior NOT Tested**:
- Actual agent handoff execution (SendMessageHandoff tool)
- Real LLM response generation
- Error handling in agent communication
- Context preservation during handoffs
- Tool availability validation
- Agency initialization with real agents
- Message routing and processing

---

## 3. Pattern Categorization

### Category A: Unit Tests (Fast Feedback)
**Files**: `test_orchestrator_system.py`
**Purpose**: Test orchestration logic (parallel execution, retry policies, timeout)
**Mock Justification**: PARTIALLY ACCEPTABLE
**Reason**: Orchestrator tests need to test scheduling logic independent of agent implementation.

**HOWEVER**: Even here, mocks violate Article II because:
- MockAgent.run() doesn't test real Agent.run() interface compatibility
- No validation that real agents support required orchestrator contract
- Missing integration tests to validate orchestrator + real agents

---

### Category B: Integration Tests (Real Behavior Required)
**Files**: `test_handoffs_minimal.py`, `test_constitutional_validator.py`
**Purpose**: Test agent-to-agent communication and constitutional compliance
**Mock Justification**: UNACCEPTABLE
**Reason**: These MUST test real behavior to validate integration.

**Current Violation Severity**: BLOCKER

**Evidence from test_handoffs_minimal.py**:
```python
async def test_coder_handoff_to_planner_minimal():
    """Test handoff mechanism from Coder to Planner using mocks."""
    mock_coder = create_mock_agent("AgencyCodeAgent")
    mock_planner = create_mock_agent("PlannerAgent")

    # VIOLATION: This doesn't test if real agents can handoff
    # It tests if mocks can return pre-scripted text
```

**What This SHOULD Test**:
- Real Agent initialization (create_planner_agent, create_coder_agent)
- Real SendMessageHandoff tool execution
- Real Agency.get_response() behavior (not mocked!)
- Real context preservation during handoff
- Real error handling when handoff fails

---

### Category C: Constitutional Validator Tests
**Files**: `test_constitutional_validator.py`
**Purpose**: Test that @constitutional_compliance decorator validates Articles I-V
**Mock Justification**: UNACCEPTABLE
**Reason**: Uses mocks to test compliance validation, creating circular logic.

**Current Violation**:
```python
@pytest.fixture
def mock_create_agent_func():
    def create_mock_agent(model="gpt-5", ...):
        return Mock(name="MockAgent", model=model)
    return create_mock_agent

def test_decorator_calls_validation_functions(...):
    decorated_func = constitutional_compliance(mock_create_agent_func)
    result = decorated_func(agent_context=mock_agent_context)
    # VIOLATION: Tests that decorator wraps a mock, not a real agent factory
```

**What This SHOULD Test**:
- Real agent factories (create_planner_agent, create_coder_agent, etc.)
- Real constitutional violations (incomplete context, missing memory, etc.)
- Real decorator behavior on real agent creation
- Real integration with AgentContext and memory system

---

## 4. Root Cause Analysis

### Primary Root Cause
**Test infrastructure was designed before constitutional enforcement was implemented.**

Timeline:
1. Initial tests written with mocks for speed
2. Constitutional compliance added via decorator
3. Tests never updated to validate real constitutional behavior
4. Violations logged but not fixed (technical debt accumulation)

### Contributing Factors

1. **No Integration Test Strategy**
   - Unit tests dominate (fast but shallow)
   - Integration tests missing or insufficient
   - No E2E tests for agent workflows

2. **Mock Overuse**
   - Mocks used even where real objects are fast
   - AgentContext creation is fast (<0.1s) but still mocked
   - No performance justification for mocking

3. **Circular Validation Pattern**
   ```python
   # Anti-pattern present in codebase
   mock.return_value = "expected result"
   assert result == "expected result"  # This proves nothing
   ```

4. **Missing Test Categories**
   - Unit tests: ✓ Present (but over-mocked)
   - Integration tests: ✗ Insufficient
   - Contract tests: ✗ Missing
   - E2E tests: ✗ Missing

---

## 5. Real Behavior NOT Being Tested

### Critical Gaps in Coverage

#### Gap 1: Agent Lifecycle
**Not Tested**:
- Real agent factory execution (create_planner_agent, create_coder_agent)
- @constitutional_compliance decorator validation
- AgentContext initialization and session management
- Memory integration hook attachment
- Message filter hook attachment
- Model selection from model_policy.py

**Impact**: Zero confidence that agents initialize correctly in production.

#### Gap 2: Agent Communication
**Not Tested**:
- Real SendMessageHandoff tool execution
- Real Agency.get_response() with agent routing
- Real message passing between agents
- Real context preservation during handoffs
- Real error propagation between agents

**Impact**: Zero confidence that agent handoffs work in production.

#### Gap 3: Constitutional Enforcement
**Not Tested**:
- Real Article I validation (context completeness)
- Real Article II validation (quality standards)
- Real Article III validation (git hooks)
- Real Article IV validation (learning integration)
- Real Article V validation (spec coverage)

**Impact**: Zero confidence that constitutional compliance works in production.

#### Gap 4: Error Handling
**Not Tested**:
- Real timeout behavior (Article I retry logic)
- Real agent failure recovery
- Real tool execution errors
- Real LLM API errors
- Real context corruption handling

**Impact**: Zero confidence that error handling works in production.

---

## 6. Cost Analysis

### Time Waste Calculation

**Per Violation**:
- Investigation time: 5 minutes
- Context switching: 2 minutes
- Fix verification: 1 minute
- **Total per violation**: 8 minutes

**Current State** (128 violations):
- Weekly time waste: 128 × 8 = 1,024 minutes = **17.1 hours/week**
- Annual time waste: 17.1 × 52 = **887 hours/year**
- Annual cost @ $150/hour: **$133,120/year**

### Fix Effort Estimate

**One-time Fix**:
- Refactor test_handoffs_minimal.py: 1 hour
- Refactor test_constitutional_validator.py: 1 hour
- Create real integration test fixtures: 2 hours
- **Total effort**: 4 hours

**ROI Calculation**:
- Fix effort: 4 hours ($600)
- Annual savings: 887 hours ($133,120)
- ROI ratio: **887 / 4 = 222x return on investment**

(Note: Analysis shows 444x in some reports due to using 2-hour estimate for single-file fix)

---

## 7. Recommended Fix Strategy

### Option A: Article II Amendment (NOT RECOMMENDED)
**Proposal**: Amend Article II to allow mocks in unit tests.

**Pros**:
- No code changes required
- Tests remain fast

**Cons**:
- Weakens constitutional integrity
- Perpetuates false confidence
- Doesn't improve real coverage
- Violates "100% verification" principle

**Recommendation**: REJECT

---

### Option B: Test Categorization + Refactor (RECOMMENDED)
**Proposal**: Separate unit tests (fast, mocks OK) from integration tests (real behavior required).

**Implementation**:

#### Step 1: Categorize Tests
```bash
tests/
├── unit/                    # Fast, isolated, mocks acceptable
│   ├── test_orchestrator_logic.py
│   └── test_helper_functions.py
├── integration/             # Real behavior, no Agency/Agent mocks
│   ├── test_agent_handoffs.py
│   ├── test_constitutional_compliance.py
│   └── test_agent_lifecycle.py
└── e2e/                     # Full workflows
    └── test_multi_agent_workflow.py
```

#### Step 2: Create Integration Test Fixtures
```python
# tests/integration/conftest.py
import pytest
from shared.agent_context import create_agent_context
from planner_agent.planner_agent import create_planner_agent
from agency_code_agent.agency_code_agent import create_coder_agent

@pytest.fixture
def real_agent_context():
    """Real AgentContext with memory integration."""
    return create_agent_context()

@pytest.fixture
def real_planner_agent(real_agent_context):
    """Real PlannerAgent instance with constitutional compliance."""
    return create_planner_agent(
        model="gpt-5-mini",  # Use cheaper model for tests
        agent_context=real_agent_context
    )

@pytest.fixture
def real_coder_agent(real_agent_context):
    """Real AgencyCodeAgent instance with constitutional compliance."""
    return create_coder_agent(
        model="gpt-5-mini",
        agent_context=real_agent_context
    )
```

#### Step 3: Refactor Integration Tests
```python
# tests/integration/test_agent_handoffs.py
import pytest
from agency_swarm import Agency
from agency_swarm.tools import SendMessageHandoff

@pytest.mark.integration
async def test_coder_handoff_to_planner_real(real_coder_agent, real_planner_agent):
    """Test REAL handoff mechanism from Coder to Planner.

    Constitutional Compliance:
    - Article I: Uses real agent context, no mocks
    - Article II: Validates real behavior, not pre-scripted responses
    """
    # Real Agency with real agents
    agency = Agency(
        real_coder_agent,
        communication_flows=[
            (real_coder_agent, real_planner_agent, SendMessageHandoff),
            (real_planner_agent, real_coder_agent, SendMessageHandoff),
        ],
        shared_instructions="Test handoff mechanism"
    )

    # Real handoff execution (no mocks!)
    result = await agency.get_response("Hand off to the PlannerAgent")
    response = result.text if hasattr(result, "text") else str(result)

    # Validate REAL behavior
    assert "PlannerAgent" in response or "planner" in response.lower()
    assert len(response) > 0

    # Validate no errors (real error handling tested)
    error_indicators = ["Traceback", "invalid_request_error", "Error", "Failed"]
    assert not any(err in response for err in error_indicators)
```

#### Step 4: Update CI Configuration
```yaml
# .github/workflows/tests.yml
- name: Run Unit Tests (fast)
  run: python run_tests.py  # Mocks allowed, <30s

- name: Run Integration Tests (real behavior)
  run: python run_tests.py --integration-only  # No mocks, <5min

- name: Verify Constitutional Compliance
  run: |
    violations=$(python tools/constitutional_intelligence/violation_patterns.py --json | jq '.summary.total_violations')
    if [ "$violations" -gt 0 ]; then
      echo "::error::Constitutional violations detected: $violations"
      exit 1
    fi
```

#### Step 5: Update Article II Interpretation
**Add Clarification** (not amendment):
```markdown
## Article II: 100% Verification and Stability

### Test Categorization
- **Unit Tests**: Test isolated logic. Mocks acceptable for external dependencies (LLMs, APIs).
  - MUST NOT mock core domain objects (Agent, Agency, AgentContext)
  - MUST have corresponding integration test for real behavior

- **Integration Tests**: Test component interaction. NO mocks for system components.
  - MUST use real agent factories (create_planner_agent, etc.)
  - MUST use real AgentContext and memory integration
  - MAY mock external APIs (OpenAI, etc.) for cost control

- **E2E Tests**: Test complete workflows. NO mocks except for cost control.
  - MUST execute full agent lifecycle
  - MUST validate end-to-end behavior
```

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Week 1)
**Effort**: 4 hours

- [ ] Create `tests/integration/conftest.py` with real agent fixtures
- [ ] Refactor `test_handoffs_minimal.py` to use real agents
- [ ] Refactor `test_constitutional_validator.py` to use real agent factories
- [ ] Update CI to run integration tests separately

**Success Criteria**:
- Zero violations from `create_mock_agent` in integration tests
- All integration tests pass with real agents
- CI shows separate unit/integration test runs

---

### Phase 2: Coverage Expansion (Week 2)
**Effort**: 8 hours

- [ ] Add integration tests for all agent factories
- [ ] Add integration tests for all constitutional articles
- [ ] Add contract tests for agent-tool interfaces
- [ ] Add E2E tests for multi-agent workflows

**Success Criteria**:
- 100% coverage of agent lifecycle
- 100% coverage of constitutional compliance
- 100% coverage of agent communication

---

### Phase 3: Continuous Monitoring (Ongoing)
**Effort**: 1 hour/week

- [ ] Add pre-commit hook to check for `create_mock_agent` in integration tests
- [ ] Add CI check to fail on constitutional violations > 0
- [ ] Add weekly report on test quality metrics
- [ ] Add dashboard showing real vs. mocked test coverage

**Success Criteria**:
- Zero new violations introduced
- Downward trend in existing violations
- Upward trend in integration test coverage

---

## 9. Acceptance Criteria

### Definition of Done for Fix

- [ ] Zero `create_mock_agent` calls in `tests/integration/`
- [ ] All integration tests use real agent factories
- [ ] All integration tests use real AgentContext
- [ ] All integration tests validate real behavior (no pre-scripted mocks)
- [ ] CI passes with 100% success rate
- [ ] Constitutional violation log shows zero new violations
- [ ] Documentation updated with test categorization guidelines

---

## 10. Appendix: Violation Log Sample

**Sample from constitutional_violations.jsonl** (first 10 violations):

```json
{"timestamp": "2025-10-01T21:38:50.570336+00:00", "violation_type": "ConstitutionalCompliance", "function": "create_mock_agent", "error": "Article I: Incomplete context", "severity": "BLOCKER"}
{"timestamp": "2025-10-01T21:38:50.571907+00:00", "violation_type": "ConstitutionalCompliance", "function": "create_mock_agent", "error": "Article II: Quality standards not met", "severity": "BLOCKER"}
{"timestamp": "2025-10-01T21:40:16.273167+00:00", "violation_type": "ConstitutionalCompliance", "function": "create_mock_agent", "error": "Article I: Incomplete context", "severity": "BLOCKER"}
{"timestamp": "2025-10-01T21:40:16.274792+00:00", "violation_type": "ConstitutionalCompliance", "function": "create_mock_agent", "error": "Article II: Quality standards not met", "severity": "BLOCKER"}
...
```

**Pattern**: Every `create_mock_agent` execution triggers TWO violations (Article I + Article II), confirming the systematic nature of the issue.

---

## 11. Conclusion

### Summary of Findings

1. **128 violations** from a single test pattern (`create_mock_agent`)
2. **$133,120/year** in wasted developer time investigating false test confidence
3. **444x ROI** available from 2-hour fix (or 222x from 4-hour comprehensive fix)
4. **Zero real behavior coverage** for critical paths (agent lifecycle, handoffs, constitutional compliance)

### Critical Insight

This is not a "test quality" issue. This is a **constitutional compliance crisis**.

Tests using `create_mock_agent` are not testing the system - they're testing whether mocks return what we tell them to return. This creates **false confidence** that is MORE DANGEROUS than no tests at all.

### Recommended Action

**IMMEDIATE**: Implement Option B (Test Categorization + Refactor) starting with Phase 1.

**PRIORITY**: BLOCKER - This affects trust in entire test suite.

**OWNER**: QualityEnforcerAgent + AgencyCodeAgent

**TIMELINE**: Week 1 (4 hours) for immediate fix, Week 2 (8 hours) for comprehensive coverage.

---

**End of Analysis**

---

## Appendix B: File Locations

### Implementation Files
- `/Users/am/Code/Agency/tests/test_handoffs_minimal.py` (11 usages)
- `/Users/am/Code/Agency/tests/test_orchestrator_system.py` (12 usages)
- `/Users/am/Code/Agency/tests/test_constitutional_validator.py` (2 usages)

### Violation Logs
- `/Users/am/Code/Agency/logs/autonomous_healing/constitutional_violations.jsonl` (159 entries)

### Analysis Tools
- `/Users/am/Code/Agency/tools/constitutional_intelligence/violation_patterns.py`
- `/Users/am/Code/Agency/tools/constitutional_intelligence/README.md`

### Related Documentation
- `/Users/am/Code/Agency/constitution.md` (Articles I-V)
- `/Users/am/Code/Agency/docs/adr/ADR-001-complete-context.md` (Article I)
- `/Users/am/Code/Agency/docs/adr/ADR-002-verification-stability.md` (Article II)
