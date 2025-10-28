# Specification: AgencyOS End-to-End Testing Framework

**ID**: SPEC-037-E2E-TESTING-FRAMEWORK
**Status**: Draft
**Created**: 2025-10-25
**Updated**: 2025-10-25
**Owner**: SpecGenerator Agent
**Related**: SPEC-031 (E2E Workflow), SPEC-009 (Test Verification Gate), ADR-026 (TDD)

---

## Goals

### What We're Building

**End-to-end testing infrastructure that makes full-system validation AUTOMATIC and COMMON, not exceptional.**

- **Goal 1**: Establish clear E2E testing taxonomy (Mission E2E, Agent E2E, Tool E2E)
- **Goal 2**: Create reusable E2E test fixtures and patterns for rapid test authoring
- **Goal 3**: Integrate E2E testing into test_generator_agent workflow (auto-propose E2E tests)
- **Goal 4**: Enable E2E tests to run locally AND in CI without modification
- **Goal 5**: Make E2E tests the STANDARD validation for complex features (not exceptional)

### Success Metrics

- **Coverage**: >80% of complex features have E2E tests within 2 sprints
- **Generation**: test_generator_agent proposes E2E tests for 100% of complex features
- **Execution**: E2E test suite completes in <600s (10 minutes)
- **Reliability**: <2% flakiness rate (E2E tests pass consistently)
- **Adoption**: E2E tests become default acceptance criteria for specs

---

## Non-Goals

**Explicitly out of scope for this specification**

- **Non-goal 1**: Performance testing infrastructure (load testing, stress testing)
  - *Rationale*: E2E tests validate correctness, not performance. Use dedicated benchmarking tools.
- **Non-goal 2**: Visual regression testing for UI components
  - *Rationale*: AgencyOS is primarily backend/CLI. UI testing requires different tooling.
- **Non-goal 3**: Chaos engineering or fault injection frameworks
  - *Rationale*: Separate testing concern. Focus on happy path + error scenarios first.
- **Non-goal 4**: Real external API integration (GitHub, OpenAI, etc.)
  - *Rationale*: E2E tests should be fast and deterministic. Mock external dependencies.
- **Non-goal 5**: Cross-platform E2E testing (Windows, Linux)
  - *Rationale*: Target macOS development environment. CI handles platform testing.

### Why These Are Non-Goals

E2E testing focuses on **validating complete workflows in isolation**. Performance, UI, chaos, and platform testing are orthogonal concerns requiring different infrastructure. Starting with core E2E validation allows rapid iteration without tooling complexity.

---

## Personas

### Persona 1: Test Generator Agent (Primary User)

- **Context**: Autonomously generates tests for new features during TDD workflow
- **Need**: Clear templates and patterns to auto-generate E2E tests alongside unit tests
- **Current Pain Point**: No guidance on when/how to propose E2E tests vs unit tests
- **Desired Outcome**: Automatically suggest E2E tests for complex features (>3 agents involved)
- **Interaction Pattern**:
  - Receive spec with acceptance criteria
  - Analyze feature complexity (agent count, external deps, workflow depth)
  - Generate E2E test template if complexity threshold met
  - Propose E2E test alongside unit tests

### Persona 2: Coding Agent (Secondary User)

- **Context**: Implements features following TDD protocol (tests first, code second)
- **Need**: Run E2E tests locally to validate full workflow before PR
- **Current Pain Point**: No easy way to validate multi-agent workflows without manual testing
- **Desired Outcome**: `pytest tests/e2e/` runs all E2E tests with fixtures auto-configured
- **Interaction Pattern**:
  - Write/review E2E tests (or use generated tests)
  - Run E2E suite locally: `pytest tests/e2e/ -v`
  - Fix failures by debugging agent interactions
  - Commit only when E2E tests pass

### Persona 3: Quality Enforcer Agent (Tertiary User)

- **Context**: Validates constitutional compliance before PR approval
- **Need**: E2E tests prove system-level constitutional compliance (not just unit tests)
- **Current Pain Point**: Unit tests don't catch integration failures (e.g., VectorStore not queried)
- **Desired Outcome**: E2E tests validate Articles I-V in realistic scenarios
- **Interaction Pattern**:
  - Review PR with E2E test coverage
  - Run E2E tests as final gate before approval
  - Reject PR if E2E tests missing for complex features
  - Verify E2E tests validate constitutional requirements

---

## Acceptance Criteria

### Functional Criteria (MUST HAVE)

- [ ] **FC-01**: E2E Testing Taxonomy Defined
  - Given: A new feature is proposed
  - When: Test generator analyzes complexity
  - Then: Feature classified as Mission E2E, Agent E2E, Tool E2E, or Unit-only
  - Validation: Decision tree documented with examples for each category

- [ ] **FC-02**: E2E Test Directory Structure Created
  - Given: E2E testing framework enabled
  - When: Developer runs `pytest tests/e2e/`
  - Then: Tests discovered in `tests/e2e/{mission,agent,tool}/` subdirectories
  - Validation: pytest collects all E2E tests, separates from unit tests

- [ ] **FC-03**: Reusable E2E Fixtures Implemented
  - Given: E2E test needs full system setup
  - When: Test imports `from tests/e2e/fixtures import full_agent_context`
  - Then: Fixture provides VectorStore, agents, memory, telemetry with auto-cleanup
  - Validation: Fixtures documented, used in >5 E2E tests, cleanup verified

