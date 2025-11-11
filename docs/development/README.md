# Development Documentation

Comprehensive guides for AgencyOS development, contribution, and best practices.

---

## Quick Start for Contributors

### Setup (5 minutes)

```bash
# Clone repository
git clone https://github.com/subtract0/AgencyOS.git
cd AgencyOS

# Create environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Configure API key
export OPENAI_API_KEY=your_key_here

# Verify setup
python run_tests.py --run-all
```

**Expected**: 5,822 tests passing, 164 skipped, 100% pass rate

---

## Development Workflow

### Branch Strategy

```bash
# Create feature branch
git checkout -b feat/your-feature-name

# Make changes and test
python run_tests.py --run-all

# Commit with descriptive message
git add .
git commit -m "feat: Add feature description"

# Push to remote
git push -u origin feat/your-feature-name

# Create pull request
gh pr create --title "Feature: Your feature" --body "Description..."
```

### Commit Message Convention

Follow conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

---

## Constitutional Requirements

All contributions MUST comply with the 7-Article Constitution:

### Article I: Complete Context Before Action
- Always read full context before making changes
- Retry on timeouts (never proceed with incomplete data)
- Fix ALL failing tests before new features

### Article II: 100% Verification and Stability
- Main branch must maintain 100% test pass rate
- No merge without completely green tests
- Quality gates are absolute (no exceptions)

### Article III: Automated Local Enforcement
- Pre-commit hooks validate changes automatically
- No manual overrides for quality standards
- Local enforcement is sufficient (CI/CD optional)

### Article IV: Continuous Learning and Improvement
- Query VectorStore for similar past solutions before implementing
- Store successful patterns after completion
- USE_ENHANCED_MEMORY=true is mandatory (constitutional requirement)

### Article V: Spec-Driven Development
- Complex features require spec.md → plan.md workflow
- Simple tasks can skip spec-kit but must verify compliance
- All implementation traces to specification

### Article VI: Red-Green-Refactor TDD Workflow
- Write tests FIRST (they must fail initially - RED)
- Implement code SECOND (iterate until 100% pass - GREEN)
- Refactor THIRD (improve while maintaining green)
- NO "pragmatic shortcuts" that skip RED phase

### Article VII: Value-First Testing Philosophy
- Test NECESSARY functionality (not trivial behavior)
- Focus on business value scenarios
- Each test should answer: "What business value does this protect?"

---

## Code Quality Standards

### Type Safety

**❌ NEVER:**
```python
# Bad: Dict[Any, Any]
config: Dict[Any, Any] = {"key": value}

# Bad: Bare any
def process(data: any) -> any:
    pass
```

**✅ ALWAYS:**
```python
# Good: Explicit Pydantic models
from pydantic import BaseModel

class Config(BaseModel):
    key: str
    value: int

# Good: Explicit types
def process(data: Config) -> Result[Output, Error]:
    pass
```

### Error Handling

**❌ NEVER:**
```python
# Bad: try/catch for control flow
try:
    result = risky_operation()
    return result
except Exception:
    return None
```

**✅ ALWAYS:**
```python
# Good: Result<T,E> pattern
from shared.type_definitions.result import Result, Ok, Err

def risky_operation() -> Result[Data, Error]:
    if success:
        return Ok(data)
    return Err(Error("Clear error message"))
```

### Function Design

- **Keep functions under 50 lines**
- **One function, one purpose**
- **Clear, descriptive names**
- **Document public APIs with docstrings**

---

## Testing Requirements

### Test-Driven Development (TDD)

1. **Write failing test first (RED)**:
```python
def test_new_feature():
    result = new_feature()
    assert result.is_ok()  # This will fail initially
```

2. **Implement minimum code (GREEN)**:
```python
def new_feature() -> Result[Data, Error]:
    return Ok(Data())  # Minimal implementation
```

3. **Refactor while maintaining green (REFACTOR)**:
```python
def new_feature() -> Result[Data, Error]:
    # Improved implementation
    data = process_efficiently()
    return Ok(data)
```

### Test Patterns

**AAA Pattern** (Arrange-Act-Assert):
```python
def test_feature():
    # Arrange: Set up test data
    context = create_agent_context()
    input_data = create_test_data()

    # Act: Execute functionality
    result = feature_function(context, input_data)

    # Assert: Verify outcomes
    assert result.is_ok()
    assert result.unwrap().value == expected_value
```

### Running Tests

```bash
# Full suite (always before commit)
python run_tests.py --run-all

# Fast unit tests only
python run_tests.py

# With Docker (Ollama integration)
python run_tests.py --with-docker --run-all
```

**Critical**: MUST use `python run_tests.py` (NOT direct pytest) due to Python 3.13 threading issues

---

## Agent Development

### Agent Factory Pattern

All agents follow a factory pattern:

```python
# agent.py
from shared.agent_context import AgentContext
from agency_swarm import Agent

def create_your_agent(
    context: AgentContext,
    model: str = "gpt-5"
) -> Agent:
    """
    Factory function for YourAgent.

    Args:
        context: Shared agent context with memory systems
        model: LLM model to use (default: gpt-5)

    Returns:
        Configured Agent instance
    """
    return Agent(
        name="YourAgent",
        instructions="Clear role definition...",
        tools=[...],  # Tool assignments
        model=model
    )
```

