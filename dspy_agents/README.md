# DSPy Agents Module

This module contains DSPy-powered implementations of Agency agents that replace static markdown-based agents with adaptive, learning-based reasoning capabilities.

## Configuration

DSPy requires Language Model configuration. The module provides automatic configuration management:

### Environment Variables

```bash
# Required - API Key (one of these)
export OPENAI_API_KEY="your-api-key"
# OR
export ANTHROPIC_API_KEY="your-api-key"

# Optional - Model Selection
export DSPY_MODEL="openai/gpt-4o-mini"  # Default model

# Optional - Agent-specific models
export PLANNER_MODEL="openai/gpt-4o"
export CODER_MODEL="openai/gpt-4o-mini"
export AUDITOR_MODEL="openai/gpt-4o-mini"
export TOOLSMITH_MODEL="openai/gpt-4o-mini"

# Optional - Auto-initialization
export AUTO_INIT_DSPY="true"  # Auto-initialize on import (default: true)
```

### Programmatic Configuration

```python
from dspy_agents.config import DSPyConfig

# Initialize DSPy
DSPyConfig.initialize()

# Configure for specific agent type
from dspy_agents.config import configure_dspy_for_agent
configure_dspy_for_agent("planner")  # Uses PLANNER_MODEL env var
```

## Features

- **Adaptive Reasoning**: Uses DSPy's structured reasoning with Chain of Thought
- **Constitutional Compliance**: Enforces Agency's constitutional principles
- **Learning from Patterns**: Learns from successful and failed executions
- **Graceful Fallback**: Works even when DSPy is not installed
- **Comprehensive Error Handling**: Robust error handling and logging
- **Automatic Configuration**: Auto-configures LM on import when API keys present

## Components

### DSPyCodeAgent

The main code agent implementation that replaces the static AgencyCodeAgent.

**Key Capabilities:**
- Task planning with constitutional constraints
- Code implementation following Agency standards
- Test-driven development enforcement
- Verification and quality checks
- Pattern learning and reuse

**Usage:**
```python
from dspy_agents.modules.code_agent import DSPyCodeAgent

# Create agent
agent = DSPyCodeAgent(model="gpt-4o-mini")

# Execute task
result = agent.forward(
    "Create a user authentication system",
    context={
        "repository_root": "/path/to/repo",
        "session_id": "session_001"
    }
)

# Check results
if result.success:
    print(f"Applied {len(result.changes)} changes")
    print(f"Added {len(result.tests)} tests")
else:
    print(f"Task failed: {result.message}")
```

### Signatures

Structured input/output specifications for agent tasks:

- `CodeTaskSignature`: Main task execution
- `PlanningSignature`: Task planning
- `ImplementationSignature`: Code implementation
- `VerificationSignature`: Quality verification
- And many more...

### Fallback Support

When DSPy is not installed, the module gracefully falls back to basic implementations that still follow Agency constitutional principles.

## Installation

For full DSPy functionality, install the requirements:

```bash
pip install -r requirements-dspy.txt
```

The module will work in fallback mode without DSPy installed.

## Constitutional Principles

The DSPyCodeAgent enforces Agency's constitutional principles:

1. **TDD is Mandatory** - Write tests before implementation
2. **Strict Typing Always** - Use concrete types, avoid Any
3. **Validate All Inputs** - Use proper validation schemas
4. **Use Repository Pattern** - Database queries through repositories
5. **Functional Error Handling** - Use Result<T, E> pattern
6. **Standardize API Responses** - Follow project format
7. **Clarity Over Cleverness** - Write simple, readable code
8. **Focused Functions** - Keep functions under 50 lines
9. **Document Public APIs** - Use clear documentation
10. **Lint Before Commit** - Run linting tools

## Learning System

The agent learns from:
- Successful task executions
- Failed attempts and their causes
- Patterns in code changes
- Quality metrics and feedback

This enables continuous improvement and adaptation to project-specific patterns.

## Integration

The DSPyCodeAgent is designed to be a drop-in replacement for the existing AgencyCodeAgent while providing enhanced capabilities when DSPy is available.