- [ ] **FC-04**: Test Generator Proposes E2E Tests
  - Given: Spec with >3 agents involved OR workflow >5 steps
  - When: test_generator_agent analyzes spec
  - Then: E2E test template generated in `tests/e2e/mission/test_{feature}.py`
  - Validation: test_generator_agent code modified, >3 E2E tests auto-generated

- [ ] **FC-05**: E2E Tests Run Locally and in CI
  - Given: E2E test suite exists
  - When: Developer runs `pytest tests/e2e/ --run-all`
  - Then: All E2E tests execute with <10 minutes total time
  - Validation: CI pipeline includes E2E test step, passes consistently

### Non-Functional Criteria (MUST HAVE)

- [ ] **NF-01**: Performance: E2E suite completes in <600s (10 minutes)
- [ ] **NF-02**: Reliability: <2% flakiness rate (98% pass consistency)
- [ ] **NF-03**: Isolation: E2E tests use unique temp directories, no cross-test pollution
- [ ] **NF-04**: Type Safety: 100% type coverage in E2E test code (mypy clean)
- [ ] **NF-05**: Parallelization: E2E tests support pytest-xdist (use `@pytest.mark.e2e`)

### Quality Criteria (Constitutional Compliance - MUST HAVE)

- [ ] **QC-01**: Article I: E2E tests retry on timeout (2x, 3x escalation)
- [ ] **QC-02**: Article II: E2E tests validate 100% test pass rate for workflows
- [ ] **QC-03**: Article IV: E2E tests verify VectorStore query/store patterns
- [ ] **QC-04**: Article V: E2E tests trace to specs (spec ID in test docstring)
- [ ] **QC-05**: Test Coverage: >95% branch coverage for E2E test utilities
- [ ] **QC-06**: Documentation: E2E testing guide with 10+ examples

### User Experience Criteria

- [ ] **UX-01**: Clear E2E test naming: `test_e2e_{category}_{feature}_{scenario}.py`
- [ ] **UX-02**: Helpful failure messages: Include agent logs, task graph state on failure
- [ ] **UX-03**: Fast feedback: Mission E2E tests run in <120s, Agent E2E <30s, Tool E2E <10s

---

## E2E Testing Taxonomy

### Definition: What is an E2E Test?

**An E2E (end-to-end) test validates a complete user workflow from start to finish, exercising multiple system components in integration.**

**Key Characteristics**:
- Tests **real behavior**, not mocked behavior (minimal mocking, only external APIs)
- Exercises **multiple components** (agents, tools, memory, telemetry)
- Validates **complete workflows** (spec → plan → code → test → verify)
- Runs in **isolated environment** (temp directories, unique session IDs)
- Produces **observable outcomes** (files created, PR made, VectorStore updated)

### E2E vs Integration vs Unit Tests

| Aspect | Unit Test | Integration Test | E2E Test |
|--------|-----------|------------------|----------|
| **Scope** | Single function/class | 2-3 components | Full workflow (5+ components) |
| **Mocking** | Heavy (external deps mocked) | Moderate (APIs mocked, DB real) | Minimal (only external APIs) |
| **Speed** | <1s per test | <5s per test | <120s per test |
| **Example** | `test_classify_tier()` | `test_vectorstore_query()` | `test_e2e_primeA_workflow()` |
| **Location** | `tests/unit/` | `tests/integration/` | `tests/e2e/` |

### Three E2E Test Categories

#### Category 1: Mission E2E (Complete Autonomous Workflows)

**Definition**: Tests that validate full mission execution from natural language intent to deliverable output.

**Characteristics**:
- Exercises `/primeA`, `/primeccc`, or other mission orchestrators
- Validates spec → plan → task graph → execution → verification → PR
- Tests 5+ agents in realistic coordination
- Validates constitutional compliance at each gate
- Produces real artifacts (files, commits, VectorStore entries)

**Example Scenarios**:
- `/primeA "Add JWT auth"` → spec.md created → tests written → code implemented → PR created
- `/primeccc` auto-selects backlog task → task graph → execution → 100% test pass → learning stored

**Test Template**:
```python
# tests/e2e/mission/test_primeA_jwt_auth.py
import pytest
from tools.orchestrator.primea_orchestrator import PrimeAOrchestrator

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_mission_primeA_jwt_authentication_workflow(
    full_agent_context,
    tmp_git_repo,
    mock_openai_api
):
    """
    E2E-MISSION-001: /primeA "Add JWT authentication" workflow.

    Validates:
    - Spec generation (Goals, Acceptance Criteria)
    - TDD test creation (tests written FIRST)
    - Code implementation (JWT auth module)
    - Test verification (100% pass rate)
    - PR creation (with spec link)
    - VectorStore learning (success pattern stored)

    Constitutional Compliance:
    - Article I: Complete workflow execution (no incomplete states)
    - Article II: 100% test pass before PR
    - Article IV: VectorStore queried for similar features
    - Article V: Spec-driven (spec.md created first)

    Spec: SPEC-037 (E2E Testing Framework)
    """
    orchestrator = PrimeAOrchestrator(context=full_agent_context, repo_path=tmp_git_repo)

    # Execute full workflow
    result = await orchestrator.execute(intent="Add JWT authentication with RSA-256 signing")

    # Validate workflow completion
    assert result.is_ok()
    execution = result.unwrap()

    # Mission-level validations
    assert execution.spec_created
    assert execution.tests_written_first  # TDD compliance
    assert execution.code_implemented
    assert execution.test_pass_rate == 1.0  # 100% pass
    assert execution.pr_created
    assert execution.vectorstore_learned

    # Verify artifacts
    assert (tmp_git_repo / "specs" / "spec-*-jwt-auth.md").exists()
    assert (tmp_git_repo / "tests" / "test_jwt_auth.py").exists()
    assert (tmp_git_repo / "auth" / "jwt.py").exists()

    # Verify constitutional compliance
    assert execution.article_i_compliant  # Complete context
    assert execution.article_ii_compliant  # 100% verification
    assert execution.article_iv_compliant  # VectorStore used
```

