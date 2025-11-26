# Docker Ollama Pytest Fixture

## Overview

The `docker_ollama` fixture provides automated Docker orchestration for Trinity Protocol integration tests that require a running Ollama service.

## Features

- **Session-scoped**: Docker Compose starts once per test session (shared across all tests)
- **Automatic health check**: Waits for Ollama to be healthy before yielding (up to 120s)
- **Exponential backoff**: Retries health check with 2s, 4s, 8s, 16s intervals (Article I compliance)
- **Graceful cleanup**: Tears down Docker services after test session (even on failures)
- **Skip support**: Set `SKIP_OLLAMA_TESTS=1` to skip Docker-dependent tests

## Constitutional Compliance

### Article I: Complete Context Before Action
- **Retry logic**: Exponential backoff (2x, 3x intervals) on health check timeouts
- **Maximum wait**: 120 seconds for Ollama to become healthy
- **Verification**: Health check must pass before yielding endpoint to tests

### Article II: 100% Verification and Stability
- **Health gate**: Tests only run if Ollama service passes health check
- **Cleanup guarantee**: Finalizer ensures Docker teardown even on test failures

## Usage

### Basic Usage

```python
import pytest

@pytest.mark.skipif(
    os.getenv("SKIP_OLLAMA_TESTS") == "1",
    reason="Skipping Ollama integration tests"
)
def test_ollama_integration(docker_ollama):
    """Integration test using Ollama service."""
    # Arrange
    endpoint = docker_ollama  # "http://localhost:11434"

    # Act - Use Ollama for inference
    response = requests.get(f"{endpoint}/api/tags")

    # Assert
    assert response.status_code == 200
```

### Multiple Tests (Session Scope)

```python
class TestOllamaIntegration:
    """Multiple tests share same Docker instance."""

    def test_first(self, docker_ollama):
        # Docker starts before this test
        assert docker_ollama == "http://localhost:11434"

    def test_second(self, docker_ollama):
        # Same Docker instance (session scope)
        assert docker_ollama == "http://localhost:11434"

    # Docker tears down after ALL tests complete
```

### With ARCHITECT Agent

```python
def test_architect_with_ollama(docker_ollama, architect_agent):
    """ARCHITECT agent integration test with real Ollama."""
    endpoint = docker_ollama
    agent = architect_agent

    # Test ARCHITECT's interaction with Ollama
    # (Code analysis, ADR recommendations, etc.)
```

## Environment Variables

### `SKIP_OLLAMA_TESTS`

Skip all Docker-dependent tests:

```bash
SKIP_OLLAMA_TESTS=1 pytest tests/trinity_protocol/
```

**Why skip?**
- CI/CD environments without Docker
- Local development without Docker installed
- Faster test runs when Docker integration not needed

## Fixture Lifecycle

1. **Session Start**: Fixture invoked for first test
2. **Environment Check**: Check `SKIP_OLLAMA_TESTS` environment variable
3. **Docker Start**: Run `docker-compose up -d ollama`
4. **Health Check**: Wait for `http://localhost:11434/api/tags` (up to 120s)
5. **Yield Endpoint**: Tests receive `"http://localhost:11434"`
6. **Session End**: All tests complete
7. **Cleanup**: Run `docker-compose down` via finalizer

## Health Check Behavior

### Exponential Backoff (Article I)

```
Attempt 1: Wait 2s  → Retry
Attempt 2: Wait 4s  → Retry
Attempt 3: Wait 8s  → Retry
Attempt 4: Wait 16s → Retry (cap at 16s)
Attempt N: Wait 16s → Retry (until 120s total)
```

### Success Criteria

- HTTP 200 response from `/api/tags`
- No exceptions (connection refused, timeout, etc.)

### Failure Handling

If health check fails after 120s:

1. Attempt cleanup: `docker-compose down`
2. Raise `RuntimeError` with diagnostic message
3. Tests are skipped (not failed)

## Cleanup Behavior

### Normal Cleanup (Test Success)

```python
def cleanup():
    subprocess.run(["docker-compose", "down"], timeout=30)
```

### Cleanup on Test Failure

Pytest finalizer ensures cleanup runs even if tests crash:

```python
request.addfinalizer(cleanup)  # Always runs, even on failure
```

### Cleanup Error Handling

```python
try:
    subprocess.run(["docker-compose", "down"])
except Exception as e:
    print(f"Warning: Docker cleanup failed: {e}")
    # Does NOT fail tests - cleanup is best-effort
```

## Error Scenarios

### Docker Not Installed

```
pytest.skip("docker-compose not installed")
```

### docker-compose.yml Not Found

```
pytest.skip("docker-compose.yml not found at /path/to/repo")
```

### Health Check Timeout

```
RuntimeError: Ollama failed to start after 120s.
Check Docker logs: docker-compose logs ollama
```

### Docker Start Failure

```
pytest.skip("Failed to start Docker Compose: <error message>")
```

## Testing the Fixture

### Validate Skip Logic

```bash
SKIP_OLLAMA_TESTS=1 pytest tests/trinity_protocol/test_docker_ollama_fixture.py -v
```

**Expected**: All Docker-dependent tests skipped

### Validate Health Check

```bash
pytest tests/trinity_protocol/test_docker_ollama_fixture.py::TestDockerOllamaFixture::test_ollama_service_is_healthy -v
```

**Expected**: Test passes after health check succeeds

### Validate Cleanup

```bash
pytest tests/trinity_protocol/test_docker_ollama_fixture.py
# After tests complete, verify:
docker ps | grep ollama  # Should NOT show running container
```

## Best Practices

### 1. Always Use Skip Decorator

```python
@pytest.mark.skipif(
    os.getenv("SKIP_OLLAMA_TESTS") == "1",
    reason="Skipping Ollama integration tests"
)
```

### 2. Session Scope Efficiency

Don't recreate Docker per test - share the session fixture:

```python
# ❌ BAD: Function-scoped (starts/stops Docker per test)
@pytest.fixture
def my_ollama():
    # Don't do this

# ✅ GOOD: Use session-scoped docker_ollama
def test_my_feature(docker_ollama):
    endpoint = docker_ollama
```

### 3. Explicit Cleanup Testing

```python
def test_cleanup_idempotent(docker_ollama):
    """Validate cleanup doesn't crash."""
    assert docker_ollama is not None
    # Cleanup will run automatically via finalizer
```

### 4. Integration Test Naming

Use clear naming for Docker-dependent tests:

```python
# tests/trinity_protocol/test_architect_ollama_integration.py
class TestArchitectOllamaIntegration:
    """Integration tests for ARCHITECT with real Ollama."""
```

## Debugging

### Check Docker Logs

```bash
docker-compose logs ollama
```

### Check Health Manually

```bash
curl http://localhost:11434/api/tags
```

### Check Running Containers

```bash
docker ps | grep ollama
```

### Force Cleanup

```bash
docker-compose down
docker ps -a | grep ollama  # Check for stopped containers
docker volume ls | grep ollama  # Check for volumes
```

## Implementation Details

### Files

- **Fixture**: `tests/trinity_protocol/conftest.py::docker_ollama`
- **Tests**: `tests/trinity_protocol/test_docker_ollama_fixture.py`
- **Examples**: `tests/trinity_protocol/test_docker_ollama_usage_example.py`
- **Docker Config**: `docker-compose.yml` (repository root)

### Dependencies

- `pytest` (fixture framework)
- `requests` (health check HTTP calls)
- `docker-compose` (Docker orchestration)

### Configuration

- **docker-compose.yml**: Ollama service definition
- **Health endpoint**: `http://localhost:11434/api/tags`
- **Timeout**: 120s maximum wait
- **Exponential backoff**: 2s, 4s, 8s, 16s (cap at 16s)

## ADR References

- **ADR-023**: Memory-aware execution (Docker memory limits)
- **ADR-001**: Complete context before action (health check retry logic)
- **ADR-002**: 100% verification (health gate before tests)

## Related Documentation

- `docker-compose.yml`: Ollama service configuration
- `docs/HARDWARE_OPTIMIZATION.md`: Memory-aware test execution
- `constitution.md`: Article I (retry logic), Article II (verification)

---

**Version**: 1.0.0
**Last Updated**: 2025-10-11
**Constitutional Compliance**: Articles I, II ✅
