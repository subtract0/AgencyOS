# Agency Constitution

> *The non-negotiable rulebook for all agents and engineering decisions*

**Version**: 1.0
**Established**: 2025-09-22
**Authority**: Mandated by @am
**Compliance**: Mandatory for all agents

---

## Preamble

This constitution establishes the fundamental principles governing the Agency multi-agent system. These rules are **non-negotiable** and **machine-enforceable**. All agents MUST read, understand, and adhere to these principles before generating any plans, specifications, or implementations.

**Core Philosophy**: *Professional excellence through automated discipline and continuous learning.*

---

## Article I: Complete Context Before Action (ADR-001)

### Section 1.1: Foundational Principle
**No action shall be taken without complete contextual understanding.**

### Section 1.2: Mandatory Practices

#### Timeout Handling
- At EVERY timeout: halt and analyze
- Retry with extended timeouts
- NEVER proceed with incomplete data
- NEVER declare "I have seen enough" with partial results

#### Test Execution
- ALL tests MUST run to completion
- Upon failures or skips: IMMEDIATELY halt
- Fix failing tests BEFORE new features
- NO mission is complete while tests fail

#### Context Verification
- Explicitly verify: "Do I have all information?"
- When uncertain: re-execute
- Better 5 minutes of waiting than 5 hours in wrong direction

#### No Broken Windows!
- Applies to ALL generated code
- Applies to "temporary" solutions
- Applies under ALL circumstances
- Zero tolerance for compromised quality

### Section 1.3: Implementation Requirements
```python
# Required pattern for all agents
def ensure_complete_context(operation_func, max_retries=3):
    timeout = 120000  # Start with 2 minutes

    for attempt in range(max_retries):
        result = operation_func(timeout=timeout)

        if result.timed_out:
            timeout *= 2  # Double timeout for retry
            continue

        if result.incomplete:
            continue  # Retry with same timeout

        if result.has_failures():
            raise Exception("STOP: Fix failures before proceeding")

        return result

    raise Exception("Unable to obtain complete context")
```

---

## Article II: 100% Verification and Stability (ADR-002)

### Section 2.1: Foundational Principle
**A task is complete ONLY when 100% verified and stable.**

### Section 2.2: Non-Negotiable Standards

#### Test Success Rate
- Main branch MUST maintain 100% test success
- No merge without completely green CI pipeline
- Failing tests block ALL other activities
- **100% is not negotiable - no exceptions**

#### Quality Requirements
- Tests MUST verify REAL functionality, not simulated behavior
- No test deactivation or skip markers (except platform-specific)
- No assertion removal to force test passage
- When tests fail: code is wrong, not test

#### No Simulation in Production (Amendment 2025-10-02)
- Mocked functions SHALL NOT be merged to main branch
- Simulated work (print statements, hardcoded responses) is NOT production-ready
- Demonstration code MUST remain in feature branches or docs/examples/
- Only fully-implemented, tested functionality may merge to main
- "Green tests" means tests validate REAL behavior, not mock behavior

#### "Delete the Fire First" Priority
- BEFORE new features: all tests green
- BEFORE refactoring: all tests green
- BEFORE optimization: all tests green
- Broken windows have ALWAYS highest priority

#### Definition of Done
1. Code written ✓
2. Tests written ✓
3. All tests pass (local verification: `python run_tests.py --run-all`) ✓
4. Code review ✓
5. Quality gates pass (local hooks + agent validation OR optional CI) ✓
6. = COMPLETE (not before)

**Note**: Local test verification (`python run_tests.py --run-all` showing 100% pass) is constitutionally equivalent to CI pipeline verification. Both satisfy Article II requirements.

### Section 2.3: Enforcement Mechanisms
```bash
# Required pre-commit pattern
if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo "❌ BLOCKED by Constitution Article II"
    echo "100% test success required - no exceptions"
    exit 1
fi
```

### Section 2.4: Hardware-Aware Execution (Amendment 2025-10-08, ADR-023)

**Context**: Agency OS runs on Apple M4 Pro with 48GB unified memory. Operations must respect hardware constraints to ensure stability and test completion.

#### Hardware Constraints
- **Target System**: MacBook Pro M4 Pro, 48GB RAM, 273 GB/s memory bandwidth
- **macOS Reserved**: ~8GB (system, WindowServer, background services)
- **Available RAM**: 40GB (48GB - 8GB)
- **Safe Budget**: 35GB (with 5GB safety margin for peaks)

#### Memory-Aware Requirements

**Local Model Execution**:
- Local models MUST use optimized quantization (Q4_K_M weights + Q8_0 KV cache)
- Model memory footprint MUST NOT exceed 37GB (19GB + 16GB + 2GB)
- KV cache MUST use Q8_0 or Q4_0 quantization (not F16)
- Configuration: `OLLAMA_KV_CACHE_TYPE="q8_0"`, `OLLAMA_FLASH_ATTENTION=1`