**When to Use Mission E2E**:
- Feature involves >3 agents
- Workflow has >5 distinct steps
- Spec complexity rated "High" or "Critical"
- Feature is user-facing mission (e.g., `/primeA`, `/heal`)

#### Category 2: Agent E2E (Single Agent Full Lifecycle)

**Definition**: Tests that validate a single agent's complete workflow from invocation to deliverable.

**Characteristics**:
- Tests one agent end-to-end (e.g., PlannerAgent, CodingAgent, TestGeneratorAgent)
- Validates agent inputs → processing → outputs → side effects
- Tests agent VectorStore integration (query before action, store after success)
- Validates agent constitutional compliance (Articles I-IV)
- Faster than Mission E2E (<30s) but more realistic than unit tests

**Example Scenarios**:
- PlannerAgent receives spec → queries VectorStore for similar plans → generates plan.md → stores patterns
- TestGeneratorAgent analyzes code → generates NECESSARY-compliant tests → validates 9 categories

**Test Template**:
```python
# tests/e2e/agent/test_planner_agent_e2e.py
import pytest
from planner_agent.planner_agent import PlannerAgent

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_agent_planner_spec_to_plan_workflow(
    full_agent_context,
    sample_spec_file,
    mock_vectorstore_with_patterns
):
    """
    E2E-AGENT-001: PlannerAgent spec → plan.md workflow.

    Validates:
    - Spec parsing (Goals, Acceptance Criteria extraction)
    - VectorStore query (similar plans retrieved, Article IV)
    - Plan generation (task breakdown, dependencies, estimates)
    - Plan validation (constitutional checklist, TDD compliance)
    - VectorStore storage (successful plan pattern stored)

    Constitutional Compliance:
    - Article I: Complete spec parsed before planning
    - Article IV: VectorStore queried for patterns (MANDATORY)
    - Article V: Spec-driven (plan traces to spec)

    Spec: SPEC-037 (E2E Testing Framework)
    """
    agent = PlannerAgent(context=full_agent_context)

    # Execute agent workflow
    result = await agent.create_plan(spec_file=sample_spec_file)

    # Validate agent outputs
    assert result.is_ok()
    plan = result.unwrap()

    # Agent-level validations
    assert plan.spec_id == "SPEC-037"
    assert len(plan.tasks) >= 5
    assert plan.tdd_compliant  # Tests before code
    assert plan.constitutional_checklist_included

    # Verify VectorStore integration (Article IV)
    assert full_agent_context.memory_queried  # MUST query before action
    assert full_agent_context.memory_stored  # MUST store after success

    # Verify plan artifacts
    plan_file = Path(plan.file_path)
    assert plan_file.exists()
    assert "## Constitutional Compliance" in plan_file.read_text()
```

**When to Use Agent E2E**:
- Testing single agent's full workflow
- Validating agent VectorStore integration
- Agent has complex state machine (>3 states)
- Agent produces artifacts (files, VectorStore entries)

#### Category 3: Tool E2E (Tool in System Context)

**Definition**: Tests that validate a tool's behavior when called in realistic system context (not isolated).

**Characteristics**:
- Tests one tool with realistic system state (VectorStore populated, agents available)
- Validates tool side effects (files created, VectorStore updated, telemetry logged)
- Tests tool error handling with real dependencies (not mocked)
- Validates tool constitutional compliance (retry logic, Result pattern)
- Fastest E2E category (<10s) but more realistic than pure unit tests

**Example Scenarios**:
- `test_verification_gate` executes real tests, queries VectorStore for patterns, rolls back on failure
- `constitutional_check` validates all 5 articles against real codebase, generates compliance report

**Test Template**:
```python
# tests/e2e/tool/test_verification_gate_e2e.py
import pytest
from tools.test_verification_gate import TestVerificationGate

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_tool_verification_gate_full_workflow(
    full_agent_context,
    tmp_git_repo_with_tests,
    real_pytest_env
):
    """
    E2E-TOOL-001: Test verification gate full workflow.

    Validates:
    - Real test execution (pytest with actual tests)
    - Memory-aware worker calculation (local model state)
    - Retry logic on timeout (Article I: 2x, 3x escalation)
    - 100% pass rate validation (Article II)
    - Git rollback on failure (restore working directory)
    - VectorStore pattern storage (Article IV)

    Constitutional Compliance:
    - Article I: Retry on timeout with exponential backoff
    - Article II: 100% test pass rate enforced
    - Article IV: Verification patterns stored

    Spec: SPEC-009 (Test Verification Gate)
    """
    gate = TestVerificationGate(context=full_agent_context, repo_path=tmp_git_repo_with_tests)

    # Execute verification gate
    result = await gate.execute(scope="all")

    # Validate gate behavior
    assert result.is_ok()
    verification = result.unwrap()

    # Tool-level validations
    assert verification.tests_executed > 0
    assert verification.pass_rate == 1.0  # Article II
    assert verification.retry_attempts >= 1  # Article I
    assert verification.memory_safe  # No OOM

    # Verify side effects
    assert full_agent_context.memory_stored  # Pattern logged (Article IV)

    # Verify rollback capability (simulate failure)
    with pytest.raises(Exception):
        await gate.execute_with_failure_injection()

    # Git state should be clean (rollback worked)
    assert git_repo_is_clean(tmp_git_repo_with_tests)
```

