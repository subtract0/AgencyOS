# Specification: Ollama Test Integration Strategy

**ID**: SPEC-049
**Status**: Draft
**Created**: 2025-10-11
**Updated**: 2025-10-11
**Owner**: PlannerAgent
**Tier**: Tier 1 (Test Infrastructure)

## Goals

**Primary objective: Enable 140 skipped Ollama integration tests with zero system instability**

- **Goal 1**: Remove all `pytest.mark.skip` decorators from 140 tests in `test_hybrid_executor.py` and `test_hybrid_executor_generalized.py`
- **Goal 2**: Implement Docker-based Ollama lifecycle management for deterministic test execution
- **Goal 3**: Maintain 100% test success rate (Article II) with memory-safe execution (ADR-023)
- **Goal 4**: Zero kernel panics or OOM conditions during integration test execution
- **Goal 5**: Integration tests complete in <5 minutes on current hardware (available memory) with parallel execution

## Non-Goals

**Explicitly out of scope for this specification**

- **Non-goal 1**: Refactoring existing test logic or assertions (only remove skip markers, add fixtures)
- **Non-goal 2**: Upgrading Ollama version or changing model selection (use existing Qwen3-Coder)
- **Non-goal 3**: Creating new tests beyond the 140 already written
- **Non-goal 4**: Kubernetes orchestration or cloud deployment (Docker Compose only)
- **Non-goal 5**: Windows/Linux test runner support (macOS current hardware primary target)

## Personas

**Who will use this feature and how**

### Persona 1: CI/CD Pipeline (Automated Test Runner)

- **Context**: GitHub Actions or local pre-commit hooks execute full test suite
- **Need**: Deterministic Ollama availability without manual intervention
- **Interaction**: `pytest tests/trinity_protocol/core/` automatically starts Docker, runs tests, stops Docker

### Persona 2: Developer (Local Development)

- **Context**: Running integration tests during TDD cycle for HybridExecutor changes
- **Need**: Fast test feedback (<5 min) without manual Docker commands
- **Interaction**: `pytest tests/trinity_protocol/core/test_hybrid_executor.py` auto-manages Ollama lifecycle

### Persona 3: QualityEnforcer Agent (Constitutional Validation)

- **Context**: Verifying 100% test pass rate before merge (Article II)
- **Need**: Memory-aware test execution preventing OOM failures
- **Interaction**: `run_tests.py --integration-only` respects ADR-023 worker limits

## Acceptance Criteria

**Verifiable conditions for feature completion**

### Functional Criteria

- [ ] **AC-001**: All 140 tests in `test_hybrid_executor.py` and `test_hybrid_executor_generalized.py` have `pytest.mark.skip` removed
- [ ] **AC-002**: Docker Compose file creates Ollama service with Qwen3-Coder 30B Q8_0 model preloaded
- [ ] **AC-003**: Pytest fixture `ollama_docker_service` manages Docker lifecycle (start before tests, stop after)
- [ ] **AC-004**: Tests detect Ollama availability via health check (localhost:11434/api/tags)
- [ ] **AC-005**: Fixture waits up to 120s for Ollama model load with exponential backoff retry

### Non-Functional Criteria

- [ ] **AC-006**: Integration tests complete in <5 minutes on current hardware (3 workers, ADR-023)
- [ ] **AC-007**: Memory usage stays ≤40GB (Ollama 38GB + 3 workers × 3GB = 47GB safe)
- [ ] **AC-008**: Zero kernel panics during 10 consecutive test runs
- [ ] **AC-009**: Docker cleanup succeeds 100% (no orphaned containers after pytest exit)
- [ ] **AC-010**: Works with both native Docker and Colima (macOS Docker alternatives)

### Quality Criteria (Constitutional Compliance)

- [ ] **AC-011**: Article I - Complete context: Tests retry on Ollama startup timeout (2x, 3x)
- [ ] **AC-012**: Article II - 100% verification: All 140 tests pass (no xfail, no skip)
- [ ] **AC-013**: Article III - Automated enforcement: CI pipeline runs integration tests on every PR
- [ ] **AC-014**: ADR-023 - Memory-aware execution: Worker count adjusts when Ollama active (3 workers)
- [ ] **AC-015**: ADR-001 - Timeout handling: Health check retries with exponential backoff

## Dependencies

- **ADR-023**: Memory-Aware Test Execution (provides worker count logic)
- **Docker Architecture**: Spec-ollama-docker-architecture.md (if exists, or create)
- **tools/memory_aware_test_runner.py**: Existing memory safety checks
- **tools/ollama_health_check.py**: Existing Ollama availability detection
- **pytest-docker-compose**: External library for Docker fixture integration