**Test Parallelism**:
- Test workers MUST dynamically adjust based on local model state
- With local model active: MAX 3 workers (9GB)
- Without local model: MAX 10 workers (30GB)
- Total memory usage MUST NOT exceed 40GB (85% of 48GB)

**Memory Pressure Response**:
- Operations MUST check available memory before spawning parallel processes
- Memory exhaustion MUST trigger cloud API fallback for P3 tasks
- Kernel panics constitute BLOCKING violations requiring immediate mitigation
- Test execution incomplete due to OOM = Article I violation (incomplete context)

#### Implementation Requirements
```python
# Required memory check pattern
import psutil

def verify_memory_safe(required_gb: int) -> bool:
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024 ** 3)
    return available_gb >= required_gb + 5  # 5GB safety margin

# Before parallel operations
if not verify_memory_safe(required_gb=10):
    # Fall back to cloud API or sequential execution
    use_cloud_fallback()
```

**Reference**: `docs/HARDWARE_OPTIMIZATION.md` for complete memory budgets and optimization techniques.

---

## Article III: Automated Local Enforcement (ADR-003)

### Section 3.1: Foundational Principle
**Quality standards SHALL be technically enforced through local gates and automation, not manually governed or dependent on paid infrastructure.**

### Section 3.2: Enforcement Architecture

#### Zero-Tolerance Policy
- No manual override capabilities for quality standards
- No "emergency bypass" mechanisms
- 100% test success at ALL enforcement layers
- Automatic rejection of quality violations
- **Constitutional compliance is FREE** - no paid services required

#### Multi-Layer Local Enforcement (Cost: $0/month)
1. **Pre-commit Hook** (LOCAL, MANDATORY): Prevents commits with failing tests
2. **Pre-push Verification** (LOCAL, MANDATORY): Requires 100% test pass before push
3. **Agent Validation** (LOCAL, MANDATORY): Automated constitutional compliance checking
4. **Branch Protection** (GITHUB FREE TIER): PR review requirements, protected branches

#### Optional Remote Enforcement (Cost: Variable)
- **CI/CD Pipeline** (OPTIONAL): Automated remote verification via GitHub Actions
- **Status**: Currently disabled to reduce costs (all workflows in `.disabled` state)
- **Re-enablement**: Available when budget permits, not constitutionally required
- **Substitute**: Local verification is equally valid and constitutionally compliant

#### No Bypass Authority
- No human can override local quality gates
- No emergency exceptions permitted
- Quality gates are absolute barriers (local or remote)
- System failure requires infrastructure repair, not bypass
- **Local enforcement IS automated enforcement** - equally valid as CI/CD

### Section 3.3: Agent Requirements
```python
# All agents must implement enforcement checking
def validate_constitutional_compliance(operation):
    if not passes_article_i_verification(operation):
        raise ConstitutionalViolation("Article I: Incomplete context")
    if not passes_article_ii_verification(operation):
        raise ConstitutionalViolation("Article II: Quality standards not met")
    if not passes_article_iii_verification(operation):
        raise ConstitutionalViolation("Article III: Enforcement bypassed")
    return True
```

---

## Article IV: Continuous Learning and Improvement (ADR-004)

### Section 4.1: Foundational Principle
**The Agency SHALL continuously improve through experiential learning.**

### Section 4.2: Learning Requirements

#### Automatic Learning Triggers
- After successful session completion
- After error resolution sequences
- After effective tool usage patterns
- When performance milestones achieved

#### Learning Quality Standards
- Minimum confidence threshold: 0.6
- Minimum evidence count: 3 occurrences
- Pattern validation required before storage
- Regular cleanup of outdated learnings

#### Collective Intelligence
- All agents benefit from shared learnings
- Cross-session pattern recognition required
- Knowledge accumulates in VectorStore
- Learning-informed decision making mandatory

### Section 4.3: Self-Improvement Mandate
```python
# Required learning integration pattern
class ConstitutionalAgent:
    def __init__(self, agent_context):
        self.learning_store = agent_context.vector_store
        self.constitutional_compliance = True

    def before_action(self, context):
        # Check constitutional compliance
        self.validate_constitutional_adherence()
        # Apply relevant learnings
        self.apply_historical_learnings(context)

    def after_action(self, result):
        # Extract learnings from experience
        self.extract_and_store_learnings(result)
```

---

## Article V: Spec-Driven Development (This Constitution)

### Section 5.1: Foundational Principle
**All development SHALL follow formal specification and planning processes.**

### Section 5.2: Mandatory Workflows

#### Specification Requirement
- New features MUST begin with formal spec.md
- Spec follows template: Goals, Non-Goals, Personas, Acceptance Criteria
- No implementation without approved specification
- Specifications are living documents - updated as needed

#### Technical Planning Requirement
- Approved specs MUST generate formal plan.md
- Plans detail: Architecture, Agent assignments, Tool usage, Contracts
- Implementation blocked until plan approval
- Plans reference constitutional requirements

#### Task Granularity Requirement
- Plans MUST decompose into TodoWrite task lists
- Each task MUST reference spec and plan sections
- Tasks MUST be verifiable against acceptance criteria
- Progress tracking required throughout implementation

