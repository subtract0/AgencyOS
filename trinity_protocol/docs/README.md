# Trinity Protocol Documentation

## Overview

Trinity Protocol is a three-layer agentic system implementing Constitutional AI principles with real-time cost tracking and autonomous orchestration.

## Architecture Layers

### 1. Cognition Layer - ARCHITECT Agent
**Purpose:** Strategic planning and task decomposition

- Analyzes user goals and creates task graphs
- Publishes tasks to `execution_queue`
- Monitors telemetry for feedback

### 2. Action Layer - EXECUTOR Agent
**Purpose:** Task execution and verification

- Subscribes to `execution_queue`
- Delegates to specialized sub-agents
- Enforces Constitutional Article II (100% test verification)
- Tracks real-time costs via CostTracker

### 3. Observation Layer - OBSERVER Agent
**Purpose:** Monitoring and analysis

- Subscribes to `telemetry_stream`
- Provides real-time dashboard
- Exports data for analysis

## Documentation Index

### Core Systems

- **[Cost Dashboard Guide](COST_DASHBOARD_GUIDE.md)** - **⭐ NEW** - Complete guide to terminal, web, and alert dashboards
- **[Cost Tracking Integration](cost_tracking_integration.md)** - Complete guide to LLM cost tracking infrastructure
- **[Cost Tracking Wiring Complete](COST_TRACKING_WIRING_COMPLETE.md)** - Phase 1 completion status and Phase 2 roadmap

### Component Documentation

- **Message Bus** (`trinity_protocol/message_bus.py`) - Pub/sub system for inter-agent communication
- **Cost Tracker** (`trinity_protocol/cost_tracker.py`) - Real-time LLM cost tracking with SQLite persistence
- **ARCHITECT Agent** (`trinity_protocol/architect_agent.py`) - Cognition layer implementation
- **EXECUTOR Agent** (`trinity_protocol/executor_agent.py`) - Action layer implementation
- **OBSERVER Agent** (`trinity_protocol/observer_agent.py`) - Observation layer implementation

### Verification

- **Verification Script** (`trinity_protocol/verify_cost_tracking.py`) - Automated infrastructure testing

## Quick Start

### Running Trinity Protocol

```python
import asyncio
from trinity_protocol.message_bus import MessageBus
from trinity_protocol.cost_tracker import CostTracker
from trinity_protocol.architect_agent import ArchitectAgent
from trinity_protocol.executor_agent import ExecutorAgent
from trinity_protocol.observer_agent import ObserverAgent
from shared.agent_context import create_agent_context

async def main():
    # Initialize infrastructure
    message_bus = MessageBus()
    cost_tracker = CostTracker(db_path="trinity_costs.db", budget_usd=100.0)
    agent_context = create_agent_context()

    # Create agents
    architect = ArchitectAgent(
        message_bus=message_bus,
        cost_tracker=cost_tracker
    )

    executor = ExecutorAgent(
        message_bus=message_bus,
        cost_tracker=cost_tracker,
        agent_context=agent_context
    )

    observer = ObserverAgent(
        message_bus=message_bus,
        cost_tracker=cost_tracker
    )

    # Run system
    await asyncio.gather(
        architect.run(),
        executor.run(),
        observer.run()
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### Cost Dashboard

Trinity Protocol includes three powerful dashboards for monitoring LLM costs:

#### 1. Terminal Dashboard (Live Updates)
```bash
# Real-time curses-based dashboard
python trinity_protocol/dashboard_cli.py terminal --live

# With custom refresh interval (10 seconds)
python trinity_protocol/dashboard_cli.py terminal --live --interval 10
```

#### 2. Web Dashboard (Browser-Based)
```bash
# Start web server on port 8080
python trinity_protocol/dashboard_cli.py web --port 8080

# Then open http://localhost:8080 in browser
```

#### 3. Cost Alerts (Automated Monitoring)
```bash
# Continuous monitoring with alerts
python trinity_protocol/dashboard_cli.py alerts --continuous --budget 10.0 --hourly-max 1.0

# Single check
python trinity_protocol/dashboard_cli.py alerts --budget 10.0
```

#### Quick Snapshot & Export
```bash
# Print snapshot to console
python trinity_protocol/dashboard_cli.py snapshot

# Export to CSV and JSON
python trinity_protocol/dashboard_cli.py export
```

#### Programmatic Access
```python
# Get cost summary
summary = cost_tracker.get_summary()
print(f"Total cost: ${summary.total_cost_usd:.4f}")
print(f"By agent: {summary.by_agent}")

