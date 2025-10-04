# Property-Based Testing Guide for Agency OS

## Table of Contents
1. [What is Property-Based Testing?](#what-is-property-based-testing)
2. [Why Property-Based Testing?](#why-property-based-testing)
3. [Quick Start](#quick-start)
4. [Writing Property Tests](#writing-property-tests)
5. [Custom Strategies](#custom-strategies)
6. [Stateful Testing](#stateful-testing)
7. [Debugging Shrinking](#debugging-shrinking)
8. [Best Practices](#best-practices)
9. [Integration with Existing Tests](#integration-with-existing-tests)

---

## What is Property-Based Testing?

Property-based testing is a testing methodology that **automatically generates thousands of test cases** based on properties/invariants rather than specific examples.

### Traditional Testing (Example-Based)
```python
def test_sort():
    assert sorted([3, 1, 2]) == [1, 2, 3]
    assert sorted([]) == []
    assert sorted([1]) == [1]
    # 3 test cases
```

### Property-Based Testing
```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_properties(lst):
    result = sorted(lst)

    # Properties that ALWAYS hold:
    assert len(result) == len(lst)  # Length preserved
    assert all(result[i] <= result[i+1] for i in range(len(result)-1))  # Sorted
    assert set(result) == set(lst)  # Elements preserved
    # Hypothesis generates 100-1000 test cases automatically!
```

**Key Difference**: Instead of writing specific examples, you define **properties that should always be true**, and Hypothesis generates diverse test cases automatically.

---

## Why Property-Based Testing?

### 1. **Automatic Edge Case Discovery**
Hypothesis finds edge cases you wouldn't think of:
- Empty lists
- Single elements
- Duplicates
- Negative numbers
- Maximum/minimum integers
- Special characters in strings
- Nested structures

### 2. **Shrinking - Minimal Failing Examples**
When a test fails, Hypothesis **automatically shrinks** the input to the **simplest case** that still fails.

Example:
```
Initial failure: [1, -5, 0, 999, -1000, 42, 0, 0, 0, 17]
After shrinking: [0, 0]  # The minimal case that reproduces the bug
```

### 3. **Exhaustive Coverage**
One property test can replace hundreds of example-based tests:
- Traditional: 10 examples = 10 test cases
- Property-based: 1 property = 1000 test cases (automatically)

### 4. **Constitutional Compliance**
Property-based testing aligns with Agency's Constitutional Articles:
- **Article I**: Complete context - tests all scenarios
- **Article II**: 100% verification - catches edge cases
- **Article V**: Spec-driven - properties define specifications

---

## Quick Start

### Running Property Tests

```bash
# Run all property tests (default: 100 examples per test)
./scripts/run_property_tests.sh

# Fast mode (20 examples - quick validation)
./scripts/run_property_tests.sh --fast

# Extensive mode (1000 examples - thorough validation)
./scripts/run_property_tests.sh --extensive

# Verbose output with statistics
./scripts/run_property_tests.sh --verbose
```

### Running Specific Tests

```bash
# Run only Result pattern tests
uv run pytest tests/property/test_property_based.py::TestResultPatternProperties -v

# Run with Hypothesis statistics
uv run pytest tests/property/ --hypothesis-show-statistics

# Run with specific Hypothesis seed (reproducibility)
uv run pytest tests/property/ --hypothesis-seed=12345
```

---

## Writing Property Tests

### Basic Property Test

```python
from hypothesis import given, strategies as st

@given(st.integers())
def test_double_is_even(x):
    """PROPERTY: Doubling any integer produces an even number."""
    result = x * 2
    assert result % 2 == 0
```

### Using Agency Custom Strategies

```python
from hypothesis import given
from tools.property_testing import result_strategy, json_value_strategy

@given(result_strategy(st.integers()))
def test_result_unwrap_or_never_fails(result):
    """PROPERTY: unwrap_or() never raises exception."""
    default = 42
    value = result.unwrap_or(default)
    # Should always succeed
    assert value is not None or value == 0
```

### Multiple Inputs

```python
from hypothesis import given, strategies as st

@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    """PROPERTY: Addition is commutative."""
    assert a + b == b + a
```

### Constraints with `assume()`

```python
from hypothesis import given, assume, strategies as st

@given(st.integers(), st.integers())
def test_division_properties(a, b):
    """PROPERTY: Division works correctly for non-zero divisors."""
    assume(b != 0)  # Filter out invalid inputs

    result = a / b
    assert result * b == a  # (Within floating point precision)
```

---

## Custom Strategies

Agency provides custom strategies for our type system in `tools/property_testing.py`.

### Available Strategies

#### 1. `result_strategy(value_strategy, error_strategy)`
Generates `Result<T, E>` instances.

```python
from tools.property_testing import result_strategy
from hypothesis import given, strategies as st

# Result with integer values
@given(result_strategy(st.integers()))
def test_result_with_ints(result):
    assert result.is_ok() or result.is_err()

# Result with complex values
@given(result_strategy(st.lists(st.text())))
def test_result_with_lists(result):
    if result.is_ok():
        assert isinstance(result.unwrap(), list)
```

#### 2. `json_value_strategy(max_leaves)`
Generates valid `JSONValue` instances.

```python
from tools.property_testing import json_value_strategy
from hypothesis import given
import json

@given(json_value_strategy())
def test_json_serialization(value):
    """PROPERTY: All JSONValues are JSON-serializable."""
    serialized = json.dumps(value)
    deserialized = json.loads(serialized)
    assert deserialized == value
```

#### 3. `memory_record_strategy()`
Generates memory records for VectorStore testing.

```python
from tools.property_testing import memory_record_strategy
from hypothesis import given

@given(memory_record_strategy())
def test_memory_structure(record):
    """PROPERTY: Memory records have required fields."""
    assert "key" in record
    assert "content" in record
    assert "tags" in record
```

### Creating Custom Strategies

```python
from hypothesis import strategies as st

@st.composite
def agent_config_strategy(draw):
    """Generate valid agent configurations."""
    return {
        "agent_id": draw(st.text(min_size=1, max_size=50)),
        "model": draw(st.sampled_from(["gpt-4", "gpt-3.5-turbo"])),
        "temperature": draw(st.floats(min_value=0.0, max_value=2.0)),
        "max_tokens": draw(st.integers(min_value=1, max_value=4000)),
    }

@given(agent_config_strategy())
def test_agent_initialization(config):
    agent = Agent(**config)
    assert agent.agent_id == config["agent_id"]
```

---

## Stateful Testing

Stateful testing validates systems that maintain state across operations. Hypothesis executes **random sequences** of operations and checks invariants.

### Example: VectorStore State Machine

```python
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
from hypothesis import strategies as st

class VectorStoreStateMachine(RuleBasedStateMachine):
    """Test VectorStore with random operation sequences."""

    def __init__(self):
        super().__init__()
        self.store = VectorStore()
        self.added_keys = set()

    @rule(key=st.text(min_size=1), content=st.text())
    def add_memory(self, key, content):
        """Add operation."""
        record = {"key": key, "content": content, "tags": []}
        self.store.add_memory(key, record)
        self.added_keys.add(key)

    @rule(key=st.text(min_size=1))
    def remove_memory(self, key):
        """Remove operation."""
        self.store.remove_memory(key)
        self.added_keys.discard(key)

    @invariant()
    def stats_are_valid(self):
        """Invariant: Stats are always valid."""
        stats = self.store.get_stats()
        assert stats["total_memories"] >= 0
```

### Running State Machines

```python
from hypothesis.stateful import run_state_machine_as_test

def test_vector_store_stateful():
    run_state_machine_as_test(VectorStoreStateMachine)
```

Hypothesis will:
1. Generate random operation sequences
2. Execute them
3. Check invariants after each step
4. Shrink to minimal failing sequence if invariants violated

---

## Debugging Shrinking

When a property test fails, Hypothesis automatically **shrinks** the input to find the **minimal failing case**.

### Example Shrinking Process

```
Initial failure:
  lst = [1, -5, 0, 999, -1000, 42, 0, 0, 0, 17]

Shrinking...
  lst = [1, -5, 0, 999]       # Still fails
  lst = [1, -5]                # Still fails
  lst = [-5, 0]                # Still fails
  lst = [0, 0]                 # Still fails

Minimal failing case:
  lst = [0, 0]
```

### Reading Shrinking Output

```
Falsifying example:
test_my_function(
    x=0,
    y=1,
)
```

This is the **simplest input** that causes failure. Fix the bug for this case, and it should fix all other cases.

### Reproducing Failures

Hypothesis caches failing examples in `.hypothesis/`:

```bash
# Reproduce failure from cache
uv run pytest tests/property/test_my_test.py

# Reproduce with specific seed
uv run pytest tests/property/ --hypothesis-seed=12345
```

### Debugging Tips

1. **Use `note()` for debugging**:
   ```python
   from hypothesis import note

   @given(st.integers())
   def test_something(x):
       note(f"Testing with x={x}")
       # ... test code
   ```

2. **Add `@example()` for known cases**:
   ```python
   from hypothesis import given, example

   @given(st.integers())
   @example(0)  # Always test with 0
   @example(-1)  # Always test with -1
   def test_something(x):
       # ... test code
   ```

3. **Use debug profile**:
   ```bash
   HYPOTHESIS_PROFILE=debug uv run pytest tests/property/
   ```

---

## Best Practices

### 1. **Write Clear Properties**

Good:
```python
@given(st.lists(st.integers()))
def test_sort_is_idempotent(lst):
    """PROPERTY: Sorting twice equals sorting once."""
    assert sorted(sorted(lst)) == sorted(lst)
```

Bad:
```python
@given(st.lists(st.integers()))
def test_sort(lst):
    """Test sorting."""  # Unclear what property is being tested
    result = sorted(lst)
    assert result  # Weak assertion
```

### 2. **Test Invariants, Not Implementation**

Good:
```python
@given(result_strategy())
def test_result_mutual_exclusivity(result):
    """PROPERTY: Result is EITHER Ok OR Err, never both."""
    assert result.is_ok() != result.is_err()
```

Bad:
```python
@given(result_strategy())
def test_result_has_underscore_value_field(result):
    """PROPERTY: Result has _value field."""  # Testing implementation
    assert hasattr(result, '_value')
```

### 3. **Use Appropriate Strategy Sizes**

```python
# Fast tests - small inputs
@given(st.lists(st.integers(), max_size=10))
def test_fast_property(lst):
    # Quick validation
    pass

# Thorough tests - larger inputs
@given(st.lists(st.integers(), max_size=1000))
def test_thorough_property(lst):
    # Comprehensive validation
    pass
```

### 4. **Combine with Example-Based Tests**

Use both approaches:
- **Property tests**: General invariants
- **Example tests**: Specific known cases

```python
# Property test - general
@given(st.integers())
def test_double_is_even(x):
    assert (x * 2) % 2 == 0

# Example test - specific regression
def test_double_zero():
    """Regression test for bug #123."""
    assert double(0) == 0
```

### 5. **Document Properties Clearly**

```python
@given(result_strategy())
def test_result_unwrap_or_safety(result):
    """
    PROPERTY: unwrap_or() never raises exception.

    This is a critical safety property of the Result pattern.
    Unlike unwrap(), unwrap_or() provides a safe way to extract
    values without risking RuntimeError.
    """
    default = 42
    value = result.unwrap_or(default)
    # Test passes if no exception raised
```

---

## Integration with Existing Tests

### Directory Structure

```
tests/
├── property/                    # Property-based tests
│   ├── __init__.py
│   ├── test_property_based.py   # Core type properties
│   └── test_critical_properties.py  # Critical function properties
├── unit/                        # Traditional unit tests
├── integration/                 # Integration tests
└── trinity_protocol/            # Trinity protocol tests
```

### Running Both Test Types

```bash
# Run all tests (unit + integration + property)
python run_tests.py --run-all

# Run only property tests
./scripts/run_property_tests.sh

# Run only unit tests
python run_tests.py
```

### CI Integration

Add to `.github/workflows/ci.yml`:

```yaml
- name: Property-Based Tests
  run: |
    HYPOTHESIS_PROFILE=ci ./scripts/run_property_tests.sh
```

### Pre-Commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Run fast property tests before commit
HYPOTHESIS_PROFILE=fast ./scripts/run_property_tests.sh
```

---

## Hypothesis Profiles

Configure test thoroughness via profiles (see `.hypothesis/settings.py`):

### Available Profiles

| Profile | Examples | Speed | Use Case |
|---------|----------|-------|----------|
| `fast` | 20 | ~5s | Quick validation during development |
| `default` | 100 | ~30s | Standard testing |
| `extensive` | 1000 | ~5min | Pre-commit, thorough validation |
| `ci` | 200 | ~1min | CI/CD pipelines |
| `debug` | 10 | Variable | Debugging failures |

### Usage

```bash
# Set profile via environment variable
HYPOTHESIS_PROFILE=extensive ./scripts/run_property_tests.sh

# Or use script flags
./scripts/run_property_tests.sh --extensive
```

---

## Real-World Examples

### Example 1: Result Pattern Monad Laws

```python
from hypothesis import given, strategies as st
from tools.property_testing import result_strategy

@given(result_strategy(st.integers()))
def test_result_left_identity(value):
    """PROPERTY: Result satisfies left identity monad law."""
    # return a >>= f === f a
    def f(x):
        return Ok(x * 2)

    result1 = Ok(value).and_then(f)
    result2 = f(value)

    assert result1.unwrap() == result2.unwrap()

@given(result_strategy(st.integers()))
def test_result_associativity(m):
    """PROPERTY: Result satisfies associativity monad law."""
    # (m >>= f) >>= g === m >>= (\\x -> f x >>= g)
    def f(x):
        return Ok(x + 1)

    def g(x):
        return Ok(x * 2)

    result1 = m.and_then(f).and_then(g)
    result2 = m.and_then(lambda x: f(x).and_then(g))

    if m.is_ok():
        assert result1.unwrap() == result2.unwrap()
```

### Example 2: RetryController Behavior

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0, max_value=10))
def test_retry_eventually_succeeds(failure_count):
    """PROPERTY: Retry succeeds if function recovers."""
    attempts = [0]

    def flaky_function():
        attempts[0] += 1
        if attempts[0] <= failure_count:
            raise ValueError("Not ready")
        return "success"

    strategy = ExponentialBackoffStrategy(
        max_attempts=failure_count + 2,
        initial_delay=0.01,
    )
    controller = RetryController(strategy=strategy)

    result = controller.execute_with_retry(flaky_function)
    assert result == "success"
```

### Example 3: JSON Roundtrip Property

```python
from hypothesis import given
from tools.property_testing import json_value_strategy
import json

@given(json_value_strategy())
def test_json_roundtrip_preserves_value(value):
    """PROPERTY: JSON serialization roundtrip preserves value."""
    serialized = json.dumps(value)
    deserialized = json.loads(serialized)
    assert deserialized == value

@given(json_value_strategy())
def test_json_is_deterministic(value):
    """PROPERTY: JSON serialization is deterministic."""
    result1 = json.dumps(value, sort_keys=True)
    result2 = json.dumps(value, sort_keys=True)
    assert result1 == result2
```

---

## Common Patterns

### Testing Idempotence

```python
@given(st.lists(st.integers()))
def test_sort_idempotent(lst):
    """PROPERTY: Sorting twice equals sorting once."""
    assert sorted(sorted(lst)) == sorted(lst)
```

### Testing Reversibility

```python
@given(st.text())
def test_encode_decode_reversible(text):
    """PROPERTY: Encode then decode returns original."""
    encoded = encode(text)
    decoded = decode(encoded)
    assert decoded == text
```

### Testing Commutativity

```python
@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    """PROPERTY: a + b == b + a."""
    assert a + b == b + a
```

### Testing Associativity

```python
@given(st.integers(), st.integers(), st.integers())
def test_addition_associative(a, b, c):
    """PROPERTY: (a + b) + c == a + (b + c)."""
    assert (a + b) + c == a + (b + c)
```

### Testing Boundary Preservation

```python
@given(st.lists(st.integers()))
def test_filter_preserves_subset(lst):
    """PROPERTY: Filtering creates subset."""
    filtered = [x for x in lst if x > 0]
    assert set(filtered).issubset(set(lst))
```

---

## Troubleshooting

### Problem: Tests are too slow

**Solution**: Use smaller strategies or fast profile
```python
# Slow
@given(st.lists(st.integers(), max_size=10000))

# Fast
@given(st.lists(st.integers(), max_size=100))
```

### Problem: Too many edge cases failing

**Solution**: Use `assume()` to filter invalid inputs
```python
@given(st.integers(), st.integers())
def test_division(a, b):
    assume(b != 0)  # Skip division by zero
    assert (a / b) * b == a
```

### Problem: Flaky tests due to randomness

**Solution**: Use `--hypothesis-seed` for reproducibility
```bash
uv run pytest tests/property/ --hypothesis-seed=12345
```

### Problem: Can't understand shrunk output

**Solution**: Add `note()` calls for debugging
```python
from hypothesis import note

@given(st.lists(st.integers()))
def test_something(lst):
    note(f"Testing with list length: {len(lst)}")
    note(f"First element: {lst[0] if lst else 'empty'}")
    # ... test code
```

---

## Resources

### Documentation
- [Hypothesis Official Docs](https://hypothesis.readthedocs.io/)
- [Property-Based Testing Introduction](https://increment.com/testing/in-praise-of-property-based-testing/)
- [John Hughes - QuickCheck](https://www.cs.tufts.edu/~nr/cs257/archive/john-hughes/quick.pdf)

### Agency Resources
- `tools/property_testing.py` - Custom strategies and helpers
- `tests/property/` - Property test examples
- `.hypothesis/settings.py` - Profile configurations

### Next Steps
1. Run existing property tests: `./scripts/run_property_tests.sh`
2. Review examples in `tests/property/test_property_based.py`
3. Write properties for your new features
4. Integrate into CI/CD pipeline

---

## Summary

Property-based testing is a powerful complement to traditional testing:

| Aspect | Example-Based | Property-Based |
|--------|---------------|----------------|
| **Coverage** | 3-10 cases | 100-1000 cases |
| **Edge cases** | Manual | Automatic |
| **Shrinking** | N/A | Minimal failing case |
| **Maintenance** | High (many examples) | Low (few properties) |
| **Speed** | Fast | Moderate |
| **Best for** | Specific regressions | General invariants |

**Use both approaches** for comprehensive testing:
- Property tests for invariants and edge case discovery
- Example tests for known regressions and specific scenarios

**Constitutional Compliance**: Property-based testing helps achieve Agency's constitutional goals of complete context (Article I) and 100% verification (Article II) by automatically testing thousands of scenarios.
