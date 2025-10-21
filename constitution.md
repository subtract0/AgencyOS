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
- Retry with extended timeouts (2x, 3x, up to 10x)
- NEVER proceed with incomplete data
- NEVER declare "I have seen enough" with partial results

#### Test Execution
- ALL tests MUST run to completion
- Upon failures or skips: IMMEDIATELY halt
- Fix failing tests BEFORE new features
- No mission is complete while tests fail

#### Context Verification
- Explicitly verify: "Do I have all information?"
- When uncertain: re-execute
- Better 5 minutes of waiting than 5 hours in wrong direction

#### No Broken Windows
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
3. All tests pass ✓
4. Code review ✓
5. CI pipeline green ✓
6. = COMPLETE (not before)

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

## Article III: Automated Merge Enforcement (ADR-003)

### Section 3.1: Foundational Principle
**Quality standards SHALL be technically enforced, not manually governed.**

### Section 3.2: Enforcement Architecture

#### Zero-Tolerance Policy
- No manual override capabilities
- No "emergency bypass" mechanisms
- 100% test success at ALL enforcement layers
- Automatic rejection of quality violations

#### Multi-Layer Enforcement
1. **Pre-commit Hook**: Local enforcement preventing bad commits
2. **Agent Validation**: Automated agent-level verification
3. **CI/CD Pipeline**: Remote verification and enforcement
4. **Branch Protection**: Repository-level safeguards

#### No Bypass Authority
- No human can override enforcement
- No emergency exceptions permitted
- Quality gates are absolute barriers
- System failure requires infrastructure repair, not bypass

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

    return True
```

### Agent Instructions Template
ALL agent instructions MUST include:

```markdown
## Constitutional Compliance

Before any action, you MUST:
1. Read and understand /constitution.md
2. Validate your planned action against all six articles
3. **Follow RED-GREEN-REFACTOR TDD workflow (Article VI - HIGHEST PRIORITY)**
   - Write tests FIRST (they MUST fail initially)
   - Implement ONLY after tests are failing
   - Iterate until 100% tests pass
   - NO "pragmatic shortcuts" that skip RED phase
4. Ensure your approach follows spec-driven development (Article V)
5. Apply relevant learnings from VectorStore (Article IV)
6. Maintain 100% quality standards (Article II)
7. Gather complete context (Article I)
8. Work within automated enforcement systems (Article III)

NEVER proceed with any action that violates constitutional principles.
Constitutional violations are BLOCKERS that must be resolved.

**Article VI is NON-NEGOTIABLE**: Tests come FIRST, implementation comes SECOND.
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