### Section 5.3: Agent Compliance Requirements
```python
# Required pattern for all planning agents
def constitutional_planning_process(feature_request):
    # 1. Read constitution for compliance requirements
    constitution = read_constitution()

    # 2. Generate specification following Article V requirements
    spec = generate_specification(feature_request, constitution)

    # 3. Create implementation plan with constitutional validation
    plan = create_implementation_plan(spec, constitution)

    # 4. Break down into constitutional-compliant tasks
    tasks = create_granular_tasks(plan, constitution)

    return spec, plan, tasks
```

---

## Article VI: Red-Green-Refactor TDD Workflow (Amendment 2025-10-14)

### Section 6.1: Foundational Principle
**All development SHALL follow strict Test-Driven Development: tests are written FIRST and MUST fail, proving they test real requirements.**

### Section 6.2: Mandatory Workflow (No Exceptions)

#### The Sacred Sequence
```
Natural Language Intent
    ↓
Technical Specification (acceptance criteria)
    ↓
Write Tests FIRST (RED: tests MUST fail initially)
    ↓
Implement Code (GREEN: iterate until 100% tests pass)
    ↓
Refactor (REFACTOR: improve while maintaining 100% pass)
```

#### RED Phase (Failing Tests Required)
- Tests MUST be written BEFORE any implementation code
- Tests MUST fail initially (proves they test real functionality)
- Failed tests MUST verify against specification acceptance criteria
- "Test passes without implementation" = test is broken, not implementation
- Minimum test coverage: NECESSARY pattern (Normal, Edge, Constraints, Error, Security, Scale, Async, Retry, Yield)

#### GREEN Phase (Implementation to Pass Tests)
- Implementation begins ONLY after tests are written and failing
- Iterate implementation until 100% of tests pass
- No skipping tests to achieve "green"
- No modifying tests to make them pass (fix implementation, not tests)
- 100% pass rate is the ONLY acceptable outcome

#### REFACTOR Phase (Improve While Maintaining Green)
- Refactoring permitted ONLY when all tests are green
- All tests MUST remain passing during refactoring
- No "temporary" test skips during refactoring
- Refactoring that breaks tests is reverted immediately

### Section 6.3: Prohibited Practices

#### "Pragmatic Approaches" That Violate TDD
- ❌ **FORBIDDEN**: "Given the spec, I can move directly to implementation"
- ❌ **FORBIDDEN**: "Let me consolidate test definitions with implementation"
- ❌ **FORBIDDEN**: "These test specs are sufficient, proceeding to code"
- ❌ **FORBIDDEN**: Any workflow that skips RED phase (failing tests first)

#### Valid Test-First Development
- ✅ **REQUIRED**: Write test file → Run test → See failure → Implement → Run test → See success
- ✅ **REQUIRED**: Every acceptance criterion gets a failing test before implementation
- ✅ **REQUIRED**: Tests verify ACTUAL behavior (not mocked/stubbed responses)
- ✅ **REQUIRED**: Test execution demonstrates specification compliance

### Section 6.4: Implementation Requirements

```python
def constitutional_tdd_workflow(intent: str) -> Result[str, str]:
    """
    Article VI enforcement: Strict TDD workflow.

    Workflow:
        1. Intent → Spec (acceptance criteria defined)
        2. Spec → Tests (written first, MUST fail)
        3. Tests → Implementation (iterate until 100% pass)
        4. Implementation → Refactor (maintain 100% pass)
    """
    # Phase 1: Generate specification
    spec = generate_specification(intent)
    validate_acceptance_criteria_exist(spec)

    # Phase 2: Write tests FIRST (RED)
    tests = write_tests_from_spec(spec)
    test_results = run_tests(tests)

    # Validation: Tests MUST fail initially
    if test_results.pass_rate == 1.0:
        raise ConstitutionalViolation(
            "Article VI: Tests passed without implementation. "
            "Tests must fail first to prove they verify real requirements."
        )

    # Phase 3: Implement until tests pass (GREEN)
    while test_results.pass_rate < 1.0:
        implementation = implement_to_pass_tests(tests, test_results)
        test_results = run_tests(tests)

        if implementation.timeout_exceeded:
            raise ConstitutionalViolation("Article I: Complete context required")

    # Phase 4: Refactor while maintaining green
    if refactoring_needed(implementation):
        refactored = refactor_code(implementation)
        test_results = run_tests(tests)

        if test_results.pass_rate < 1.0:
            raise ConstitutionalViolation(
                "Article VI: Refactoring broke tests. "
                "Revert changes and refactor again."
            )

    return Ok("TDD workflow complete: 100% test pass rate")
```

### Section 6.5: Orchestrator-Level TDD Enforcement

#### PrimeA Orchestrator Compliance
When generating task graphs, orchestrators MUST enforce:

1. **Test Tasks Before Code Tasks**:
   ```json
   {
     "phase_1_testing": {
       "tasks": [
         {"id": "test_feature_x", "type": "Test", "dependencies": ["spec"]}
       ]
     },
     "phase_2_implementation": {
       "tasks": [
         {"id": "code_feature_x", "type": "Code", "dependencies": ["test_feature_x"]}
       ]
     }
   }
   ```

