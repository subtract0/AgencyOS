# Constitutional Test Agent Migration Guide

## Overview

This guide helps migrate from **unconstitutional mock agents** to **constitutional real agents** in tests.

**Constitutional Violation**: 217 usages of `create_mock_agent()` violate **Article II, Section 2.2**:
> "Tests MUST verify REAL functionality, not simulated behavior"
> "Mocked functions SHALL NOT be merged to main branch"

**Solution**: Use `create_constitutional_test_agent()` and `create_test_agent_context()` for **real behavior** in tests.

---

## Quick Migration

### Before (Constitutional Violation ❌)

```python
from unittest.mock import create_autospec, MagicMock
from agency_swarm import Agent

def create_mock_agent(name: str) -> MagicMock:
    mock_agent = create_autospec(Agent, instance=True)
    mock_agent.name = name
    mock_agent.model = "gpt-5-mini"
    mock_agent.tools = []
    return mock_agent

# Usage
mock_coder = create_mock_agent("AgencyCodeAgent")
mock_planner = create_mock_agent("PlannerAgent")
```

### After (Constitutional Compliance ✅)

```python
from tests.fixtures.constitutional_test_agents import create_constitutional_test_agent

# Usage
coder = create_constitutional_test_agent("AgencyCodeAgent")
planner = create_constitutional_test_agent("PlannerAgent")
```

**Result**: Real Agent instances with actual behavior, not simulated.

---

## Context Migration

### Before (Mock Context ❌)

```python
from unittest.mock import Mock

@pytest.fixture
def mock_agent_context():
    context = Mock()
    context.store_memory = Mock()
    context.search_memories = Mock(return_value=[])
    return context

# Usage
def test_something(mock_agent_context):
    mock_agent_context.store_memory("key", "value", tags=["test"])
    # Memory doesn't actually work - just mocked
```

### After (Real Context ✅)

```python
from tests.fixtures.constitutional_test_agents import create_test_agent_context

# Usage
def test_something():
    context = create_test_agent_context(session_id="test_123")
    context.store_memory("key", "value", tags=["test"])
    results = context.search_memories(["test"], include_session=True)
    assert len(results) > 0  # Real verification
```

**Result**: Actual memory operations work, verifying real behavior.

---

## Migration Patterns

### Pattern 1: Simple Agent Creation

```python
# Before
mock_agent = create_mock_agent("TestAgent")

# After
agent = create_constitutional_test_agent("TestAgent")
```

### Pattern 2: Agent with Custom Configuration

```python
# Before
mock_agent = create_mock_agent("TestAgent")
mock_agent.model = "gpt-5"
mock_agent.temperature = 0.9

# After
agent = create_constitutional_test_agent(
    "TestAgent",
    model="gpt-5",
    temperature=0.9  # Note: deprecated in newer agency_swarm
)
```

### Pattern 3: Multiple Agents

```python
# Before
mock_coder = create_mock_agent("AgencyCodeAgent")
mock_planner = create_mock_agent("PlannerAgent")
mock_auditor = create_mock_agent("AuditorAgent")

# After
coder = create_constitutional_test_agent("AgencyCodeAgent")
planner = create_constitutional_test_agent("PlannerAgent")
auditor = create_constitutional_test_agent("AuditorAgent")
```

### Pattern 4: Agent + Context Together

```python
# Before
mock_agent = create_mock_agent("TestAgent")
mock_context = Mock()
mock_context.store_memory = Mock()

# After
from tests.fixtures.constitutional_test_agents import create_test_agent_with_context

agent, context = create_test_agent_with_context("TestAgent")
context.store_memory("agent:created", {"name": agent.name}, tags=["test"])
```

### Pattern 5: Pytest Fixtures

```python
# Before
@pytest.fixture
def test_agent():
    return create_mock_agent("TestAgent")

# After
@pytest.fixture
def test_agent():
    from tests.fixtures.constitutional_test_agents import create_constitutional_test_agent
    return create_constitutional_test_agent("TestAgent")

# Or use built-in fixture
def test_something(constitutional_test_agent):
    agent = constitutional_test_agent("TestAgent")
    assert isinstance(agent, Agent)
```

---

## Constitutional Compliance Checklist

When migrating tests, verify:

- ✅ **Article I**: Complete context - real objects, not partial mocks
- ✅ **Article II**: Real behavior - actual functionality verified
- ✅ **Article III**: Automated enforcement - tests can run in CI
- ✅ **Article IV**: Learning support - context has memory
- ✅ **Article V**: Spec-driven - follows formal specification

---

## Performance Comparison

| Approach | Initialization Time | Memory Usage | Constitutional |
|----------|-------------------|--------------|----------------|
| `create_mock_agent()` | ~5ms | Low | ❌ Violates Article II |
| `create_constitutional_test_agent()` | ~80ms | Medium | ✅ Compliant |
| `create_test_agent_context()` | ~30ms | Low | ✅ Compliant |
| **Combined** | **~110ms** | **Medium** | **✅ Compliant** |

**Verdict**: Slightly slower (~100ms vs 5ms), but **constitutionally required** for main branch.

---

## Files Requiring Migration

Total violations: **217 usages** across test suite.

Major files:
- `tests/test_handoffs_minimal.py` - 5 usages
- `tests/test_orchestrator_system.py` - Multiple usages
- `tests/test_constitutional_validator.py` - 1 usage
- Many others across `tests/` directory

**Search command**:
```bash
# Find all create_mock_agent usages
grep -r "create_mock_agent" tests/

# Count total violations
grep -r "create_mock_agent" tests/ | wc -l
```

---

## Testing Your Migration

After migrating, verify constitutional compliance:

```bash
# Run migrated tests
uv run pytest tests/your_test_file.py -v

# Verify no mock usage
grep -n "Mock\|MagicMock" tests/your_test_file.py

# Check performance
uv run pytest tests/your_test_file.py --durations=10
```

**Success criteria**:
- ✅ All tests pass with real agents
- ✅ No `Mock` or `MagicMock` imports
- ✅ Test duration < 5s (acceptable for real agents)

---

## Common Issues

### Issue 1: "Agent initialization too slow"

**Solution**: Tests with real agents are slightly slower (~100ms vs 5ms). This is **acceptable** for constitutional compliance.

```python
# If really needed, cache agent creation
@pytest.fixture(scope="module")  # Reuse across test module
def shared_agent():
    return create_constitutional_test_agent("SharedAgent")
```

### Issue 2: "Tests fail with real agents"

**Solution**: Good! Real agents expose real bugs that mocks hide.

```python
# Before: Mock hides the bug
mock_agent.some_method = Mock(return_value="fake")

# After: Real agent exposes the issue
agent = create_constitutional_test_agent("TestAgent")
# If this fails, fix the real code, not the test
```

### Issue 3: "Need to verify tool calls"

**Solution**: Real agents have real tools. Verify actual behavior.

```python
# Before: Mock verification
mock_agent.tools = [MockTool]
assert mock_agent.tools[0].called

# After: Real verification
agent = create_constitutional_test_agent("TestAgent", tools=[RealTool])
# Verify real tool behavior, not mock calls
```

---

## Benefits of Migration

1. **Constitutional Compliance**: Satisfies Article II (no mocks in main)
2. **Real Bug Detection**: Catches issues mocks hide
3. **Integration Testing**: Tests actual agent behavior
4. **Future-Proof**: Works with real Agent API changes
5. **Learning Support**: Context enables Article IV compliance

---

## Getting Help

**Documentation**:
- `tests/fixtures/constitutional_test_agents.py` - Implementation
- `tests/fixtures/test_constitutional_test_agents.py` - Test examples
- `constitution.md` - Article II requirements

**Examples**:
- See `TestUsageExamples` class in test file
- Check existing migrated tests (once migration starts)

**Questions**: Consult constitution.md Article II for "Mocks ≠ Green" amendment.

---

## Summary

**Old Way (Violates Constitution)**:
```python
mock_agent = create_mock_agent("TestAgent")  # ❌ Article II violation
```

**New Way (Constitutional Compliance)**:
```python
agent = create_constitutional_test_agent("TestAgent")  # ✅ Article II compliant
```

**Impact**: 217 violations → 0 violations (after full migration)

**Timeline**: Migrate incrementally, prioritize high-value test files first.

---

*Last Updated*: 2025-10-04
*Constitutional Authority*: Article II, Section 2.2 (Mocks ≠ Green Amendment)