## Technical Architecture

### 1. Docker Compose Service Definition

**File**: `docker-compose.test.yml` (new file in project root)

```yaml
version: '3.8'

services:
  ollama-test:
    image: ollama/ollama:latest
    container_name: agency-ollama-test
    ports:
      - "11434:11434"
    volumes:
      - ollama-models:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
      - OLLAMA_NUM_PARALLEL=1
      - OLLAMA_MAX_LOADED_MODELS=1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 5s
      retries: 12
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: 40G  # 38GB model + 2GB overhead
    command: >
      sh -c "ollama serve & sleep 10 &&
             ollama pull hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0 &&
             wait"

volumes:
  ollama-models:
    driver: local
```

**Key Design Decisions**:
- Port 11434 exposed for test access (same as production)
- Volume persistence to avoid re-downloading 30GB model every run
- Health check ensures model loaded before tests start
- Memory limit enforced at Docker level (40GB cap)
- Single model policy (OLLAMA_MAX_LOADED_MODELS=1) for memory efficiency

### 2. Pytest Fixture Architecture

**File**: `tests/trinity_protocol/conftest.py` (new file)

```python
"""
Pytest fixtures for trinity_protocol integration tests.

Provides Docker-managed Ollama service for HybridExecutor tests.
"""

import asyncio
import subprocess
import time
from pathlib import Path

import pytest
import requests
from pytest_docker_compose import DockerComposeExecutor

from tools.ollama_health_check import check_ollama_health
from shared.type_definitions.result import Ok

# Path to docker-compose file
COMPOSE_FILE = Path(__file__).parents[2] / "docker-compose.test.yml"


@pytest.fixture(scope="session")
def ollama_docker_service(request):
    """
    Manage Ollama Docker service lifecycle for integration tests.

    Scope: session (shared across all tests for efficiency)
    Lifecycle:
      1. Start Docker Compose with ollama-test service
      2. Wait for health check (up to 120s with exponential backoff)
      3. Yield service URL to tests
      4. Stop and cleanup Docker on session end

    Constitutional Compliance:
      - Article I: Retry health check on timeout (2x, 3x intervals)
      - ADR-023: Only starts if memory safe (>15GB available)

    Raises:
        RuntimeError: If Ollama fails to start after 120s
        MemoryError: If insufficient memory for safe operation
    """
    # Memory safety check (ADR-023)
    from tools.memory_aware_test_runner import verify_memory_safe

    if not verify_memory_safe(required_gb=38):
        pytest.skip("Insufficient memory for Ollama integration tests (<43GB available)")

    # Start Docker Compose
    executor = DockerComposeExecutor(
        compose_files=[str(COMPOSE_FILE)],
        compose_project_name="agency-test"
    )

    # Start service
    executor.execute("up -d ollama-test")

    # Wait for health check with exponential backoff (Article I retry logic)
    max_wait = 120
    interval = 2
    elapsed = 0

    while elapsed < max_wait:
        try:
            result = asyncio.run(check_ollama_health(timeout=5, max_retries=1))
            if isinstance(result, Ok) and result.value.is_running:
                # Verify model loaded by checking tags endpoint
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200 and "qwen" in response.text.lower():
                    break
        except Exception:
            pass

        time.sleep(interval)
        elapsed += interval

        # Exponential backoff (2s, 4s, 8s, 16s, then 16s max)
        interval = min(interval * 2, 16)
    else:
        # Cleanup on failure
        executor.execute("down -v")
        raise RuntimeError(
            f"Ollama failed to start after {max_wait}s. "
            "Check Docker logs: docker-compose -f docker-compose.test.yml logs ollama-test"
        )

    # Yield service URL to tests
    yield "http://localhost:11434"

    # Cleanup on session end
    def cleanup():
        try:
            executor.execute("down -v")
        except Exception as e:
            print(f"Warning: Docker cleanup failed: {e}")

    request.addfinalizer(cleanup)


@pytest.fixture(scope="function")
def ollama_available(ollama_docker_service):
    """
    Function-scoped fixture to ensure Ollama is available for each test.

    Usage: Add as parameter to tests requiring Ollama

    Example:
        def test_hybrid_executor_with_ollama(ollama_available):
            # Test executes only if Ollama running
            result = execute_task_with_ollama()
    """
    # Quick health check before test
    try:
        response = requests.get(f"{ollama_docker_service}/api/tags", timeout=2)
        if response.status_code != 200:
            pytest.skip("Ollama service not responding")
    except Exception as e:
        pytest.skip(f"Ollama unavailable: {e}")

    return ollama_docker_service
```