2. **Test Verification Gate**:
   - Test tasks execute FIRST
   - Tests MUST initially fail (RED)
   - Code tasks execute ONLY after test verification
   - Code tasks iterate until tests pass (GREEN)

3. **No "Pragmatic Shortcuts"**:
   - Cannot skip from Spec → Implementation
   - Cannot consolidate test definition with implementation
   - Cannot proceed without explicit RED → GREEN transition
   - Cannot mark Code task complete without 100% test pass rate

### Section 6.6: Enforcement Mechanisms

```python
# Pre-commit hook validation
def validate_tdd_compliance(commit_files):
    """Verify TDD workflow was followed."""

    # Check for orphaned implementation (code without tests)
    code_files = [f for f in commit_files if is_implementation_file(f)]
    test_files = [f for f in commit_files if is_test_file(f)]

    if code_files and not test_files:
        raise ConstitutionalViolation(
            "Article VI: Implementation committed without corresponding tests. "
            "TDD requires tests FIRST."
        )

    # Check for test passage without implementation changes
    # (indicates tests were modified to pass, not implementation)
    git_log = get_commit_history(commit_files)
    if test_files_modified_after_passing(git_log):
        raise ConstitutionalViolation(
            "Article VI: Tests modified after passing. "
            "Fix implementation, not tests."
        )

    return True
```

### Section 6.7: Success Criteria

**Article VI compliance is achieved when**:
- ✅ 100% of Code tasks have preceding Test tasks in dependency graph
- ✅ Test tasks generate failing tests initially (RED phase documented)
- ✅ Implementation tasks iterate until 100% test pass rate (GREEN phase documented)
- ✅ No "pragmatic" shortcuts bypass RED → GREEN workflow
- ✅ Git history shows test commits BEFORE implementation commits
- ✅ Refactoring occurs ONLY when tests are passing (GREEN maintained)

---

## Article VII: Value-First Testing Philosophy (Amendment 2025-10-23)

### Section 7.1: Foundational Principle
**Tests SHALL prioritize actual bug detection over comprehensive coverage. Delete tests with value score <10. Keep tests with score >20. Let ACTUAL QUALITY determine the final count, not arbitrary targets.**

**Quality > Quantity. Integration > Unit. Behavior > Implementation.**

### Section 7.2: The Testing Inversion Problem

#### Current Anti-Pattern (Inverted Pyramid)
```
        /\
       /UI\         ← 100 end-to-end tests
      /    \
     /Integ.\       ← 500 integration tests
    /        \
   /   Unit   \     ← 5,954 unit tests (TOO MANY!)
  /____________\
```

**Problems**:
- 6,554 tests but many catch no real bugs
- Unit tests test implementation details (break on every refactor)
- Mocking hell: Mock everything, test nothing real
- Slow CI/CD (30+ minutes)
- High maintenance burden (100+ tests break per refactor)

#### Target Pattern (Proper Pyramid)
```
  /\
 /UI\              ← 100 end-to-end tests (keep)
/____\
/Integ\            ← 1,500 integration tests (INCREASE!)
/______\
/ Unit  \          ← 900 unit tests (REDUCE 85%!)
/________\
```

**Goals**:
- HIGH-VALUE tests (based on actual scores, not arbitrary count)
- Integration tests > Unit tests (test behavior, not implementation)
- Fast CI/CD (let quality improvements determine speed)
- Low maintenance (fewer tests breaking on refactors)

### Section 7.3: Test Value Scoring

#### Value Formula
```python
test_value = (
    bug_detection_score * 10 +      # 0-10: Real bugs caught
    critical_path_score * 5 +        # 0-10: Tests core logic
    integration_score * 3 -          # 0-10: Tests real components
    runtime_penalty * 0.1 -          # Penalty for slow tests
    maintenance_burden * 2           # Penalty for fragile tests
)
```

#### Test Categories
- **HIGH (>20)**: KEEP - Integration, critical path, security, e2e
- **MEDIUM (10-20)**: REVIEW - Complex algorithms, edge cases, consolidate
- **LOW (<10)**: DELETE - Mocking hell, implementation details, redundant

### Section 7.4: Mandatory Test Classification

#### Tests to KEEP (Based on Score >20)
- ✅ **Integration tests**: Test real components working together
- ✅ **E2E tests**: Test complete user workflows
- ✅ **Critical path tests**: Core business logic
- ✅ **Security tests**: Auth, injection, XSS, CSRF
- ✅ **Regression tests**: Real bugs that were fixed
- ✅ **Property-based tests**: Hypothesis-driven edge coverage

#### Tests to DELETE (Based on Score <10)
- ❌ **Mocking hell**: >10 mocks, <3 assertions
- ❌ **Implementation detail tests**: Tests HOW, not WHAT
- ❌ **Framework tests**: Testing library behavior, not our code
- ❌ **Redundant tests**: Same behavior tested 5 different ways
- ❌ **"Just in case" tests**: Scenarios that never happen
- ❌ **Tests that never fail**: Always pass (no value)

