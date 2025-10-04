# Mutation Testing Guide

## What is Mutation Testing?

**Mutation testing** is a technique to verify the effectiveness of your test suite by deliberately introducing bugs (mutations) into your code and checking if your tests catch them.

### The Core Concept

```python
# Original code
def add(a, b):
    return a + b

# Mutation #1: Change operator (+ to -)
def add(a, b):
    return a - b  # If tests still pass, they're broken!

# Mutation #2: Change to constant
def add(a, b):
    return 0  # Tests should definitely catch this

# Mutation #3: Return None
def add(a, b):
    return None  # Tests must fail here
```

**If tests pass with mutated code → Tests are inadequate**
**If tests fail with mutated code → Tests are working correctly**

---

## Why Mutation Testing is Critical

### Mars Rover Standard

NASA's Mars Rover missions require **mutation testing** to ensure test suites are actually effective. A test suite that passes with buggy code is worse than useless—it gives false confidence.

### Constitutional Compliance

**Article II: 100% Verification and Stability**
- Tests must verify REAL functionality, not simulated behavior
- Mutation testing proves tests catch bugs
- Required for Mars Rover standard compliance

### The Problem Mutation Testing Solves

```python
# BAD TEST - Doesn't actually verify behavior
def test_calculate_total():
    result = calculate_total([1, 2, 3])
    assert result  # Just checks truthy, not value!

# GOOD TEST - Mutation testing would catch this
def test_calculate_total():
    result = calculate_total([1, 2, 3])
    assert result == 6  # Specific value check
```

Mutation testing would reveal the first test is inadequate by changing the implementation and seeing the test still pass.

---

## How Mutation Testing Works

### 1. Generate Mutations

The framework analyzes your code using AST (Abstract Syntax Tree) and generates mutations:

**Arithmetic Operators:**
- `+` → `-`, `*`
- `-` → `+`, `/`
- `*` → `/`, `+`
- `/` → `*`, `//`

**Comparison Operators:**
- `==` → `!=`, `<`
- `!=` → `==`, `>`
- `<` → `>`, `<=`
- `>` → `<`, `>=`

**Boolean Operators:**
- `and` → `or`
- `or` → `and`
- `not x` → `x` (remove negation)

**Constants:**
- `True` → `False`
- `False` → `True`
- `42` → `0`
- `"hello"` → `""`

**Return Statements:**
- `return value` → `return None`

### 2. Apply Each Mutation

For each mutation:
1. Backup original file
2. Apply mutation
3. Run test suite
4. Restore original file

### 3. Calculate Mutation Score

```
Mutation Score = (Mutations Caught) / (Total Mutations)
```

**Target: 95%+ (Mars Rover Standard)**

- **100%**: Perfect - all mutations caught
- **95%+**: Excellent - Mars Rover standard
- **80-95%**: Good - strong coverage
- **60-80%**: Fair - needs improvement
- **<60%**: Poor - inadequate test suite

---

## Using the Mutation Testing Framework

### Quick Start

```bash
# Run mutation testing on critical modules
./scripts/run_mutation_tests.sh

# Quick mode (test only 2 modules)
./scripts/run_mutation_tests.sh --quick

# Full mode (all critical modules)
./scripts/run_mutation_tests.sh --full

# Test specific file
./scripts/run_mutation_tests.sh --file shared/agent_context.py
```

### Programmatic Usage

```python
from tools.mutation_testing import (
    MutationConfig,
    MutationTester,
)

# Configure mutation testing
config = MutationConfig(
    target_files=["my_module.py"],
    test_command="pytest tests/test_my_module.py -v",
    mutation_types=["arithmetic", "comparison", "boolean"],
    timeout_seconds=60,
    parallel=False
)

# Run mutation testing
tester = MutationTester(config)
result = tester.run()

if result.is_ok():
    score = result.unwrap()
    print(f"Mutation Score: {score.mutation_score:.2%}")

    # Generate report
    report = tester.generate_report(score)
    print(report)
else:
    print(f"Error: {result.unwrap_err()}")
```

### Configuration Options