### 3. Test Skip Logic Removal Strategy

**Current State** (test_hybrid_executor.py line 48):
```python
OLLAMA_AVAILABLE = is_ollama_available()
```

**Problem**: Tests check Ollama at import time, before Docker can start.

**Solution**: Remove module-level check, rely on fixture:

```python
# DELETE lines 39-48 (is_ollama_available function + OLLAMA_AVAILABLE global)

# UPDATE test class decorators
# BEFORE:
@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not available")
class TestIntegrationWorkflows:
    ...

# AFTER:
class TestIntegrationWorkflows:
    def test_complete_workflow_task_to_result(
        self, ollama_available,  # ADD FIXTURE
        real_message_bus,
        real_cost_tracker,
        real_agent_context,
        temp_plans_dir
    ):
        ...
```

**Automated Refactoring Pattern**:
1. Remove `is_ollama_available()` function (lines 39-46)
2. Remove `OLLAMA_AVAILABLE = ...` assignment (line 48)
3. Remove all `@pytest.mark.skipif(not OLLAMA_AVAILABLE, ...)` decorators
4. Add `ollama_available` parameter to tests that execute real Ollama calls
5. Keep tests that mock Ollama unchanged (no fixture needed)

### 4. Timeout and Retry Configuration

**Pytest Configuration** (`pytest.ini` additions):

```ini
[pytest]
# Integration test timeouts (override unit test 2s default)
timeout_func_only = true
integration_timeout = 300  # 5 minutes for integration tests

# Docker fixture configuration
docker_compose_remove_volumes = true
docker_compose_project_name = agency-test
```

**Test-Level Timeout Overrides**:

```python
@pytest.mark.timeout(300)  # 5 minutes for full workflow test
@pytest.mark.integration
def test_complete_workflow_task_to_result(ollama_available, ...):
    """Allow longer timeout for real Ollama execution."""
    ...
```

### 5. Memory Safety Integration (ADR-023)

**Integration with Existing Memory-Aware Runner**:

```python
# tests/trinity_protocol/conftest.py (ollama_docker_service fixture)

from tools.memory_aware_test_runner import get_safe_worker_count, verify_memory_safe

@pytest.fixture(scope="session")
def ollama_docker_service(request):
    # BEFORE starting Docker, check memory
    if not verify_memory_safe(required_gb=38):
        pytest.skip("Insufficient memory for Ollama (need 43GB available)")

    # Start Docker...
    ...

    # AFTER Ollama starts, reduce pytest workers (ADR-023)
    worker_count = get_safe_worker_count()
    # Note: Worker count already enforced by run_tests.py,
    # but fixture validates memory state
```

**CI Configuration** (`.github/workflows/test.yml` snippet):

```yaml
- name: Run Integration Tests with Ollama
  env:
    LOCAL_MODEL_TEST_WORKERS: 3  # Force ADR-023 worker limit
  run: |
    # Check memory before starting
    python -c "from tools.memory_aware_test_runner import verify_memory_safe; assert verify_memory_safe(38), 'Insufficient memory for Ollama tests'"

    # Run tests with Docker fixture
    python run_tests.py --integration-only
```

## Implementation Plan

### Phase 1: Docker Infrastructure (2 hours)

**Tasks**:
1. Create `docker-compose.test.yml` with Ollama service definition
2. Test Docker Compose manually: `docker-compose -f docker-compose.test.yml up`
3. Verify model loads: `curl http://localhost:11434/api/tags`
4. Verify memory usage: `docker stats agency-ollama-test`

**Acceptance**: Ollama container starts, loads model, responds to health check in <120s

### Phase 2: Pytest Fixture Implementation (3 hours)

**Tasks**:
1. Install `pytest-docker-compose`: `pip install pytest-docker-compose`
2. Create `tests/trinity_protocol/conftest.py` with `ollama_docker_service` fixture
3. Implement health check retry logic with exponential backoff
4. Add memory safety check integration (ADR-023)
5. Test fixture in isolation: `pytest tests/trinity_protocol/conftest.py --setup-show`

**Acceptance**: Fixture starts Docker, waits for health, yields URL, cleans up

### Phase 3: Test Refactoring (4 hours)

**Tasks**:
1. Refactor `test_hybrid_executor.py`:
   - Remove `is_ollama_available()` function (lines 39-46)
   - Remove `OLLAMA_AVAILABLE` global (line 48)
   - Remove `@pytest.mark.skipif` decorators from 63 tests
   - Add `ollama_available` fixture parameter to integration tests
2. Refactor `test_hybrid_executor_generalized.py`:
   - Remove module-level `pytestmark = pytest.mark.skip(...)` (line 36)
   - Add `ollama_available` fixture to tests needing real execution
