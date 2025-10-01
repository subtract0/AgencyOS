# Cost Tracking Integration Guide

## Overview

This document describes how to integrate real LLM cost tracking into Agency agents using the Trinity Protocol CostTracker system.

## Architecture

### CostTracker API

The `CostTracker` class (`trinity_protocol/cost_tracker.py`) provides:

- **Real-time cost tracking** for LLM API calls
- **Per-agent cost breakdowns**
- **Per-task cost attribution**
- **Model tier-based pricing** (Local, Cloud Mini, Cloud Standard, Cloud Premium)
- **SQLite persistence** for historical cost data
- **Dashboard visualization** with export to JSON/CSV

### Model Tiers

```python
from trinity_protocol.cost_tracker import ModelTier

ModelTier.LOCAL           # Free (Ollama) - $0
ModelTier.CLOUD_MINI      # GPT-4o-mini, Claude Haiku - $0.00015/$0.0006 per 1K tokens
ModelTier.CLOUD_STANDARD  # GPT-4, Claude Sonnet - $0.0025/$0.01 per 1K tokens
ModelTier.CLOUD_PREMIUM   # GPT-5, Claude Opus - $0.005/$0.015 per 1K tokens
```

### Current Implementation Status

**Phase 1: Infrastructure Wiring** ✅ COMPLETE

All agent factories now accept and store `cost_tracker`:
- `create_agency_code_agent()` ✅
- `create_test_generator_agent()` ✅
- `create_toolsmith_agent()` ✅
- `create_quality_enforcer_agent()` ✅
- `create_merger_agent()` ✅
- `create_work_completion_summary_agent()` ✅
- EXECUTOR passes cost_tracker to all sub-agents ✅

**Phase 2: LLM Call Wrapping** 🚧 PENDING

Agents need to wrap their LLM calls to report actual token usage.

## Phase 2: Wrapping LLM Calls

### Pattern for Agent Integration

Each agent should wrap LLM calls with cost tracking:

```python
import time
from trinity_protocol.cost_tracker import ModelTier

# Inside agent execution logic:
def execute_with_cost_tracking(self, task_prompt: str, task_id: str, correlation_id: str):
    """Execute LLM call with cost tracking."""

    # Get cost_tracker from agent context (stored during factory creation)
    cost_tracker = getattr(self.agent_context, 'cost_tracker', None)

    if cost_tracker is None:
        # Fallback: execute without tracking
        return self._llm_generate(task_prompt)

    # Track execution time
    start_time = time.time()

    try:
        # Execute LLM call
        response = self._llm_generate(task_prompt)

        # Determine model tier based on model name
        model_tier = determine_tier(self.model_name)

        # Extract token counts from response
        input_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') else 0
        output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') else 0

        # Track successful call
        cost_tracker.track_call(
            agent=self.__class__.__name__,
            model=self.model_name,
            model_tier=model_tier,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_seconds=time.time() - start_time,
            success=True,
            task_id=task_id,
            correlation_id=correlation_id
        )

        return response

    except Exception as e:
        # Track failed call
        cost_tracker.track_call(
            agent=self.__class__.__name__,
            model=self.model_name,
            model_tier=ModelTier.CLOUD_STANDARD,  # Assume standard tier on error
            input_tokens=0,
            output_tokens=0,
            duration_seconds=time.time() - start_time,
            success=False,
            task_id=task_id,
            correlation_id=correlation_id
        )
        raise


def determine_tier(model_name: str) -> ModelTier:
    """Map model name to pricing tier."""
    model_lower = model_name.lower()

    if 'ollama' in model_lower or 'local' in model_lower:
        return ModelTier.LOCAL
    elif 'mini' in model_lower or 'haiku' in model_lower or 'nano' in model_lower:
        return ModelTier.CLOUD_MINI
    elif 'gpt-5' in model_lower or 'opus' in model_lower or 'o1' in model_lower:
        return ModelTier.CLOUD_PREMIUM
    else:
        return ModelTier.CLOUD_STANDARD
```

### Integration Points by Agent

#### 1. AgencyCodeAgent
**Files to modify:**
- Main LLM calls in agent execution loop
- Tool invocations that use LLM

**Wrapper location:** Before `agent.run()` or during tool execution

#### 2. TestGeneratorAgent
**Files to modify:**
- `GenerateTests.run()` method where LLM analysis occurs
- Test code generation calls

**Wrapper location:** In `GenerateTests` tool execution

#### 3. ToolsmithAgent
**Files to modify:**
- Tool scaffolding logic
- Test generation for new tools

**Wrapper location:** Main agent execution flow

#### 4. QualityEnforcerAgent
**Files to modify:**
- Constitutional check LLM calls
- Quality analysis prompts
- Auto-fix suggestion generation

