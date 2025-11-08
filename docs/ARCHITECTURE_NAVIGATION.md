# Architecture Navigation: Post-Agency-Swarm Pivot

**Status**: ✅ **Pivot COMPLETE but dependency not cleaned up**

---

## What Happened

### The Pivot
You successfully replaced **agency-swarm** (heavy framework) with **LeanAgent** (minimal, direct API):

```
Before: agency_swarm.Agent → ~10,000 lines of framework code
After:  LeanAgent → ~300 lines of direct OpenAI API calls
```

### Files Created (The Real System)
- ✅ `shared/lean_agent.py` - Core lightweight agent (Result pattern, type-safe)
- ✅ `shared/lean_adapter.py` - Backward compatibility for old imports
- ✅ `scripts/autonomous_worker.py` - Updated to use LeanAgent directly

---

## The Problem

### Unfinished Cleanup
1. ❌ **requirements.txt still lists** `git+https://github.com/subtract0/agency-swarm.git@main`
   - This is causing segfaults (threading issues with Python 3.13)
   - Not actually used if LeanAgent is working properly
   
2. ⚠️ **Some tests still import agency-swarm directly** (instead of using adapter)
   - `tests/test_agency.py` - Imports `agency_swarm`
   - `tests/test_planner_agent.py` - Imports `agency_swarm`
   - `tests/fixtures/constitutional_test_agents.py` - Imports `agency_swarm`
   - And others...

### Impact
- ❌ Python crashes when agency-swarm loads (threading bug)
- ❌ Repository claims to use LeanAgent but still depends on broken agency-swarm
- ❌ New installations fail to get private repo `https://github.com/subtract0/agency-swarm.git`

---

## Navigation: What's What

### Your New Architecture (What You Actually Use)

```
shared/
├── lean_agent.py ✅ CORE
│   ├── LeanAgent - Direct OpenAI API, no framework bloat
│   ├── AgentConfig - Type-safe configuration (Pydantic)
│   ├── Tool - Tool definition for function calling
│   └── Message - Thread-safe message history
│
└── lean_adapter.py ✅ COMPATIBILITY LAYER
    ├── Agent - Drop-in replacement for agency_swarm.Agent
    ├── Agency - Single-agent wrapper (minimal)
    └── (Just converts old-style kwargs to LeanAgent config)

scripts/
└── autonomous_worker.py ✅ USES LEAN AGENT DIRECTLY
    └── Agents claim tasks, execute instantly (no hangs)

tests/
├── test_lean_agent.py ✅ Tests the new system
├── test_lean_adapter.py ✅ Tests backward compatibility
└── test_agency.py ❌ Still uses agency_swarm directly
```

---

## The Real Agents (Using Lean System)

These are YOUR actual agents using LeanAgent/adapter:

- `agents/` folder agents (if any) - Check if they use adapter
- `coding_agent/` - Check if upgraded
- `planner_agent/` - Check if upgraded
- `auditor_agent/` - Check if upgraded

**To check if an agent uses LeanAgent**:
```bash
grep -l "from shared.lean" agents/*.py  # Shows migrated agents
grep -l "from agency_swarm" agents/*.py  # Shows old agents
```

---

## What Needs To Happen (Priority Order)

### URGENT (Blocks tests)
1. **Remove agency-swarm from requirements.txt** 
   - Line 2 has git dependency (causes install failure)
   - Replace with comment: `# Replaced with LeanAgent in shared/lean_agent.py`

2. **Verify agents use adapter or LeanAgent directly**
   ```bash
   # Show which agents still import old agency_swarm
   grep -r "from agency_swarm import" agents/
   
   # Update them to:
   # from shared.lean_adapter import Agent  (for compatibility)
   # OR
   # from shared.lean_agent import LeanAgent (for new code)
   ```

### IMPORTANT (Cleanup)
3. **Update tests that import agency_swarm directly**
   - `tests/test_agency.py` → Use adapter
   - `tests/test_planner_agent.py` → Use adapter
   - `tests/fixtures/constitutional_test_agents.py` → Use adapter

4. **Verify autonomous_worker still works** with LeanAgent

### NICE TO HAVE
5. **Document which agents migrated** (PR or ADR)
6. **Remove old agency-swarm imports** once all tests pass
7. **Pin Python 3.12** in `.python-version` file

---

## Quick Diagnosis

```bash
# Check if agency-swarm is ACTUALLY being used
grep -r "from agency_swarm" agents/ tests/ scripts/ --include="*.py" | wc -l

# If > 0: Still using old imports, need to migrate
# If = 0: Successfully migrated (just remove from requirements)

# Check what LeanAgent imports look like
grep -r "from shared.lean" agents/ tests/ --include="*.py"
```

---

## Your Long-Term Memory Integration

The LeanAgent system is designed for:
- ✅ **Single responsibility** - One agent, one task
- ✅ **Shared memory** - Access to VectorStore/Firestore
- ✅ **Result pattern** - Type-safe error handling
- ✅ **Direct orchestration** - No framework overhead
- ✅ **Cost tracking** - Direct API calls = transparent costs

### Example: Agents with Shared Memory
```python
from shared.lean_agent import LeanAgent, AgentConfig
from shared.memory import VectorStore  # Your shared memory

# Agent has access to common long-term memory
agent = LeanAgent(AgentConfig(
    name="coder",
    instructions="You are a coding expert. Check VectorStore for patterns.",
    model="gpt-4o"
))

# Memory is accessed via shared singleton, not framework magic
response = agent.run("Help me refactor this function")
```

---

## Files & Locations (For Reference)

| What | Where | Status |
|------|-------|--------|
| **New agent system** | `shared/lean_agent.py` | ✅ Complete |
| **Compatibility** | `shared/lean_adapter.py` | ✅ Complete |
| **Autonomous worker** | `scripts/autonomous_worker.py` | ✅ Updated |
| **Tests for new system** | `tests/test_lean_agent.py` | ✅ Written |
| **Old framework** | `requirements.txt:2` | ❌ Delete |
| **Your actual agents** | `agents/` | ⚠️ Check if migrated |

---

## Next Steps (What To Do Now)

**STOP RUNNING FULL TEST SUITE** - You have another agent working in the folder.

Instead:
1. **Read** this file
2. **Understand** that your pivot IS working (LeanAgent exists and works)
3. **Assess** which agents still need migration (grep for agency_swarm imports)
4. **Plan** cleanup with main agent (don't conflict)

**Don't interrupt** the other agent's work. Coordinate the cleanup.

---

## Summary

**You successfully pivoted away from agency-swarm ✅**

What remains:
- ❌ Remove agency-swarm from requirements.txt
- ⚠️ Migrate remaining test imports
- ⚠️ Verify all agents use LeanAgent/adapter

The real system is **LeanAgent + Adapter**, living in `shared/`. The old agency-swarm is just cruft left behind.

---

*See LEAN_AGENT_REFACTOR.md for technical deep dive.*
*See test_lean_agent.py for usage examples.*