```python
MutationConfig(
    target_files: List[str]       # Files to mutate
    test_command: str             # Command to run tests
    mutation_types: List[str]     # Which mutation types to apply
    timeout_seconds: int = 60     # Test execution timeout
    parallel: bool = True         # Run mutations in parallel
)
```

**Available Mutation Types:**
- `"arithmetic"` - Arithmetic operators (+, -, *, /, %)
- `"comparison"` - Comparison operators (==, !=, <, >, <=, >=)
- `"boolean"` - Boolean operators (and, or, not)
- `"constant"` - Constant values (True, False, numbers, strings)
- `"return"` - Return statements

---

## Interpreting Results

### Mutation Report

```
================================================================================
MUTATION TESTING REPORT
================================================================================

Total Mutations: 45
Mutations Caught: 43
Mutations Survived: 2
Mutation Score: 95.56%

✅ EXCELLENT - Mars Rover standard achieved (95%+)

================================================================================
SURVIVING MUTATIONS (Tests failed to catch these bugs)
================================================================================

Mutation ID: arith_0012
File: shared/agent_context.py:127
Original: count + 1
Mutated:  count - 1
Execution Time: 2.34s

Mutation ID: comp_0005
File: shared/memory.py:89
Original: if score > threshold:
Mutated:  if score >= threshold:
Execution Time: 1.87s

================================================================================
```

### What Surviving Mutations Mean

**Each surviving mutation represents a bug your tests didn't catch.**

Example:
```python
# Original code
def is_positive(x):
    return x > 0

# Mutation: x > 0 → x >= 0
def is_positive(x):
    return x >= 0  # Different behavior at x=0!

# If tests pass with mutation, you're missing:
def test_is_positive_at_zero():
    assert not is_positive(0)  # This test would catch it
```

### Fixing Surviving Mutations

1. **Analyze the mutation**: What behavior change did it introduce?
2. **Add specific test**: Write test that would fail with the mutation
3. **Re-run mutation testing**: Verify new test catches the mutation

---

## Best Practices

### 1. Start with Critical Modules

Don't try to mutation test your entire codebase at once. Start with:
- Core business logic
- Security-critical code
- Frequently-changed modules
- Bug-prone areas

### 2. Target 95%+ Mutation Score

The Mars Rover standard is 95%+. Anything less indicates inadequate testing.

### 3. Use Mutation Testing in CI/CD

```bash
# In your CI pipeline
./scripts/run_mutation_tests.sh --quick
if [ $? -ne 0 ]; then
    echo "Mutation testing failed - test suite inadequate"
    exit 1
fi
```

### 4. Focus on Surviving Mutations

Don't celebrate a 95% score if you have 5% surviving mutations. **Each surviving mutation is a real bug your tests don't catch.**

### 5. Combine with Coverage Tools

```bash
# Get coverage
pytest --cov=my_module --cov-report=term-missing

# Then run mutation testing
./scripts/run_mutation_tests.sh --file my_module.py
```

High coverage + high mutation score = truly tested code.

---

## Common Pitfalls

### Pitfall #1: Testing Implementation, Not Behavior

```python
# BAD - Tests implementation details
def test_calculate():
    calculator = Calculator()
    calculator._internal_state = 5  # Accessing internals
    assert calculator._internal_state == 5

# GOOD - Tests behavior
def test_calculate():
    result = Calculator().add(2, 3)
    assert result == 5
```

Mutation testing would reveal the first test doesn't verify actual functionality.

### Pitfall #2: Weak Assertions

```python
# BAD - Weak assertion
def test_process_data():
    result = process_data(input)
    assert result  # Just checks truthy

# GOOD - Specific assertion
def test_process_data():
    result = process_data({"key": "value"})
    assert result == {"processed": "value", "status": "success"}
```

### Pitfall #3: Not Testing Edge Cases

```python
# INCOMPLETE
def test_divide():
    assert divide(10, 2) == 5

# COMPLETE - Catches division by zero mutations
def test_divide():
    assert divide(10, 2) == 5
    assert divide(10, 3) == 3.333...
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)
```