**When to Use Tool E2E**:
- Tool has complex side effects (file I/O, VectorStore, git operations)
- Tool interacts with multiple system components
- Tool has retry/fallback logic to validate
- Tool is critical path (used in every workflow)

---

## E2E Test Directory Structure

```
tests/
├── e2e/                                   # All E2E tests (isolated from unit tests)
│   ├── __init__.py
│   ├── conftest.py                        # E2E-specific fixtures
│   │
│   ├── mission/                           # Mission E2E tests (full workflows)
│   │   ├── __init__.py
│   │   ├── test_primeA_jwt_auth.py        # /primeA JWT auth workflow
│   │   ├── test_primeA_two_stage.py       # Two-stage approval workflow
│   │   ├── test_primeccc_backlog.py       # Auto-select from backlog
│   │   └── test_heal_autonomous.py        # /heal auto-fix workflow
│   │
│   ├── agent/                             # Agent E2E tests (single agent lifecycle)
│   │   ├── __init__.py
│   │   ├── test_planner_agent_e2e.py      # Spec → plan.md workflow
│   │   ├── test_coder_agent_e2e.py        # Plan → code + tests workflow
│   │   ├── test_test_generator_e2e.py     # NECESSARY test generation
│   │   └── test_quality_enforcer_e2e.py   # Constitutional audit workflow
│   │
│   ├── tool/                              # Tool E2E tests (tool in system context)
│   │   ├── __init__.py
│   │   ├── test_verification_gate_e2e.py  # Test gate with real pytest
│   │   ├── test_constitutional_check_e2e.py
│   │   ├── test_vectorstore_sync_e2e.py   # VectorStore cross-session learning
│   │   └── test_pr_creator_e2e.py         # PR creation with gh CLI
│   │
│   └── fixtures/                          # E2E test fixtures (reusable)
│       ├── __init__.py
│       ├── agent_fixtures.py              # Full agent context, memory, VectorStore
│       ├── repo_fixtures.py               # Tmp git repos with realistic structure
│       ├── mock_fixtures.py               # Mock external APIs (OpenAI, GitHub)
│       └── data_fixtures.py               # Sample specs, plans, task graphs
│
├── unit/                                  # Unit tests (isolated, fast)
├── integration/                           # Integration tests (2-3 components)
├── necessary/                             # NECESSARY pattern validation tests
├── property/                              # Property-based tests
└── conftest.py                            # Global fixtures
```

**Rationale**:
- **Separation**: E2E tests isolated in `tests/e2e/` to avoid accidental collection with unit tests
- **Categorization**: Three subdirectories (mission, agent, tool) map to taxonomy
- **Fixtures**: Centralized in `tests/e2e/fixtures/` for reuse across all E2E tests
- **Pytest marks**: `@pytest.mark.e2e` enables selective test running

**Pytest Configuration** (`pytest.ini`):
```ini
[pytest]
markers =
    e2e: End-to-end tests (full workflows, slower, realistic)
    mission_e2e: Mission-level E2E tests (complete orchestrator workflows)
    agent_e2e: Agent-level E2E tests (single agent lifecycle)
    tool_e2e: Tool-level E2E tests (tool in system context)

# Run only unit tests by default (fast feedback)
addopts = --ignore=tests/e2e

# To run E2E tests explicitly:
# pytest tests/e2e/ -v --run-all
# pytest tests/e2e/mission/ -v  # Mission E2E only
# pytest tests/e2e/ -m "not tool_e2e"  # Skip tool E2E
```

---

## Reusable E2E Fixtures

### Fixture Design Principles

1. **Full System Setup**: Provide VectorStore, agents, memory, telemetry (not mocked internally)
2. **Automatic Cleanup**: Use `yield` pattern to teardown resources after test
3. **Realistic Data**: Fixtures use realistic specs, plans, task graphs (not minimal examples)
4. **Isolation**: Each test gets unique temp directories, session IDs (no pollution)
5. **Performance**: Fixtures lazy-load expensive resources (VectorStore, models)

### Core E2E Fixtures

#### Fixture 1: `full_agent_context` (Complete AgentContext)

```python
# tests/e2e/fixtures/agent_fixtures.py
import pytest
from pathlib import Path
from shared.agent_context import create_agent_context
from agency_memory.vectorstore import VectorStore

@pytest.fixture
async def full_agent_context(tmp_path):
    """
    Provide complete AgentContext with VectorStore, memory, telemetry.

    Includes:
    - Unique session ID (isolated per test)
    - VectorStore with temp storage (auto-cleanup)
    - Memory API enabled (store/search)
    - Telemetry disabled (avoid log pollution)

    Usage:
        async def test_e2e(full_agent_context):
            result = await agent.execute(context=full_agent_context)
            assert full_agent_context.memory_stored
    """
    session_id = f"e2e_test_{uuid.uuid4()}"

    # Create temp VectorStore directory
    vectorstore_dir = tmp_path / ".agency" / "vectorstore"
    vectorstore_dir.mkdir(parents=True, exist_ok=True)

    # Initialize AgentContext
    context = create_agent_context(
        session_id=session_id,
        vectorstore_path=str(vectorstore_dir),
        enable_telemetry=False  # Avoid log pollution
    )

    yield context

    # Cleanup: Close VectorStore connections
    if hasattr(context, "vectorstore"):
        await context.vectorstore.close()

    # Remove temp files
    shutil.rmtree(tmp_path, ignore_errors=True)
```

