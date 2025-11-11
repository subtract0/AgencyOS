# Testing Documentation

Complete guide to AgencyOS test infrastructure, execution, and standards.

---

## Quick Start

```bash
# Run full test suite (RECOMMENDED)
python run_tests.py --run-all

# Run unit tests only
python run_tests.py

# Run with Docker (enables Ollama integration tests)
python run_tests.py --with-docker --run-all
```

**Expected Results**: 5,822 tests passing, 164 skipped, 0 failures (100% pass rate)

---

## Current Test Status

**Latest Status**: See [ACTUAL_TEST_STATUS.md](ACTUAL_TEST_STATUS.md)

**Key Metrics**:
- **5,822 tests** passing (100% pass rate)
- **164 tests** skipped (Ollama integration tests without Docker)
- **3:51 execution time** for full suite
- **175+ test files** across codebase

---

## Critical Requirements

### MUST Use Official Test Runner

**✅ CORRECT:**
```bash
python run_tests.py --run-all
```

**❌ INCORRECT (Will Segfault):**
```bash
.venv/bin/python -m pytest tests/  # AVOID - Python 3.13 incompatibility
```

### Why Direct pytest Fails

Python 3.13.7 + agency-swarm has threading bugs in `agents/tracing/processors.py:268`:
- Direct pytest execution causes segmentation faults at ~74% progress
- Official test runner uses `uv run pytest` with proper environment isolation
- Memory-aware parallelism prevents resource contention

---

## Test Categories

### Unit Tests (5,822 total)
- **Agent Tests**: 10 agent modules with factory pattern tests
- **Tool Tests**: 56+ production tools with security/validation tests
- **Memory Tests**: VectorStore, EnhancedMemoryStore, Anthropic Memory Tool
- **Infrastructure Tests**: Shared modules, model policy, type definitions
- **Constitutional Tests**: Governance framework enforcement

### Integration Tests (164 - Requires Docker)
- **Ollama Tests**: Local model integration (Q8_0 quantization)
- **End-to-End Workflows**: Multi-agent orchestration scenarios
- **Docker Compose**: Automated Ollama container lifecycle

---

## Test Execution Modes

### Standard (Unit Tests Only)
```bash
python run_tests.py --run-all
```
- Fastest execution (~4 minutes)
- Skips 164 Ollama integration tests
- Safe for CI/CD environments without Docker

### With Docker (Full Suite)
```bash
python run_tests.py --with-docker --run-all
```
- Enables 164 Ollama integration tests
- Requires Docker Desktop or Docker Engine
- Auto-manages Ollama container lifecycle

### Fast Mode
```bash
python run_tests.py --fast
```
- Quick smoke tests for rapid feedback
- Useful during active development

---

## Test Runner Architecture

### Memory-Aware Parallelism

The test runner automatically adjusts worker count based on system resources:

```python
from tools.memory_aware_test_runner import get_safe_worker_count

worker_count = get_safe_worker_count()
# Returns:
# - 1 worker if <10GB RAM available
# - 3 workers if local model active (prevents exhaustion)
# - 10 workers for cloud-only execution
# - 6 workers for moderate systems
```

**Benefits**:
- Prevents OOM crashes
- Optimizes for M1/M2/M3 Mac unified memory
- Adapts to local Ollama model presence

### Test Runner Features

1. **Environment Isolation**: Uses `uv run pytest` for clean environments
2. **Threading Safety**: Avoids Python 3.13 + agency-swarm conflicts
3. **Docker Integration**: Auto-detects and manages Ollama containers
4. **Progress Tracking**: Real-time test execution feedback
5. **Result Aggregation**: Clear pass/fail/skip reporting

---

## Constitutional Requirements

### Article I: Complete Context Before Action
- **ALL tests MUST run to completion** (never partial results)
- Retry on timeout (2x, 3x, up to 10x)
- Fix failing tests BEFORE new features

### Article II: 100% Verification and Stability
- **Main branch: 100% test success ALWAYS** (no exceptions)
- No merge without 100% test pass
- Definition of Done: Code + Tests + Pass + Review ✓

### Article III: Automated Local Enforcement
- Pre-commit hooks validate test success
- No manual overrides for quality standards
- CI/CD is OPTIONAL (local enforcement sufficient)

---

## Python Version Compatibility

### Recommended: Python 3.12
- ✅ Stable with agency-swarm
- ✅ No known threading issues
- ✅ Production-ready

### Python 3.13 (Known Issues)
- ⚠️ **Segfaults** with direct pytest execution
- ⚠️ Threading bugs in agency-swarm dependency
- ⚠️ Requires official test runner (`python run_tests.py`)

**Workaround**: Always use `python run_tests.py` on Python 3.13

---

## CI/CD Status

### GitHub Actions: ❌ BLOCKED
- **Issue**: Billing/payment failure
- **Impact**: No automated test runs on push
- **Workaround**: Manual local validation required
- **Status**: External blocker, requires repository owner action

### Local Enforcement: ✅ ACTIVE
- Pre-commit hooks validate changes
- Branch protection via local tests
- Constitutional compliance enforced locally

---

## Troubleshooting

### Segmentation Faults
**Symptom**: Tests crash at ~74% progress with "Fatal Python error: Segmentation fault"

**Solution**:
```bash
# Use official test runner (NOT direct pytest)
python run_tests.py --run-all
```

### Collection Errors
**Symptom**: `ImportError: No module named 'sklearn'`

**Solution**:
```bash
pip install scikit-learn>=1.0.0
```

### Docker Integration Issues
**Symptom**: Ollama tests skipped or container unhealthy

**Solution**:
```bash
# Start Ollama container
docker compose up -d

# Verify health
docker compose ps
docker compose logs ollama

# Run tests with Docker
python run_tests.py --with-docker --run-all
```

---

## Test Writing Standards

### TDD Workflow (Article VI)
1. **RED**: Write failing test first
2. **GREEN**: Implement minimum code to pass
3. **REFACTOR**: Improve while maintaining green

### Value-First Testing (Article VII)
- Test NECESSARY functionality (not trivial behavior)
- Focus on business value scenarios
- Avoid testing framework internals

### Test Patterns

**AAA Pattern** (Arrange-Act-Assert):
```python
def test_feature():
    # Arrange: Set up test data
    context = create_agent_context()

    # Act: Execute functionality
    result = some_function(context)

    # Assert: Verify outcomes
    assert result.is_ok()
    assert result.unwrap() == expected_value
```

**Result Pattern** (Type-Safe Errors):
```python
def test_error_handling():
    result = risky_operation()

    assert result.is_err()
    assert isinstance(result.unwrap_err(), ExpectedError)
```

---

## Related Documentation

- **Test Status**: [ACTUAL_TEST_STATUS.md](ACTUAL_TEST_STATUS.md) - Current test health
- **Architecture**: [../ARCHITECTURE.md](../ARCHITECTURE.md) - Technical architecture overview
- **Constitution**: [../../constitution.md](../../constitution.md) - Testing governance (Articles I-VII)
- **ADR-002**: Verification and stability mandate
- **ADR-023**: Memory-aware test execution

---

## Quick Reference

| Command | Purpose | Duration |
|---------|---------|----------|
| `python run_tests.py --run-all` | Full unit suite | ~4 min |
| `python run_tests.py --fast` | Quick smoke tests | <1 min |
| `python run_tests.py --with-docker --run-all` | Full suite + integration | ~5 min |
| `python run_tests.py --integration-only` | Ollama tests only | ~1 min |

---

**Last Updated**: 2025-01-30
**Status**: 100% pass rate maintained
**Next Milestone**: CI/CD billing resolution