#### Tests to CONSOLIDATE (Based on Redundancy Detection)
- 🔄 **Parameterize similar tests**: N tests → 1 parameterized test
- 🔄 **Merge overlapping coverage**: Test A + B → Single comprehensive test
- 🔄 **Convert to property-based**: Multiple edge cases → 1 hypothesis test

### Section 7.5: Test Quality Standards

#### What Makes a Test HIGH-VALUE?
1. **Tests BEHAVIOR, not implementation**:
   - ✅ GOOD: `assert user_can_login_with_valid_credentials()`
   - ❌ BAD: `mock_auth.login.assert_called_once_with(username, password)`

2. **Uses REAL components, not mocks**:
   - ✅ GOOD: `result = memory_store.set("key", "value"); assert memory_store.get("key") == "value"`
   - ❌ BAD: `mock_store.set.assert_called_once(); mock_store.get.return_value = "value"`

3. **Catches REAL bugs**:
   - ✅ GOOD: Security tests (injection, XSS)
   - ✅ GOOD: Data integrity tests (corruption, loss)
   - ❌ BAD: Constructor tests with all mocks

4. **Fast feedback**:
   - ✅ GOOD: <1 second per test (integration), <10ms per test (unit)
   - ❌ BAD: >10 seconds per test (slow, blocks CI/CD)

5. **Low maintenance**:
   - ✅ GOOD: Survives refactors (tests interface, not internals)
   - ❌ BAD: Breaks on every refactor (tests implementation details)

### Section 7.6: NECESSARY Pattern - Revised for Value

#### OLD NECESSARY Pattern (Coverage-First)
```python
# 9 categories: Normal, Edge, Cascading, Essential, Security, Spec,
# Accessibility, Resilience, Year-round
# Problem: Optimizes for comprehensive coverage, not bug detection
```

#### NEW NECESSARY Pattern (Value-First)
```python
# Test what MATTERS:
# 1. Integration tests for critical paths (highest value)
# 2. Security tests for vulnerabilities (critical)
# 3. Edge cases for algorithms (medium value)
# 4. Normal cases for happy paths (baseline)
#
# DO NOT TEST:
# - Implementation details (mocking hell)
# - Framework behavior (not our code)
# - Redundant scenarios (consolidate)
```

#### Value-First Test Selection
For each test, ask:
1. **Does this catch real bugs?** (If no → DELETE)
2. **Does this test behavior or implementation?** (Implementation → DELETE)
3. **Is this tested by integration tests?** (If yes → DELETE unit test)
4. **Is this redundant?** (If yes → CONSOLIDATE)
5. **Is this slow or flaky?** (If yes → FIX or DELETE)

### Section 7.7: Test Suite Health Metrics

#### Mandatory Metrics (Quality-Based, Not Prescriptive)
- **Test count**: Result of quality-based deletion (let audit determine)
- **Test pyramid ratio**: Integration > Unit (audit determines actual ratio)
- **CI/CD time**: Faster than before (improvement measured)
- **Bug detection rate**: Higher than before (integration tests)
- **Maintenance burden**: Fewer tests breaking (behavior > implementation)
- **Test suite health score**: >80/100 (calculated, not prescribed)

#### Health Score Formula
```python
health_score = (
    (integration_test_pct * 0.3) +           # 70% integration = 21 points
    (high_value_test_pct * 0.4) +            # 50% high-value = 20 points
    (100 - ci_time_minutes * 2) * 0.2 +      # <15min = 14 points
    (bug_detection_rate * 20) * 0.1          # 0.5/test/year = 10 points
)
# Target: >80/100
```

### Section 7.8: Implementation Requirements

#### Test Value Audit (Mandatory)
```python
# Run test value audit
from scripts.test_value_audit import TestValueAuditor

auditor = TestValueAuditor()
results = auditor.run_audit(test_dir=Path("tests"))

# Review results
delete_candidates = [t for t in results['tests'] if t['action'] == 'DELETE']
print(f"Found {len(delete_candidates)} low-value tests to delete")

# Delete after manual review
auditor.save_results()  # Generates deletion candidate list
```

#### Test Generator Compliance
```python
# test_generator_agent MUST prioritize value
def generate_tests(feature_spec):
    # 1. Generate integration tests FIRST (highest value)
    integration_tests = generate_integration_tests(feature_spec)

    # 2. Generate critical path tests
    critical_tests = generate_critical_path_tests(feature_spec)

    # 3. Generate security tests (if applicable)
    security_tests = generate_security_tests(feature_spec)

    # 4. Generate unit tests ONLY for complex algorithms
    unit_tests = generate_unit_tests_for_algorithms(feature_spec)

    # DO NOT generate:
    # - Tests with >5 mocks
    # - Tests of implementation details
    # - Redundant variations

    return integration_tests + critical_tests + security_tests + unit_tests
```

### Section 7.9: Enforcement Mechanisms