# Export data
cost_tracker.export_json("costs.json")
```

See **[Cost Dashboard Guide](COST_DASHBOARD_GUIDE.md)** for complete documentation.

## Integration Status

### Phase 1: Infrastructure Wiring ✅ COMPLETE

All Agency sub-agents accept and store `cost_tracker`:

- ✅ AgencyCodeAgent
- ✅ TestGeneratorAgent
- ✅ ToolsmithAgent
- ✅ QualityEnforcerAgent
- ✅ MergerAgent
- ✅ WorkCompletionSummaryAgent

EXECUTOR passes cost_tracker to all sub-agents automatically.

### Phase 2: LLM Call Wrapping 🚧 PENDING

See [Cost Tracking Integration Guide](cost_tracking_integration.md) for:
- Wrapping patterns for each agent
- Token extraction from LLM responses
- Integration examples

## Constitutional Compliance

Trinity Protocol enforces Agency OS constitution:

**Article I: Complete Context Before Action**
- Retry mechanisms with exponential backoff
- Full message bus persistence

**Article II: 100% Verification and Stability**
- EXECUTOR runs full test suite after every task
- No merge without 100% pass rate

**Article III: Automated Merge Enforcement**
- Zero manual overrides
- Quality gates are absolute

**Article IV: Continuous Learning and Improvement**
- Cost data feeds optimization decisions
- Telemetry enables pattern analysis

**Article V: Spec-Driven Development**
- All tasks trace to specifications
- Plans externalized to `/tmp/executor_plans/`

## Testing

### Verify Infrastructure

```bash
# Test cost tracking wiring
python trinity_protocol/verify_cost_tracking.py

# Expected output:
# ✅ All verification tests passed!
# Total: 6 | Passed: 6 | Failed: 0
```

### Run Integration Demo

```bash
# Full Trinity Protocol demo
python trinity_protocol/trinity_demo.py

# Watch dashboard in real-time:
# - Task processing
# - Cost accumulation
# - Agent coordination
```

## Model Pricing Tiers

```python
from trinity_protocol.cost_tracker import ModelTier

# Pricing per 1K tokens (input/output)
ModelTier.LOCAL           # $0.00 / $0.00
ModelTier.CLOUD_MINI      # $0.00015 / $0.0006
ModelTier.CLOUD_STANDARD  # $0.0025 / $0.01
ModelTier.CLOUD_PREMIUM   # $0.005 / $0.015
```

## Architecture Diagram

```
User Goal
    ↓
ARCHITECT (Cognition)
    ↓
execution_queue (MessageBus)
    ↓
EXECUTOR (Action)
    ├─→ AgencyCodeAgent ────→ CostTracker
    ├─→ TestGeneratorAgent ──→ CostTracker
    ├─→ ToolsmithAgent ──────→ CostTracker
    ├─→ QualityEnforcerAgent → CostTracker
    ├─→ MergerAgent ─────────→ CostTracker
    └─→ WorkCompletionSummaryAgent → CostTracker
    ↓
telemetry_stream (MessageBus)
    ↓
OBSERVER (Observation)
    └─→ Dashboard / Export
```

## Message Flow

```
1. ARCHITECT receives user goal
2. ARCHITECT creates task graph
3. ARCHITECT publishes to execution_queue
4. EXECUTOR subscribes to execution_queue
5. EXECUTOR delegates to sub-agents (parallel execution)
6. Sub-agents track LLM costs via CostTracker
7. EXECUTOR runs absolute verification (Article II)
8. EXECUTOR publishes to telemetry_stream
9. OBSERVER subscribes to telemetry_stream
10. OBSERVER updates dashboard
```

## File Structure

```
trinity_protocol/
├── architect_agent.py          # Cognition layer
├── executor_agent.py           # Action layer (sub-agent orchestration)
├── observer_agent.py           # Observation layer
├── message_bus.py              # Pub/sub messaging
├── cost_tracker.py             # LLM cost tracking
├── trinity_demo.py             # Integration demo
├── verify_cost_tracking.py     # Infrastructure tests
├── docs/
│   ├── README.md               # This file
│   ├── cost_tracking_integration.md
│   └── COST_TRACKING_WIRING_COMPLETE.md
└── trinity_costs.db            # SQLite cost database
```

## Sub-Agent Registry

EXECUTOR manages 6 specialized Agency agents:

| Agent | Purpose | Model | Tier |
|-------|---------|-------|------|
| CodeWriter | Implementation | gpt-5 | Premium |
| TestArchitect | Test generation | gpt-5 | Premium |
| ToolDeveloper | Tool creation | gpt-5 | Premium |
| ImmunityEnforcer | Quality checks | gpt-5 | Premium |
| ReleaseManager | Merge operations | gpt-5 | Premium |
| TaskSummarizer | Summaries | gpt-5-nano | Mini |

## Next Steps

1. **Implement Phase 2** - Wrap LLM calls in each agent to report actual token usage
2. ✅ **Cost Dashboard** - Terminal, web, and alert dashboards now available
3. **Optimize model selection** - Use cost data to inform agent model choices
4. **Learning integration** - Feed cost patterns to LearningAgent
5. **24-hour autonomous test** - Validate cost tracking under continuous operation

## References

- **Agency OS Constitution:** `/Users/am/Code/Agency/constitution.md`
- **ADR Index:** `/Users/am/Code/Agency/docs/adr/ADR-INDEX.md`
- **Trinity Week 6 Spec:** Previous implementation notes

---

**Last Updated:** 2025-10-01
**Status:** Phase 1 Complete ✅
**Next:** Phase 2 - LLM Call Wrapping