### Agent Communication

Agents communicate via AgentContext:

```python
from shared.agent_context import AgentContext

# Store information for other agents
context.store_memory(
    "pattern_name",
    {"data": "content"},
    tags=["agent", "pattern"]
)

# Search for relevant information
results = context.search_memories(
    ["pattern", "error_handling"],
    include_session=True
)
```

---

## Tool Development

### Tool Structure

```python
# tools/your_tool.py
from typing import Dict, Any
from shared.type_definitions.result import Result, Ok, Err

def your_tool(
    input_param: str,
    optional_param: int = 10
) -> Result[Dict[str, Any], str]:
    """
    Clear description of tool purpose.

    Args:
        input_param: Description of required parameter
        optional_param: Description of optional parameter

    Returns:
        Result containing output dict or error message

    Example:
        >>> result = your_tool("test")
        >>> assert result.is_ok()
    """
    try:
        # Implementation
        output = {"result": "success"}
        return Ok(output)
    except Exception as e:
        return Err(f"Error: {str(e)}")
```

### Tool Testing

```python
# tests/test_your_tool.py
def test_your_tool_success():
    # Arrange
    input_param = "test_value"

    # Act
    result = your_tool(input_param)

    # Assert
    assert result.is_ok()
    assert result.unwrap()["result"] == "success"

def test_your_tool_error_handling():
    # Arrange
    invalid_input = ""

    # Act
    result = your_tool(invalid_input)

    # Assert
    assert result.is_err()
```

---

## Memory Systems

### Three-Tier Architecture

1. **Anthropic Memory Tool** (Cross-conversation):
```python
context.enable_anthropic_memory()
tool = context.get_anthropic_memory_tool()
tool.create("/memories/agency_backlog/task.md", "TODO: ...")
```

2. **VectorStore** (Institutional learning):
```python
context.store_memory("pattern", data, tags=["type"])
learnings = context.search_memories(["pattern"])
```

3. **Session Context** (Temporary):
```python
context.set_metadata("key", value)
value = context.get_metadata("key")
```

---

## Related Documentation

### For New Contributors
- **[CONTRIBUTING.md](../../CONTRIBUTING.md)** - Contribution guidelines
- **[QUICK_START.md](../../QUICK_START.md)** - 5-minute setup guide
- **[constitution.md](../../constitution.md)** - Governance framework (7 Articles)

### For Development
- **[ARCHITECTURE.md](../ARCHITECTURE.md)** - Technical architecture
- **[ROADMAP.md](../ROADMAP.md)** - Project roadmap
- **[testing/README.md](../testing/README.md)** - Testing guide

### For Advanced Topics
- **[adr/ADR-INDEX.md](../adr/ADR-INDEX.md)** - Architectural Decision Records
- **[LOCAL_MODEL_OPTIMIZATION.md](../LOCAL_MODEL_OPTIMIZATION.md)** - Local Ollama setup

---

## High-Leverage Recommendations

See [HIGH_LEVERAGE_RECOMMENDATIONS.md](HIGH_LEVERAGE_RECOMMENDATIONS.md) for:
- 10x improvement opportunities
- 100x leverage moves
- Strategic optimization paths

---

## Environment Variables

### Core Configuration

```bash
# Required
OPENAI_API_KEY=your_anthropic_key

# Model Selection
AGENCY_MODEL=gpt-5                    # Global default
PLANNER_MODEL=gpt-5                   # Per-agent override
CODER_MODEL=gpt-5
AUDITOR_MODEL=gpt-5

# Memory & Learning (MANDATORY)
USE_ENHANCED_MEMORY=true              # Constitutional requirement (Article IV)

# Local Model Integration (Optional)
USE_LOCAL_MODEL=true                  # Enable Ollama for simple tasks
LOCAL_MODEL_NAME=qwen3-coder:30b      # Model name

# Testing
FORCE_RUN_ALL_TESTS=1                 # Full suite (5,822 tests)
```

---

## Git Worktree Workflow (Advanced)

For parallel autonomous execution without conflicts:

```bash
# Create isolated worktree
git worktree add ../AgencyOS-feature -b feat/your-feature

# Work in isolation
cd ../AgencyOS-feature
# Make changes...

# Commit and push
git add . && git commit -m "feat: Add feature"
git push -u origin feat/your-feature

# Cleanup after merge
cd /path/to/AgencyOS
git worktree remove ../AgencyOS-feature
git worktree prune
```

---

## Common Issues

### Python 3.13 Segfaults
**Solution**: Always use `python run_tests.py` (NOT direct pytest)

### Import Errors (sklearn)
**Solution**: `pip install scikit-learn>=1.0.0`

### CI/CD Blocked
**Status**: External billing issue, use local validation

### Type Violations
**Solution**: Replace `Dict[Any, Any]` with Pydantic models

---

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/subtract0/AgencyOS/issues)
- **Discussions**: [GitHub Discussions](https://github.com/subtract0/AgencyOS/discussions)
- **Documentation**: Start with [README.md](../../README.md)

---

**Last Updated**: 2025-01-30
**Contributors**: See [CONTRIBUTING.md](../../CONTRIBUTING.md)
