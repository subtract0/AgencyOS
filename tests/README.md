# Test Organization

## Quick Reference

Fast feedback loop (TDD):
```bash
pytest tests/unit -m unit          # Fast unit tests (<30s) - DEFAULT for TDD
pytest tests/                       # All tests (~7min) - PRE-COMMIT
```

Selective execution:
```bash
pytest tests/unit                   # Unit tests only (~30s)
pytest tests/integration            # Integration tests (~2min)
pytest tests/e2e                    # End-to-end tests (~5min)
pytest tests/benchmark              # Performance benchmarks
pytest -m "not slow"                # Skip slow tests
pytest -m "unit and not github"     # Unit tests without GitHub API
```

## Directory Structure

```
tests/
├── unit/                   # Fast, isolated tests (mock external deps)
│   ├── tools/             # Tool-specific unit tests
│   ├── agents/            # Agent logic tests
│   └── shared/            # Shared module tests
├── integration/           # Cross-component tests (real deps)
│   ├── memory/            # Memory integration tests
│   └── learning/          # Learning system tests
├── e2e/                   # Full workflow tests
│   └── workflows/         # Complete user workflows
├── trinity_protocol/      # Trinity protocol tests
├── dspy_agents/          # DSPy agent tests
├── necessary/            # NECESSARY pattern validation
├── benchmark/            # Performance tests
└── fixtures/             # Shared test data and helpers

```

## Test Categories

### Unit Tests (tests/unit/)
- **Speed**: <1s per test, <30s total
- **Dependencies**: All external dependencies mocked
- **Purpose**: Test individual functions/classes in isolation
- **Examples**:
  - Tool behavior (cache, validation, parsing)
  - Model serialization/deserialization
  - Utility functions
  - Type safety checks

### Integration Tests (tests/integration/)
- **Speed**: 1-10s per test, ~2min total
- **Dependencies**: Real dependencies (filesystem, memory store)
- **Purpose**: Test component interactions
- **Examples**:
  - Agent-to-agent communication
  - Memory persistence
  - Tool chaining
  - Repository pattern validation

### End-to-End Tests (tests/e2e/)
- **Speed**: 10-60s per test, ~5min total
- **Dependencies**: Full system (may use test fixtures)
- **Purpose**: Validate complete workflows
- **Examples**:
  - Spec → Plan → Code workflow
  - Autonomous healing cycle
  - Learning loop end-to-end
  - Multi-agent orchestration

### Benchmark Tests (tests/benchmark/)
- **Speed**: Variable (1-60s per test)
- **Dependencies**: Real system components
- **Purpose**: Performance measurement and regression detection
- **Examples**:
  - Tool cache performance
  - Memory search latency
  - Agent response times
  - Vector store operations

## Pytest Markers

All tests should be marked appropriately:

```python
import pytest

@pytest.mark.unit  # Fast unit test
def test_cache_hit():
    ...

@pytest.mark.integration  # Integration test
def test_agent_handoff():
    ...

@pytest.mark.e2e  # End-to-end test
def test_full_workflow():
    ...

@pytest.mark.slow  # Slow test (>5s)
def test_expensive_operation():
    ...

@pytest.mark.benchmark  # Performance test
def test_cache_performance():
    ...

@pytest.mark.github  # Requires GitHub API
def test_pr_creation():
    ...
```

## Best Practices

### Writing Fast Unit Tests
1. **Mock external dependencies**: Use `unittest.mock` or `pytest-mock`
2. **Avoid I/O**: No file system, network, or database calls
3. **Keep focused**: Test one thing per test
4. **Use fixtures**: Share setup via pytest fixtures

### Migration Checklist
When moving tests to organized structure:

- [ ] Identify test type (unit/integration/e2e)
- [ ] Move to appropriate directory
- [ ] Add pytest markers (`@pytest.mark.unit`, etc.)
- [ ] Update imports if needed
- [ ] Verify test still passes: `pytest path/to/test.py -v`
- [ ] Run full suite to ensure no breakage

## Performance Targets

| Category | Target Time | Parallel | Total Tests |
|----------|-------------|----------|-------------|
| Unit | <30s | 8 workers | ~1,200 |
| Integration | ~2min | 4 workers | ~400 |
| E2E | ~5min | 2 workers | ~100 |
| Full Suite | ~7min | Auto | ~1,700 |

## Configuration

See `pytest.ini` for detailed configuration:
- Parallel execution: `-n 8` (configurable)
- Test discovery: `test_*.py` pattern
- Markers: Enforce strict markers (`--strict-markers`)
- Async support: `pytest-asyncio` auto mode

## Continuous Integration

Pre-commit hooks run unit tests only (fast feedback).
Full CI pipeline runs all tests on push/PR.

```bash
# Pre-commit (local)
pytest tests/unit -m unit --tb=short

# CI (full validation)
pytest tests/ --tb=short --junitxml=results.xml
```

## Migration Status

Phase 4 Implementation:
- ✅ Directory structure created
- ✅ README documentation
- ✅ pytest.ini markers configured
- 🔄 Incremental test migration (ongoing)

Current organization:
- Unit tests: Partially migrated to `tests/unit/`
- Integration tests: In `tests/integration/`
- Trinity tests: In `tests/trinity_protocol/`
- DSPy tests: In `tests/dspy_agents/`
- Root tests: Legacy location (to be migrated)

## Future Work

1. **Complete migration**: Move remaining root-level tests
2. **Fixture consolidation**: Centralize shared fixtures in `tests/fixtures/`
3. **Performance optimization**: Identify and optimize slow tests
4. **Coverage tracking**: Per-category coverage reports
5. **Test generation**: Auto-generate test skeletons from code

---

**Speed is quality.** Fast tests enable TDD. TDD enables clean code.