#### Fixture 2: `tmp_git_repo` (Realistic Git Repository)

```python
# tests/e2e/fixtures/repo_fixtures.py
import pytest
import subprocess
from pathlib import Path

@pytest.fixture
def tmp_git_repo(tmp_path):
    """
    Provide temporary git repository with realistic AgencyOS structure.

    Includes:
    - Initialized git repo (git init)
    - Directory structure (specs/, plans/, tests/, src/)
    - .gitignore, README.md
    - Initial commit (clean working directory)

    Usage:
        def test_e2e(tmp_git_repo):
            result = orchestrator.execute(repo_path=tmp_git_repo)
            assert (tmp_git_repo / "specs" / "spec-001.md").exists()
    """
    repo_path = tmp_path / "agency_test_repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

    # Create directory structure
    (repo_path / "specs").mkdir()
    (repo_path / "plans").mkdir()
    (repo_path / "tests").mkdir()
    (repo_path / "src").mkdir()

    # Create initial files
    (repo_path / ".gitignore").write_text("__pycache__/\n*.pyc\n.pytest_cache/\n")
    (repo_path / "README.md").write_text("# Test Repository\n")

    # Initial commit
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)

    yield repo_path

    # Cleanup handled by tmp_path fixture
```

#### Fixture 3: `mock_openai_api` (Deterministic OpenAI Responses)

```python
# tests/e2e/fixtures/mock_fixtures.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_openai_api():
    """
    Mock OpenAI API for deterministic E2E tests.

    Provides:
    - Embedding API: Returns consistent embeddings
    - Chat API: Returns predefined responses based on prompt patterns
    - Retry logic: Simulates occasional timeouts (Article I testing)

    Usage:
        def test_e2e(mock_openai_api):
            # OpenAI calls will return mocked responses
            result = await agent.execute(...)
    """
    with patch("openai.AsyncOpenAI") as mock_client:
        # Mock embeddings
        mock_embeddings = AsyncMock()
        mock_embeddings.create.return_value = MagicMock(
            data=[MagicMock(embedding=[0.1] * 1536)]  # Consistent embedding
        )

        # Mock chat completions
        mock_chat = AsyncMock()
        mock_chat.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Mocked response"))]
        )

        mock_client.return_value.embeddings = mock_embeddings
        mock_client.return_value.chat.completions = mock_chat

        yield mock_client
```

#### Fixture 4: `sample_spec_file` (Realistic Spec for Testing)

```python
# tests/e2e/fixtures/data_fixtures.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_spec_file(tmp_path):
    """
    Provide realistic spec file for testing agent workflows.

    Includes:
    - Complete spec-kit format (Goals, Non-Goals, Personas, Acceptance Criteria)
    - Constitutional checklist
    - Realistic acceptance criteria (5+ items)

    Usage:
        def test_e2e(sample_spec_file):
            result = planner_agent.create_plan(spec_file=sample_spec_file)
            assert result.is_ok()
    """
    spec_content = """# Specification: JWT Authentication

**ID**: SPEC-TEST-JWT-AUTH
**Status**: Draft
**Created**: 2025-10-25
**Owner**: Test

## Goals

- Goal 1: Implement JWT authentication with RSA-256 signing
- Goal 2: Support token expiration and refresh
- Goal 3: Integrate with existing user model

## Non-Goals

- Non-goal 1: OAuth2 integration (future enhancement)

## Personas

### Persona 1: API Client
- Context: Authenticates via JWT tokens
- Need: Secure, stateless authentication

## Acceptance Criteria

- [ ] FC-01: JWT tokens generated with RSA-256
- [ ] FC-02: Token expiration enforced (default 1 hour)
- [ ] FC-03: Refresh tokens supported (7 day expiration)
- [ ] NF-01: Performance: Token verification <10ms p99
- [ ] QC-01: Test Coverage: >95%

## Constitutional Compliance

- [ ] Article I: Complete context before implementation
- [ ] Article II: 100% test pass rate
- [ ] Article IV: VectorStore patterns applied
"""

    spec_file = tmp_path / "specs" / "spec-test-jwt-auth.md"
    spec_file.parent.mkdir(parents=True, exist_ok=True)
    spec_file.write_text(spec_content)

    yield spec_file
```

### Fixture Usage Examples

```python
# Example 1: Mission E2E with all fixtures
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_mission_full_workflow(
    full_agent_context,
    tmp_git_repo,
    mock_openai_api,
    sample_spec_file
):
    orchestrator = PrimeAOrchestrator(
        context=full_agent_context,
        repo_path=tmp_git_repo
    )

    result = await orchestrator.execute(spec_file=sample_spec_file)

    assert result.is_ok()
    assert (tmp_git_repo / "plans" / "plan-001.md").exists()


# Example 2: Agent E2E with selective fixtures
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_agent_planner(full_agent_context, sample_spec_file):
    planner = PlannerAgent(context=full_agent_context)

    result = await planner.create_plan(spec_file=sample_spec_file)

    assert result.is_ok()
    assert full_agent_context.memory_queried  # Article IV


# Example 3: Tool E2E with minimal fixtures
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_tool_verification_gate(full_agent_context, tmp_git_repo):
    gate = TestVerificationGate(context=full_agent_context, repo_path=tmp_git_repo)

    result = await gate.execute(scope="unit")

    assert result.is_ok()
```

---

