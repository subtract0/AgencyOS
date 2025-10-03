# Common Code Patterns Quick Reference

**Essential patterns used throughout Agency codebase**

## Result<T, E> Pattern (Error Handling)

```python
from shared.type_definitions.result import Result, Ok, Err

def process_data(data: str) -> Result[ProcessedData, str]:
    """Return Ok(data) on success, Err(message) on failure."""
    if not data:
        return Err("Empty data")

    try:
        processed = ProcessedData(data)
        return Ok(processed)
    except ValidationError as e:
        return Err(f"Validation failed: {e}")

# Usage
result = process_data("test")
match result:
    case Ok(data):
        print(f"Success: {data}")
    case Err(error):
        print(f"Error: {error}")
```

## Pydantic Models (Type Safety)

**NEVER use Dict[Any, Any] - ALWAYS use concrete Pydantic models**

```python
from pydantic import BaseModel, Field
from shared.type_definitions.json import JSONValue

class DataModel(BaseModel):
    """Always typed, never Dict[Any, Any]."""
    name: str = Field(..., description="Required name")
    count: int = Field(default=0, ge=0)
    metadata: JSONValue = Field(default_factory=dict)  # Use JSONValue for dynamic data

    class Config:
        frozen = True  # Immutable after creation
```

## Agent Context (Memory API)

```python
from shared.agent_context import AgentContext

# Store memory
context.store_memory(
    key="pattern_name",
    content="pattern description",
    tags=["agent", "pattern", "success"]
)

# Search memories
results = context.search_memories(
    tags=["pattern"],
    include_session=True  # Include current session
)

# Access cost tracker (if enabled)
if context.cost_tracker:
    context.cost_tracker.log_usage(tokens=100, model="gpt-5", cost_usd=0.001)
```

## Constitutional Validation

```python
from shared.constitutional_validator import validate_constitutional_compliance

# Every agent action MUST validate
@validate_constitutional_compliance
def agent_action(context, task):
    """Decorator ensures Articles I-V compliance."""
    # Implementation
    pass
```

## Model Selection (Per-Agent Policy)

```python
from shared.model_policy import agent_model

# Get model for specific agent (respects env overrides)
model = agent_model("planner")  # Returns PLANNER_MODEL or default
model = agent_model("coder")    # Returns CODER_MODEL or default
model = agent_model("summary")  # Returns gpt-5-mini (cost-optimized)
```

## Test-Driven Development (TDD)

```python
# ALWAYS write test FIRST, then implementation

# tests/test_feature.py
def test_feature_success():
    """Test successful feature execution."""
    # Arrange
    input_data = create_test_data()

    # Act
    result = process_feature(input_data)

    # Assert
    assert isinstance(result, Ok)
    assert result.value.count == 5
```

## Function Size Limit

**Constitutional Requirement: <50 lines per function**

```python
# ❌ BAD: 64 lines
def long_function():
    # ... 64 lines of code ...
    pass

# ✅ GOOD: Extract sub-functions
def main_function():
    """Orchestrate sub-operations (<50 lines)."""
    data = prepare_data()  # <50 lines
    result = process_data(data)  # <50 lines
    return finalize_result(result)  # <50 lines
```

## Timeout Handling (Article I Compliance)

```python
from shared.timeout_wrapper import with_constitutional_timeout

@with_constitutional_timeout(base_timeout=120000)  # 2 minutes
def operation():
    """Retries with 2x, 3x, 5x, 10x multipliers on timeout."""
    # Implementation
    pass
```

## TodoWrite Usage

```python
# For multi-step tasks (3+ steps)
todos = [
    {"content": "Step 1", "status": "in_progress", "activeForm": "Doing step 1"},
    {"content": "Step 2", "status": "pending", "activeForm": "Doing step 2"},
    {"content": "Step 3", "status": "pending", "activeForm": "Doing step 3"}
]

# MUST have exactly ONE in_progress at a time
# Mark completed IMMEDIATELY after finishing
```

---

## Anti-Patterns (NEVER DO)

### ❌ Dict[Any, Any]
```python
data: Dict[Any, Any] = {}  # FORBIDDEN
```

### ❌ Try/Catch for Control Flow
```python
try:
    result = operation()
except Exception:
    return None  # BAD: Use Result pattern
```

### ❌ Functions >50 Lines
```python
def huge_function():
    # ... 100 lines ...  # VIOLATION: Article VIII
    pass
```

### ❌ Bare `any` Type
```python
def process(data: any):  # FORBIDDEN: Use explicit types
    pass
```

---

**Constitutional Requirement**: All code MUST follow these patterns
