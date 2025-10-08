---
description: Activate autonomous self-healing protocols (NoneType auto-fix, patching)
settingSources: [project]
---

## Mission: Autonomous Self-Healing

Your context is now focused on activating and managing the autonomous self-healing functions of the system.

### SDK Configuration for Long-Running Healing

Healing operations may take time. Use SDK client for continuous session:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Edit", "Bash", "constitution_check"],
    permission_mode="acceptEdits",  # Auto-apply healing fixes
    max_turns=50  # Allow extended healing cycles
)

async with ClaudeSDKClient(options) as client:
    # Continuous healing loop
    await client.query("Run constitutional audit and auto-heal violations")

    async for message in client.receive_messages():
        if message.type == "result":
            # Healing complete
            break
        # Stream progress updates
        print(message)
```

### Workflow
1. **Check System Status:** Run `./agency_cli health` to determine current health state.
2. **Analyze Telemetry:** Call `/agent learning_agent` with focus on telemetry pattern analysis.
3. **Identify Errors:** Use `core/self_healing.py` to detect current issues.
4. **Healing Process:** Call `/agent quality_enforcer` to fix identified problems.
5. **Verification:** Run `python run_tests.py --run-all` - 100% success rate required.
6. **Learn Patterns:** Store successful healing patterns for future application.

### Start Context
- `/read constitution.md`
- `/read core/self_healing.py`
- `/read core/telemetry.py`
- `/read core/patterns.py`

### Activated Feature Flags
```bash
export ENABLE_UNIFIED_CORE=true
export PERSIST_PATTERNS=true
```