## Test Generator Integration

### Current test_generator_agent Behavior

**Existing Workflow**:
1. Receive spec with acceptance criteria
2. Analyze code structure (functions, classes, dependencies)
3. Generate NECESSARY-compliant unit tests (9 categories)
4. Propose tests in `tests/unit/` directory

**Gap**: No E2E test generation for complex features

### Enhanced test_generator_agent Workflow

**New Workflow** (with E2E integration):
1. Receive spec with acceptance criteria
2. **Analyze feature complexity** (NEW):
   - Agent count involved
   - Workflow depth (number of sequential steps)
   - External dependencies (VectorStore, git, APIs)
   - Spec complexity rating (Low, Medium, High, Critical)
3. **Classify test requirements** (NEW):
   - Unit tests: Always required
   - Integration tests: If >2 components interact
   - E2E tests: If complexity threshold met
4. Generate unit tests (existing behavior)
5. **Generate E2E tests** (NEW):
   - If Mission E2E: Create `tests/e2e/mission/test_{feature}.py`
   - If Agent E2E: Create `tests/e2e/agent/test_{agent}_e2e.py`
   - If Tool E2E: Create `tests/e2e/tool/test_{tool}_e2e.py`
6. Propose all tests together (unit + integration + E2E)

### Complexity Threshold Decision Tree

```python
def should_generate_e2e_tests(spec: Specification) -> tuple[bool, str]:
    """
    Determine if E2E tests required based on spec complexity.

    Returns:
        (should_generate, e2e_category)

    Decision tree:
    - Mission E2E: >3 agents OR >5 workflow steps OR spec complexity "High"
    - Agent E2E: Single agent with >3 states OR agent produces artifacts
    - Tool E2E: Tool has side effects (file I/O, VectorStore, git)
    - None: Simple feature, unit tests sufficient
    """
    agent_count = count_agents_in_spec(spec)
    workflow_steps = count_workflow_steps(spec)
    complexity = spec.metadata.get("complexity", "Medium")

    # Mission E2E criteria
    if agent_count > 3:
        return (True, "mission")
    if workflow_steps > 5:
        return (True, "mission")
    if complexity in ["High", "Critical"]:
        return (True, "mission")

    # Agent E2E criteria
    if agent_count == 1 and has_complex_state_machine(spec):
        return (True, "agent")
    if produces_artifacts(spec):
        return (True, "agent")

    # Tool E2E criteria
    if has_side_effects(spec):
        return (True, "tool")

    # No E2E required
    return (False, "none")
```

### E2E Test Template Generation

**Mission E2E Template**:
```python
def generate_mission_e2e_test(spec: Specification) -> str:
    """Generate Mission E2E test from spec."""

    template = f"""# tests/e2e/mission/test_{spec.slug}_e2e.py
import pytest
from tools.orchestrator.primea_orchestrator import PrimeAOrchestrator

@pytest.mark.e2e
@pytest.mark.mission_e2e
@pytest.mark.asyncio
async def test_e2e_mission_{spec.slug}_workflow(
    full_agent_context,
    tmp_git_repo,
    mock_openai_api
):
    '''
    E2E-MISSION: {spec.title} complete workflow.

    Validates:
{generate_validation_bullets(spec.acceptance_criteria)}

    Constitutional Compliance:
{generate_constitutional_bullets(spec)}

    Spec: {spec.id}
    '''
    orchestrator = PrimeAOrchestrator(
        context=full_agent_context,
        repo_path=tmp_git_repo
    )

    # Execute workflow
    result = await orchestrator.execute(intent="{spec.goals[0]}")

    # Validate completion
    assert result.is_ok()
    execution = result.unwrap()

    # Mission-level validations
{generate_assertions(spec.acceptance_criteria)}

    # Constitutional validations
    assert execution.article_i_compliant
    assert execution.article_ii_compliant
    assert execution.article_iv_compliant
"""

    return template
```

### Modified test_generator_agent Code

**Changes to `test_generator_agent/test_generator_agent.py`**:

```python
class TestGeneratorAgent:
    async def generate_tests(self, spec: Specification) -> Result[TestSuite, Error]:
        """
        Generate comprehensive test suite (unit + integration + E2E).

        NEW: Analyzes spec complexity to determine E2E test requirements.
        """
        # Existing: Generate unit tests
        unit_tests = await self._generate_unit_tests(spec)

        # NEW: Analyze complexity
        should_e2e, e2e_category = self._should_generate_e2e_tests(spec)

        test_suite = TestSuite(unit_tests=unit_tests)

        if should_e2e:
            # NEW: Generate E2E tests
            e2e_tests = await self._generate_e2e_tests(spec, e2e_category)
            test_suite.e2e_tests = e2e_tests

            self.logger.info(
                f"✅ E2E tests required: {e2e_category} "
                f"(agents: {spec.agent_count}, steps: {spec.workflow_steps})"
            )

        return Ok(test_suite)

    def _should_generate_e2e_tests(self, spec: Specification) -> tuple[bool, str]:
        """Decision tree for E2E test generation (see above)."""
        # Implementation of complexity threshold logic
        ...

    async def _generate_e2e_tests(
        self,
        spec: Specification,
        category: Literal["mission", "agent", "tool"]
    ) -> list[E2ETest]:
        """
        Generate E2E tests based on category.

        NEW: Uses templates (mission/agent/tool) to generate realistic E2E tests.
        """
        if category == "mission":
            return self._generate_mission_e2e_tests(spec)
        elif category == "agent":
            return self._generate_agent_e2e_tests(spec)
        elif category == "tool":
            return self._generate_tool_e2e_tests(spec)
```