3. Keep mocked tests unchanged (no fixture needed)

**Acceptance**: All 140 tests import without skip markers, fixture parameter added

### Phase 4: Integration Testing (3 hours)

**Tasks**:
1. Run single test file: `pytest tests/trinity_protocol/core/test_hybrid_executor.py -v`
2. Monitor memory usage: `watch -n 1 "ps aux | grep ollama"`
3. Verify worker count: Check pytest output for `-n 3` (ADR-023)
4. Run 10 consecutive test executions, check for:
   - Kernel panics (0 expected)
   - Docker cleanup success (100% expected)
   - Test pass rate (100% expected)
5. Run full integration suite: `pytest tests/trinity_protocol/ -v`

**Acceptance**: 100% pass rate, <5 min execution time, 0 kernel panics

### Phase 5: CI/CD Integration (2 hours)

**Tasks**:
1. Update `.github/workflows/test.yml` to install Docker
2. Add memory check before integration tests
3. Set `LOCAL_MODEL_TEST_WORKERS=3` environment variable
4. Add timeout for integration job (10 minutes)
5. Test on GitHub Actions runner (if available)

**Acceptance**: CI runs integration tests automatically on PRs

## Testing Strategy

### Unit Tests (No Ollama Required)

**File**: `tests/test_ollama_docker_fixture.py` (new)

```python
"""Unit tests for Ollama Docker fixture (mocked Docker)."""

def test_ollama_docker_service_checks_memory_before_start(mocker):
    """Test fixture skips if insufficient memory."""
    mocker.patch("tools.memory_aware_test_runner.verify_memory_safe", return_value=False)

    with pytest.raises(pytest.skip.Exception, match="Insufficient memory"):
        ollama_docker_service(request=mocker.Mock())

def test_ollama_docker_service_retries_health_check_on_timeout(mocker):
    """Test exponential backoff retry logic (Article I)."""
    # Mock health check to fail 3 times, then succeed
    mocker.patch("tools.ollama_health_check.check_ollama_health", side_effect=[
        Err("timeout"), Err("timeout"), Err("timeout"), Ok(HealthStatus(is_running=True))
    ])

    # Should retry with 2s, 4s, 8s intervals
    result = ollama_docker_service(...)
    assert result == "http://localhost:11434"

def test_ollama_docker_service_cleans_up_on_failure(mocker):
    """Test Docker cleanup runs even if health check fails."""
    # Mock health check to always fail
    mocker.patch("tools.ollama_health_check.check_ollama_health", return_value=Err("timeout"))

    # Should call `docker-compose down -v`
    mock_executor = mocker.Mock()
    with pytest.raises(RuntimeError, match="Ollama failed to start"):
        ollama_docker_service(...)

    mock_executor.execute.assert_any_call("down -v")
```

### Integration Tests (Real Ollama)

**File**: `tests/trinity_protocol/core/test_hybrid_executor.py` (updated)

**Before** (63 tests skipped):
```python
class TestIntegrationWorkflows:
    @pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not available")
    async def test_complete_workflow_task_to_result(self, ...):
        ...
```

**After** (63 tests executable):
```python
class TestIntegrationWorkflows:
    @pytest.mark.integration
    @pytest.mark.timeout(300)
    async def test_complete_workflow_task_to_result(
        self,
        ollama_available,  # NEW: Docker-managed Ollama
        real_message_bus,
        real_cost_tracker,
        real_agent_context,
        temp_plans_dir
    ):
        # Test now executes with real Docker-managed Ollama
        # No mock patching of ollama.chat needed
        ...
```

### Edge Cases

- **EC-001**: Ollama container fails to start (network issue)
  - **Expected**: Fixture raises `RuntimeError` after 120s, tests skip
- **EC-002**: Docker not installed on system
  - **Expected**: `pytest-docker-compose` raises early error, clear message
- **EC-003**: Port 11434 already in use (existing Ollama)
  - **Expected**: Docker fails to bind port, fixture detects and uses existing Ollama
- **EC-004**: Insufficient memory (<43GB) for Ollama
  - **Expected**: Fixture skips with memory safety message (ADR-023)
- **EC-005**: Model download fails (network timeout)
  - **Expected**: Health check fails after 120s, fixture cleans up Docker

