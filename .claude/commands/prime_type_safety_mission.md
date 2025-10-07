---
description: Execute Type Safety Implementation Plan (multi-phase, constitutional compliance)
settingSources: [project]
---

## Mission: Implement True Type Safety

Your sole objective is to execute the "Type Safety Implementation Plan." This is a long-term, multi-phase mission to bring the codebase into full constitutional compliance with genuine, verifiable type safety.

### SDK Configuration for Multi-Phase Execution

Type safety implementation spans multiple phases. Use SDK client to maintain session continuity:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Bash", "analyze_type_patterns"],
    permission_mode="acceptEdits",
    max_turns=100  # Long-running mission
)

async with ClaudeSDKClient(options) as client:
    # Phase 1: Setup tooling
    await client.query("Execute Phase 1: Setup mypy and analysis tooling")
    await process_phase_1()

    # Phase 2: Fix violations (continues in same session)
    await client.query("Execute Phase 2: Fix Dict[Any, Any] violations")
    await process_phase_2()

    # ... additional phases
```

## Workflow
1. **Internalize the Plan**: Your first action is to read the full plan document to load the mission parameters into your context.

2. **Begin Phase 1**: Start execution of Phase 1 of the plan, which focuses on setting up the foundational tooling like mypy and the initial analysis.

3. **Report Progress**: Provide regular updates as you complete each major step outlined in the plan.

## Start Context
/read docs/type_safety_implementation_plan.md