---

## CI/CD Integration

### Running E2E Tests Locally

```bash
# Run all E2E tests (10 min timeout)
pytest tests/e2e/ -v --run-all --timeout=600

# Run only Mission E2E tests
pytest tests/e2e/mission/ -v --run-all

# Run only Agent E2E tests
pytest tests/e2e/agent/ -v

# Run only Tool E2E tests
pytest tests/e2e/tool/ -v

# Run E2E tests with specific marker
pytest -m mission_e2e -v

# Skip E2E tests (default pytest behavior)
pytest  # Runs only unit tests
```

### CI Pipeline Integration

**GitHub Actions Workflow** (`.github/workflows/e2e-tests.yml`):

```yaml
name: E2E Tests

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  e2e-tests:
    runs-on: macos-latest
    timeout-minutes: 15

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-asyncio pytest-timeout

      - name: Run E2E Tests
        run: |
          pytest tests/e2e/ -v --run-all --timeout=600 --junit-xml=e2e-results.xml
        env:
          USE_ENHANCED_MEMORY: true
          ML_AB_TEST_ENABLED: false  # Disable ML for deterministic tests

      - name: Upload E2E Test Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-test-results
          path: e2e-results.xml

      - name: Fail on E2E Test Failure
        if: failure()
        run: |
          echo "❌ E2E tests failed. Check logs above."
          exit 1
```

### run_tests.py Integration

**Add `--e2e` flag to `run_tests.py`**:

```python
# run_tests.py (additions)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-all", action="store_true", help="Run all tests")
    parser.add_argument("--e2e", action="store_true", help="Run E2E tests only")  # NEW
    parser.add_argument("--no-e2e", action="store_true", help="Skip E2E tests")  # NEW
    args = parser.parse_args()

    pytest_args = []

    if args.e2e:
        # Run only E2E tests
        pytest_args.extend(["tests/e2e/", "-v", "--run-all", "--timeout=600"])
    elif args.no_e2e:
        # Skip E2E tests (default behavior)
        pytest_args.extend(["--ignore=tests/e2e"])
    elif args.run_all:
        # Run all tests including E2E
        pytest_args.extend(["--run-all"])

    exit_code = pytest.main(pytest_args)
    sys.exit(exit_code)
```

**Usage**:
```bash
# Run only E2E tests
python run_tests.py --e2e

# Run all tests including E2E
python run_tests.py --run-all

# Run all tests EXCEPT E2E (default)
python run_tests.py --no-e2e
```

---

## Performance Requirements

### E2E Test Speed Targets

| Category | Target Time | Max Timeout | Parallel Workers |
|----------|-------------|-------------|------------------|
| **Mission E2E** | <120s per test | 300s | 1 (sequential, complex state) |
| **Agent E2E** | <30s per test | 60s | 3 (moderate parallelism) |
| **Tool E2E** | <10s per test | 30s | 5 (high parallelism) |
| **Full E2E Suite** | <600s total | 900s | pytest-xdist (auto workers) |

### Performance Optimization Strategies

**1. Lazy Fixture Loading**:
```python
@pytest.fixture
def expensive_vectorstore(request):
    """Lazy load VectorStore only if test uses it."""
    if not hasattr(request, "_vectorstore"):
        request._vectorstore = VectorStore(temp_path)
    return request._vectorstore
```

**2. Fixture Caching** (session scope):
```python
@pytest.fixture(scope="session")
def mock_openai_client():
    """Reuse mock client across all E2E tests in session."""
    return create_mock_openai_client()
```

**3. Parallel Execution** (pytest-xdist):
```bash
# Auto-detect workers (use all CPU cores)
pytest tests/e2e/ -n auto

# Fixed worker count (safe for E2E state)
pytest tests/e2e/ -n 3
```

**4. Test Timeouts** (pytest-timeout):
```python
@pytest.mark.e2e
@pytest.mark.timeout(120)  # 2 minute max
async def test_e2e_mission_long_workflow(...):
    ...
```

---

## Documentation Requirements

### E2E Testing Guide

**Create `docs/E2E_TESTING_GUIDE.md`** with:

1. **Introduction**: What is E2E testing? Why use it?
2. **Taxonomy**: Mission vs Agent vs Tool E2E (with examples)
3. **Writing E2E Tests**: Step-by-step tutorial
4. **Fixtures**: How to use `full_agent_context`, `tmp_git_repo`, etc.
5. **Running Tests**: Local and CI execution
6. **Debugging**: Common issues and troubleshooting
7. **Examples**: 10+ annotated E2E test examples
8. **Best Practices**: DRY fixtures, realistic data, fast cleanup

### Inline Documentation

**Every E2E test MUST include**:
- Docstring with:
  - E2E test ID (e.g., `E2E-MISSION-001`)
  - What workflow is validated
  - Constitutional compliance checklist
  - Spec ID traceability
- Comments explaining non-obvious assertions
- Type hints for all fixtures

**Example**:
```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_mission_primeA_jwt_auth(
    full_agent_context: AgentContext,
    tmp_git_repo: Path,
    mock_openai_api: MagicMock
) -> None:
    """
    E2E-MISSION-001: /primeA JWT authentication workflow.

    Validates complete mission lifecycle:
    1. Spec generation (Goals, Acceptance Criteria)
    2. TDD test creation (tests written FIRST - Article VI)
    3. Code implementation (JWT auth module)
    4. Test verification (100% pass rate - Article II)
    5. PR creation (with spec link)
    6. VectorStore learning (success pattern stored - Article IV)

    Constitutional Compliance:
    - Article I: Complete workflow execution (no incomplete states)
    - Article II: 100% test pass before PR
    - Article IV: VectorStore queried for similar features
    - Article V: Spec-driven (spec.md created first)

    Spec: SPEC-037 (E2E Testing Framework)
    """
    # Test implementation...
```

