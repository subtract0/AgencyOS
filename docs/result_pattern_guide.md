# Result Pattern Implementation Guide

## Overview

The Result<T, E> pattern is a functional programming approach to error handling that makes errors explicit and type-safe. Inspired by Rust's Result type, this implementation provides a better alternative to exception-based error handling for control flow.

## Why Use Result Pattern?

### Problems with Traditional Exception Handling

```python
# Traditional approach - errors are implicit
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero")  # Caller must know this can happen
    return a / b

# Usage requires defensive programming
try:
    result = divide(10, 0)
    print(f"Result: {result}")
except ValueError as e:
    print(f"Error: {e}")
```

### Benefits of Result Pattern

```python
from shared.type_definitions.result import Result, Ok, Err

# Result approach - errors are explicit in the type signature
def divide(a: float, b: float) -> Result[float, str]:
    if b == 0:
        return Err("Division by zero")  # Error is part of the return type
    return Ok(a / b)

# Usage is explicit and type-safe
result = divide(10, 0)
if result.is_ok():
    print(f"Result: {result.unwrap()}")
else:
    print(f"Error: {result.unwrap_err()}")
```

**Key Benefits:**
- **Explicit error handling**: Errors are part of the type signature
- **Type safety**: Compiler/IDE can catch unhandled error cases
- **No hidden exceptions**: All possible outcomes are visible
- **Composable**: Easy to chain operations that may fail
- **Performance**: No exception overhead for expected errors

## Basic Usage

### Creating Results

```python
from shared.type_definitions.result import Result, Ok, Err, ok, err

# Create Ok result
success = Ok(42)
success = ok(42)  # Convenience function

# Create Err result
failure = Err("Something went wrong")
failure = err("Something went wrong")  # Convenience function
```

### Checking Results

```python
result = divide(10, 2)

# Check result type
if result.is_ok():
    value = result.unwrap()
    print(f"Success: {value}")
elif result.is_err():
    error = result.unwrap_err()
    print(f"Error: {error}")
```

### Safe Unwrapping

```python
# Safe unwrapping with defaults
value = result.unwrap_or(0)  # Returns 0 if error

# Safe unwrapping with function
value = result.unwrap_or_else(lambda err: len(err))  # Returns error length if error

# Unsafe unwrapping (raises RuntimeError if wrong type)
value = result.unwrap()  # Only use if you're certain it's Ok
error = result.unwrap_err()  # Only use if you're certain it's Err
```

## Advanced Usage

### Mapping Operations

```python
# Transform Ok values
result = Ok(5)
doubled = result.map(lambda x: x * 2)  # Ok(10)

# Transform Err values
result = Err("error")
formatted = result.map_err(lambda e: f"Error: {e}")  # Err("Error: error")

# Chaining maps
result = Ok(5).map(lambda x: x * 2).map(lambda x: x + 1)  # Ok(11)
```

### Chaining Operations with and_then

```python
def safe_parse_int(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"Invalid integer: {s}")

def safe_divide(a: int, b: int) -> Result[float, str]:
    if b == 0:
        return Err("Division by zero")
    return Ok(a / b)

# Chain operations that may fail
result = (safe_parse_int("10")
         .and_then(lambda x: safe_parse_int("2")
                  .and_then(lambda y: safe_divide(x, y))))

# Result is Ok(5.0) if all operations succeed
# Result is Err(...) if any operation fails
```

### Error Recovery with or_else

```python
def primary_operation() -> Result[str, str]:
    return Err("Primary failed")

def fallback_operation(error: str) -> Result[str, str]:
    return Ok(f"Fallback for: {error}")

# Try primary, fallback to secondary
result = primary_operation().or_else(fallback_operation)
# Result is Ok("Fallback for: Primary failed")
```

### Using try_result for Exception Conversion

```python
from shared.type_definitions.result import try_result

# Convert exception-throwing code to Result
def risky_operation():
    return int("not_a_number")  # This will raise ValueError

result = try_result(risky_operation)
# Result is Err("invalid literal for int() with base 10: 'not_a_number'")

# Catch specific exception types
result = try_result(risky_operation, ValueError)
```

## Real-World Example: Enhanced Memory Store

The `EnhancedMemoryStoreResult` class demonstrates how to apply the Result pattern to a complex system:

```python
from agency_memory.enhanced_memory_store_result import EnhancedMemoryStoreResult

store = EnhancedMemoryStoreResult()

# Store operation with explicit error handling
result = store.store_result("key1", "content", ["tag1"])
if result.is_err():
    print(f"Store failed: {result.unwrap_err()}")
    return

# Search operation with explicit error handling
search_result = store.search_result(["tag1"])
match search_result:
    case Ok(memories):
        print(f"Found {len(memories.memories)} memories")
    case Err(error):
        print(f"Search failed: {error}")

# Chaining operations
combined_result = (store.search_result(["tag1"])
                  .and_then(lambda sr: store.semantic_search_result("query")
                           .map(lambda semantic: sr.memories + semantic)))
```