---

## Performance Considerations

### Mutation Testing is Slow

Each mutation requires running your entire test suite. For `N` mutations:
- **Time = N × (test suite execution time)**

### Optimization Strategies

1. **Use `--quick` mode** during development
2. **Test only changed files** in PRs
3. **Run full mutation testing** on main branch only
4. **Enable parallel execution** (use `parallel=True`)
5. **Cache mutation results** for unchanged code

### Example Timing

```
Module: shared/agent_context.py
Total Mutations: 45
Test Suite Time: 2.3s
Total Time: 45 × 2.3s ≈ 104s (1.7 minutes)
```

---

## Integration with Agency OS

### Constitutional Compliance Check

```python
from tools.mutation_testing import MutationTester, MutationConfig

def verify_mars_rover_compliance(module_path: str) -> bool:
    """Verify module meets Mars Rover mutation testing standard."""
    config = MutationConfig(
        target_files=[module_path],
        test_command="pytest tests/ -v",
        mutation_types=["arithmetic", "comparison", "boolean", "constant"],
        timeout_seconds=120
    )

    tester = MutationTester(config)
    result = tester.run()

    if result.is_err():
        return False

    score = result.unwrap()
    return score.mutation_score >= 0.95  # 95%+ required
```

### Pre-Commit Hook

Add to `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: mutation-testing
      name: Mutation Testing
      entry: ./scripts/run_mutation_tests.sh --quick
      language: script
      pass_filenames: false
```

---

## Troubleshooting

### Issue: Mutation testing takes too long

**Solution**: Use `--quick` mode or test specific files
```bash
./scripts/run_mutation_tests.sh --quick
./scripts/run_mutation_tests.sh --file specific_module.py
```

### Issue: Mutations not being generated

**Possible causes**:
- File has syntax errors (can't parse AST)
- No code matching mutation patterns
- File is empty or only has comments

**Check**:
```python
from tools.mutation_testing import ArithmeticMutator

code = """
def add(a, b):
    return a + b
"""

mutator = ArithmeticMutator()
mutations = mutator.generate_mutations(code, "test.py")
print(f"Generated {len(mutations)} mutations")
```

### Issue: Tests timeout during mutation testing

**Solution**: Increase timeout
```python
config = MutationConfig(
    target_files=["slow_module.py"],
    test_command="pytest tests/",
    mutation_types=["arithmetic"],
    timeout_seconds=300  # 5 minutes
)
```

---

## Advanced Usage

### Custom Mutation Types

Extend the framework with custom mutators:

```python
from tools.mutation_testing import BaseMutator, Mutation, MutationType
import ast

class CustomMutator(BaseMutator):
    """Custom mutation logic."""

    def generate_mutations(self, code: str, file_path: str) -> List[Mutation]:
        # Parse code
        tree = ast.parse(code)

        # Generate custom mutations
        mutations = []

        # Your mutation logic here

        return mutations

# Register custom mutator
MutationTester.MUTATOR_REGISTRY["custom"] = CustomMutator
```

### Mutation Testing Specific Functions

```python
# Test only arithmetic in specific function
config = MutationConfig(
    target_files=["module.py"],
    test_command="pytest tests/test_module.py::test_specific_function",
    mutation_types=["arithmetic"]
)
```

---

## References

- **Mars Rover Testing Standards**: NASA JPL Software Engineering Standards
- **Mutation Testing Research**: "Mutation Testing: A Survey" (Jia & Harman, 2011)
- **Agency Constitution**: Article II - 100% Verification and Stability

---

## Summary

**Mutation testing is the ultimate test of test quality.**

- ✅ Verifies tests catch bugs (not just run)
- ✅ Reveals weak assertions and missing edge cases
- ✅ Required for Mars Rover standard compliance
- ✅ Constitutional requirement (Article II)

**Target: 95%+ mutation score**

If your tests don't catch deliberately introduced bugs, they won't catch real bugs either.

---

*"Trust tests that catch mutations, not tests that just pass."*

**Version**: 1.0
**Last Updated**: 2025-10-03
