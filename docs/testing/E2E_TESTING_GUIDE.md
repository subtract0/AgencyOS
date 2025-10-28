# E2E Testing Guide - AgencyOS

**Version**: 1.0.0
**Status**: Production
**Created**: 2025-10-25
**Specification**: SPEC-037-E2E-TESTING-FRAMEWORK

---

## Table of Contents

1. [Introduction](#introduction)
2. [E2E Testing Taxonomy](#e2e-testing-taxonomy)
3. [Quick Start](#quick-start)
4. [Writing E2E Tests](#writing-e2e-tests)
5. [E2E Fixtures](#e2e-fixtures)
6. [Running E2E Tests](#running-e2e-tests)
7. [Debugging E2E Tests](#debugging-e2e-tests)
8. [Best Practices](#best-practices)
9. [Constitutional Compliance](#constitutional-compliance)
10. [Examples](#examples)

---

## Introduction

### What is E2E Testing?

**End-to-end (E2E) testing** validates complete user workflows from start to finish, exercising multiple system components in integration. E2E tests verify that the entire system works together as expected in realistic scenarios.

**Key Characteristics:**
- Tests **real behavior**, not mocked behavior (minimal mocking, only external APIs)
- Exercises **multiple components** (agents, tools, memory, telemetry)
- Validates **complete workflows** (spec → plan → code → test → verify)
- Runs in **isolated environment** (temp directories, unique session IDs)
- Produces **observable outcomes** (files created, PR made, VectorStore updated)

### When to Use E2E Tests

**Use E2E tests when:**
- ✅ Feature involves >3 agents
- ✅ Workflow has >5 distinct steps
- ✅ Spec complexity rated "High" or "Critical"
- ✅ Feature is user-facing mission (e.g., `/primeA`, `/heal`)
- ✅ Testing multi-agent coordination
- ✅ Validating constitutional compliance (Articles I-V)

**Use unit tests when:**
- ❌ Testing single function/class
- ❌ No external dependencies
- ❌ Simple logic (<3 steps)
- ❌ Speed is critical (<1s per test)

### E2E vs Integration vs Unit Tests

| Aspect | Unit Test | Integration Test | E2E Test |
|--------|-----------|------------------|----------|
| **Scope** | Single function/class | 2-3 components | Full workflow (5+ components) |
| **Mocking** | Heavy (external deps mocked) | Moderate (APIs mocked, DB real) | Minimal (only external APIs) |
| **Speed** | <1s per test | <5s per test | <120s per test |
| **Example** | `test_classify_tier()` | `test_vectorstore_query()` | `test_e2e_primeA_workflow()` |
| **Location** | `tests/unit/` | `tests/integration/` | `tests/e2e/` |

---

## E2E Testing Taxonomy

AgencyOS E2E tests are categorized into three types:

### 1. Mission E2E (Complete Autonomous Workflows)

**Definition**: Tests that validate full mission execution from natural language intent to deliverable output.

**Characteristics:**
- Exercises `/primeA`, `/primeccc`, or other mission orchestrators
- Validates spec → plan → task graph → execution → verification → PR
- Tests 5+ agents in realistic coordination
- Validates constitutional compliance at each gate
- Produces real artifacts (files, commits, VectorStore entries)

**Example Scenarios:**
- `/primeA "Add JWT auth"` → spec.md created → tests written → code implemented → PR created
- `/primeccc` auto-selects backlog task → task graph → execution → 100% test pass → learning stored

**When to Use**: Feature involves >3 agents OR workflow >5 steps OR spec complexity "High"

### 2. Agent E2E (Single Agent Full Lifecycle)

**Definition**: Tests that validate a single agent's complete workflow from invocation to deliverable.

**Characteristics:**
- Tests one agent end-to-end (e.g., PlannerAgent, CodingAgent, TestGeneratorAgent)
- Validates agent inputs → processing → outputs → side effects
- Tests agent VectorStore integration (query before action, store after success)
- Validates agent constitutional compliance (Articles I-IV)
- Faster than Mission E2E (<30s) but more realistic than unit tests

**Example Scenarios:**
- PlannerAgent receives spec → queries VectorStore for similar plans → generates plan.md → stores patterns
- TestGeneratorAgent analyzes code → generates NECESSARY-compliant tests → validates 9 categories

**When to Use**: Testing single agent's full workflow OR validating agent VectorStore integration

### 3. Tool E2E (Tool in System Context)

**Definition**: Tests that validate a tool's behavior when called in realistic system context (not isolated).

**Characteristics:**
- Tests one tool with realistic system state (VectorStore populated, agents available)
- Validates tool side effects (files created, VectorStore updated, telemetry logged)
- Tests tool error handling with real dependencies (not mocked)
- Validates tool constitutional compliance (retry logic, Result pattern)
- Fastest E2E category (<10s) but more realistic than pure unit tests

**Example Scenarios:**
- `test_verification_gate` executes real tests, queries VectorStore for patterns, rolls back on failure
- `constitutional_check` validates all 5 articles against real codebase, generates compliance report

**When to Use**: Tool has complex side effects OR tool interacts with multiple system components

---

## Quick Start

### Running E2E Tests

```bash
# Run all E2E tests (10 minute timeout)
python run_tests.py --e2e

# Run only Mission E2E tests
pytest tests/e2e/mission/ -v

# Run only Agent E2E tests
pytest tests/e2e/agent/ -v

# Run only Tool E2E tests
pytest tests/e2e/tool/ -v

# Run specific E2E test
pytest tests/e2e/test_e2e_fixtures.py::test_full_agent_context_fixture_creates_vectorstore -v

# Run E2E tests with specific marker
pytest -m mission_e2e -v
```

### Current Status

**E2E Tests Status** (as of 2025-10-25):
- **Total Tests**: 65 E2E tests
- **Passing**: 22 tests (infrastructure tests)
- **Failing**: 43 tests (awaiting implementation)

**Passing Tests** (Infrastructure Ready):
- ✅ `test_e2e_fixtures.py`: Fixture tests (9 tests)
- ✅ `test_e2e_runner.py`: Test runner tests (13 tests)

**Failing Tests** (TDD - Written Before Implementation):
- ⏳ `test_planner_agent_e2e.py`: 11 tests (awaiting PlannerAgent refactor)
- ⏳ `test_simple_mission_e2e.py`: 12 tests (awaiting PrimeAOrchestrator)
- ⏳ `test_test_verification_gate_e2e.py`: 12 tests (awaiting gate implementation)

These failures are **expected** - this is TDD (Test-Driven Development). Tests written FIRST, implementation SECOND.

---

## Writing E2E Tests

### Test Structure

Every E2E test follows this pattern:

```python
import pytest
from pathlib import Path

@pytest.mark.e2e  # Required: marks test as E2E
@pytest.mark.asyncio  # If async
async def test_e2e_feature_name(
    full_agent_context,  # Fixture: AgentContext with VectorStore
    tmp_git_repo,        # Fixture: Temporary git repository
    mock_openai_api,     # Fixture: Mocked OpenAI API
    e2e_test_env         # Fixture: Environment variables
):
    """
    E2E-CATEGORY-ID: Feature description.

    Validates:
    - Workflow step 1
    - Workflow step 2
    - Workflow step 3

    Constitutional Compliance:
    - Article I: Complete context before action
    - Article IV: VectorStore query/store patterns

    Spec: SPEC-037 (E2E Testing Framework)
    """
    # Arrange: Setup test data
    test_data = prepare_test_data()

    # Act: Execute E2E workflow
    result = execute_workflow(test_data, full_agent_context)

    # Assert: Validate outcomes
    assert result.is_ok()
    assert result.unwrap().tests_passed is True
```

### Fixture Usage

**Required Fixtures:**

1. **`full_agent_context`**: Complete AgentContext with VectorStore
   ```python
   def test_e2e(full_agent_context):
       # Store memory
       full_agent_context.store_memory("key", {"data": "value"}, tags=["test"])

       # Search memory
       results = full_agent_context.search_memories(tags=["test"])
   ```

2. **`tmp_git_repo`**: Temporary git repository with AgencyOS structure
   ```python
   def test_e2e(tmp_git_repo):
       # Create files
       (tmp_git_repo / "specs" / "spec.md").write_text("content")

       # Run git commands
       assert (tmp_git_repo / ".git").exists()
   ```

3. **`mock_openai_api`**: Deterministic OpenAI API responses
   ```python
   def test_e2e(mock_openai_api):
       response = mock_openai_api.create_completion(...)
       assert response["choices"][0]["text"] == "Mocked response for: ..."
   ```

4. **`e2e_test_env`**: Environment variable configuration
   ```python
   def test_e2e(e2e_test_env):
       import os
       assert os.getenv("E2E_TEST_MODE") == "true"
       assert os.getenv("USE_ENHANCED_MEMORY") == "true"
   ```

### Test Markers

**Required Markers:**

```python
@pytest.mark.e2e  # All E2E tests MUST have this marker
@pytest.mark.mission_e2e  # For Mission E2E tests
@pytest.mark.agent_e2e  # For Agent E2E tests
@pytest.mark.tool_e2e  # For Tool E2E tests
@pytest.mark.slow  # For tests >30s execution time
@pytest.mark.asyncio  # For async tests
```

**Example:**

```python
@pytest.mark.e2e
@pytest.mark.mission_e2e
@pytest.mark.asyncio
async def test_e2e_mission_primeA_jwt_auth(...):
    """Mission E2E test for JWT auth workflow."""
    pass
```

---

## E2E Fixtures

### Available Fixtures

All E2E fixtures are defined in `tests/e2e/conftest.py`:

1. **`full_agent_context`**: Complete AgentContext with VectorStore
2. **`tmp_git_repo`**: Temporary git repository
3. **`mock_openai_api`**: Mocked OpenAI API
4. **`e2e_test_env`**: Environment configuration
5. **`sample_spec_file`**: Realistic specification file

### Fixture Details

#### 1. `full_agent_context` Fixture

**Purpose**: Provides complete AgentContext with VectorStore, memory, and telemetry.

**Includes:**
- Unique session ID (isolated per test)
- VectorStore with temp storage (auto-cleanup)
- Memory API enabled (store/search)
- Telemetry disabled (avoid log pollution)

**Usage:**

```python
def test_e2e(full_agent_context):
    # Store memory (Article IV)
    full_agent_context.store_memory(
        key="test_key",
        content={"data": "value"},
        tags=["test", "pattern"]
    )

    # Search memory (Article IV)
    results = full_agent_context.search_memories(
        tags=["test"],
        query="pattern"
    )

    assert len(results) > 0
```

**Cleanup**: Automatic VectorStore cleanup after test completes.

#### 2. `tmp_git_repo` Fixture

**Purpose**: Provides temporary git repository with realistic AgencyOS structure.

**Includes:**
- Initialized git repo (git init)
- Directory structure (specs/, plans/, tests/, tools/, shared/)
- `.gitignore`, `README.md`, `pyproject.toml`
- Initial commit (clean working directory)

**Usage:**

```python
def test_e2e(tmp_git_repo):
    # Create files
    spec_file = tmp_git_repo / "specs" / "spec-001.md"
    spec_file.write_text("# Specification")

    # Verify git repo
    assert (tmp_git_repo / ".git").exists()

    # Check git status
    import subprocess
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True
    )
    # Initially clean
    assert result.stdout.strip() == ""
```

**Cleanup**: Automatic removal of temp directory after test completes.

#### 3. `mock_openai_api` Fixture

**Purpose**: Mocks OpenAI API for deterministic E2E tests.

**Provides:**
- Deterministic completions (no real API calls)
- Consistent embeddings (hash-based)
- No API cost

**Usage:**

```python
def test_e2e(mock_openai_api):
    # Mock completion
    response = mock_openai_api.create_completion(
        model="gpt-4",
        prompt="Test prompt",
        max_tokens=50
    )

    assert response["choices"][0]["text"].startswith("Mocked response for:")

    # Deterministic: same input = same output
    response2 = mock_openai_api.create_completion(
        model="gpt-4",
        prompt="Test prompt",
        max_tokens=50
    )
    assert response == response2
```

#### 4. `e2e_test_env` Fixture

**Purpose**: Configures environment variables for E2E testing.

**Sets:**
- `E2E_TEST_MODE=true`
- `USE_ENHANCED_MEMORY=true` (Article IV requirement)
- `OPENAI_API_KEY=test-key-e2e-safe` (no real credentials)
- `PYTEST_TIMEOUT=120`
- `ML_AB_TEST_ENABLED=false` (deterministic behavior)
- `ENABLE_TELEMETRY=false` (avoid log pollution)

**Usage:**

```python
def test_e2e(e2e_test_env):
    import os

    # Verify E2E mode
    assert os.getenv("E2E_TEST_MODE") == "true"

    # Verify Article IV compliance
    assert os.getenv("USE_ENHANCED_MEMORY") == "true"

    # Safe API key
    assert "test-key" in os.getenv("OPENAI_API_KEY")
```

---

## Running E2E Tests

### Command Line

```bash
# Run all E2E tests
python run_tests.py --e2e

# Run with verbose output
python run_tests.py --e2e -v

# Run specific test file
pytest tests/e2e/test_e2e_fixtures.py -v

# Run specific test
pytest tests/e2e/test_e2e_fixtures.py::test_full_agent_context_fixture_creates_vectorstore -v

# Run with markers
pytest -m mission_e2e -v  # Only Mission E2E
pytest -m agent_e2e -v    # Only Agent E2E
pytest -m tool_e2e -v     # Only Tool E2E

# Skip E2E tests (default)
python run_tests.py  # Runs unit tests only
```

### Timeout Configuration

E2E tests use longer timeouts than unit tests:

- **Mission E2E**: <120s per test (max 300s timeout)
- **Agent E2E**: <30s per test (max 60s timeout)
- **Tool E2E**: <10s per test (max 30s timeout)
- **Full E2E Suite**: <600s total (10 minutes)

**Override timeout:**

```bash
# Increase timeout for slow tests
pytest tests/e2e/ --timeout=900  # 15 minutes
```

### Parallel Execution

E2E tests support pytest-xdist for parallel execution:

```bash
# Auto-detect workers (use all CPU cores)
pytest tests/e2e/ -n auto

# Fixed worker count
pytest tests/e2e/ -n 3

# Serial execution (safest)
pytest tests/e2e/ -n 1
```

**Note**: E2E tests use unique temp directories, so parallel execution is safe for most tests. Mission E2E tests may require serial execution due to complex state.

---

## Debugging E2E Tests

### Common Issues

#### 1. Fixture Setup Failures

**Symptom**: `TypeError: create_agent_context() got an unexpected keyword argument`

**Solution**: Check `shared/agent_context.py` for correct signature:

```python
# Correct usage
context = create_agent_context(session_id="test_session")

# Incorrect usage
context = create_agent_context(memory_dir="/path")  # memory_dir not supported
```

#### 2. VectorStore Initialization Failures

**Symptom**: `AssertionError: assert False` in `test_full_agent_context_fixture_creates_vectorstore`

**Solution**: Ensure `USE_ENHANCED_MEMORY=true` in environment:

```python
import os
assert os.getenv("USE_ENHANCED_MEMORY") == "true"
```

#### 3. Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'tools.orchestrator.prime_a_orchestrator'`

**Solution**: This is expected for TDD tests. Implementation comes AFTER tests.

#### 4. Test Timeouts

**Symptom**: `Failed: Timeout (>60.0s) from pytest-timeout`

**Solution**: Increase timeout for slow tests:

```python
@pytest.mark.e2e
@pytest.mark.timeout(120)  # 2 minute timeout
async def test_e2e_slow_workflow(...):
    pass
```

### Debugging Tips

1. **Use `-v` flag**: Shows detailed test output
   ```bash
   pytest tests/e2e/ -v
   ```

2. **Use `-s` flag**: Shows print statements
   ```bash
   pytest tests/e2e/ -s
   ```

3. **Run single test**: Isolate failing test
   ```bash
   pytest tests/e2e/test_e2e_fixtures.py::test_name -v -s
   ```

4. **Check logs**: E2E tests create temp directories
   ```bash
   # Find temp directories
   ls /tmp/e2e_test_*

   # Check VectorStore state
   ls /tmp/e2e_test_*/.agency/vectorstore/
   ```

5. **Use debugger**: Add breakpoint
   ```python
   def test_e2e(full_agent_context):
       import pdb; pdb.set_trace()
       # Debug here
   ```

---

## Best Practices

### 1. Test Isolation

**DO**: Use unique temp directories
```python
def test_e2e(tmp_git_repo):
    # Each test gets unique tmp_git_repo
    test_file = tmp_git_repo / "test.txt"
    test_file.write_text("data")
```

**DON'T**: Share state between tests
```python
# ❌ WRONG
global_state = {}

def test_e2e_1():
    global_state["key"] = "value"  # Pollutes other tests

def test_e2e_2():
    assert "key" in global_state  # Depends on test_e2e_1
```

### 2. Realistic Data

**DO**: Use realistic specifications and data
```python
def test_e2e(sample_spec_file):
    # sample_spec_file is realistic spec with Goals, Personas, Criteria
    assert sample_spec_file.exists()
```

**DON'T**: Use minimal/unrealistic data
```python
# ❌ WRONG
spec_content = "# Spec"  # Too minimal
```

### 3. Fast Cleanup

**DO**: Use fixtures with automatic cleanup
```python
@pytest.fixture
def my_fixture(tmp_path):
    resource = create_resource(tmp_path)
    yield resource
    # Cleanup automatic (tmp_path removed by pytest)
```

**DON'T**: Manual cleanup in tests
```python
# ❌ WRONG
def test_e2e():
    temp_dir = Path("/tmp/manual_cleanup")
    temp_dir.mkdir()
    try:
        # Test logic
        pass
    finally:
        shutil.rmtree(temp_dir)  # Manual cleanup is fragile
```

### 4. Clear Assertions

**DO**: Specific, descriptive assertions
```python
assert result.is_ok(), f"Workflow failed: {result.error}"
assert mission_result["tests_passing"] is True
assert mission_result["test_pass_rate"] == 1.0  # 100% pass
```

**DON'T**: Vague assertions
```python
# ❌ WRONG
assert result  # What does this validate?
assert x  # Unclear
```

### 5. Constitutional Compliance

**DO**: Validate constitutional requirements
```python
def test_e2e_mission(full_agent_context, tmp_git_repo):
    result = execute_mission(...)

    # Article I: Complete context
    assert result["phases_completed"] >= 4

    # Article II: 100% test pass
    assert result["test_pass_rate"] == 1.0

    # Article IV: VectorStore integration
    assert result["vectorstore_queried"] is True
    assert result["pattern_stored"] is True
```

---

## Constitutional Compliance

### Article I: Complete Context Before Action

**Requirement**: E2E tests execute complete workflows (no partial states).

**Validation:**

```python
def test_e2e_article_i_compliance(full_agent_context):
    # Execute complete workflow
    result = execute_workflow()

    # Validate: All phases completed (no incomplete states)
    assert result["phases_completed"] == expected_phases
    assert result["status"] == "complete"
```

### Article II: 100% Verification and Stability

**Requirement**: E2E tests validate 100% test pass rate.

**Validation:**

```python
def test_e2e_article_ii_compliance(full_agent_context):
    result = execute_workflow()

    # Validate: 100% test pass rate
    assert result["test_pass_rate"] == 1.0
    assert result["tests_passing"] is True
    assert result["tests_failed"] == 0
```

### Article IV: Continuous Learning and Improvement

**Requirement**: E2E tests verify VectorStore query/store patterns.

**Validation:**

```python
def test_e2e_article_iv_compliance(full_agent_context):
    # Query VectorStore before action (MANDATORY)
    patterns = full_agent_context.search_memories(tags=["pattern"])

    # Execute workflow
    result = execute_workflow(patterns)

    # Store pattern after success (MANDATORY)
    full_agent_context.store_memory(
        key="success_pattern",
        content={"result": result},
        tags=["success", "pattern"]
    )

    # Validate: VectorStore integration
    assert result["vectorstore_queried"] is True
    assert result["pattern_stored"] is True
```

### Article VI: Test-Driven Development (TDD)

**Requirement**: Tests written BEFORE implementation.

**Validation:**

```python
def test_e2e_article_vi_compliance(full_agent_context):
    result = execute_workflow()

    # Validate: TDD workflow (tests before code)
    workflow = result["workflow"]
    test_index = workflow.index("test_generation")
    code_index = workflow.index("code_generation")

    assert test_index < code_index, "Tests MUST come before code (TDD)"

    # Validate: Tests failed initially (RED phase)
    assert result["initial_test_status"] == "failing"

    # Validate: Tests pass after implementation (GREEN phase)
    assert result["final_test_status"] == "passing"
```

---

## Examples

### Example 1: Mission E2E Test

```python
import pytest
from tools.orchestrator.prime_a_orchestrator import PrimeAOrchestrator

@pytest.mark.e2e
@pytest.mark.mission_e2e
@pytest.mark.asyncio
async def test_e2e_mission_simple_feature(
    full_agent_context,
    tmp_git_repo,
    mock_openai_api
):
    """
    E2E-MISSION-001: Simple feature implementation workflow.

    Validates:
    - Mission execution from intent to completion
    - TDD workflow (tests before code)
    - 100% test pass rate
    - VectorStore integration

    Constitutional Compliance:
    - Article I: Complete workflow execution
    - Article II: 100% test pass
    - Article IV: VectorStore query/store
    - Article VI: TDD (tests first)

    Spec: SPEC-037 (E2E Testing Framework)
    """
    # Arrange: Mission intent
    mission_intent = "Add type hints to validate_email function"

    # Act: Execute mission
    orchestrator = PrimeAOrchestrator(
        agent_context=full_agent_context,
        working_dir=tmp_git_repo
    )

    result = orchestrator.execute_mission(
        intent=mission_intent,
        two_stage=False
    )

    # Assert: Mission completes successfully
    assert result.is_ok()
    mission_result = result.unwrap()

    # Validate workflow
    assert mission_result["status"] == "complete"
    assert mission_result["phases_completed"] >= 4

    # Validate TDD (Article VI)
    assert mission_result["tests_written"] > 0
    assert mission_result["tests_passing"] is True

    # Validate Article IV (VectorStore)
    assert mission_result["vectorstore_queried"] is True
    assert mission_result["pattern_stored"] is True
```

### Example 2: Agent E2E Test

```python
import pytest
from planner_agent.planner import PlannerAgent

@pytest.mark.e2e
@pytest.mark.agent_e2e
@pytest.mark.asyncio
async def test_e2e_agent_planner_workflow(
    full_agent_context,
    sample_spec_file
):
    """
    E2E-AGENT-001: PlannerAgent spec → plan.md workflow.

    Validates:
    - Spec parsing and plan generation
    - VectorStore query for similar plans
    - Plan validation and traceability

    Constitutional Compliance:
    - Article I: Complete spec parsed
    - Article IV: VectorStore queried/stored

    Spec: SPEC-037 (E2E Testing Framework)
    """
    # Arrange: PlannerAgent
    agent = PlannerAgent(context=full_agent_context)

    # Act: Create plan from spec
    result = await agent.create_plan(spec_file=sample_spec_file)

    # Assert: Plan created successfully
    assert result.is_ok()
    plan = result.unwrap()

    # Validate plan content
    assert plan.spec_id == "SPEC-E2E-TEST-001"
    assert len(plan.tasks) >= 3

    # Validate Article IV (VectorStore integration)
    patterns = full_agent_context.search_memories(tags=["plan"])
    assert len(patterns) > 0  # Pattern stored
```

### Example 3: Tool E2E Test

```python
import pytest
from tools.test_verification_gate import TestVerificationGate

@pytest.mark.e2e
@pytest.mark.tool_e2e
@pytest.mark.asyncio
async def test_e2e_tool_verification_gate(
    full_agent_context,
    tmp_git_repo
):
    """
    E2E-TOOL-001: Test verification gate full workflow.

    Validates:
    - Real test execution with pytest
    - Retry logic on timeout (Article I)
    - 100% pass rate validation (Article II)
    - VectorStore pattern storage (Article IV)

    Constitutional Compliance:
    - Article I: Retry on timeout
    - Article II: 100% test pass enforced
    - Article IV: Patterns stored

    Spec: SPEC-009 (Test Verification Gate)
    """
    # Arrange: Create test files in tmp_git_repo
    test_file = tmp_git_repo / "tests" / "test_sample.py"
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text("""
def test_passes():
    assert True
""")

    # Act: Execute verification gate
    gate = TestVerificationGate(
        context=full_agent_context,
        repo_path=tmp_git_repo
    )

    result = await gate.execute(scope="all")

    # Assert: Tests passed
    assert result.is_ok()
    verification = result.unwrap()

    assert verification.tests_executed > 0
    assert verification.pass_rate == 1.0  # 100% pass

    # Validate Article IV (pattern storage)
    patterns = full_agent_context.search_memories(tags=["verification"])
    assert len(patterns) > 0
```

---

## Summary

**E2E Testing in AgencyOS**:
- ✅ **Infrastructure Ready**: Fixtures, fixtures, runner, utilities implemented
- ✅ **22 Tests Passing**: Infrastructure tests validate framework
- ⏳ **43 Tests Pending**: TDD tests written, awaiting implementation
- ✅ **Constitutional Compliance**: Articles I, II, IV, VI validated
- ✅ **Documentation Complete**: Guide, examples, best practices

**Next Steps**:
1. Implement PrimeAOrchestrator (12 mission tests)
2. Implement TestVerificationGate (12 tool tests)
3. Refactor PlannerAgent (11 agent tests)
4. Run `python run_tests.py --e2e` → All 65 tests pass (GREEN phase)

**Resources**:
- Specification: `specs/spec-037-e2e-testing-framework.md`
- Fixtures: `tests/e2e/conftest.py`
- Utilities: `tests/e2e/utils.py`
- Runner: `run_tests.py --e2e`

---

**E2E Testing validates complete workflows end-to-end. Test the system as users experience it, not as functions exist in isolation.**