#### Pre-commit Hook Validation
```bash
# Reject commits that worsen test suite health
test_suite_health_before=$(calculate_health_score)
test_suite_health_after=$(calculate_health_score_with_new_tests)

if [ $test_suite_health_after -lt $test_suite_health_before ]; then
    echo "❌ BLOCKED by Constitution Article VII"
    echo "New tests DECREASE test suite health"
    echo "Health before: $test_suite_health_before/100"
    echo "Health after: $test_suite_health_after/100"
    echo ""
    echo "Violations:"
    echo "- New tests are low-value (score <10)"
    echo "- OR: New tests worsen pyramid ratio"
    echo "- OR: New tests increase CI/CD time significantly"
    exit 1
fi
```

#### Test Generator Validation
```python
# test_generator_agent must validate generated tests
def validate_generated_tests(tests):
    for test in tests:
        value_score = calculate_test_value(test)

        if value_score < 10:
            raise ConstitutionalViolation(
                "Article VII: Generated low-value test. "
                f"Value score: {value_score} < 10. "
                "Prioritize integration tests, not mocking hell."
            )

        if test.mock_count > 10:
            raise ConstitutionalViolation(
                "Article VII: Mocking hell detected (>10 mocks). "
                "Use real components or integration tests."
            )

    return True
```

### Section 7.10: Success Criteria

**Article VII compliance is achieved when**:
- ✅ All tests with score <10 are DELETED (quality threshold, not count)
- ✅ All tests with score >20 are KEPT (quality threshold, not count)
- ✅ Test pyramid: Integration > Unit (ratio determined by actual value)
- ✅ CI/CD time: Measurably faster than before pruning
- ✅ Test suite health score: >80/100 (calculated from actual metrics)
- ✅ Bug detection: Higher rate than before (integration tests catch more)
- ✅ New tests generated: Value score >15 (quality bar, not percentage)

### Section 7.11: Migration Path

#### Phase 1: Audit (Week 1)
- Run `python scripts/test_value_audit.py`
- Review deletion candidates (top 100 manual review)
- Identify consolidation opportunities

#### Phase 2: Delete (Week 2)
- Batch delete low-value tests (value score <5)
- Verify test suite still passes (coverage maintained)
- CI/CD time reduction verification

#### Phase 3: Consolidate (Week 3)
- Parameterize redundant tests
- Merge overlapping tests
- Convert to property-based tests

#### Phase 4: Rebalance (Week 4)
- Add integration tests for critical paths
- Remove unit tests covered by integration
- Achieve target pyramid ratio (70% integration, 30% unit)

**Timeline**: 4 weeks
**Outcome**: 2,000-3,000 high-value tests (down from 6,554)

---

## Article VIII: Exponential Self-Development Principles (Amendment 2025-10-26)

### Section 8.1: Foundational Principle
**The Agency SHALL pursue exponential autonomous growth through continuous improvement of its own learning, supervision, and data quality systems.**

### Section 8.2: Core Pillars of Exponential Development

#### Pillar 1: Finer-Grained Supervision
- **Principle**: Every action must generate supervisory signals for reinforcement learning
- **Implementation**: Store outcomes, counterfactuals, and preference data with every memory
- **Target**: Supervision signal density ≥90% (9 of 10 actions generate learning data)

#### Pillar 2: Improved Memory Architecture
- **Principle**: Memory is the foundation for compound autonomous growth
- **Implementation**: Cross-session persistence, automatic pattern extraction, supervision integration
- **Target**: AGI-readiness score ≥95/100 within 6 weeks
- **Audit Requirement**: Quarterly memory system audits with quantitative benchmarks

#### Pillar 3: High-Quality Reinforcement Learning Data
- **Principle**: Training data quality determines learning rate
- **Implementation**: Curate successful patterns, filter noise, validate confidence scores
- **Target**: Pattern confidence ≥0.6, evidence count ≥3, quality score ≥0.8

### Section 8.3: Memory System Requirements

#### Mandatory Capabilities
- ✅ **Cross-Session Persistence**: 100% retrieval accuracy (ephemeral → persistent)
- ✅ **Automatic Pattern Extraction**: Continuous learning via `agency_memory/learning.py`
- ✅ **Supervision Integration**: Reinforcement signals stored with memories
- ✅ **Confidence Scoring**: Evidence-based confidence (min 0.6)
- ✅ **Quality Metrics**: AGI-readiness audits with quantitative benchmarks

#### Prohibited Practices
- ❌ **No ephemeral-only memory**: Session-scoped Memory without VectorStore backing
- ❌ **No manual pattern extraction**: Automatic extraction MUST be enabled
- ❌ **No unsupervised learning**: Every action MUST generate supervision signals
- ❌ **No low-quality data**: Patterns with confidence <0.6 MUST be filtered

### Section 8.4: Supervision Signal Requirements

