# AgentLoader Usage Guide

> Hybrid DSPy/Traditional Agent Instantiation System

## Overview

The `AgentLoader` implements [ADR-007](../adr/ADR-007-dspy-agent-loader-hybrid-architecture.md) to provide a unified interface for loading agents with either DSPy or traditional Python implementations.

**Key Features:**
- ✅ Parse frontmatter from `.claude/agents/*.md` files
- ✅ Automatic DSPy availability detection
- ✅ Graceful fallback to traditional implementations
- ✅ Performance telemetry for A/B comparison
- ✅ Constitutional compliance (Articles I, II, IV, V)

## Basic Usage

### Loading an Agent

```python
from src.agency.agents.loader import AgentLoader

# Initialize the loader
loader = AgentLoader()

# Load an agent from its markdown definition
agent = loader.load_agent(".claude/agents/auditor.md")

# The loader automatically:
# 1. Parses the frontmatter to determine preferred implementation
# 2. Checks if DSPy is available
# 3. Loads preferred implementation or falls back
# 4. Wraps with telemetry if comparison is enabled
```

### Force Specific Implementation

```python
# Force DSPy implementation (will fail if DSPy unavailable)
agent = loader.load_agent(
    ".claude/agents/auditor.md",
    force_implementation="dspy"
)

# Force traditional implementation (always works)
agent = loader.load_agent(
    ".claude/agents/auditor.md",
    force_implementation="traditional"
)
```

### Loading from Parsed Frontmatter

```python
from src.agency.agents.loader import AgentLoader, AgentFrontmatter

loader = AgentLoader()

# Parse frontmatter manually
frontmatter = loader._parse_frontmatter(".claude/agents/auditor.md")
markdown_body = loader._parse_body(".claude/agents/auditor.md")

# Load from parsed data
agent = loader.load_agent_from_frontmatter(frontmatter, markdown_body)
```

## Agent Frontmatter Format

Each agent markdown file should have YAML frontmatter:

```yaml
---
name: agent-name
description: Agent description
implementation:
  traditional: "src/agency/agents/agent_name.py"
  dspy: "src/agency/agents/dspy/agent_name.py"
  preferred: dspy  # or "traditional"
  features:
    dspy:
      - "Adaptive prompting"
      - "Self-tuning thresholds"
    traditional:
      - "Static rule-based logic"
rollout:
  status: gradual
  fallback: traditional  # or "none"
  comparison: true  # Enable telemetry
---

# Agent Markdown Body

Rest of the agent specification...
```

## Telemetry & Performance Comparison

When `comparison: true` is set in frontmatter, agents are wrapped with `TelemetryWrapper`:

```python
from src.agency.agents.loader import AgentLoader

loader = AgentLoader()
agent = loader.load_agent(".claude/agents/auditor.md")

# Execute agent methods (telemetry is automatically collected)
result = agent.execute(task)

# Get performance metrics
if hasattr(agent, 'get_metrics'):
    metrics = agent.get_metrics()
    print(f"Calls: {metrics['call_count']}")
    print(f"Avg Latency: {metrics['avg_latency_ms']:.2f}ms")
    print(f"Error Rate: {metrics['error_rate']:.2%}")
    print(f"Implementation: {metrics['implementation']}")
```

### Metrics Collected

- **call_count**: Number of method invocations
- **error_count**: Number of exceptions raised
- **last_latency_ms**: Latency of most recent call
- **total_latency_ms**: Cumulative latency
- **avg_latency_ms**: Average latency per call
- **error_rate**: Percentage of calls that failed
- **implementation**: "dspy" or "traditional"

## Fallback Behavior

The loader implements multiple fallback layers per **Constitution Article II** (100% Verification):

### Layer 1: DSPy Unavailable
```
Preferred: dspy → DSPy not installed → Load traditional
```

### Layer 2: DSPy Load Failure
```
Preferred: dspy → DSPy load raises exception → Load traditional
```

### Layer 3: Traditional Load Failure
```
All loads fail → Raise LoaderError (with detailed message)
```

## DSPy-Migrated Agents

Five agents currently have DSPy implementations:

1. **auditor** - Adaptive prompting, self-tuning thresholds
2. **code_agent** - Context-aware refactoring, learned test patterns
3. **learning_agent** - Meta-learning, automatic pattern optimization
4. **planner** - Learned task decomposition, adaptive estimation
5. **toolsmith** - API design learning, adaptive test generation

## Advanced Usage

### Checking DSPy Availability

```python
loader = AgentLoader()

if loader._check_dspy_available():
    print("DSPy is available - using enhanced reasoning")
else:
    print("DSPy unavailable - using traditional implementations")
```

### Accessing Loaded Agents Cache

```python
loader = AgentLoader()

# Load agents
auditor = loader.load_agent(".claude/agents/auditor.md")
planner = loader.load_agent(".claude/agents/planner.md")

# Access cached instances
cached_auditor = loader.loaded_agents["auditor"]
cached_planner = loader.loaded_agents["planner"]
```

### Custom Error Handling

```python
from src.agency.agents.loader import AgentLoader, LoaderError

loader = AgentLoader()

try:
    agent = loader.load_agent(".claude/agents/nonexistent.md")
except LoaderError as e:
    print(f"Failed to load agent: {e}")
    # Handle error (log, alert, retry, etc.)
```

## Constitutional Compliance

The loader enforces Agency constitutional requirements:

### Article I: Complete Context Before Action
- ✅ Verifies DSPy availability before attempting load
- ✅ Parses complete frontmatter before proceeding
- ✅ Validates all required fields present

### Article II: 100% Verification and Stability
- ✅ Multiple fallback layers ensure system never fails
- ✅ Traditional implementation always available as backup
- ✅ Comprehensive error messages for debugging

### Article IV: Continuous Learning
- ✅ Telemetry wrapper collects performance data
- ✅ Metrics enable data-driven decisions
- ✅ A/B comparison between implementations

### Article V: Spec-Driven Development
- ✅ Markdown remains source of truth
- ✅ Frontmatter provides structured metadata
- ✅ Agent behavior defined in markdown body

## Error Handling

### Common Errors

#### File Not Found
```python
LoaderError: File not found: /path/to/agent.md
```
**Solution**: Verify agent file path is correct

#### Invalid YAML
```python
LoaderError: Invalid YAML in agent.md: ...
```
**Solution**: Check frontmatter YAML syntax

#### Missing Required Fields
```python
LoaderError: Missing required field(s): implementation, rollout
```
**Solution**: Add missing fields to frontmatter

#### Both Implementations Failed
```python
LoaderError: Failed to load agent 'name': ...
```
**Solution**: Check implementation module paths are correct

## Testing

The loader includes 26 comprehensive tests:

```bash
# Run all loader tests
poetry run pytest tests/test_agent_loader.py -v

# Test specific functionality
poetry run pytest tests/test_agent_loader.py::TestAgentFrontmatterParsing -v
poetry run pytest tests/test_agent_loader.py::TestDSPyAvailabilityChecking -v
poetry run pytest tests/test_agent_loader.py::TestTelemetryWrapper -v

# Test with real agents
poetry run pytest tests/test_agent_loader.py::TestRealAgentLoading -v
```

## Future Enhancements

Planned improvements per ADR-007:

1. **Complete DSPy Implementation Loading**
   - Currently stubs - will implement dynamic module import
   - Full integration with DSPy agent constructors

2. **Complete Traditional Implementation Loading**
   - Dynamic module import from paths
   - Agent constructor parameter passing

3. **Enhanced Telemetry**
   - Persist metrics to Firestore
   - Visualization dashboards
   - Automated A/B test analysis

4. **Remaining Agent Migrations**
   - Migrate 5 additional agents to DSPy
   - Full Agency coverage with hybrid support

## References

- [ADR-007: DSPy Agent Loader](../adr/ADR-007-dspy-agent-loader-hybrid-architecture.md)
- [Agency Constitution](../../constitution.md)
- [Agent Definitions](./.claude/agents/)
- [Loader Implementation](../../src/agency/agents/loader.py)
- [Loader Tests](../../tests/test_agent_loader.py)

---

*Last Updated: 2025-09-30*