## Best Practices

### 1. Use Result for Expected Errors

```python
# Good: Use Result for business logic errors
def withdraw_money(account: Account, amount: float) -> Result[Account, str]:
    if amount > account.balance:
        return Err("Insufficient funds")
    return Ok(account.with_balance(account.balance - amount))

# Avoid: Don't use Result for programming errors
def get_first_item(items: List[T]) -> Result[T, str]:
    if not items:
        return Err("Empty list")  # This should probably be an assertion
    return Ok(items[0])
```

### 2. Define Error Types

```python
class DatabaseError:
    CONNECTION_FAILED = "connection_failed"
    QUERY_TIMEOUT = "query_timeout"
    INVALID_QUERY = "invalid_query"

def query_database(sql: str) -> Result[List[Row], str]:
    try:
        # Database operation
        return Ok(rows)
    except ConnectionError:
        return Err(DatabaseError.CONNECTION_FAILED)
    except TimeoutError:
        return Err(DatabaseError.QUERY_TIMEOUT)
```

### 3. Provide Legacy Compatibility

```python
class ServiceWithResult:
    def new_method(self, data: str) -> Result[Output, str]:
        # New Result-based method
        pass

    def legacy_method(self, data: str) -> Output:
        # Legacy method that maintains compatibility
        result = self.new_method(data)
        if result.is_err():
            logger.error(f"Operation failed: {result.unwrap_err()}")
            raise RuntimeError(result.unwrap_err())
        return result.unwrap()
```

### 4. Use Type Aliases for Common Patterns

```python
from shared.type_definitions.result import ResultStr, ResultException

# Use type aliases for consistency
def parse_config(path: str) -> ResultStr[Config]:
    pass

def database_operation() -> ResultException[Data]:
    pass
```

### 5. Chain Operations Efficiently

```python
# Good: Chain related operations
result = (validate_input(data)
         .and_then(process_data)
         .and_then(save_to_database)
         .map(format_response))

# Avoid: Nested if statements
input_result = validate_input(data)
if input_result.is_ok():
    process_result = process_data(input_result.unwrap())
    if process_result.is_ok():
        # ... more nesting
```

## Migration Strategy

### Phase 1: Add Result Methods Alongside Legacy Methods

```python
class ExistingService:
    def existing_method(self, data: str) -> str:
        # Keep existing method for compatibility
        result = self.existing_method_result(data)
        return result.unwrap_or("")

    def existing_method_result(self, data: str) -> ResultStr[str]:
        # New Result-based method
        if not data:
            return Err("Data cannot be empty")
        return Ok(data.upper())
```

### Phase 2: Gradually Adopt Result Pattern

```python
# Start using Result pattern in new code
def new_feature(input: Input) -> Result[Output, str]:
    return (validate_input(input)
           .and_then(process_input)
           .map(format_output))
```

### Phase 3: Convert Critical Paths

```python
# Convert error-prone operations to Result pattern
def critical_operation() -> Result[CriticalData, CriticalError]:
    # Replace try/catch with explicit error handling
    pass
```

## Testing Result-Based Code

```python
def test_successful_operation():
    result = divide(10, 2)
    assert result.is_ok()
    assert result.unwrap() == 5.0

def test_error_operation():
    result = divide(10, 0)
    assert result.is_err()
    assert "Division by zero" in result.unwrap_err()

def test_chained_operations():
    result = (Ok(10)
             .and_then(lambda x: Ok(x * 2))
             .and_then(lambda x: Ok(x + 5)))
    assert result.unwrap() == 25

def test_error_propagation():
    result = (Ok(10)
             .and_then(lambda x: Err("Something failed"))
             .and_then(lambda x: Ok(x * 2)))  # This won't execute
    assert result.is_err()
    assert result.unwrap_err() == "Something failed"
```

## Performance Considerations

The Result pattern has minimal performance overhead:

- **No exception overhead**: Normal Result operations don't throw exceptions
- **Zero-cost abstractions**: Most operations compile to simple conditional checks
- **Memory efficient**: Result objects are lightweight containers

```python
# Benchmark comparison
import time

# Exception-based approach
def exception_based():
    try:
        return divide_may_throw(10, 0)
    except ValueError:
        return 0

# Result-based approach
def result_based():
    result = divide_result(10, 0)
    return result.unwrap_or(0)

# Result pattern is typically faster for expected errors
```

## Conclusion

The Result pattern provides a robust foundation for error handling that:

- Makes errors explicit and type-safe
- Improves code reliability and maintainability
- Enables functional composition of operations
- Reduces hidden control flow and unexpected exceptions

By adopting this pattern incrementally, teams can significantly improve their error handling without breaking existing code.