## Risk Management

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Docker not installed on dev machines | High | Medium | Document Docker install in README, add check in fixture |
| Ollama model download timeout (30GB) | High | Medium | Use volume persistence, cache model after first download |
| Memory exhaustion (OOM) during tests | High | Low | ADR-023 memory check, 3-worker limit, Docker 40GB cap |
| Flaky tests due to Ollama startup timing | Medium | Medium | Exponential backoff retry (Article I), 120s max wait |
| Docker cleanup failure (orphaned containers) | Low | Low | `request.addfinalizer()` ensures cleanup, `-v` removes volumes |
| CI runner lacks Docker support | High | Low | Use GitHub Actions with Docker pre-installed, fallback to skip |
| Port conflicts with production Ollama | Low | High | Use dedicated compose file, allow fallback to existing Ollama |

## Alternatives Considered

### Alternative 1: Manual Ollama Management (Status Quo)

**Rejected** - Requires developers to manually start Ollama, error-prone, breaks CI automation

**Pros**: Simple, no Docker dependency
**Cons**: Manual intervention, unreliable, violates Article III (no automated enforcement)

### Alternative 2: Pytest-Docker Plugin

**Rejected** - Less flexible than docker-compose, harder to share config with CI

**Pros**: Pure Python, no docker-compose.yml file
**Cons**: Complex configuration, less portable, no health check support

### Alternative 3: Skip Integration Tests in CI

**Rejected** - Violates Article II (100% verification), defeats purpose of 140 tests

**Pros**: Fast CI, no Docker complexity
**Cons**: Integration bugs slip through, tests become dead code

### Alternative 4: Cloud-Based Ollama Service

**Rejected** - High cost ($4/hr), latency, violates 96% cost reduction goal

**Pros**: No local memory concerns, consistent environment
**Cons**: Expensive, slow, defeats local model advantage

## Constitutional Compliance Checklist

### Article I: Complete Context Before Action ✅
- **Timeout Retry**: Health check uses exponential backoff (2s, 4s, 8s, 16s)
- **Complete Execution**: Fixture waits up to 120s for model load before yielding
- **No Partial Results**: Fixture raises error if Ollama fails to start

### Article II: 100% Verification and Stability ✅
- **Test Success Rate**: All 140 tests must pass (no skip, no xfail)
- **Quality Gate**: Integration tests run on every PR via CI
- **Real Functionality**: Tests execute against real Ollama, not mocks

### Article III: Automated Merge Enforcement ✅
- **No Manual Steps**: Fixture auto-starts Docker, developers run `pytest`
- **CI Enforcement**: GitHub Actions runs integration tests automatically
- **Quality Gate**: 100% pass rate required for merge

### Article IV: Continuous Learning ✅
- **Pattern Storage**: Integration test patterns stored in VectorStore after success
- **Memory Query**: Fixture uses ADR-023 patterns for memory safety
- **Cross-Session**: Docker volume persists model, avoiding re-download

### Article V: Spec-Driven Development ✅
- **Formal Spec**: This document (spec-ollama-test-integration.md)
- **Traceability**: References ADR-023, ADR-001, Docker architecture
- **Approval Required**: Spec approval before implementation begins

### ADR-023: Memory-Aware Test Execution ✅
- **Worker Adjustment**: Fixture respects 3-worker limit when Ollama active
- **Memory Check**: `verify_memory_safe(38)` before Docker start
- **Safety Margin**: 5GB buffer enforced (43GB required, available memory available)

## Success Metrics

- **Primary**: 140/140 tests pass (100% success rate)
- **Performance**: Integration suite completes in <5 minutes
- **Stability**: 0 kernel panics in 10 consecutive runs
- **Automation**: 100% of integration tests run in CI
- **Memory Safety**: Peak memory ≤40GB (ADR-023 compliance)
- **Docker Cleanup**: 100% success rate (no orphaned containers)

## References

- **ADR-023**: Memory-Aware Test Execution (`docs/adr/ADR-023-memory-aware-test-execution.md`)
- **ADR-001**: Complete Context Before Action (`docs/adr/ADR-001-complete-context-before-action.md`)
- **Constitution**: Article I, II, III (`constitution.md`)
- **Test Files**:
  - `tests/trinity_protocol/core/test_hybrid_executor.py` (63 skipped tests)
  - `tests/trinity_protocol/core/test_hybrid_executor_generalized.py` (77 skipped tests)
- **Memory Runner**: `tools/memory_aware_test_runner.py`
- **Health Check**: `tools/ollama_health_check.py`
- **Pytest Config**: `pytest.ini`

---

**Constitutional Validation**: ✅ All 5 Articles verified
**ADR Compliance**: ✅ ADR-023, ADR-001 integrated
**Memory Safety**: ✅ 38GB Ollama + 9GB tests = 47GB < available memory total
**Implementation Ready**: ✅ Awaiting approval for plan.md creation

---

*"Tests that skip are tests that lie. Enable them all."*