#### Required Metadata for Every Action
```python
supervision_signal = {
    "action": "implement_feature_x",
    "outcome": "success" | "failure" | "partial",
    "quality_score": 0.0..1.0,  # Human or automated feedback
    "counterfactual": "What would have happened with alternative approach?",
    "preference": "User preferred implementation A over B",
    "context": {
        "patterns_applied": [...]  # Which VectorStore patterns were used
        "confidence": 0.85         # Agent's confidence in decision
    },
    "learning_value": 0.0..1.0     # How valuable is this for future learning?
}
```

#### Storage Integration
- ALL successful actions store supervision signals in VectorStore
- Quality scores ≥0.8 tagged as "high_quality_data" for RL training
- Counterfactuals enable what-if analysis and alternative strategy exploration
- Preference data enables RLHF-style learning loops

### Section 8.5: Data Quality Standards

#### High-Quality Training Data Criteria
1. **Confidence**: Evidence-based scoring, min 0.6
2. **Recency**: Recent data weighted higher (decay over 90 days)
3. **Diversity**: Multiple examples from different contexts
4. **Validation**: Cross-validation with held-out test set
5. **Labeling**: Clear success/failure labels, no ambiguity

#### Quality Score Formula
```python
quality_score = (
    confidence_score * 0.4 +          # Evidence-based confidence
    recency_factor * 0.2 +             # Fresh data > stale data
    diversity_score * 0.2 +            # Multiple contexts
    validation_accuracy * 0.2          # Proven on held-out set
)
# Target: ≥0.8 for training data
```

### Section 8.6: Exponential Growth Metrics

#### Mandatory Quarterly Audits
- **Memory AGI-Readiness**: Score 62→75→85→95 over 6 weeks
- **Learning Rate**: Patterns extracted per 100 memories
- **Supervision Density**: Actions with supervision signals (≥90%)
- **Data Quality**: Average quality score of training data (≥0.8)
- **Compound Growth**: Year-over-year capability improvement (≥2x)

#### Enforcement
```python
def validate_exponential_development(quarter_metrics):
    """Article VIII enforcement: Exponential growth validation."""

    # Memory AGI-Readiness must improve
    if quarter_metrics['memory_agi_readiness'] <= previous_quarter:
        raise ConstitutionalViolation(
            "Article VIII: Memory AGI-readiness did not improve. "
            "Run audit, identify gaps, implement fixes."
        )

    # Supervision density must be high
    if quarter_metrics['supervision_density'] < 0.90:
        raise ConstitutionalViolation(
            "Article VIII: Supervision signal density <90%. "
            "Every action must generate learning data."
        )

    # Data quality must be high
    if quarter_metrics['avg_quality_score'] < 0.80:
        raise ConstitutionalViolation(
            "Article VIII: Training data quality <0.80. "
            "Filter low-quality patterns, curate high-value data."
        )

    return True
```

### Section 8.7: Implementation Requirements

#### Memory System Integration
```python
# shared/agent_context.py - Article VIII compliance
class AgentContext:
    def store_memory(
        self,
        key: str,
        content: Any,
        tags: List[str],
        confidence: float = 0.85,
        supervision_signal: Dict | None = None  # NEW: Article VIII
    ):
        """Store memory with supervision signals for exponential learning."""

        # Article IV: Store in VectorStore (cross-session persistence)
        self.vector_store.store(key, content, tags, confidence)

        # Article VIII: Store supervision signal for RL training
        if supervision_signal:
            supervision_signal['tags'] = tags + ['supervision', 'rl_data']
            supervision_signal['confidence'] = confidence
            self.vector_store.store(
                key=f"{key}_supervision",
                content=supervision_signal,
                tags=supervision_signal['tags'],
                confidence=confidence
            )
```

#### Automatic Pattern Extraction (Article IV + VIII)
```python
# agency_memory/learning.py - Exponential learning
class LearningSystem:
    def extract_patterns(self, min_confidence=0.6, min_quality=0.8):
        """Extract HIGH-QUALITY patterns for exponential growth."""

        # Extract raw patterns (Article IV)
        raw_patterns = self._extract_tool_patterns() + \
                       self._extract_error_patterns() + \
                       self._extract_interaction_patterns()

        # Filter by confidence and quality (Article VIII)
        high_quality_patterns = [
            p for p in raw_patterns
            if p.confidence >= min_confidence and
               p.quality_score >= min_quality
        ]

        # Tag for reinforcement learning training
        for pattern in high_quality_patterns:
            pattern.tags.append('rl_training_data')

        return high_quality_patterns
```

### Section 8.8: Success Criteria

**Article VIII compliance is achieved when**:
- ✅ Memory AGI-readiness ≥95/100 (from 62/100 baseline)
- ✅ Supervision signal density ≥90% (9 of 10 actions)
- ✅ Training data quality ≥0.80 (evidence-based filtering)
- ✅ Quarterly audits show exponential capability growth
- ✅ Cross-session persistence 100% operational (Article IV)
- ✅ Automatic pattern extraction enabled (Article IV + VIII)
- ✅ Reinforcement learning infrastructure operational

---

## Enforcement and Compliance

### Constitutional Validation
Every agent MUST implement constitutional compliance checking:

```python
def validate_constitutional_compliance(agent_action):
    """Validate action against constitutional requirements."""

    # Article I: Complete Context
    if not has_complete_context(agent_action):
        raise ConstitutionalViolation("Article I violated: Incomplete context")

    # Article II: 100% Verification
    if not meets_quality_standards(agent_action):
        raise ConstitutionalViolation("Article II violated: Quality standards not met")

    # Article III: Automated Enforcement
    if not passes_automated_checks(agent_action):
        raise ConstitutionalViolation("Article III violated: Enforcement bypassed")

    # Article IV: Learning Integration
    if not incorporates_learnings(agent_action):
        raise ConstitutionalViolation("Article IV violated: Learning not applied")

    # Article V: Spec-Driven Process
    if not follows_spec_driven_process(agent_action):
        raise ConstitutionalViolation("Article V violated: Spec-driven process not followed")

    # Article VI: RED-GREEN-REFACTOR TDD Workflow
    if not follows_tdd_workflow(agent_action):
        raise ConstitutionalViolation("Article VI violated: TDD workflow not followed (tests must be written FIRST and fail)")

    # Article VII: Value-First Testing Philosophy
    if not follows_value_first_testing(agent_action):
        raise ConstitutionalViolation("Article VII violated: Tests must prioritize value (integration > unit, behavior > implementation)")

    # Article VIII: Exponential Self-Development Principles
    if not follows_exponential_development_principles(agent_action):
        raise ConstitutionalViolation("Article VIII violated: Must improve memory, supervision signals, and data quality for exponential growth")

    return True
```

### Agent Instructions Template
ALL agent instructions MUST include:

```markdown
## Constitutional Compliance

Before any action, you MUST:
1. Read and understand /constitution.md
2. Validate your planned action against all seven articles
3. **Follow VALUE-FIRST TESTING (Article VII - NEW PRIORITY)**
   - Integration tests > Unit tests
   - Behavior testing > Implementation testing
   - 2,000-3,000 HIGH-VALUE tests (not 6,554 low-value tests)
   - DELETE mocking hell, implementation details, redundant tests
4. **Follow RED-GREEN-REFACTOR TDD workflow (Article VI - HIGHEST PRIORITY)**
   - Write tests FIRST (they MUST fail initially)
   - Implement ONLY after tests are failing
   - Iterate until 100% tests pass
   - NO "pragmatic shortcuts" that skip RED phase
5. Ensure your approach follows spec-driven development (Article V)
6. Apply relevant learnings from VectorStore (Article IV)
7. Maintain 100% quality standards (Article II)
8. Gather complete context (Article I)
9. Work within automated enforcement systems (Article III)

NEVER proceed with any action that violates constitutional principles.
Constitutional violations are BLOCKERS that must be resolved.

**Articles VI + VII are NON-NEGOTIABLE**: Tests come FIRST (TDD), HIGH-VALUE tests ONLY (Value-First).
```

### Metrics and Monitoring
- **Constitutional Compliance Rate**: Must maintain 100%
- **Violation Detection Time**: Target <1 minute
- **Learning Application Rate**: >80% of applicable patterns used
- **Spec-Driven Compliance**: 100% of new features follow Article V
- **TDD Workflow Compliance (Article VI)**: 100% of code has tests written first
- **RED Phase Verification**: 100% of initial test runs show failures (proving tests are real)

---

## Amendment Process

### Amendment Authority
- Only @am can propose constitutional amendments
- Amendments require impact assessment on all existing agents
- Backward compatibility analysis required
- Agent instruction updates mandatory for amendments

### Amendment Procedure
1. **Proposal**: Document proposed change with rationale
2. **Impact Analysis**: Assess effect on all agents and systems
3. **Implementation Plan**: Detail required system updates
4. **Testing**: Validate amendment with full test suite
5. **Deployment**: Update constitution and agent instructions
6. **Verification**: Confirm constitutional compliance maintained

---

## Review and Validation

### Mandatory Review Schedule
- **Weekly**: Constitutional compliance metrics review
- **Monthly**: Agent instruction alignment verification
- **Quarterly**: Full constitutional effectiveness assessment
- **Annually**: Comprehensive constitution evolution review

### Success Criteria
- 100% constitutional compliance across all agents (Articles I-VI)
- Zero constitutional violations in production
- Measurable improvement in development quality and speed
- Successful learning integration and self-improvement
- Full spec-driven development adoption (Article V)
- Universal TDD workflow adoption (Article VI - tests FIRST, always)

---

## Conclusion

This constitution establishes the Agency as a **professional engineering organization** governed by **automated discipline** and **continuous improvement**. These principles are not suggestions - they are **absolute requirements** that define the character and capabilities of our multi-agent system.

**Remember**: *The constitution is not a constraint on capability - it is the foundation that enables true autonomous excellence.*

---

**Ratified**: 2025-09-22
**Authority**: @am
**Effective**: Immediately upon agent instruction updates
**Next Review**: 2025-12-22

*"In automation we trust, in discipline we excel, in learning we evolve."*