---

## Risk Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **E2E Test Flakiness** | High | Medium | Deterministic mocks, unique temp dirs, retry logic |
| **Slow E2E Execution** | Medium | High | Lazy fixtures, caching, parallel workers, timeouts |
| **E2E Test Maintenance** | High | Medium | Reusable fixtures, templates, test generator automation |
| **VectorStore Pollution** | Medium | Low | Isolated temp VectorStore per test, cleanup fixtures |
| **CI Timeout** | Medium | Low | 15-minute timeout, fail fast on errors, parallel execution |
| **Mock Drift** | Low | Medium | Periodic mock validation against real APIs |

---

## Implementation Guidance

### Phase 1: Infrastructure (Week 1)

**Deliverables**:
- Directory structure: `tests/e2e/{mission,agent,tool}/`
- Core fixtures: `full_agent_context`, `tmp_git_repo`, `mock_openai_api`
- pytest configuration: markers, ignore patterns
- Documentation: `docs/E2E_TESTING_GUIDE.md`

**Acceptance**:
- [ ] Directory structure created
- [ ] 3 core fixtures implemented and tested
- [ ] pytest markers working (`pytest -m e2e`)
- [ ] E2E testing guide published

### Phase 2: Templates & Examples (Week 2)

**Deliverables**:
- Mission E2E template
- Agent E2E template
- Tool E2E template
- 10 example E2E tests (3 mission, 4 agent, 3 tool)

**Acceptance**:
- [ ] Templates generate runnable tests
- [ ] 10 example tests passing
- [ ] Templates documented in guide

### Phase 3: Test Generator Integration (Week 3)

**Deliverables**:
- Modified `test_generator_agent.py`
- Complexity threshold decision tree
- E2E test auto-generation for 5+ specs

**Acceptance**:
- [ ] test_generator_agent proposes E2E tests
- [ ] 5+ specs auto-generate E2E tests
- [ ] Complexity threshold validated

### Phase 4: CI Integration (Week 4)

**Deliverables**:
- GitHub Actions workflow (`.github/workflows/e2e-tests.yml`)
- `run_tests.py --e2e` flag
- CI passing with E2E tests

**Acceptance**:
- [ ] CI runs E2E tests on PR
- [ ] E2E tests complete in <10 minutes
- [ ] Failures block merge

---

## Constitutional Compliance Checklist

### Article I: Complete Context Before Action ✅

- [x] E2E tests validate complete workflows (no partial execution)
- [x] Retry logic tested in Tool E2E (timeout scenarios)
- [x] Fixtures provide complete system setup (VectorStore, agents, memory)

### Article II: 100% Verification and Stability ✅

- [x] E2E tests validate 100% test pass rate (Mission E2E validates Article II)
- [x] E2E tests trace to specs (spec ID in docstring)
- [x] Quality gates: E2E tests required for complex features

### Article III: Automated Merge Enforcement ✅

- [x] CI runs E2E tests automatically (no manual trigger)
- [x] E2E test failure blocks merge (CI enforcement)
- [x] No bypass mechanisms (failures must be fixed)

### Article IV: Continuous Learning and Improvement ✅

- [x] E2E tests validate VectorStore integration (Agent E2E)
- [x] E2E tests verify query-before-action pattern
- [x] E2E tests verify store-after-success pattern
- [x] test_generator_agent learns from E2E patterns (templates improve)

### Article V: Spec-Driven Development ✅

- [x] E2E tests generated from specs (test_generator_agent integration)
- [x] E2E tests trace to spec IDs (docstring metadata)
- [x] Acceptance criteria map to E2E test assertions

---

## References

### Related Specifications

- **SPEC-031**: E2E Workflow Implementation (UnifiedPrimeAOrchestrator)
- **SPEC-009**: Test Verification Gate (Tool E2E example)
- **SPEC-030**: Foundation Automation Test Coverage

### Architecture Decision Records

- **ADR-026**: Test-Driven Autonomy (TDD protocol, NECESSARY validator)
- **ADR-002**: 100% Verification and Stability (quality gates)
- **ADR-004**: Continuous Learning System (VectorStore integration)

### External Documentation

- **pytest Documentation**: https://docs.pytest.org/en/stable/
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **pytest-xdist**: https://pytest-xdist.readthedocs.io/

---

## Approval and Sign-Off

**Created By**: SpecGenerator Agent
**Reviewed By**: Planner, ChiefArchitect, QualityEnforcer
**Approved By**: User/Product Owner

**Approval Criteria**:

- [x] All sections complete (Goals, Non-Goals, Personas, Acceptance Criteria)
- [x] Taxonomy clearly defined (Mission, Agent, Tool E2E)
- [x] Fixtures documented with examples
- [x] test_generator_agent integration designed
- [x] CI/CD integration specified
- [x] Constitutional compliance validated (Articles I-V)
- [x] Risk mitigation strategies defined

**Approval Date**: _Pending Review_
**Approver Signature**: _Pending_

---

**Living Document**: This specification will be updated during implementation to reflect learnings and refinements from actual E2E test development.

---

*"Test the system as users experience it, not as functions exist in isolation."*