**Wrapper location:** `ConstitutionalCheck`, `QualityAnalysis`, `AutoFixSuggestion` tools

#### 5. MergerAgent
**Files to modify:**
- Pre-merge validation logic
- Commit message generation (if LLM-based)

**Wrapper location:** Merge orchestration flow

#### 6. WorkCompletionSummaryAgent
**Files to modify:**
- `RegenerateWithGpt5` tool (already has some tracking structure)
- Summary generation calls

**Wrapper location:** `RegenerateWithGpt5.run()` method

### Agency Swarm Integration

For `agency-swarm` agents, wrap the agent's `run()` method or tool invocations:

```python
from agency_swarm import Agent

class CostTrackedAgent(Agent):
    """Agent wrapper with cost tracking."""

    def __init__(self, *args, cost_tracker=None, agent_context=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cost_tracker = cost_tracker
        self.agent_context = agent_context

    def run(self, message: str, task_id: str = None, correlation_id: str = None):
        """Override run() to add cost tracking."""

        if self.cost_tracker is None:
            return super().run(message)

        start_time = time.time()

        try:
            response = super().run(message)

            # Extract tokens (agency-swarm may expose this via response metadata)
            # This is framework-specific
            input_tokens = getattr(response, 'input_tokens', len(message) // 4)  # Fallback estimate
            output_tokens = getattr(response, 'output_tokens', len(str(response)) // 4)

            self.cost_tracker.track_call(
                agent=self.name,
                model=self.model,
                model_tier=determine_tier(self.model),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_seconds=time.time() - start_time,
                success=True,
                task_id=task_id,
                correlation_id=correlation_id
            )

            return response

        except Exception as e:
            self.cost_tracker.track_call(
                agent=self.name,
                model=self.model,
                model_tier=ModelTier.CLOUD_STANDARD,
                input_tokens=0,
                output_tokens=0,
                duration_seconds=time.time() - start_time,
                success=False,
                task_id=task_id,
                correlation_id=correlation_id
            )
            raise
```

## EXECUTOR Integration

The EXECUTOR already has cost tracking wired in `_execute_sub_agent()` method:

```python
# trinity_protocol/executor_agent.py lines 325-357

# Estimates token usage (Phase 2 will use actual values)
estimated_input_tokens = len(task_prompt) // 4
estimated_output_tokens = len(response) // 4

# Tracks cost for each sub-agent execution
llm_call = self.cost_tracker.track_call(
    agent=agent_name,
    model=model_name,
    model_tier=model_tier,
    input_tokens=estimated_input_tokens,
    output_tokens=estimated_output_tokens,
    duration_seconds=duration_seconds,
    success=True,
    task_id=task_id,
    correlation_id=correlation_id
)
```

**Phase 2 Task:** Replace estimates with actual token counts from agent responses.

## Dashboard Usage

Once LLM calls are wrapped, the dashboard will show real costs:

```python
# In EXECUTOR or any component with cost_tracker:
executor.print_cost_dashboard()

# Or access programmatically:
summary = executor.cost_tracker.get_summary()
print(f"Total cost: ${summary.total_cost_usd:.4f}")
print(f"By agent: {summary.by_agent}")
print(f"By model: {summary.by_model}")
```

## Testing Cost Tracking

```python
# Test with in-memory database
from trinity_protocol.cost_tracker import CostTracker, ModelTier

tracker = CostTracker(db_path=":memory:")

# Simulate LLM call
tracker.track_call(
    agent="TestAgent",
    model="gpt-5",
    model_tier=ModelTier.CLOUD_PREMIUM,
    input_tokens=1000,
    output_tokens=500,
    duration_seconds=2.5,
    success=True,
    task_id="test-123",
    correlation_id="corr-456"
)

# Verify tracking
summary = tracker.get_summary()
assert summary.total_cost_usd > 0
assert "TestAgent" in summary.by_agent
```

## Next Steps (Phase 2)

1. **Identify LLM call sites** in each agent's codebase
2. **Extract actual token counts** from LLM responses (framework-specific)
3. **Wrap calls** with cost tracking pattern
4. **Test** that costs appear in dashboard
5. **Validate** cost accuracy against OpenAI/Anthropic billing

## Constitutional Compliance

This work supports:
- **Article IV (Continuous Learning):** Cost data informs optimization decisions
- **Article I (Complete Context):** Full visibility into resource usage
- **Article II (100% Verification):** Accurate cost tracking for budget enforcement

## References

- CostTracker implementation: `/Users/am/Code/Agency/trinity_protocol/cost_tracker.py`
- EXECUTOR integration: `/Users/am/Code/Agency/trinity_protocol/executor_agent.py`
- Agent factories: `agency_code_agent/`, `test_generator_agent/`, etc.
